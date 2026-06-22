from dotenv import load_dotenv
import os

# Core pipeline modules
from scanners.scanner_manager import ScannerManager
from ai.gemini_classifier import GeminiClassifier
from core.deduplication_engine import DeduplicationEngine
from exports.csv_exporter import CSVExporter

# Config system
from config.settings_loader import SettingsLoader
from log_config import LogConfig
from scheduler_utils import start_scheduler

# Load environment variables
load_dotenv()
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")


# =========================
# PIPELINE CORE
# =========================
def run_pipeline(app_log, scanner_log, ai_log, settings):

    app_log.info("Pipeline execution started")

    print("\n" + "=" * 60)
    print("      SCANIQ - APPLICATION DISCOVERY TOOL")
    print("=" * 60)

    # =========================
    # STEP 1: SCANNING
    # =========================
    manager = ScannerManager()

    scanner_log.info("Scanner manager started")

    results = manager.run_all_scans()

    scanner_log.info("Scanning completed")

    print("\n[SCAN SUMMARY]")
    for k, v in results["summary"].items():
        print(f"  {k:<20}: {v}")

    # =========================
    # STEP 2: DEDUPLICATION
    # =========================
    print("\n[DEDUP] Running rule-based deduplication...")

    dedup_engine = DeduplicationEngine()

    clean_apps = dedup_engine.deduplicate(results)

    dedup_summary = dedup_engine.get_summary(clean_apps)

    app_log.info(
        f"Dedup completed - Unique apps: "
        f"{dedup_summary['total_unique_apps']}"
    )

    print(
        f"Unique Applications: "
        f"{dedup_summary['total_unique_apps']}"
    )

    # =========================
    # STEP 3: AI PROCESSING
    # =========================
    print("\n[AI] Initializing classifier...")

    classifier = GeminiClassifier(GEMINI_API_KEY)

    if classifier.check_internet():

        ai_log.info("AI Mode: Online (Gemini enabled)")

        print("[AI] Online mode enabled")

        print("[AI Dedup] Processing semantic duplicates...")

        ai_clean_apps = classifier.deduplicate_apps(clean_apps)

        print(f"After AI dedup: {len(ai_clean_apps)} apps")

        classified_apps = classifier.classify_apps(ai_clean_apps)

    else:

        ai_log.warning("AI Mode: Offline")

        print("[AI] Offline mode - skipping AI classification")

        classified_apps = clean_apps

    # =========================
    # STEP 4: EXPORT
    # =========================
    print("\n[EXPORT] Creating CSV report...")

    exporter = CSVExporter(
        output_dir=settings.get_export_path()
    )

    export_path = exporter.export(
        classified_apps,
        filename="Software_Inventory.csv"
    )

    app_log.info(
        f"Export completed: {export_path}"
    )

    print(
        f"\nDONE → Report generated at:\n{export_path}"
    )

    app_log.info(
        "Pipeline completed successfully"
    )


# =========================
# MAIN ENTRY
# =========================
def main():

    # Load settings
    settings = SettingsLoader()

    # Setup logging
    log_manager = LogConfig(settings)

    logger_dict = log_manager.setup_logging()

    print("Logger Keys:", logger_dict.keys())

    app_log = logger_dict["application"]
    scanner_log = logger_dict["scanner"]
    ai_log = logger_dict["ai_processing"]

    app_log.info("SCANIQ system initialized")

    export_path = settings.get_export_path()
    scan_time = settings.get_scan_time()

    app_log.info(f"Export path: {export_path}")
    app_log.info(f"Scan time configured: {scan_time}")

    print("\nSYSTEM READY")
    print(f"Export Path : {export_path}")
    print(f"Scan Time   : {scan_time}")

    app_log.info("Application logger working")
    scanner_log.info("Scanner logger working")
    ai_log.info("AI logger working")

    mode = (
        settings.get_mode()
        if hasattr(settings, "get_mode")
        else "manual"
    )

    if mode.lower() == "scheduled":

        app_log.info("Running in scheduled mode")

        start_scheduler(
            settings,
            lambda: run_pipeline(
                app_log,
                scanner_log,
                ai_log,
                settings
            )
        )

    else:

        app_log.info("Running in manual mode")

        run_pipeline(
            app_log,
            scanner_log,
            ai_log,
            settings
        )

if __name__ == "__main__":
    main()