import os
import logging

logger = logging.getLogger(__name__)

class PortableScanner:

    # Portable apps இருக்கக்கூடிய common locations
    SCAN_PATHS = [
        os.path.expanduser("~\\Desktop"),
        os.path.expanduser("~\\Downloads"),
        os.path.expanduser("~\\Documents"),
        "C:\\PortableApps",
        "C:\\Tools",
        "D:\\PortableApps",
        "D:\\Tools",
    ]

    PORTABLE_EXTENSIONS = ['.exe', '.cmd', '.bat']

    def scan(self):
        apps = []
        for path in self.SCAN_PATHS:
            if os.path.exists(path):
                apps.extend(self._scan_folder(path))
        logger.info(f"Portable Scanner: {len(apps)} apps found")
        return apps

    def _scan_folder(self, folder_path):
        apps = []
        try:
            for item in os.listdir(folder_path):
                full_path = os.path.join(folder_path, item)
                ext = os.path.splitext(item)[1].lower()
                if os.path.isfile(full_path) and ext in self.PORTABLE_EXTENSIONS:
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