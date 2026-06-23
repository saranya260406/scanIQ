import os
import json
import logging

logger = logging.getLogger(__name__)

class BrowserAppScanner:

    def scan(self):
        extensions = []
        # All users-ஐ scan பண்ணும்
        for user_path in self._get_all_user_paths():
            extensions.extend(self._scan_chrome(user_path))
            extensions.extend(self._scan_edge(user_path))
        logger.info(f"Browser App Scanner: {len(extensions)} extensions found")
        return extensions

    def _get_all_user_paths(self):
        """Get all user profile paths from C drive"""
        user_paths = []
        users_dir = r"C:\Users"
        skip_folders = {'Public', 'Default', 'Default User', 'All Users'}
        try:
            for user in os.listdir(users_dir):
                if user in skip_folders:
                    continue
                full_path = os.path.join(users_dir, user)
                if os.path.isdir(full_path):
                    user_paths.append(full_path)
        except Exception as e:
            logger.error(f"Users folder scan error: {e}")
        return user_paths

    def _scan_chrome(self, user_path):
        chrome_path = os.path.join(
            user_path,
            r"AppData\Local\Google\Chrome\User Data\Default\Extensions"
        )
        return self._scan_browser_extensions(chrome_path, 'Chrome')

    def _scan_edge(self, user_path):
        edge_path = os.path.join(
            user_path,
            r"AppData\Local\Microsoft\Edge\User Data\Default\Extensions"
        )
        return self._scan_browser_extensions(edge_path, 'Edge')

    def _scan_browser_extensions(self, extensions_path, browser_name):
        extensions = []
        if not os.path.exists(extensions_path):
            logger.warning(f"{browser_name} extensions path not found: {extensions_path}")
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
            name = manifest.get('name', 'Unknown')
            if name.startswith('__MSG_'):
                name = manifest.get('short_name', ext_id)
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