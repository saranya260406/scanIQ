import winreg
import datetime
import logging

logger = logging.getLogger(__name__)

class MSIScanner:

    REGISTRY_PATHS = [
        (winreg.HKEY_LOCAL_MACHINE, r"SOFTWARE\Microsoft\Windows\CurrentVersion\Uninstall"),
        (winreg.HKEY_LOCAL_MACHINE, r"SOFTWARE\WOW6432Node\Microsoft\Windows\CurrentVersion\Uninstall"),
        (winreg.HKEY_CURRENT_USER, r"SOFTWARE\Microsoft\Windows\CurrentVersion\Uninstall"),
    ]

    def scan(self):
        apps = []
        for hive, path in self.REGISTRY_PATHS:
            apps.extend(self._scan_registry_path(hive, path))
        logger.info(f"MSI Scanner: {len(apps)} apps found")
        return apps

    def _scan_registry_path(self, hive, path):
        apps = []
        try:
            registry_key = winreg.OpenKey(hive, path)
            num_subkeys = winreg.QueryInfoKey(registry_key)[0]
            for i in range(num_subkeys):
                try:
                    subkey_name = winreg.EnumKey(registry_key, i)
                    subkey_path = path + "\\" + subkey_name
                    subkey = winreg.OpenKey(hive, subkey_path)
                    app = self._extract_app_info(subkey)
                    if app and app.get('name'):
                        apps.append(app)
                    winreg.CloseKey(subkey)
                except Exception:
                    continue
            winreg.CloseKey(registry_key)
        except Exception as e:
            logger.error(f"Registry read error: {e}")
        return apps

    def _extract_app_info(self, subkey):
        def get_value(key, name):
            try:
                return winreg.QueryValueEx(key, name)[0]
            except Exception:
                return None

        name = get_value(subkey, 'DisplayName')
        if not name:
            return None

        raw_date = get_value(subkey, 'InstallDate')
        install_date = self._parse_date(raw_date)

        size_kb = get_value(subkey, 'EstimatedSize')
        size_mb = round(size_kb / 1024, 2) if size_kb else None

        return {
            'name': name,
            'publisher': get_value(subkey, 'Publisher') or 'Unknown',
            'version': get_value(subkey, 'DisplayVersion') or 'Unknown',
            'install_date': install_date,
            'install_location': get_value(subkey, 'InstallLocation') or 'Unknown',
            'size_mb': size_mb,
            'uninstall_string': get_value(subkey, 'UninstallString') or '',
            'type': 'MSI'
        }

    def _parse_date(self, raw_date):
        if not raw_date or len(str(raw_date)) != 8:
            return 'Unknown'
        try:
            return datetime.datetime.strptime(str(raw_date), '%Y%m%d').strftime('%d-%m-%Y')
        except Exception:
            return 'Unknown'