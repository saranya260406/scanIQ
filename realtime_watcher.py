"""
Real-Time App File Watcher
Downloads/Desktop/Documents/etc -la app installer (.exe/.msi)
allathu archive (.zip/.rar/.7z) file pudhusa varum udane,
full system scan trigger aagi, scheduled scan mathiri puthu CSV create aagum.
Photo, video, doc, txt - ellame ignore aagum.
"""

import os
import sys
import time
import string
import logging
import threading

try:
    from watchdog.observers import Observer
    from watchdog.events import FileSystemEventHandler
except ImportError:
    print("watchdog package illa! Install pannunga:")
    print("    pip install watchdog")
    sys.exit(1)

# Indha extensions mattum trigger pannum - installer + archive (zip-ku exe irukkalam)
WATCH_EXTENSIONS = {
    '.exe', '.msi', '.msix', '.msixbundle', '.appx', '.appxbundle',
    '.zip', '.rar', '.7z',
}

# System folders skip
SKIP_FOLDERS = {
    'windows', 'system volume information', '$recycle.bin',
    'recovery', 'perflogs', 'programdata', 'temp', 'tmp',
    'node_modules', '__pycache__', '.git', 'appdata',
    'program files', 'program files (x86)',
    'windowsapps', 'winsxs', 'servicing',
}

# User folders mattum watch
WATCH_FOLDERS = {
    'downloads', 'desktop', 'documents', 'videos', 'music',
    'pictures', 'onedrive',
}

if getattr(sys, 'frozen', False):
    PROJECT_DIR = os.path.dirname(sys.executable)
else:
    PROJECT_DIR = os.path.dirname(os.path.abspath(__file__))

LOG_DIR = os.path.join(PROJECT_DIR, "logs")
os.makedirs(LOG_DIR, exist_ok=True)

log = logging.getLogger("application")


def should_skip(path: str) -> bool:
    path_lower = path.lower()
    for skip in SKIP_FOLDERS:
        if f"\\{skip}\\" in path_lower or path_lower.endswith(f"\\{skip}"):
            return True
    return False


def is_user_folder(path: str) -> bool:
    path_lower = path.lower()
    for watch in WATCH_FOLDERS:
        if f"\\{watch}\\" in path_lower or f"\\{watch}" in path_lower:
            return True
    drive = os.path.splitdrive(path)[0].upper()
    if drive != "C:":
        return True
    return False


def get_all_drives() -> list:
    drives = []
    for letter in string.ascii_uppercase:
        drive = f"{letter}:\\"
        if os.path.exists(drive):
            drives.append(drive)
    return drives


class FileWatchHandler(FileSystemEventHandler):
    """
    App installer/archive file detect aana udane scan_callback() call panni
    full scan trigger pannum. 15 seconds debounce - multiple files ஒரே
    நேரத்தில் வந்தாலும் ஒரே scan-ல சேரும்.
    """

    DEBOUNCE_SECONDS = 15

    def __init__(self, scan_callback=None):
        super().__init__()
        self.scan_callback = scan_callback
        self._last_trigger = 0
        self._lock = threading.Lock()

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
        name = os.path.basename(path)

        if ext not in WATCH_EXTENSIONS:
            return
        if should_skip(path):
            return
        if not is_user_folder(path):
            return

        time.sleep(1.5)
        if not os.path.exists(path):
            return

        log.info(f"App/installer file detected: {name} -> triggering full scan")
        print(f"\nNew app/installer detected: {name}")

        self._trigger_scan()

    def _trigger_scan(self):
        with self._lock:
            now = time.time()
            if now - self._last_trigger < self.DEBOUNCE_SECONDS:
                log.info("Scan already triggered recently - skipping duplicate")
                return
            self._last_trigger = now

        if self.scan_callback:
            threading.Thread(target=self.scan_callback, daemon=True).start()
        else:
            log.warning("No scan_callback set - cannot trigger scan")


def main():
    """Standalone test mode - callback illama, detection mattum log pannum."""
    print("=" * 55)
    print("  Real-Time File Watcher - Started (standalone test)")
    print("=" * 55)

    drives = get_all_drives()
    log.info(f"Watching drives: {drives}")
    print(f"Watching drives: {', '.join(drives)}")
    print("\nPress Ctrl+C to stop.\n")

    observer = Observer()
    handler = FileWatchHandler()

    for drive in drives:
        try:
            observer.schedule(handler, drive, recursive=True)
        except Exception as e:
            log.error(f"Could not watch {drive}: {e}")

    observer.start()
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        observer.stop()
        print("\nStopped.")
    observer.join()


if __name__ == "__main__":
    main()