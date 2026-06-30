"""
Real-Time App File Watcher
Downloads/Desktop/Documents/etc -la app installer (.exe/.msi)
allathu archive (.zip/.rar/.7z) file pudhusa varum udane,
installer process exit aaguravaraikkum wait pannitu,
full system scan trigger aagi puthu CSV create aagum.
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

WATCH_EXTENSIONS = {
    '.exe', '.msi', '.msix', '.msixbundle', '.appx', '.appxbundle',
    '.zip', '.rar', '.7z',
}

SKIP_FOLDERS = {
    'windows', 'system volume information', '$recycle.bin',
    'recovery', 'perflogs', 'programdata', 'temp', 'tmp',
    'node_modules', '__pycache__', '.git', 'appdata',
    'program files', 'program files (x86)',
    'windowsapps', 'winsxs', 'servicing',
}

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
    App installer/archive file detect aana udane:
    - .exe/.msi: fixed wait pannitu (install mudikkura time kuduthu)
    - .zip/.rar/.7z: konjam wait pannitu
    apparam scan trigger pannum.

    Scan already RUNNING-na, puthu request "pending"-ah mark pannitu,
    current scan mudinjadhum automatic-ah next scan start aagum
    (skip pannaadhu - queue pannum).
    """

    ZIP_WAIT_SECONDS = 5
    INSTALL_WAIT_SECONDS = 45  # installer download + run aagi mudikkura time

    def __init__(self, scan_callback=None):
        super().__init__()
        self.scan_callback = scan_callback
        self._lock = threading.Lock()
        self._scan_running = False
        self._scan_pending = False
        self._pending_name = None

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

        log.info(f"App/installer file detected: {name}")
        print(f"\nNew app/installer detected: {name}")

        threading.Thread(
            target=self._wait_and_trigger,
            args=(ext, name),
            daemon=True
        ).start()

    def _wait_and_trigger(self, ext, name):
        if ext in ('.zip', '.rar', '.7z'):
            log.info(f"'{name}' is an archive - waiting {self.ZIP_WAIT_SECONDS}s")
            time.sleep(self.ZIP_WAIT_SECONDS)
        else:
            log.info(f"Waiting {self.INSTALL_WAIT_SECONDS}s for '{name}' to finish installing...")
            time.sleep(self.INSTALL_WAIT_SECONDS)

        self._request_scan(name)

    def _request_scan(self, name):
        """
        Scan already run aaguthunna, indha request-ah pending-ah
        mark pannrom - skip pannaadhu. Current scan mudinjadhum,
        automatic-ah oru extra scan run aagum (pending request-ku).
        """
        with self._lock:
            self._pending_name = name
            if self._scan_running:
                log.info(f"Scan already running - queuing scan for '{name}' after current scan finishes")
                self._scan_pending = True
                return
            self._scan_running = True

        self._run_scan_loop()

    def _run_scan_loop(self):
        """
        Scan run pannitu, run aagikkitu irukkura nerathula
        innoru file vandhu pending mark aana, andha scan-um
        immediate-ah apparam run aagum.
        """
        while True:
            with self._lock:
                current_name = self._pending_name

            if self.scan_callback:
                try:
                    self.scan_callback(detected_file={'name': current_name})
                except TypeError:
                    # scan_callback detected_file accept pannaatha fallback
                    try:
                        self.scan_callback()
                    except Exception as e:
                        log.error(f"Scan callback error: {e}")
                except Exception as e:
                    log.error(f"Scan callback error: {e}")
            else:
                log.warning("No scan_callback set - cannot trigger scan")

            with self._lock:
                if self._scan_pending:
                    self._scan_pending = False
                    continue  # innoru scan run pannrom
                else:
                    self._scan_running = False
                    break


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