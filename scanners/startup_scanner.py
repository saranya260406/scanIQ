import winreg
import os
import logging

logger = logging.getLogger(__name__)

class StartupScanner:

    REGISTRY_PATHS = [
        (winreg.HKEY_LOCAL_MACHINE, r"SOFTWARE\Microsoft\Windows\CurrentVersion\Run"),
        (winreg.HKEY_LOCAL_MACHINE, r"SOFTWARE\Microsoft\Windows\CurrentVersion\RunOnce"),
        (winreg.HKEY_CURRENT_USER, r"SOFTWARE\Microsoft\Windows\CurrentVersion\Run"),
        (winreg.HKEY_CURRENT_USER, r"SOFTWARE\Microsoft\Windows\CurrentVersion\RunOnce"),
    ]

    STARTUP_FOLDERS = [
        os.path.expanduser(r"~\AppData\Roaming\Microsoft\Windows\Start Menu\Programs\Startup"),
        r"C:\ProgramData\Microsoft\Windows\Start Menu\Programs\Startup",
    ]

    INBUILT_PATH_KEYWORDS = [
        'C:\\Windows\\',
        'C:\\Program Files\\WindowsApps\\',
        'C:\\ProgramData\\Microsoft\\Windows\\',
        'C:\\Windows\\System32\\',
        'C:\\Windows\\SysWOW64\\',
        'Microsoft\\Edge',
        'Microsoft\\EdgeUpdate',
        '%windir%',
        '%systemroot%',
    ]

    def _is_inbuilt_path(self, command: str) -> bool:
        """Path-based inbuilt detection — no skip list"""
        if not command:
            return False
        cmd_lower = command.lower()
        for keyword in self.INBUILT_PATH_KEYWORDS:
            if keyword.lower() in cmd_lower:
                return True
        return False

    def scan(self):
        startup_items = []
        startup_items.extend(self._scan_registry())
        startup_items.extend(self._scan_startup_folders())
        logger.info(f"Startup Scanner: {len(startup_items)} items found")
        return startup_items

    def _scan_registry(self):
        items = []
        for hive, path in self.REGISTRY_PATHS:
            try:
                key = winreg.OpenKey(hive, path)
                num_values = winreg.QueryInfoKey(key)[1]
                for i in range(num_values):
                    try:
                        name, value, _ = winreg.EnumValue(key, i)
                        # Path-based inbuilt check
                        if self._is_inbuilt_path(value):
                            continue
                        items.append({
                            'name': name,
                            'command': value,
                            'location': f"Registry: {path}",
                            'file_exists': os.path.exists(
                                value.strip('"').split()[0]
                            ),
                            'type': 'Startup'
                        })
                    except Exception:
                        continue
                winreg.CloseKey(key)
            except Exception as e:
                logger.error(f"Startup registry scan error: {e}")
        return items

    def _scan_startup_folders(self):
        items = []
        for folder in self.STARTUP_FOLDERS:
            if not os.path.exists(folder):
                continue
            try:
                for item in os.listdir(folder):
                    full_path = os.path.join(folder, item)
                    if not os.path.isfile(full_path):
                        continue
                    if self._is_inbuilt_path(full_path):
                        continue
                    items.append({
                        'name': os.path.splitext(item)[0],
                        'command': full_path,
                        'location': folder,
                        'file_exists': True,
                        'type': 'Startup'
                    })
            except Exception as e:
                logger.error(f"Startup folder scan error: {e}")
        return items