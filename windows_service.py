import sys
import json
import time
import logging
import threading
import schedule
from datetime import datetime
import os

import win32serviceutil
import win32service
import win32event
import servicemanager

from config.settings_loader import SettingsLoader
from log_config import LogConfig
from scanners.scanner_manager import ScannerManager
from ai.gemini_classifier import GeminiClassifier
from core.deduplication_engine import DeduplicationEngine
from exports.csv_exporter import CSVExporter


# ─── Settings Load (settings.json) ─────────────────────────────────
def load_settings():
    return SettingsLoader()


# ─── Core Scan Logic ────────────────────────────────────────────────
def run_scan():
    settings = load_settings()
    log_manager = LogConfig(settings)
    logger_dict = log_manager.setup_logging()

    app_log = logger_dict["application"]
    scanner_log = logger_dict["scanner"]
    ai_log = logger_dict["ai_processing"]

    GEMINI_API_KEY = settings.get_api_key()

    app_log.info(f"Scan started at {datetime.now()}")

    try:
        # Step 1: Scan
        manager = ScannerManager()
        scanner_log.info("All scanners starting...")
        results = manager.run_all_scans()
        scanner_log.info("All scanners completed")

        # Step 2: Deduplicate
        dedup_engine = DeduplicationEngine()
        clean_apps = dedup_engine.deduplicate(results)
        app_log.info(f"Deduplication: {len(clean_apps)} unique apps")

        # Step 3: AI Classify
        classifier = GeminiClassifier(GEMINI_API_KEY)
        ai_log.info("Classification starting")
        if classifier.check_internet():
            ai_clean_apps = classifier.deduplicate_apps(clean_apps)
            classified_apps = classifier.classify_apps(ai_clean_apps)
            ai_log.info(f"Classification complete: {len(classified_apps)} apps")
        else:
            ai_log.warning("No internet — skipping AI classification")
            classified_apps = clean_apps

        # Step 4: Export CSV
        exporter = CSVExporter(output_dir=settings.get_export_path())
        export_path = exporter.export(classified_apps, filename="Software_Inventory.csv")

        app_log.info(f"Scan complete. CSV exported successfully")

    except Exception as e:
        app_log.error(f"Scan error: {e}")


# ─── Windows Service Class ──────────────────────────────────────────
class AppDiscoveryService(win32serviceutil.ServiceFramework):
    _svc_name_ = "AppDiscoveryService"
    _svc_display_name_ = "Application Discovery Service"
    _svc_description_ = "Scans installed applications and exports to CSV automatically."

    def __init__(self, args):
        win32serviceutil.ServiceFramework.__init__(self, args)
        self.stop_event = win32event.CreateEvent(None, 0, 0, None)
        self.running = True

        logging.basicConfig(
            filename="service.log",
            level=logging.INFO,
            format="%(asctime)s - %(levelname)s - %(message)s"
        )

    def SvcStop(self):
        self.ReportServiceStatus(win32service.SERVICE_STOP_PENDING)
        win32event.SetEvent(self.stop_event)
        self.running = False
        logging.info("Service stopping...")

    def SvcDoRun(self):
        servicemanager.LogMsg(
            servicemanager.EVENTLOG_INFORMATION_TYPE,
            servicemanager.PYS_SERVICE_STARTED,
            (self._svc_name_, '')
        )
        logging.info("AppDiscovery Service started")
        self._run_scheduler()

    def _run_scheduler(self):
        settings = load_settings()
        scan_time = settings.get_scan_time()

        logging.info(f"Scheduler: daily CSV export at {scan_time}")
        print(f"[SCHEDULER] Service running. Daily CSV export time: {scan_time}")

        schedule.every().day.at(scan_time).do(self._run_scan_thread)

        while self.running:
            schedule.run_pending()
            if win32event.WaitForSingleObject(self.stop_event, 30000) == win32event.WAIT_OBJECT_0:
                break

    def _run_scan_thread(self):
        thread = threading.Thread(target=run_scan, daemon=True)
        thread.start()


# ─── Entry Point ────────────────────────────────────────────────────
if __name__ == '__main__':
    if len(sys.argv) == 1:
        servicemanager.Initialize()
        servicemanager.PrepareToHostSingle(AppDiscoveryService)
        servicemanager.StartServiceCtrlDispatcher()
    elif '--scan-now' in sys.argv:
        print("=" * 50)
        print(" Manual Scan Triggered")
        print("=" * 50)
        run_scan()
    else:
        win32serviceutil.HandleCommandLine(AppDiscoveryService)