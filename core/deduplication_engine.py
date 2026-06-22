import logging
import re

logger = logging.getLogger(__name__)

class DeduplicationEngine:

    def deduplicate(self, results: dict) -> list:
        all_apps = []

        source_map = {
            'msi_apps':      'MSI',
            'user_apps':     'UserApp',
            'store_apps':    'StoreApp',
            'portable_apps': 'Portable',
            'zip_files':     'ZipFile',
            'browser_apps':  'BrowserExtension',
        }

        for key, source_label in source_map.items():
            for app in results.get(key, []):
                app['source'] = source_label
                all_apps.append(app)

        logger.info(f"Total before dedup: {len(all_apps)}")

        seen: dict[str, dict] = {}

        for app in all_apps:
            name    = self._normalize(app.get('name', ''))
            version = self._normalize(str(app.get('version', '')))
            key     = f"{name}||{version}"

            if key in seen:
                existing = seen[key]
                existing_sources = existing.get('sources', [existing.get('source', '')])
                new_source       = app.get('source', '')
                if new_source and new_source not in existing_sources:
                    existing_sources.append(new_source)
                existing['sources'] = existing_sources

                if (not existing.get('install_location') or
                        existing.get('install_location') == 'Unknown'):
                    loc = app.get('install_location', '')
                    if loc and loc != 'Unknown':
                        existing['install_location'] = loc
            else:
                app['sources'] = [app.get('source', '')]
                seen[key] = app

        deduped = list(seen.values())
        logger.info(f"After dedup: {len(deduped)} unique apps")
        return deduped

    def get_summary(self, apps: list) -> dict:
        return {
            'total_unique_apps': len(apps),
        }

    def _normalize(self, text: str) -> str:
        text = text.lower().strip()
        text = re.sub(r'[^a-z0-9]', '', text)
        return text