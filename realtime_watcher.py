"""
Real-Time File/App Watcher
Ella drives layum (C:, D:, E: etc.) continuously watch paNNi,
pudhusa edhachum file/app varum udane — main.py scan pannura
SAME format-la, SAME single combined CSV-la add paNNum.

Run pannanum: python realtime_watcher.py
(Idhu background-la continuous run aagum — Ctrl+C pannina mattum stop aagum)
"""

import os
import sys
import time
import string
import logging
import csv
import glob
from datetime import datetime

try:
    from watchdog.observers import Observer
    from watchdog.events import FileSystemEventHandler
except ImportError:
    print("watchdog package illa! Install pannunga:")
    print("    pip install watchdog")
    sys.exit(1)

# ── Config ────────────────────────────────────────────────────────────────────

# Category mapping — same logic as user_files_scanner.py
CATEGORY_MAP = {
    '.pdf': 'Document', '.doc': 'Document', '.docx': 'Document',
    '.xls': 'Document', '.xlsx': 'Document', '.ppt': 'Document',
    '.pptx': 'Document', '.txt': 'Document', '.rtf': 'Document',
    '.odt': 'Document', '.ods': 'Document', '.odp': 'Document',
    '.csv': 'Document',

    '.zip': 'Archive', '.rar': 'Archive', '.7z': 'Archive',
    '.tar': 'Archive', '.gz': 'Archive', '.cab': 'Archive',
    '.iso': 'Archive', '.img': 'Archive',

    '.exe': 'Installer', '.msi': 'Installer', '.msix': 'Installer',
    '.msixbundle': 'Installer', '.appx': 'Installer',
    '.appxbundle': 'Installer', '.setup': 'Installer',

    '.mp3': 'Audio', '.wav': 'Audio', '.flac': 'Audio',
    '.aac': 'Audio', '.ogg': 'Audio', '.wma': 'Audio', '.m4a': 'Audio',

    '.py': 'Code', '.js': 'Code', '.ts': 'Code', '.java': 'Code',
    '.cs': 'Code', '.cpp': 'Code', '.c': 'Code', '.go': 'Code',
    '.html': 'Code', '.css': 'Code', '.php': 'Code', '.rb': 'Code',
    '.sh': 'Code', '.bat': 'Code', '.ps1': 'Code', '.sql': 'Code',

    '.json': 'Data', '.xml': 'Data', '.yaml': 'Data', '.yml': 'Data',
    '.sqlite': 'Data', '.ini': 'Data', '.cfg': 'Data', '.conf': 'Data',

    '.lnk': 'Shortcut', '.url': 'Shortcut',
}

# Images & videos — skip (same as user_files_scanner.py)
SKIP_EXTENSIONS = {
    '.jpg', '.jpeg', '.png', '.gif', '.bmp', '.webp',
    '.tiff', '.tif', '.raw', '.heic', '.heif', '.svg',
    '.ico', '.psd', '.ai', '.eps',
    '.mp4', '.avi', '.mkv', '.mov', '.wmv', '.flv',
    '.webm', '.m4v', '.3gp', '.mpeg', '.mpg', '.ts',
    '.db', '.thumbs', '.tmp', '.crdownload', '.partial',
}

PROJECT_DIR = os.path.dirname(os.path.abspath(__file__))
OUTPUT_DIR  = os.path.join(PROJECT_DIR, "exports")
LOG_DIR     = os.path.join(PROJECT_DIR, "logs")
os.makedirs(OUTPUT_DIR, exist_ok=True)
os.makedirs(LOG_DIR, exist_ok=True)

# Exact same columns as csv_exporter.py
CSV_FIELDS = [
    'Name', 'Publisher', 'Version', 'Category', 'Risk Level',
    'Recommendation', 'AI Description', 'Installed On', 'Size',
    'Install Location', 'Drive', 'Source',
]

SKIP_FOLDERS = {
    'windows', 'system volume information', '$recycle.bin',
    'recovery', 'perflogs', 'programdata', 'temp', 'tmp',
    'node_modules', '__pycache__', '.git', 'appdata',
}

# ── Logging ───────────────────────────────────────────────────────────────────

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[
        logging.FileHandler(os.path.join(LOG_DIR, "realtime_watcher.log"), encoding="utf-8"),
        logging.StreamHandler(sys.stdout),
    ],
)
log = logging.getLogger("RealTimeWatcher")


# ── Helpers ───────────────────────────────────────────────────────────────────

def should_skip(path: str) -> bool:
    path_lower = path.lower()
    return any(f"\\{skip}\\" in path_lower or path_lower.endswith(f"\\{skip}") for skip in SKIP_FOLDERS)


def get_all_drives() -> list[str]:
    drives = []
    for letter in string.ascii_uppercase:
        drive = f"{letter}:\\"
        if os.path.exists(drive):
            drives.append(drive)
    return drives


def format_size(size_mb: float) -> str:
    if size_mb >= 1024:
        return f"{round(size_mb / 1024, 2)} GB"
    return f"{round(size_mb, 2)} MB"


def find_main_csv() -> str:
    """
    Find the SAME single combined CSV that main.py produces.
    If main.py hasn't run yet, fall back to a fixed-name file
    so real-time entries are never lost — main.py will then
    append into this same file on its next run too.
    """
    matches = glob.glob(os.path.join(OUTPUT_DIR, "Software_Inventory_ALL_*.csv"))
    if matches:
        return max(matches, key=os.path.getmtime)
    return os.path.join(OUTPUT_DIR, "Software_Inventory_ALL.csv")


def append_row_to_csv(csv_path: str, record: dict):
    file_exists = os.path.exists(csv_path)
    with open(csv_path, "a", newline="", encoding="utf-8-sig") as f:
        writer = csv.DictWriter(f, fieldnames=CSV_FIELDS, extrasaction="ignore")
        if not file_exists:
            writer.writeheader()
        writer.writerow(record)


# ── Event Handler ─────────────────────────────────────────────────────────────

class FileWatchHandler(FileSystemEventHandler):

    def on_created(self, event):
        if event.is_directory:
            return
        self._handle_file(event.src_path)

    def on_moved(self, event):
        if event.is_directory:
            return
        self._handle_file(event.dest_path)

    def _handle_file(self, path: str):
        ext = os.path.splitext(path)[1].lower()

        # Skip images, videos, temp/partial download files
        if ext in SKIP_EXTENSIONS:
            return
        if should_skip(path):
            return

        # Wait briefly — file might still be writing (large downloads)
        time.sleep(1.5)

        try:
            if not os.path.exists(path):
                return

            size_mb  = round(os.path.getsize(path) / (1024 * 1024), 2)
            drive    = os.path.splitdrive(path)[0].upper()
            name     = os.path.basename(path)
            category = CATEGORY_MAP.get(ext, 'Other')

            record = {
                'Name':              name,
                'Publisher':         'Unknown',
                'Version':           'Unknown',
                'Category':          category,
                'Risk Level':        '',
                'Recommendation':    '',
                'AI Description':    '',
                'Installed On':      datetime.now().strftime('%d-%m-%Y'),
                'Size':              format_size(size_mb),
                'Install Location':  path,
                'Drive':             drive,
                'Source':            'RealTimeDownload',
            }

            main_csv = find_main_csv()
            append_row_to_csv(main_csv, record)

            log.info(f"NEW FILE DETECTED → {name} ({size_mb} MB) on {drive} → added to {main_csv}")
            print(f"\n🔔 New file detected: {name}")
            print(f"   Category: {category}  |  Drive: {drive}  |  Size: {format_size(size_mb)}")
            print(f"   Added to: {os.path.basename(main_csv)}\n")

        except (PermissionError, OSError) as e:
            log.warning(f"Could not process {path}: {e}")
        except Exception as e:
            log.error(f"Error processing {path}: {e}")


# ── Main Watcher ──────────────────────────────────────────────────────────────

def main():
    print("=" * 55)
    print("  Real-Time File Watcher — Started")
    print("=" * 55)

    drives = get_all_drives()
    log.info(f"Watching drives: {drives}")
    print(f"Watching drives: {', '.join(drives)}")
    print(f"Tracking ALL file types (images/videos excluded)")
    print(f"Writing to single combined CSV in: {OUTPUT_DIR}")
    print("\nPress Ctrl+C to stop.\n")
    print("=" * 55)

    observer = Observer()
    handler  = FileWatchHandler()

    watched_count = 0
    for drive in drives:
        try:
            observer.schedule(handler, drive, recursive=True)
            watched_count += 1
        except Exception as e:
            log.error(f"Could not watch {drive}: {e}")

    if watched_count == 0:
        log.error("No drives could be watched. Exiting.")
        return

    observer.start()
    log.info(f"Watcher started on {watched_count} drive(s).")

    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        observer.stop()
        log.info("Watcher stopped by user.")
        print("\nStopped.")

    observer.join()


if __name__ == "__main__":
    main()