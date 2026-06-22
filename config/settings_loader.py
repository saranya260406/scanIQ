import json
import os

class SettingsLoader:
    def __init__(self, path="settings.json"):
        self.path = path
        self.config = self._load()

    def _load(self):
        if not os.path.exists(self.path):
            raise FileNotFoundError("settings.json not found")

        with open(self.path, "r") as f:
            return json.load(f)

    def get(self):
        return self.config

    def get_log_config(self):
        return self.config.get("LogKey", {})

    def get_export_path(self):
        return self.config.get("ExportFolderPath", "exports/")

    def get_scan_time(self):
        return self.config.get("ScanTime", "00:00")