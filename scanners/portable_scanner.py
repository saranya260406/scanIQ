import os
import logging
import string

logger = logging.getLogger(__name__)

class PortableScanner:

    SKIP_FOLDERS = {
        'ALL': [
            'Windows', 'System Volume Information', '$Recycle.Bin',
            'Recovery', 'PerfLogs', '$WinREAgent', 'Config.Msi',
            'ProgramData', 'Temp', 'tmp',
        ],
        'C:\\': [
            'Program Files', 'Program Files (x86)', 'Users',
            'Windows', 'System Volume Information', '$Recycle.Bin',
            'Recovery', 'PerfLogs', '$WinREAgent', 'Config.Msi',
            'ProgramData', 'Temp', 'tmp',
            # Inbuilt driver / chipset folders — Windows-oda part, manufacturer factory install pannathu
            'Drivers', 'Intel', 'AMD', 'NVIDIA', 'NVIDIA Corporation',
            'Dell', 'HP', 'Lenovo', 'Realtek', 'Synaptics',
        ]
    }

    def _get_all_drives(self):
        drives = []
        for letter in string.ascii_uppercase:
            drive = f"{letter}:\\"
            if os.path.exists(drive):
                drives.append(drive)
        return drives

    def scan(self):
        apps = []
        drives = self._get_all_drives()
        for drive in drives:
            apps.extend(self._scan_drive(drive))
        logger.info(f"Portable Scanner: {len(apps)} folders found")
        return apps

    def _scan_drive(self, drive_path):
        apps = []
        skip = self.SKIP_FOLDERS.get(drive_path, self.SKIP_FOLDERS['ALL'])
        try:
            for item in os.listdir(drive_path):
                full_path = os.path.join(drive_path, item)
                if not os.path.isdir(full_path):
                    continue
                if item in skip or item.startswith('$'):
                    continue
                if self._has_exe_recursive(full_path):
                    apps.append({
                        'name': item,
                        'publisher': 'Unknown',
                        'version': 'Unknown',
                        'install_location': full_path,
                        'size_mb': None,
                        'type': 'Portable',
                        'source': 'portable'
                    })
        except Exception as e:
            logger.error(f"Portable scan error {drive_path}: {e}")
        return apps

    def _has_exe_recursive(self, folder_path):
        try:
            for root, dirs, files in os.walk(folder_path):
                for f in files:
                    if f.lower().endswith('.exe'):
                        return True
        except Exception:
            pass
        return False
