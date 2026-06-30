import json
import os
import sys
import logging

logger = logging.getLogger(__name__)


class SettingsLoader:

    DEFAULTS = {
        "Mode": "scheduled",  # CHANGED: Default to scheduled
        "LogKey": {
            "LogType": 1,
            "Days": 2
        },
        "ExportFolderPath": "exports/",
        "ScanTime": "11:45",  # CHANGED: Default to 11:45
        "GeminiApiKey": ""
    }

    def __init__(self, path=None):
        # If no path provided, find settings.json in project directory
        if path is None:
            if getattr(sys, 'frozen', False):
                # Running as EXE
                project_path = os.path.dirname(sys.executable)
            else:
                # Running as script
                project_path = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
            
            path = os.path.join(project_path, "settings.json")
        
        self.path = os.path.abspath(path)
        self.config = self._load()
        self.config = self._validate(self.config)

    # ---------------- LOAD ----------------
    def _load(self):
        if not os.path.exists(self.path):
            logger.warning(f"Settings file not found: {self.path}. Using defaults.")
            return {}

        try:
            with open(self.path, "r", encoding="utf-8") as f:
                data = json.load(f)
                logger.info(f"Settings loaded from: {self.path}")
                return data if isinstance(data, dict) else {}
        except Exception as e:
            logger.error(f"Error loading settings from {self.path}: {e}. Using defaults.")
            return {}

    # ---------------- VALIDATE ----------------
    def _validate(self, cfg):
        base = self.DEFAULTS.copy()
        base.update(cfg)
        cfg = base
        
        logger.info(f"Settings validation - Mode: {cfg.get('Mode')}, ScanTime: {cfg.get('ScanTime')}, ExportPath: {cfg.get('ExportFolderPath')}")

        # ---------------- MODE ----------------
        mode = cfg.get("Mode", "scheduled").strip().lower()
        if mode not in ["scheduled", "manual"]:
            mode = self.DEFAULTS["Mode"]
        cfg["Mode"] = mode
        logger.debug(f"Mode set to: {mode}")

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
        logger.debug(f"Export path set to: {export_path}")

        # ---------------- SCAN TIME ----------------
        scan_time = str(cfg.get("ScanTime", "")).strip()

        if not self._safe_time(scan_time):
            scan_time = self.DEFAULTS["ScanTime"]
            logger.warning(f"Invalid ScanTime provided. Using default: {scan_time}")
        
        cfg["ScanTime"] = scan_time
        logger.debug(f"Scan time set to: {scan_time}")

        # ---------------- GEMINI API KEY ----------------
        api_key = cfg.get("GeminiApiKey", "").strip()
        cfg["GeminiApiKey"] = api_key

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
                logger.debug(f"Time validation failed: not a string - {type(t)}")
                return False

            h, m = t.split(":")
            h, m = int(h), int(m)
            
            is_valid = 0 <= h <= 23 and 0 <= m <= 59
            if not is_valid:
                logger.debug(f"Time out of range: {t}")
            return is_valid

        except Exception as e:
            logger.debug(f"Time parse error for '{t}': {e}")
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

    def get_api_key(self):
        return self.config.get("GeminiApiKey", "")