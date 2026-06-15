import sys
import json
import time
import logging
import threading
from datetime import datetime, timedelta

import win32serviceutil
import win32service
import win32event
import servicemanager

from logging_module.logger_test import setup_logger
from scanners.scanner_manager import ScannerManager
from ai.gemini_classifier import GeminiClassifier
from core.deduplication_engine import DeduplicationEngine
from exports.csv_exporter import CSVExporter

# ─── Config Load ───────────────────────────────────────────
def load_config():
    try:
        with open('config.json', 'r') as f:
            return json.load(f)
    except Exception:
        return {
            "scan_interval_hours": 24,
            "output_dir": "exports",
            "gemini_api_key": "",
            "max_apps_to_classify": 20
        }

# ─── Core Scan Logic ───────────────────────────────────────
def run_scan():
    config = load_config()
    loggers = setup_logger()
    app_log = loggers['application']
    scanner_log = loggers['scanner']
    ai_log = loggers['ai_processing']

    app_log.info(f"Scan started at {datetime.now()}")
    print(f"\n[{datetime.now()}] Scan starting...")

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
    classifier = GeminiClassifier(config['gemini_api_key'])
    ai_log.info("Classification starting")

    if classifier.check_internet():
        max_apps = config.get('max_apps_to_classify', 20)
        classified_apps = classifier.classify_apps(clean_apps[:max_apps])
        ai_log.info(f"Classification complete: {len(classified_apps)} apps")
    else:
        ai_log.warning("No internet — skipping AI classification")
        classified_apps = clean_apps

    # Step 4: Export CSV
    exporter = CSVExporter(output_dir=config.get('output_dir', 'exports'))
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    export_path = exporter.export(classified_apps, filename=f"Software_Inventory_{timestamp}.csv")

    app_log.info(f"Scan complete. CSV: {export_path}")
    print(f"[{datetime.now()}] Scan complete → {export_path}")

# ─── Windows Service Class ─────────────────────────────────
class AppDiscoveryService(win32serviceutil.ServiceFramework):
    _svc_name_ = "AppDiscoveryService"
    _svc_display_name_ = "Application Discovery Service"
    _svc_description_ = "Scans installed applications and exports to CSV automatically."

    def __init__(self, args):
        win32serviceutil.ServiceFramework.__init__(self, args)
        self.stop_event = win32event.CreateEvent(None, 0, 0, None)
        self.running = True

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
        config = load_config()
        interval_hours = config.get('scan_interval_hours', 24)

        logging.info(f"Scheduler: scan every {interval_hours} hours")

        # Service start ஆனவுடனே ஒரு முறை scan பண்ணும்
        self._run_scan_thread()

        next_scan = datetime.now() + timedelta(hours=interval_hours)

        while self.running:
            now = datetime.now()
            if now >= next_scan:
                self._run_scan_thread()
                config = load_config()
                interval_hours = config.get('scan_interval_hours', 24)
                next_scan = datetime.now() + timedelta(hours=interval_hours)
                logging.info(f"Next scan scheduled at: {next_scan}")

            # 60 seconds wait பண்ணி check பண்ணும்
            win32event.WaitForSingleObject(self.stop_event, 60000)

    def _run_scan_thread(self):
        thread = threading.Thread(target=run_scan, daemon=True)
        thread.start()


# ─── Entry Point ───────────────────────────────────────────
if __name__ == '__main__':
    if len(sys.argv) == 1:
        # Service mode
        servicemanager.Initialize()
        servicemanager.PrepareToHostSingle(AppDiscoveryService)
        servicemanager.StartServiceCtrlDispatcher()

    elif '--scan-now' in sys.argv:
        # Manual scan
        print("=" * 50)
        print("  Manual Scan Triggered")
        print("=" * 50)
        run_scan()

    else:
        # install / uninstall / start / stop எல்லாம் handle பண்ணும்
        win32serviceutil.HandleCommandLine(AppDiscoveryService)