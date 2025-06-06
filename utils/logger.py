import logging
from typing import Optional
from pathlib import Path
from utils.config import config

class Logger:
    _instance = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(Logger, cls).__new__(cls)
            cls._instance._initialize_logger()
        return cls._instance
    
    def _initialize_logger(self):
        self.logger = logging.getLogger(__name__)
        logging_config = config.settings.logging
        
        # Set log level
        self.logger.setLevel(logging_config.level)
        
        # Create formatter
        formatter = logging.Formatter(logging_config.format)
        
        # Console handler
        console_handler = logging.StreamHandler()
        console_handler.setFormatter(formatter)
        self.logger.addHandler(console_handler)
        
        # File handler if specified
        if logging_config.file:
            file_path = Path(logging_config.file)
            file_path.parent.mkdir(parents=True, exist_ok=True)
            file_handler = logging.FileHandler(file_path)
            file_handler.setFormatter(formatter)
            self.logger.addHandler(file_handler)
    
    def get_logger(self):
        return self.logger

logger = Logger().get_logger()
