import os
import logging
import string

logger = logging.getLogger(__name__)

class PortableScanner:

    SKIP_FOLDERS = [
        'Windows', 'System Volume Information', '$Recycle.Bin',
        'Recovery', 'PerfLogs', '$WinREAgent', 'Config.Msi',
        'Program Files', 'Program Files (x86)', 'ProgramData',
        'Users', 'Temp', 'tmp'
    ]

    def _get_non_system_drives(self):
        drives = []
        for letter in string.ascii_uppercase:
            if letter == 'C':
                continue
            drive = f"{letter}:\\"
            if os.path.exists(drive):
                drives.append(drive)
        return drives

    def scan(self):
        apps = []
        drives = self._get_non_system_drives()
        logger.info(f"Portable scan drives: {drives}")

        for drive in drives:
            apps.extend(self._scan_top_level_folders(drive))

        logger.info(f"Portable Scanner: {len(apps)} folders found")
        return apps

    def _scan_top_level_folders(self, drive_path):
        apps = []
        try:
            for item in os.listdir(drive_path):
                full_path = os.path.join(drive_path, item)

                if not os.path.isdir(full_path):
                    continue
                if item in self.SKIP_FOLDERS or item.startswith('$'):
                    continue

                # Folder-க்குள்ள .exe இருந்தா portable app
                exe_found = None
                try:
                    for f in os.listdir(full_path):
                        if f.lower().endswith('.exe'):
                            exe_found = os.path.join(full_path, f)
                            break
                except Exception:
                    pass

                apps.append({
                    'name': item,
                    'publisher': 'Unknown',
                    'version': 'Unknown',
                    'install_location': full_path,
                    'exe_path': exe_found or '',
                    'size_mb': None,
                    'type': 'Portable',
                    'source': 'portable'
                })

        except Exception as e:
            logger.error(f"Portable scan error {drive_path}: {e}")

        return apps