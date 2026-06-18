import os
import string
import logging
from datetime import datetime

logger = logging.getLogger(__name__)

class ZipScanner:

    ZIP_EXTENSIONS = ['.zip', '.rar', '.7z', '.tar', '.gz', '.exe', '.msi', '.iso']

    def _get_scan_paths(self):
        paths = [
            os.path.expanduser("~\\Downloads"),
            os.path.expanduser("~\\Desktop"),
            os.path.expanduser("~\\Documents"),
        ]
        for drive in string.ascii_uppercase:
            if drive == "C":
                continue
            drive_path = f"{drive}:\\"
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

    def _scan_folder(self, folder_path, depth=0, max_depth=3):
        files = []
        if depth > max_depth:
            return files
        try:
            for item in os.listdir(folder_path):
                full_path = os.path.join(folder_path, item)

                # Subfolder — recursive scan
                if os.path.isdir(full_path):
                    files.extend(self._scan_folder(full_path, depth + 1, max_depth))

                # File — extension check
                elif os.path.isfile(full_path):
                    ext = os.path.splitext(item)[1].lower()
                    if ext in self.ZIP_EXTENSIONS:
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