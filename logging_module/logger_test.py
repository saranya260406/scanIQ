import logging
import os
from datetime import datetime
from logging.handlers import RotatingFileHandler


def setup_logger():

    # Create logs folder
    os.makedirs("logs", exist_ok=True)

    # Daily log filename
    log_file = datetime.now().strftime("logs/%Y-%m-%d.log")

    # Log format with milliseconds
    formatter = logging.Formatter(
        '%(asctime)s.%(msecs)03d %(levelname)s [%(name)s] %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )

    # Single log file
    common_handler = RotatingFileHandler(
        filename=log_file,
        maxBytes=5 * 1024 * 1024,
        backupCount=30,
        encoding='utf-8'
    )

    common_handler.setFormatter(formatter)

    # Application Logger
    app_logger = logging.getLogger('ApplicationService')
    app_logger.handlers.clear()
    app_logger.setLevel(logging.INFO)
    app_logger.addHandler(common_handler)

    # Scanner Logger
    scanner_logger = logging.getLogger('ScannerService')
    scanner_logger.handlers.clear()
    scanner_logger.setLevel(logging.INFO)
    scanner_logger.addHandler(common_handler)

    # AI Logger
    ai_logger = logging.getLogger('AIService')
    ai_logger.handlers.clear()
    ai_logger.setLevel(logging.INFO)
    ai_logger.addHandler(common_handler)

    # Export Logger
    export_logger = logging.getLogger('ExportService')
    export_logger.handlers.clear()
    export_logger.setLevel(logging.INFO)
    export_logger.addHandler(common_handler)

    # Error Logger
    error_logger = logging.getLogger('ErrorService')
    error_logger.handlers.clear()
    error_logger.setLevel(logging.ERROR)
    error_logger.addHandler(common_handler)

    return {
        'application': app_logger,
        'scanner': scanner_logger,
        'ai_processing': ai_logger,
        'export': export_logger,
        'error': error_logger
    }


# Test
if __name__ == "__main__":

    logs = setup_logger()

    logs['application'].info("Application started")
    logs['scanner'].info("Software scan completed files=150")
    logs['ai_processing'].info("AI analysis completed findings=25")
    logs['export'].info("CSV export completed")
    logs['error'].error("Sample error")

    print("Log created successfully")