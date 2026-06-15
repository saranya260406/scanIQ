import logging
import os
from logging.handlers import RotatingFileHandler

def setup_logger():
    """
    4 log files setup பண்ணும்:
    - application.log
    - scanner.log
    - ai_processing.log
    - export.log
    - error.log
    """
    os.makedirs('logs', exist_ok=True)

    log_format = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    formatter = logging.Formatter(log_format)

    # 1. Application log — General info
    app_logger = logging.getLogger('application')
    app_logger.setLevel(logging.INFO)
    app_handler = RotatingFileHandler('logs/application.log', maxBytes=5*1024*1024, backupCount=3)
    app_handler.setFormatter(formatter)
    app_logger.addHandler(app_handler)

    # 2. Scanner log — Scanner details
    scanner_logger = logging.getLogger('scanner')
    scanner_logger.setLevel(logging.DEBUG)
    scanner_handler = RotatingFileHandler('logs/scanner.log', maxBytes=5*1024*1024, backupCount=3)
    scanner_handler.setFormatter(formatter)
    scanner_logger.addHandler(scanner_handler)

    # 3. AI Processing log — Gemini API calls
    ai_logger = logging.getLogger('ai_processing')
    ai_logger.setLevel(logging.DEBUG)
    ai_handler = RotatingFileHandler('logs/ai_processing.log', maxBytes=5*1024*1024, backupCount=3)
    ai_handler.setFormatter(formatter)
    ai_logger.addHandler(ai_handler)

    # 4. Export log — CSV export details
    export_logger = logging.getLogger('export')
    export_logger.setLevel(logging.INFO)
    export_handler = RotatingFileHandler('logs/export.log', maxBytes=5*1024*1024, backupCount=3)
    export_handler.setFormatter(formatter)
    export_logger.addHandler(export_handler)

    # 5. Error log — எல்லா errors-உம்
    error_logger = logging.getLogger('error')
    error_logger.setLevel(logging.ERROR)
    error_handler = RotatingFileHandler('logs/error.log', maxBytes=5*1024*1024, backupCount=3)
    error_handler.setFormatter(formatter)
    error_logger.addHandler(error_handler)

    # Console handler — terminal-லயும் காட்டும்
    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.INFO)
    console_handler.setFormatter(formatter)

    # Root logger-க்கு console add பண்ணும்
    root_logger = logging.getLogger()
    root_logger.setLevel(logging.DEBUG)
    root_logger.addHandler(console_handler)

    return {
        'application': app_logger,
        'scanner': scanner_logger,
        'ai_processing': ai_logger,
        'export': export_logger,
        'error': error_logger
    }