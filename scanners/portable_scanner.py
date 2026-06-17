import os
import logging
import string

logger = logging.getLogger(__name__)

class PortableScanner:

    # System folders skip பண்ணும் (Windows internal files)
    SKIP_FOLDERS = [
        'Windows', 'System Volume Information', '$Recycle.Bin',
        'Recovery', 'PerfLogs', '$WinREAgent', 'Config.Msi'
    ]

    def get_all_drives(self):
        drives = []
        for letter in string.ascii_uppercase:
            drive = f"{letter}:\\"
            if os.path.exists(drive):
                drives.append(drive)
        return drives

    def scan(self):
        apps = []
        drives = self.get_all_drives()
        logger.info(f"Found drives: {drives}")

        for drive in drives:
            logger.info(f"Scanning drive: {drive}")
            apps.extend(self._scan_folder(drive, drive))

        logger.info(f"Total files found: {len(apps)}")
        return apps

    def _scan_folder(self, folder_path, drive_name):
        apps = []

        try:
            for root, dirs, files in os.walk(folder_path):

                # System folders skip பண்ணும்
                dirs[:] = [
                    d for d in dirs
                    if d not in self.SKIP_FOLDERS
                    and not d.startswith('$')
                ]

                for file in files:
                    full_path = os.path.join(root, file)
                    ext = os.path.splitext(file)[1].lower()
                    name = os.path.splitext(file)[0]

                    try:
                        size_mb = round(os.path.getsize(full_path) / (1024 * 1024), 2)

                        apps.append({
                            'name': name,
                            'file': file,
                            'extension': ext,
                            'publisher': 'Unknown',
                            'version': 'Unknown',
                            'install_location': full_path,
                            'size_mb': size_mb,
                            'type': 'Portable',
                            'drive': drive_name
                        })

                    except Exception:
                        continue

        except Exception as e:
            logger.error(f"Drive scan error {folder_path}: {e}")

        return apps