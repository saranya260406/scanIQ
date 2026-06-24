import json
import os


class SettingsLoader:

    DEFAULTS = {
        "Mode": "manual",
        "LogKey": {
            "LogType": 1,
            "Days": 2
        },
        "ExportFolderPath": "exports/",
        "ScanTime": "10:00"
    }

    def __init__(self, path="settings.json"):
        self.path = path
        self.config = self._load()
        self.config = self._validate(self.config)

    # ---------------- LOAD ----------------
    def _load(self):
        if not os.path.exists(self.path):
            return {}

        try:
            with open(self.path, "r", encoding="utf-8") as f:
                data = json.load(f)
                return data if isinstance(data, dict) else {}
        except Exception:
            return {}

    # ---------------- VALIDATE ----------------
    def _validate(self, cfg):

        base = self.DEFAULTS.copy()
        base.update(cfg)
        cfg = base

        # ---------------- MODE ----------------
        if cfg.get("Mode") not in ["scheduled", "manual"]:
            cfg["Mode"] = self.DEFAULTS["Mode"]

        # ---------------- LOGKEY ----------------
        log = cfg.get("LogKey", {})

        # ---- LogType (empty / null / invalid safe) ----
        log_type = self._safe_int(
            log.get("LogType"),
            self.DEFAULTS["LogKey"]["LogType"],
            allowed=[1, 2]
        )

        # ---- Days (empty / null / invalid safe) ----
        days = self._safe_int(
            log.get("Days"),
            self.DEFAULTS["LogKey"]["Days"],
            min_value=1
        )

        cfg["LogKey"] = {
            "LogType": log_type,
            "Days": days
        }

        # ---------------- EXPORT PATH ----------------
        export_path = cfg.get("ExportFolderPath")

        if not self._safe_path(export_path):
            export_path = self.DEFAULTS["ExportFolderPath"]

        export_path = os.path.abspath(export_path)
        os.makedirs(export_path, exist_ok=True)

        cfg["ExportFolderPath"] = export_path

        # ---------------- SCAN TIME ----------------
        scan_time = cfg.get("ScanTime")

        if not self._safe_time(scan_time):
            scan_time = self.DEFAULTS["ScanTime"]

        cfg["ScanTime"] = scan_time

        return cfg

    # ---------------- SAFE INT ----------------
    def _safe_int(self, value, default, allowed=None, min_value=None):

        try:
            value = int(value)

            if allowed and value not in allowed:
                return default

            if min_value is not None and value < min_value:
                return default

            return value

        except Exception:
            return default

    # ---------------- SAFE PATH ----------------
    def _safe_path(self, path):

        if not path:
            return False
        if not isinstance(path, str):
            return False
        if path.strip() == "":
            return False

        try:
            abs_path = os.path.abspath(path)
            drive = os.path.splitdrive(abs_path)[0]

            if drive and not os.path.exists(drive + "\\"):
                return False

            return True
        except Exception:
            return False

    # ---------------- SAFE TIME ----------------
    def _safe_time(self, t):

        try:
            if not isinstance(t, str):
                return False

            h, m = t.split(":")
            h, m = int(h), int(m)

            return 0 <= h <= 23 and 0 <= m <= 59

        except Exception:
            return False

    # ---------------- GETTERS ----------------
    def get(self):
        return self.config

    def get_log_config(self):
        return self.config.get("LogKey", self.DEFAULTS["LogKey"])

    def get_export_path(self):
        return self.config.get("ExportFolderPath", self.DEFAULTS["ExportFolderPath"])

    def get_scan_time(self):
        return self.config.get("ScanTime", self.DEFAULTS["ScanTime"])

    def get_mode(self):
        return self.config.get("Mode", self.DEFAULTS["Mode"])