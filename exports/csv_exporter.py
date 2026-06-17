import csv
import os
import logging
from datetime import datetime

logger = logging.getLogger(__name__)

SKIP_SOURCES = ['zip_files']


class CSVExporter:

    def __init__(self, output_dir: str = "exports"):
        self.output_dir = output_dir
        os.makedirs(output_dir, exist_ok=True)

    def export(self, app_list: list, filename: str = None) -> dict:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

        filtered, skipped_count = self._filter_apps(app_list)
        logger.info(f"Exporting {len(filtered)} apps ({skipped_count} skipped)")

        all_fname = f"Software_Inventory_ALL_{timestamp}.csv"
        all_fpath = os.path.join(self.output_dir, all_fname)
        self._write_csv(all_fpath, filtered)

        print(f"[Export] ✓ ALL drives → {len(filtered)} apps → {all_fpath}")
        print(f"[Export]   {skipped_count} installer files skipped")

        return {'ALL': all_fpath}

    def _write_csv(self, filepath: str, apps: list):
        fieldnames = [
            'Name',
            'Publisher',
            'Version',
            'Installed On',
            'Size',
            'Install Location',
            'Drive',
            'Source',
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
            sources = app.get('sources', [app.get('source', '')])
            if isinstance(sources, str):
                sources = [sources]
            if any(skip in src for src in sources for skip in SKIP_SOURCES):
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