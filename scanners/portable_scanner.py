import os
import logging
import string

logger = logging.getLogger(__name__)

class PortableScanner:

    PORTABLE_EXTENSIONS = ['.exe', '.cmd', '.bat']

    def get_all_drives(self):
        """Windows-ல் இருக்கும் எல்லா drives-யும் கண்டுபிடிக்கும்"""
        drives = []
        for letter in string.ascii_uppercase:
            drive = f"{letter}:\\"
            if os.path.exists(drive):
                drives.append(drive)
        return drives

    def scan(self):
        apps = []

        # all drives dynamically add
        drives = self.get_all_drives()

        # optional: common user folders add
        extra_paths = [
            os.path.expanduser("~\\Desktop"),
            os.path.expanduser("~\\Downloads"),
            os.path.expanduser("~\\Documents"),
        ]

        scan_paths = drives + extra_paths

        for path in scan_paths:
            apps.extend(self._scan_folder(path))

        logger.info(f"Portable Scanner: {len(apps)} apps found")
        return apps

    def _scan_folder(self, folder_path):
        apps = []

        try:
            for item in os.listdir(folder_path):
                full_path = os.path.join(folder_path, item)

                if not os.path.isfile(full_path):
                    continue

                ext = os.path.splitext(item)[1].lower()

                if ext in self.PORTABLE_EXTENSIONS:
                    size_mb = round(os.path.getsize(full_path) / (1024 * 1024), 2)

                    apps.append({
                        'name': os.path.splitext(item)[0],
                        'publisher': 'Unknown',
                        'version': 'Unknown',
                        'install_location': full_path,
                        'size_mb': size_mb,
                        'type': 'Portable'
                    })

        except Exception as e:
            logger.error(f"Portable scan error {folder_path}: {e}")

        return apps