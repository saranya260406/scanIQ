import os
import logging
import string

logger = logging.getLogger(__name__)

class PortableScanner:

    SKIP_FOLDERS = [
        'Windows', 'System Volume Information', '$Recycle.Bin',
        'Recovery', 'PerfLogs', '$WinREAgent', 'Config.Msi',
        'ProgramData', 'Temp', 'tmp', 'WinSxS',
    ]

    SKIP_DRIVES_FOLDERS = {
        'C:\\': [
            'Windows', 'System Volume Information', '$Recycle.Bin',
            'Recovery', 'PerfLogs', '$WinREAgent', 'Config.Msi',
            'ProgramData', 'Temp', 'tmp', 'WinSxS',
            'Program Files', 'Program Files (x86)', 'Users',
        ]
    }

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
        logger.info(f"Portable scan drives: {drives}")

        for drive in drives:
            apps.extend(self._scan_top_level_folders(drive))

        logger.info(f"Portable Scanner: {len(apps)} folders found")
        return apps

    def _scan_top_level_folders(self, drive_path):
        apps = []

        skip = self.SKIP_DRIVES_FOLDERS.get(drive_path, self.SKIP_FOLDERS)

        try:
            for item in os.listdir(drive_path):
                full_path = os.path.join(drive_path, item)

                if not os.path.isdir(full_path):
                    continue
                if item in skip or item.startswith('$'):
                    continue

                main_exe = self._find_main_exe(full_path, item)

                if not main_exe:
                    continue

                apps.append({
                    'name': item,
                    'publisher': 'Unknown',
                    'version': 'Unknown',
                    'install_location': full_path,
                    'exe_path': main_exe,
                    'size_mb': None,
                    'type': 'Portable',
                    'source': 'portable'
                })

        except Exception as e:
            logger.error(f"Portable scan error {drive_path}: {e}")

        return apps

    def _find_main_exe(self, folder_path, folder_name):
        """Folder name-ஓட match ஆகற exe மட்டும் return பண்ணும்"""
        try:
            exes = []
            for f in os.listdir(folder_path):
                if f.lower().endswith('.exe'):
                    exes.append(f)

            if not exes:
                return None

            folder_lower = folder_name.lower()
            for exe in exes:
                if folder_lower in exe.lower() or exe.lower().replace('.exe', '') in folder_lower:
                    return os.path.join(folder_path, exe)

            return os.path.join(folder_path, exes[0])

        except Exception:
            return None