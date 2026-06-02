import logging
import os
from logging.handlers import RotatingFileHandler
import sys

# Ensure logs directory exists
LOG_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), "logs")
os.makedirs(LOG_DIR, exist_ok=True)

class KatibLogger:
    _instance = None
    
    @staticmethod
    def get_logger(name="Katib"):
        if KatibLogger._instance is None:
            KatibLogger._instance = KatibLogger._setup_logger(name)
        return KatibLogger._instance
    
    @staticmethod
    def _setup_logger(name):
        logger = logging.getLogger(name)
        logger.setLevel(logging.INFO)
        
        # Avoid adding handlers multiple times if logger is already configured
        if logger.hasHandlers():
            return logger
            
        # File Handler (Rotating)
        log_file = os.path.join(LOG_DIR, "katib.log")
        file_handler = RotatingFileHandler(log_file, maxBytes=5*1024*1024, backupCount=3)
        file_formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
        file_handler.setFormatter(file_formatter)
        
        # Console Handler
        console_handler = logging.StreamHandler(sys.stdout)
        console_formatter = logging.Formatter('%(message)s') # Keep console clean, file detailed
        console_handler.setFormatter(console_formatter)
        
        logger.addHandler(file_handler)
        logger.addHandler(console_handler)
        
        return logger

# Convenience function
def get_logger(name="Katib"):
    return KatibLogger.get_logger(name)
