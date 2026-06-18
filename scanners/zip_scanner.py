import os
import string
import logging
from datetime import datetime

logger = logging.getLogger(__name__)

class ZipScanner:

    ZIP_EXTENSIONS = ['.zip', '.rar', '.7z', '.tar', '.gz', '.exe', '.msi', '.iso']

    SKIP_FOLDERS = [
        'Windows', 'System Volume Information', '$Recycle.Bin',
        'Recovery', 'PerfLogs', '$WinREAgent', 'Config.Msi',
        'ProgramData', 'Temp', 'tmp', 'Program Files', 
        'Program Files (x86)', 'Users'
    ]

    def _get_scan_paths(self):
        paths = [
            os.path.expanduser("~\\Downloads"),
            os.path.expanduser("~\\Desktop"),
            os.path.expanduser("~\\Documents"),
        ]
        for drive in string.ascii_uppercase:
            drive_path = f"{drive}:\\"
            if drive == "C":
                continue
            if os.path.exists(drive_path):
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

                # Subfolders skip — extracted files வேண்டாம்
                if os.path.isdir(full_path):
                    continue

                ext = os.path.splitext(item)[1].lower()
                if os.path.isfile(full_path) and ext in self.ZIP_EXTENSIONS:
                    size_bytes = os.path.getsize(full_path)
                    size_mb = round(size_bytes / (1024 * 1024), 2)
                    modified_time = os.path.getmtime(full_path)
                    modified_date = datetime.fromtimestamp(modified_time).strftime('%d-%m-%Y %H:%M')
                    files.append({
                        'name': item,
                        'extension': ext,
                        'size_mb': size_mb,
                        'location': full_path,
                        'modified_date': modified_date,
                        'type': 'ZipFile'
                    })
        except Exception as e:
            logger.error(f"Zip scan error {folder_path}: {e}")
        return files