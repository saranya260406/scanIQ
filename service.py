import win32serviceutil
import win32service
import win32event
import servicemanager
import sys
import os
import logging
import threading

# Project path
PROJECT_PATH = r"C:\Users\SARANYA\OneDrive\Documents\ApplicationDiscoveryProject"

sys.path.insert(0, PROJECT_PATH)

from dotenv import load_dotenv
load_dotenv(os.path.join(PROJECT_PATH, ".env"))

from scanners.scanner_manager import ScannerManager
from ai.gemini_classifier import GeminiClassifier
from core.deduplication_engine import DeduplicationEngine
from exports.csv_exporter import CSVExporter
from config.settings_loader import SettingsLoader
from log_config import LogConfig
from scheduler_utils import start_scheduler
from realtime_watcher import FileWatchHandler, get_all_drives

try:
    from watchdog.observers import Observer
except ImportError:
    Observer = None


class ScanIQService(win32serviceutil.ServiceFramework):

    _svc_name_ = "scanIQ"
    _svc_display_name_ = "scanIQ"
    _svc_description_ = "ScanIQ - Windows Application Discovery Tool"

    def __init__(self, args):
        win32serviceutil.ServiceFramework.__init__(self, args)
        self.hWaitStop = win32event.CreateEvent(None, 0, 0, None)
        self.running = True
        self.observer = None

        logging.basicConfig(
            filename=os.path.join(PROJECT_PATH, "service.log"),
            level=logging.INFO,
            format="%(asctime)s - %(levelname)s - %(message)s"
        )
        self.logger = logging.getLogger("ScanIQService")

    def SvcStop(self):
        self.logger.info("Service stop requested")
        self.ReportServiceStatus(win32service.SERVICE_STOP_PENDING)
        win32event.SetEvent(self.hWaitStop)
        self.running = False
        if self.observer:
            self.observer.stop()

    def SvcDoRun(self):
        self.logger.info("ScanIQ Service started")
        servicemanager.LogMsg(
            servicemanager.EVENTLOG_INFORMATION_TYPE,
            servicemanager.PYS_SERVICE_STARTED,
            (self._svc_name_, "")
        )
        self.main()

    def main(self):
        try:
            os.chdir(PROJECT_PATH)

            settings = SettingsLoader()
            log_manager = LogConfig(settings)
            logger_dict = log_manager.setup_logging()

            app_log = logger_dict["application"]
            scanner_log = logger_dict["scanner"]
            ai_log = logger_dict["ai_processing"]

            GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

            # =========================
            # REALTIME WATCHER START
            # =========================
            if Observer:
                self.observer = Observer()
                handler = FileWatchHandler()
                for drive in get_all_drives():
                    try:
                        self.observer.schedule(handler, drive, recursive=True)
                    except Exception as e:
                        self.logger.error(f"Could not watch {drive}: {e}")
                self.observer.start()
                app_log.info("RealTime Watcher started")
            else:
                app_log.warning("watchdog not installed - RealTime Watcher skipped")

            # =========================
            # PIPELINE RUN
            # =========================
            mode = (
                settings.get_mode()
                if hasattr(settings, "get_mode")
                else "manual"
            )

            if mode.lower() == "schedule":
                app_log.info("Service: Running in scheduled mode")
                start_scheduler(
                    settings,
                    lambda: self._run_pipeline(
                        app_log, scanner_log, ai_log,
                        settings, GEMINI_API_KEY
                    )
                )
                win32event.WaitForSingleObject(self.hWaitStop, win32event.INFINITE)
            else:
                app_log.info("Service: Running in manual mode")
                # Pipeline thread-ல் run பண்ணு — watcher background-ல் இருக்கும்
                pipeline_thread = threading.Thread(
                    target=self._run_pipeline,
                    args=(app_log, scanner_log, ai_log, settings, GEMINI_API_KEY),
                    daemon=True
                )
                pipeline_thread.start()
                # Watcher running-ஆ இருக்கும் வரை wait பண்ணு
                win32event.WaitForSingleObject(self.hWaitStop, win32event.INFINITE)

            if self.observer:
                self.observer.join()

        except Exception as e:
            self.logger.error(f"Service error: {e}")

    def _run_pipeline(self, app_log, scanner_log, ai_log, settings, GEMINI_API_KEY):
        try:
            app_log.info("Pipeline started from service")

            manager = ScannerManager()
            results = manager.run_all_scans()
            scanner_log.info("Scanning completed")

            dedup_engine = DeduplicationEngine()
            clean_apps = dedup_engine.deduplicate(results)

            classifier = GeminiClassifier(GEMINI_API_KEY)

            if classifier.check_internet():
                ai_clean_apps = classifier.deduplicate_apps(clean_apps)
                classified_apps = classifier.classify_apps(ai_clean_apps)
                ai_log.info("AI classification done")
            else:
                classified_apps = clean_apps
                ai_log.warning("Offline mode - skipping AI")

            exporter = CSVExporter(output_dir=settings.get_export_path())
            export_path = exporter.export(classified_apps, filename="Software_Inventory.csv")

            app_log.info(f"Export done: {export_path}")

        except Exception as e:
            app_log.error(f"Pipeline error: {e}")


if __name__ == "__main__":
    if len(sys.argv) == 1:
        servicemanager.Initialize()
        servicemanager.PrepareToHostSingle(ScanIQService)
        servicemanager.StartServiceCtrlDispatcher()
    else:
        win32serviceutil.HandleCommandLine(ScanIQService)
    