import logging
import re

logger = logging.getLogger(__name__)


class DeduplicationEngine:
    """
    Scanner results-ல இருக்க duplicate apps-ஐ remove பண்ணி
    clean, normalized app list return பண்ணும்.
    """

    def __init__(self):
        # Deduplicate பண்ண use ஆகும் key: (normalized_name, publisher)
        self.seen = {}

    def normalize_name(self, name: str) -> str:
        """
        App name-ஐ normalize பண்ணும்:
        - Lowercase
        - Extra spaces remove
        - Version numbers remove (e.g. "App 1.2.3" → "App")
        - Special characters strip
        """
        if not name:
            return ""
        name = name.lower().strip()
        # Version numbers remove (1.0, 2.3.4, v1.0 etc.)
        name = re.sub(r'\bv?\d+(\.\d+)+\b', '', name)
        # Special characters remove
        name = re.sub(r'[^\w\s]', '', name)
        # Extra spaces remove
        name = re.sub(r'\s+', ' ', name).strip()
        return name

    def normalize_publisher(self, publisher) -> str:
        """
        Publisher name normalize பண்ணும்
        """
        if not publisher:
            return "unknown"
        # Dict or list ஆ இருந்தா skip பண்ணு
        if not isinstance(publisher, str):
            return "unknown"
        publisher = publisher.lower().strip()
        publisher = re.sub(r'\s+', ' ', publisher)
        return publisher

    def _safe_str(self, value) -> str:
        """
        Any value-ஐ safely string-ஆ convert பண்ணும்
        """
        if not value:
            return ''
        if isinstance(value, str):
            return value
        if isinstance(value, (int, float)):
            return str(value)
        return ''

    def _make_key(self, app: dict) -> str:
        """
        Duplicate check-க்கு unique key உருவாக்கும்
        """
        name = self.normalize_name(
            self._safe_str(app.get('name')) or self._safe_str(app.get('app_name'))
        )
        publisher = self.normalize_publisher(
            self._safe_str(app.get('publisher')) or self._safe_str(app.get('vendor'))
        )
        return f"{name}||{publisher}"

    def _source_priority(self, source: str) -> int:
        """
        எந்த scanner-ஓட data more reliable-னு priority குடுக்கும்
        Higher number = Higher priority
        """
        priority_map = {
            'msi': 5,
            'user_app': 4,
            'store': 3,
            'portable': 2,
            'startup': 2,
            'service': 2,
            'process': 1,
            'browser': 1,
            'zip': 1,
            'deleted_trace': 0,
        }
        for key in priority_map:
            if key in source.lower():
                return priority_map[key]
        return 1

    def _merge_app(self, existing: dict, new_app: dict) -> dict:
        """
        இரண்டு duplicate apps-ல இருந்து best data merge பண்ணும்
        """
        merged = existing.copy()

        # Higher priority source-ஓட data prefer பண்ணும்
        existing_priority = self._source_priority(existing.get('source', ''))
        new_priority = self._source_priority(new_app.get('source', ''))

        if new_priority > existing_priority:
            # New app data better — override பண்ணு
            for field in ['name', 'app_name', 'version', 'publisher', 'install_path', 'install_date']:
                if new_app.get(field):
                    merged[field] = new_app[field]

        # Sources combine பண்ணு (எந்தெந்த scanner-ல கண்டுபிடிச்சதுன்னு track பண்ண)
        existing_sources = existing.get('sources', [existing.get('source', 'unknown')])
        new_source = new_app.get('source', 'unknown')
        if new_source not in existing_sources:
            existing_sources.append(new_source)
        merged['sources'] = existing_sources

        return merged

    def deduplicate(self, all_results: dict) -> list:
        """
        scanner_manager-ஓட run_all_scans() result-ஐ input-ஆ எடுத்து
        deduplicated, normalized app list return பண்ணும்.

        Args:
            all_results (dict): ScannerManager.run_all_scans() return value

        Returns:
            list: Clean, unique app list
        """
        self.seen = {}
        total_raw = 0
        skipped = 0

        # எந்தெந்த scanner key-ஐ process பண்ணணும்
        scanner_keys = [
            'msi_apps',
            'user_apps',
            'store_apps',
            'portable_apps',
            'zip_files',
            'browser_apps',
            'deleted_traces',
            'processes',
            'services',
            'startup_items',
        ]

        for key in scanner_keys:
            apps = all_results.get(key, [])
            if not apps:
                continue

            logger.debug(f"Processing {len(apps)} entries from '{key}'")

            for app in apps:
                if not isinstance(app, dict):
                    skipped += 1
                    continue

                # Source tag add பண்ணு (இல்லன்னா key-ஐ use பண்ணு)
                if 'source' not in app:
                    app['source'] = key

                total_raw += 1
                dedup_key = self._make_key(app)

                if not dedup_key.startswith('||'):  # valid name இருக்கா check
                    if dedup_key in self.seen:
                        # Duplicate — merge பண்ணு
                        self.seen[dedup_key] = self._merge_app(self.seen[dedup_key], app)
                        logger.debug(f"Duplicate merged: {app.get('name', app.get('app_name', 'Unknown'))}")
                    else:
                        # New unique app
                        app_copy = app.copy()
                        app_copy['sources'] = [app.get('source', 'unknown')]
                        self.seen[dedup_key] = app_copy
                else:
                    skipped += 1
                    logger.debug(f"Skipped app with no name: {app}")

        clean_list = list(self.seen.values())

        logger.info(f"Deduplication complete: {total_raw} raw → {len(clean_list)} unique apps ({skipped} skipped)")
        print(f"\n[Deduplication] {total_raw} raw entries → {len(clean_list)} unique apps ({skipped} skipped)")

        return clean_list

    def get_summary(self, clean_list: list) -> dict:
        """
        Deduplicated list-ஓட summary return பண்ணும்
        """
        source_counts = {}
        for app in clean_list:
            for src in app.get('sources', [app.get('source', 'unknown')]):
                source_counts[src] = source_counts.get(src, 0) + 1

        return {
            'total_unique_apps': len(clean_list),
            'source_breakdown': source_counts,
        }