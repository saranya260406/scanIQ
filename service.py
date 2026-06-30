import win32serviceutil
import win32service
import win32event
import servicemanager
import sys
import os
import logging
import threading

# Dynamic path
if getattr(sys, 'frozen', False):
    PROJECT_PATH = os.path.dirname(sys.executable)
else:
    PROJECT_PATH = os.path.dirname(os.path.abspath(__file__))

sys.path.insert(0, PROJECT_PATH)

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
        self.stop_event = threading.Event()

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
        self.stop_event.set()
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

            GEMINI_API_KEY = settings.get_api_key()

            # RealTime Watcher
            if Observer:
                self.observer = Observer()
                handler = FileWatchHandler(
                    scan_callback=lambda detected_file=None: self._run_pipeline(
                        app_log, scanner_log, ai_log, settings, GEMINI_API_KEY,
                        detected_file=detected_file
                    )
                )
                for drive in get_all_drives():
                    try:
                        self.observer.schedule(handler, drive, recursive=True)
                    except Exception as e:
                        self.logger.error(f"Could not watch {drive}: {e}")
                self.observer.start()
                app_log.info("RealTime Watcher started")
            else:
                app_log.warning("watchdog not installed - RealTime Watcher skipped")

            # Pipeline
            mode = (
                settings.get_mode()
                if hasattr(settings, "get_mode")
                else "manual"
            )

            if mode.lower() == "scheduled":
                app_log.info("Service: Running in scheduled mode")

                start_scheduler(
                    settings,
                    lambda: self._run_pipeline(
                        app_log, scanner_log, ai_log,
                        settings, GEMINI_API_KEY
                    ),
                    self.stop_event
                )

                win32event.WaitForSingleObject(self.hWaitStop, win32event.INFINITE)

            else:
                app_log.info("Service: Running in manual mode")
                pipeline_thread = threading.Thread(
                    target=self._run_pipeline,
                    args=(app_log, scanner_log, ai_log, settings, GEMINI_API_KEY),
                    daemon=True
                )
                pipeline_thread.start()
                win32event.WaitForSingleObject(self.hWaitStop, win32event.INFINITE)

            if self.observer:
                self.observer.join()

        except Exception as e:
            self.logger.error(f"Service error: {e}")

    def _run_pipeline(self, app_log, scanner_log, ai_log, settings, GEMINI_API_KEY, detected_file=None):
        try:
            app_log.info("Pipeline started from service")

            manager = ScannerManager()
            results = manager.run_all_scans()
            scanner_log.info("Scanning completed")

            dedup_engine = DeduplicationEngine()
            clean_apps = dedup_engine.deduplicate(results)
            app_log.info(f"Dedup completed - Unique apps: {len(clean_apps)}")

            classifier = GeminiClassifier(GEMINI_API_KEY)

            if classifier.check_internet():
                ai_log.info("AI Mode: Online (Gemini enabled)")

                ai_clean_apps = classifier.deduplicate_apps(clean_apps)
                ai_log.info(f"AI Dedup complete: {len(ai_clean_apps)} apps")

                classified_apps = classifier.classify_apps(ai_clean_apps)
                ai_log.info("AI classification done")
            else:
                classified_apps = clean_apps
                ai_log.warning("Offline mode - skipping AI")

            # RealTime Watcher trigger pannina file irundha,
            # automatic-ah ஒரு extra row-ah CSV-la add pannrom
            if detected_file:
                already_present = any(
                    (app.get('name') or '').strip().lower() ==
                    detected_file['name'].strip().lower()
                    for app in classified_apps
                )
                if not already_present:
                    classified_apps.append({
                        'name': detected_file['name'],
                        'publisher': 'Unknown',
                        'version': 'Unknown',
                        'install_date': detected_file.get('detected_date', ''),
                        'install_location': detected_file.get('path', 'Unknown'),
                        'size_mb': detected_file.get('size_mb'),
                        'source': 'RealTimeDownload',
                    })
                    app_log.info(f"Added detected file to CSV: {detected_file['name']}")

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