import winreg
import os
import logging

logger = logging.getLogger(__name__)

# Unga SARANYA account-oda SID - 'whoami /user' la kitta output
USER_SID = r"S-1-5-21-1456990233-2880578857-2040869081-1001"
# SARANYA account-oda actual user folder path
USER_PROFILE_PATH = r"C:\Users\SARANYA"


class StartupScanner:
    REGISTRY_PATHS = [
        (winreg.HKEY_LOCAL_MACHINE, r"SOFTWARE\Microsoft\Windows\CurrentVersion\Run"),
        (winreg.HKEY_LOCAL_MACHINE, r"SOFTWARE\Microsoft\Windows\CurrentVersion\RunOnce"),
        # HKEY_CURRENT_USER thavira, HKEY_USERS\<SID> mela direct point pannurom
        # Service LocalSystem-la run aanalum, idhu correct user profile-ah padikkum
        (winreg.HKEY_USERS, USER_SID + r"\SOFTWARE\Microsoft\Windows\CurrentVersion\Run"),
        (winreg.HKEY_USERS, USER_SID + r"\SOFTWARE\Microsoft\Windows\CurrentVersion\RunOnce"),
    ]
    STARTUP_FOLDERS = [
        # os.path.expanduser("~") LocalSystem profile-ku point pannum, athanala hardcode pannurom
        USER_PROFILE_PATH + r"\AppData\Roaming\Microsoft\Windows\Start Menu\Programs\Startup",
        r"C:\ProgramData\Microsoft\Windows\Start Menu\Programs\Startup",
    ]

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
                        try:
                            exists = os.path.exists(value.strip('"').split()[0])
                        except Exception:
                            exists = False
                        items.append({
                            'name': name,
                            'command': value,
                            'location': f"Registry: {path}",
                            'file_exists': exists,
                            'type': 'Startup'
                        })
                    except Exception:
                        continue
                winreg.CloseKey(key)
            except Exception as e:
                logger.error(f"Startup registry scan error ({path}): {e}")
        return items

    def _scan_startup_folders(self):
        items = []
        for folder in self.STARTUP_FOLDERS:
            if not os.path.exists(folder):
                continue
            try:
                for item in os.listdir(folder):
                    full_path = os.path.join(folder, item)
                    if os.path.isfile(full_path):
                        items.append({
                            'name': os.path.splitext(item)[0],
                            'command': full_path,
                            'location': folder,
                            'file_exists': True,
                            'type': 'Startup'
                        })
            except Exception as e:
                logger.error(f"Startup folder scan error ({folder}): {e}")
        return items