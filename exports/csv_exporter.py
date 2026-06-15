import csv
import os
import logging
from datetime import datetime

logger = logging.getLogger(__name__)


class CSVExporter:

    def __init__(self, output_dir: str = "exports"):
        self.output_dir = output_dir
        os.makedirs(output_dir, exist_ok=True)

    def export(self, app_list: list, filename: str = None) -> str:
        if not filename:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"Software_Inventory_{timestamp}.csv"

        filepath = os.path.join(self.output_dir, filename)

        fieldnames = [
            'Name',
            'Publisher',
            'Installed On',
            'Size (MB)',
            'Version',
            'Source',
        ]

        try:
            with open(filepath, 'w', newline='', encoding='utf-8-sig') as csvfile:
                writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
                writer.writeheader()

                for app in app_list:
                    writer.writerow(self._map_app(app))

            logger.info(f"CSV exported: {filepath} ({len(app_list)} apps)")
            print(f"\n[Export] ✓ {len(app_list)} apps exported → {filepath}")
            return filepath

        except Exception as e:
            logger.error(f"CSV export failed: {e}")
            print(f"\n[Export] ✗ Export failed: {e}")
            raise

    def _map_app(self, app: dict) -> dict:
        # Size format
        size_mb = app.get('size_mb')
        if size_mb:
            try:
                size_val = float(size_mb)
                if size_val >= 1024:
                    size_str = f"{round(size_val / 1024, 2)} GB"
                else:
                    size_str = f"{round(size_val, 2)} MB"
            except:
                size_str = ''
        else:
            size_str = ''

        # Source
        sources = app.get('sources', [])
        if isinstance(sources, list) and sources:
            source_str = ', '.join(sources)
        else:
            source_str = self._safe(app.get('source', ''))

        return {
            'Name'        : self._safe(app.get('name') or app.get('app_name')),
            'Publisher'   : self._safe(app.get('publisher') or app.get('vendor')),
            'Installed On': self._safe(app.get('install_date')),
            'Size (MB)'   : size_str,
            'Version'     : self._safe(app.get('version')),
            'Source'      : source_str,
        }

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
        return {
            'total_exported': len(app_list),
        }