from dotenv import load_dotenv
import os
from logging_module.logger_test import setup_logger
from scanners.scanner_manager import ScannerManager
from ai.gemini_classifier import GeminiClassifier
from core.deduplication_engine import DeduplicationEngine
from exports.csv_exporter import CSVExporter

load_dotenv()
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

def main():
    loggers = setup_logger()
    app_log = loggers['application']
    scanner_log = loggers['scanner']
    ai_log = loggers['ai_processing']

    app_log.info("Application Discovery Tool started")

    print("=" * 50)
    print("  Application Discovery - Scanner")
    print("=" * 50)

    manager = ScannerManager()
    scanner_log.info("All scanners starting...")
    results = manager.run_all_scans()
    scanner_log.info("All scanners completed")

    summary = results['summary']
    print("\n" + "=" * 50)
    print("  SCAN COMPLETE - SUMMARY")
    print("=" * 50)
    print(f"  Total Apps      : {summary['total_apps']}")
    print(f"  MSI Apps        : {summary['msi_count']}")
    print(f"  User Apps       : {summary['user_count']}")
    print(f"  Store Apps      : {summary['store_count']}")
    print(f"  Portable Apps   : {summary['portable_count']}")
    print(f"  Zip Files       : {summary['zip_count']}")
    print(f"  Browser Exts    : {summary['browser_count']}")
    print("=" * 50)

    print("\n[Dedup] Removing duplicates...")
    dedup_engine = DeduplicationEngine()
    clean_apps = dedup_engine.deduplicate(results)
    dedup_summary = dedup_engine.get_summary(clean_apps)
    app_log.info(f"Deduplication complete: {dedup_summary['total_unique_apps']} unique apps")

    print("\n" + "=" * 50)
    print("  DEDUPLICATION COMPLETE")
    print("=" * 50)
    print(f"  Unique Apps     : {dedup_summary['total_unique_apps']}")
    print("=" * 50)

    # Step 3: Gemini AI
    print("\n[AI] Gemini starting...")
    classifier = GeminiClassifier(GEMINI_API_KEY)
    classified_apps = []

    if classifier.check_internet():
        print("[AI] Internet available — Online mode (Gemini)")

        print(f"\n[AI Dedup] {len(clean_apps)} apps — AI duplicate filter starting...")
        ai_clean_apps = classifier.deduplicate_apps(clean_apps)

        print("\n" + "=" * 50)
        print("  AI DEDUPLICATION COMPLETE")
        print("=" * 50)
        print(f"  Before AI Dedup : {len(clean_apps)}")
        print(f"  After AI Dedup  : {len(ai_clean_apps)}")
        print(f"  Removed         : {len(clean_apps) - len(ai_clean_apps)}")
        print("=" * 50)

        classified_apps = ai_clean_apps
        ai_log.info(f"AI Dedup complete: {len(classified_apps)} apps")

    else:
        print("[AI] No internet — Offline mode")
        classified_apps = clean_apps

    # Step 4: CSV Export
    print("\n[Export] Exporting to CSV...")
    exporter = CSVExporter(output_dir="exports")
    export_path = exporter.export(classified_apps)
    export_summary = exporter.export_summary(classified_apps)

    print("\n" + "=" * 50)
    print("  EXPORT COMPLETE")
    print("=" * 50)
    print(f"  Total Exported  : {export_summary['total_exported']}")
    print("=" * 50)

    print(f"\n[Done] CSV ready at: {export_path}")

if __name__ == "__main__":
    main()