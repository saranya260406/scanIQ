import os
import logging
from datetime import datetime, timedelta


class LogTypeFilter(logging.Filter):

    def __init__(self, log_type):
        super().__init__()

        if log_type == 1:
            self.allowed = {
                logging.INFO,
                logging.WARNING
            }
        else:
            self.allowed = {
                logging.ERROR,
                logging.DEBUG
            }

    def filter(self, record):
        return record.levelno in self.allowed


class LogConfig:

    def __init__(self, settings):
        self.settings = settings
        self.log_cfg = settings.get_log_config()

    def setup_logging(self):

        self.cleanup_old_logs()

        os.makedirs("logs", exist_ok=True)

        log_file = os.path.join(
            "logs",
            f"{datetime.now().strftime('%Y-%m-%d')}.log"
        )

        formatter = logging.Formatter(
            "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
        )

        handler = logging.FileHandler(
            log_file,
            encoding="utf-8"
        )

        handler.setFormatter(formatter)

        log_type = self.log_cfg.get("LogType", 1)
        handler.addFilter(LogTypeFilter(log_type))

        logger_names = [
            "application",
            "scanner",
            "ai_processing"
        ]

        loggers = {}

        for name in logger_names:

            logger = logging.getLogger(name)

            logger.setLevel(logging.DEBUG)

            # duplicate handler avoid
            logger.handlers.clear()

            logger.addHandler(handler)

            loggers[name] = logger

        return loggers

    def cleanup_old_logs(self):

        days = self.log_cfg.get("Days", 7)

        cutoff = datetime.now() - timedelta(days=days)

        if not os.path.exists("logs"):
            return

        for file in os.listdir("logs"):

            file_path = os.path.join("logs", file)

            if os.path.isfile(file_path):

                created = datetime.fromtimestamp(
                    os.path.getctime(file_path)
                )

                if created < cutoff:
                    os.remove(file_path)