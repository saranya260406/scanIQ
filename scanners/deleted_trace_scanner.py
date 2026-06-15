import os
import winreg
import logging

logger = logging.getLogger(__name__)

class DeletedTraceScanner:

    def scan(self):
        traces = []
        traces.extend(self._scan_registry_traces())
        traces.extend(self._scan_leftover_folders())
        logger.info(f"Deleted Trace Scanner: {len(traces)} traces found")
        return traces

    def _scan_registry_traces(self):
        traces = []
        # Uninstall registry-ல இருக்கு ஆனா folder இல்லாத apps
        registry_paths = [
            (winreg.HKEY_LOCAL_MACHINE, r"SOFTWARE\Microsoft\Windows\CurrentVersion\Uninstall"),
            (winreg.HKEY_LOCAL_MACHINE, r"SOFTWARE\WOW6432Node\Microsoft\Windows\CurrentVersion\Uninstall"),
            (winreg.HKEY_CURRENT_USER, r"SOFTWARE\Microsoft\Windows\CurrentVersion\Uninstall"),
        ]
        for hive, path in registry_paths:
            try:
                registry_key = winreg.OpenKey(hive, path)
                num_subkeys = winreg.QueryInfoKey(registry_key)[0]
                for i in range(num_subkeys):
                    try:
                        subkey_name = winreg.EnumKey(registry_key, i)
                        subkey = winreg.OpenKey(registry_key, path + "\\" + subkey_name)
                        try:
                            name = winreg.QueryValueEx(subkey, 'DisplayName')[0]
                        except Exception:
                            continue
                        try:
                            location = winreg.QueryValueEx(subkey, 'InstallLocation')[0]
                        except Exception:
                            location = ''
                        # Folder இல்லன்னா — deleted trace!
                        if location and not os.path.exists(location):
                            traces.append({
                                'name': name,
                                'expected_location': location,
                                'trace_type': 'Registry trace — folder missing',
                                'type': 'DeletedTrace'
                            })
                        winreg.CloseKey(subkey)
                    except Exception:
                        continue
                winreg.CloseKey(registry_key)
            except Exception as e:
                logger.error(f"Registry trace scan error: {e}")
        return traces

    def _scan_leftover_folders(self):
        traces = []
        # Common leftover folders
        check_paths = [
            r"C:\Program Files",
            r"C:\Program Files (x86)",
        ]
        known_publishers = [
            'Adobe', 'Microsoft', 'Google', 'Mozilla',
            'Blizzard', 'Epic Games', 'Steam', 'Valve'
        ]
        for base_path in check_paths:
            if not os.path.exists(base_path):
                continue
            try:
                for folder in os.listdir(base_path):
                    full_path = os.path.join(base_path, folder)
                    if not os.path.isdir(full_path):
                        continue
                    # Folder empty-ஆ இருந்தா leftover
                    contents = os.listdir(full_path)
                    if len(contents) == 0:
                        traces.append({
                            'name': folder,
                            'expected_location': full_path,
                            'trace_type': 'Empty leftover folder',
                            'type': 'DeletedTrace'
                        })
            except Exception as e:
                logger.error(f"Leftover folder scan error: {e}")
        return traces