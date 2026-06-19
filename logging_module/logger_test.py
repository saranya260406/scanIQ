import logging
import os
from datetime import datetime


def setup_logger():
    # logs folder create
    os.makedirs("logs", exist_ok=True)

    # Daily log file
    log_file = os.path.join(
        "logs",
        f"{datetime.now().strftime('%Y-%m-%d_%H-%M')}.log"
)

    # Root logger
    logger = logging.getLogger()
    logger.setLevel(logging.DEBUG)

    # Duplicate handlers avoid
    if logger.handlers:
        logger.handlers.clear()

    # File handler
    file_handler = logging.FileHandler(
        log_file,
        mode="a",
        encoding="utf-8"
    )

    # Format
    formatter = logging.Formatter(
        "%(asctime)s | %(levelname)s | %(message)s",
        datefmt="%H:%M"
    )

    file_handler.setFormatter(formatter)
    logger.addHandler(file_handler)

    # Existing code compatibility
    return {
        "application": logger,
        "scanner": logger,
        "ai_processing": logger,
        "export": logger,
        "error": logger
    }