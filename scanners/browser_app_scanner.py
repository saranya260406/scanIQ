import os
import json
import logging
import re

logger = logging.getLogger(__name__)

class BrowserAppScanner:

    def scan(self):
        extensions = []
        extensions.extend(self._scan_chrome())
        extensions.extend(self._scan_edge())
        logger.info(f"Browser App Scanner: {len(extensions)} extensions found")
        return extensions

    def _scan_chrome(self):
        extensions = []
        chrome_path = os.path.expanduser(
            r"~\AppData\Local\Google\Chrome\User Data\Default\Extensions"
        )
        extensions.extend(self._scan_browser_extensions(chrome_path, 'Chrome'))
        return extensions

    def _scan_edge(self):
        extensions = []
        edge_path = os.path.expanduser(
            r"~\AppData\Local\Microsoft\Edge\User Data\Default\Extensions"
        )
        extensions.extend(self._scan_browser_extensions(edge_path, 'Edge'))
        return extensions

    def _scan_browser_extensions(self, extensions_path, browser_name):
        extensions = []
        if not os.path.exists(extensions_path):
            logger.warning(f"{browser_name} extensions path not found")
            return extensions
        try:
            for ext_id in os.listdir(extensions_path):
                ext_folder = os.path.join(extensions_path, ext_id)
                if not os.path.isdir(ext_folder):
                    continue
                for version_folder in os.listdir(ext_folder):
                    manifest_path = os.path.join(ext_folder, version_folder, 'manifest.json')
                    if os.path.exists(manifest_path):
                        ext_info = self._read_manifest(manifest_path, browser_name, ext_id)
                        if ext_info:
                            extensions.append(ext_info)
                        break
        except Exception as e:
            logger.error(f"{browser_name} scan error: {e}")
        return extensions

    def _read_manifest(self, manifest_path, browser_name, ext_id):
        try:
            with open(manifest_path, 'r', encoding='utf-8') as f:
                manifest = json.load(f)

            name = manifest.get('name', '')

            # __MSG_ format skip
            if name.startswith('__MSG_'):
                name = manifest.get('short_name', '')

            # Readable name இல்லன்னா skip — random ID-like names filter
            if not name or name.startswith('__MSG_'):
                return None

            # Pure random ID (எல்லாம் lowercase letters மட்டும், 20+ chars) skip
            if re.match(r'^[a-z]{20,}$', name):
                return None

            return {
                'name': name,
                'version': manifest.get('version', 'Unknown'),
                'description': manifest.get('description', '')[:100],
                'browser': browser_name,
                'extension_id': ext_id,
                'publisher': manifest.get('author', 'Unknown'),
                'type': 'BrowserExtension'
            }
        except Exception as e:
            logger.error(f"Manifest read error: {e}")
            return None