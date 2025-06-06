import logging
import logging.handlers
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
        """Initialize the logger with configuration."""
        logging_config = config.get('logging')
        
        # Create logs directory if it doesn't exist
        log_dir = Path(logging_config.get('file', 'logs/search_system.log')).parent
        log_dir.mkdir(parents=True, exist_ok=True)
        
        # Create logger
        self.logger = logging.getLogger('search_system')
        self.logger.setLevel(logging_config.get('level', 'INFO'))
        
        # Create formatter
        formatter = logging.Formatter(logging_config.get('format', '%(asctime)s - %(name)s - %(levelname)s - %(message)s'))
        
        # Create file handler with rotation
        file_handler = logging.handlers.RotatingFileHandler(
            logging_config.get('file', 'logs/search_system.log'),
            maxBytes=logging_config.get('max_bytes', 10485760),
            backupCount=logging_config.get('backup_count', 5)
        )
        file_handler.setFormatter(formatter)
        
        # Create console handler
        console_handler = logging.StreamHandler()
        console_handler.setFormatter(formatter)
        
        # Add handlers to logger
        self.logger.addHandler(file_handler)
        self.logger.addHandler(console_handler)
        
        # Prevent duplicate logs
        self.logger.propagate = False

    def get_logger(self):
        """Get the configured logger instance."""
        return self.logger

# Create singleton instance
logger = Logger().get_logger()
