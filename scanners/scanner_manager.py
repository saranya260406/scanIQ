import logging
import os
from scanners.msi_scanner import MSIScanner
from scanners.user_app_scanner import UserAppScanner
from scanners.store_scanner import StoreScanner
from scanners.zip_scanner import ZipScanner
from scanners.browser_app_scanner import BrowserAppScanner
from scanners.metadata_extractor import MetadataExtractor
from scanners.portable_scanner import PortableScanner

logger = logging.getLogger(__name__)

class ScannerManager:

    def __init__(self):
        self.msi_scanner        = MSIScanner()
        self.user_scanner       = UserAppScanner()
        self.store_scanner      = StoreScanner()
        self.zip_scanner        = ZipScanner()
        self.browser_scanner    = BrowserAppScanner()
        self.metadata_extractor = MetadataExtractor()
        self.portable_scanner   = PortableScanner()

    def _extract_drive(self, path: str):
        if not path:
            return "UNKNOWN"
        return os.path.splitdrive(path)[0] or "UNKNOWN"

    def _add_drive_column(self, items):
        for item in items:
            path = (
                item.get("install_location") or
                item.get("path") or
                item.get("location") or
                item.get("command") or
                item.get("expected_location") or
                ""
            )
            item["drive"] = self._extract_drive(path)
        return items

    def run_all_scans(self):
        results = {}

        print("\n[1] MSI Apps Scanning...")
        results['msi_apps'] = self._add_drive_column(self.msi_scanner.scan())
        print(f"    ✓ {len(results['msi_apps'])} MSI apps found")

        print("[2] User Apps Scanning...")
        results['user_apps'] = self._add_drive_column(self.user_scanner.scan())
        print(f"    ✓ {len(results['user_apps'])} User apps found")

        print("[3] Store Apps Scanning...")
        results['store_apps'] = self._add_drive_column(self.store_scanner.scan())
        print(f"    ✓ {len(results['store_apps'])} Store apps found")

        print("[4] Portable Apps Scanning...")
        results['portable_apps'] = self._add_drive_column(self.portable_scanner.scan())
        print(f"    ✓ {len(results['portable_apps'])} Portable folders found")

        print("[5] Zip / Setup Files Scanning...")
        results['zip_files'] = self._add_drive_column(self.zip_scanner.scan())
        print(f"    ✓ {len(results['zip_files'])} Zip files found")

        print("[6] Browser Extensions Scanning...")
        results['browser_apps'] = self._add_drive_column(self.browser_scanner.scan())
        print(f"    ✓ {len(results['browser_apps'])} Extensions found")

        print("[7] Deleted Traces — SKIPPED")
        results['deleted_traces'] = []

        print("[8] Metadata Extracting...")
        results['msi_apps'] = self.metadata_extractor.extract(results['msi_apps'])
        results['msi_apps'] = self._add_drive_column(results['msi_apps'])
        print(f"    ✓ Metadata extracted for {len(results['msi_apps'])} apps")

        results['startup_items'] = []
        results['processes']     = []
        results['services']      = []

        results['summary'] = self._generate_summary(results)
        return results

    def _generate_summary(self, results):
        total_apps = (
            len(results.get('msi_apps', [])) +
            len(results.get('user_apps', [])) +
            len(results.get('store_apps', [])) +
            len(results.get('portable_apps', []))
        )
        return {
            'total_apps':     total_apps,
            'msi_count':      len(results.get('msi_apps', [])),
            'user_count':     len(results.get('user_apps', [])),
            'store_count':    len(results.get('store_apps', [])),
            'portable_count': len(results.get('portable_apps', [])),
            'zip_count':      len(results.get('zip_files', [])),
            'browser_count':  len(results.get('browser_apps', [])),
        }