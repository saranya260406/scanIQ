import csv
import os
import re
import logging
from datetime import datetime

logger = logging.getLogger(__name__)


class CSVExporter:

    # These sources = raw files, not installed apps — skip
    SKIP_SOURCES = ['ZipFile', 'RealTimeDownload']

    # Names matching these = junk — skip
    SKIP_NAME_PATTERNS = [
        r'^[a-z]{20,}$',                          # random lowercase IDs (browser ext)
        r'^[a-zA-Z0-9]{30,}$',                    # long random alphanumeric
        r'^Microsoft(Edge|Copilot)AutoLaunch_.*', # Microsoft auto-launch junk
        r'^ModifiableWindowsApps$',
        r'^Uninstall Information$',
        r'^SecurityHealth$',
        r'^desktop$',
    ]

    # File extensions = not an app — skip
    SKIP_EXTENSIONS = {'.exe', '.msi', '.zip', '.rar', '.7z', '.appx', '.msix'}

    def __init__(self, output_dir: str = "exports"):
        self.output_dir = output_dir
        os.makedirs(output_dir, exist_ok=True)
        self._compiled_patterns = [
            re.compile(p, re.IGNORECASE) for p in self.SKIP_NAME_PATTERNS
        ]

    def export(self, app_list: list, filename: str = None) -> dict:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

        filtered, skipped_count = self._filter_apps(app_list)
        logger.info(f"Exporting {len(filtered)} apps ({skipped_count} skipped)")

        all_fname = f"Software_Inventory_ALL_{timestamp}.csv"
        all_fpath = os.path.join(self.output_dir, all_fname)
        self._write_csv(all_fpath, filtered)

        print(f"[Export] ✓ ALL drives → {len(filtered)} apps → {all_fpath}")
        print(f"[Export]   {skipped_count} entries skipped")

        return {'ALL': all_fpath}

    def _write_csv(self, filepath: str, apps: list):
        fieldnames = [
            'Name', 'Publisher', 'Version',
            'Installed On', 'Size', 'Install Location', 'Drive', 'Source',
        ]
        try:
            with open(filepath, 'w', newline='', encoding='utf-8-sig') as f:
                writer = csv.DictWriter(f, fieldnames=fieldnames)
                writer.writeheader()
                for app in apps:
                    writer.writerow(self._map_app(app))
            logger.info(f"CSV written: {filepath} ({len(apps)} rows)")
        except Exception as e:
            logger.error(f"CSV write failed {filepath}: {e}")
            raise

    def _map_app(self, app: dict) -> dict:
        return {
            'Name':             self._safe(app.get('name') or app.get('app_name')),
            'Publisher':        self._safe(app.get('publisher') or app.get('company') or app.get('vendor')),
            'Version':          self._safe(app.get('version') or app.get('file_version')),
            'Installed On':     self._safe(app.get('install_date') or app.get('file_created')),
            'Size':             self._format_size(app.get('size_mb')),
            'Install Location': self._safe(app.get('install_location')),
            'Drive':            self._detect_drive(app),
            'Source':           self._format_sources(app),
        }

    def _filter_apps(self, app_list: list) -> tuple[list, int]:
        filtered = []
        skipped  = 0
        for app in app_list:
            # 1. Source filter — skip raw files
            sources = app.get('sources', [app.get('source', '')])
            if isinstance(sources, str):
                sources = [sources]
            if any(skip.lower() in src.lower() for src in sources for skip in self.SKIP_SOURCES):
                skipped += 1
                continue

            # 2. Name filter — skip if name ends with exe/zip etc.
            name = (app.get('name') or app.get('app_name') or '').strip()
            ext = os.path.splitext(name)[1].lower()
            if ext in self.SKIP_EXTENSIONS:
                skipped += 1
                continue

            # 3. Pattern filter — skip random IDs and junk names
            if any(p.match(name) for p in self._compiled_patterns):
                skipped += 1
                continue

            filtered.append(app)
        return filtered, skipped

    def _detect_drive(self, app: dict) -> str:
        path = (
            app.get('install_location') or
            app.get('installLocation') or
            app.get('path') or
            app.get('exe_path') or
            app.get('expected_location') or
            ''
        )
        if not path:
            return 'UNKNOWN'
        try:
            drive, _ = os.path.splitdrive(str(path))
            return drive.upper() if drive else 'UNKNOWN'
        except Exception:
            return 'UNKNOWN'

    def _format_size(self, size_mb) -> str:
        if not size_mb:
            return ''
        try:
            val = float(size_mb)
            if val >= 1024:
                return f"{round(val / 1024, 2)} GB"
            return f"{round(val, 2)} MB"
        except Exception:
            return ''

    def _format_sources(self, app: dict) -> str:
        sources = app.get('sources', [])
        if isinstance(sources, list) and sources:
            return ', '.join(sources)
        return self._safe(app.get('source', ''))

    def _safe(self, value) -> str:
        if value is None:
            return ''
        if isinstance(value, str):
            return value.strip()
        if isinstance(value, (int, float)):
            return str(value)
        if isinstance(value, dict):
            return ''
        return str(value)

    def export_summary(self, app_list: list) -> dict:
        return {'total_exported': len(app_list)}