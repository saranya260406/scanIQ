import os
import string
import logging
import zipfile
from datetime import datetime

logger = logging.getLogger(__name__)

class ZipScanner:

    SCAN_PATHS_USER = [
        os.path.expanduser("~\\Downloads"),
        os.path.expanduser("~\\Desktop"),
        os.path.expanduser("~\\Documents"),
    ]

    SKIP_FOLDERS = [
        'Windows', 'System Volume Information', '$Recycle.Bin',
        'Recovery', 'PerfLogs', '$WinREAgent', 'Config.Msi',
        'ProgramData', 'Temp', 'tmp', 'Program Files',
        'Program Files (x86)', 'Users'
    ]

    def _get_scan_paths(self):
        paths = list(self.SCAN_PATHS_USER)
        for drive in string.ascii_uppercase:
            if drive == "C":
                continue
            drive_path = f"{drive}:\\"
            if os.path.exists(drive_path):
                try:
                    for item in os.listdir(drive_path):
                        full_path = os.path.join(drive_path, item)
                        if os.path.isdir(full_path) and item not in self.SKIP_FOLDERS and not item.startswith('$'):
                            paths.append(full_path)
                except Exception:
                    pass
                paths.append(drive_path)
        return paths

    def scan(self):
        files = []
        for path in self._get_scan_paths():
            if os.path.exists(path):
                files.extend(self._scan_folder(path))
        logger.info(f"Zip Scanner: {len(files)} files found")
        return files

    def _scan_folder(self, folder_path):
        files = []
        try:
            for item in os.listdir(folder_path):
                full_path = os.path.join(folder_path, item)
                if os.path.isdir(full_path):
                    continue
                ext = os.path.splitext(item)[1].lower()
                if ext == '.zip':
                    # Zip-ல exe இருந்தா zip name மட்டும்
                    if self._has_exe_inside(full_path):
                        size_mb = round(os.path.getsize(full_path) / (1024 * 1024), 2)
                        files.append({
                            'name': os.path.splitext(item)[0],
                            'extension': '.zip',
                            'size_mb': size_mb,
                            'location': full_path,
                            'install_location': full_path,
                            'modified_date': datetime.fromtimestamp(
                                os.path.getmtime(full_path)
                            ).strftime('%d-%m-%Y %H:%M'),
                            'type': 'ZipFile',
                            'source': 'ZipFile'
                        })
        except Exception as e:
            logger.error(f"Zip scan error {folder_path}: {e}")
        return files

    def _has_exe_inside(self, zip_path):
        try:
            with zipfile.ZipFile(zip_path, 'r') as zf:
                for name in zf.namelist():
                    if name.lower().endswith('.exe'):
                        return True
        except Exception:
            pass
        return False