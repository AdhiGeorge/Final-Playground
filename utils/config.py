import os
import yaml
from dotenv import load_dotenv
from pathlib import Path
from pydantic import ValidationError, BaseModel
from .config_models import AppConfig, SearchConfig, URLValidationConfig, ScrapingConfig, BM25Config, LoggingConfig
import logging

# Basic logger for config loading issues, independent of the main app logger
_config_loader_logger = logging.getLogger('config_loader')
# Configure this basic logger minimally if not already configured elsewhere
if not _config_loader_logger.handlers:
    _handler = logging.StreamHandler()
    _formatter = logging.Formatter('%(asctime)s - config_loader - %(levelname)s - %(message)s')
    _handler.setFormatter(_formatter)
    _config_loader_logger.addHandler(_handler)
    _config_loader_logger.setLevel(logging.INFO)
    _config_loader_logger.propagate = False

class Config:
    _instance = None

    def __new__(cls, *args, **kwargs):
        if cls._instance is None:
            cls._instance = super(Config, cls).__new__(cls)
            cls._instance._initialized = False # Ensure _initialized is set before __init__ is called
        return cls._instance

    def __init__(self):
        # Get the root directory (parent of utils)
        current_dir = Path(__file__).parent
        root_dir = current_dir.parent
        
        # Load environment variables
        env_path = root_dir / ".env"
        if hasattr(self, '_initialized') and self._initialized: # Check if already initialized
            return
        
        load_dotenv(env_path)
        
        # Load YAML config
        self.config_path = config_path = root_dir / "config.yaml"
        if not config_path.exists():
            raise FileNotFoundError(f"Configuration file not found at {config_path}")
            
        with open(config_path, 'r') as f:
            yaml_data = yaml.safe_load(f)
        
        if yaml_data is None:
            _config_loader_logger.error(f"Error parsing YAML file {self.config_path}: invalid YAML.")

        try:
            self.settings = AppConfig(**yaml_data)
            _config_loader_logger.info("Configuration loaded and validated successfully using AppConfig.")
        except ValidationError as e:
            _config_loader_logger.error(f"Configuration validation error: {e}", exc_info=True)
            # Log detailed errors from Pydantic
            for error in e.errors():
                _config_loader_logger.error(f"  Field: {'.'.join(map(str, error['loc']))}, Message: {error['msg']}, Type: {error['type']}")
            detailed_error_message = "\n".join([f"  - Field '{'.'.join(map(str, error['loc']))}': {error['msg']}" for error in e.errors()])
            _config_loader_logger.error(detailed_error_message)
            raise ValueError(detailed_error_message) from e

    def get(self, key_path: str, default=None):
        """
        Retrieves a value from the loaded Pydantic configuration model using a dot-separated key path.
        Example: 'search.max_results' will access config.settings.search.max_results.
        """
        obj = self.settings
        keys = key_path.split('.')
        current_path_trace = []

        for key in keys:
            current_path_trace.append(key)
            if isinstance(obj, BaseModel):  # Pydantic model
                if hasattr(obj, key):
                    obj = getattr(obj, key)
                else:
                    # logger.debug(f"Key '{key}' not found in Pydantic model at path '{'.'.join(current_path_trace)}'. Returning default.")
                    return default
            elif isinstance(obj, dict):  # Dictionary
                if key in obj:
                    obj = obj[key]
                else:
                    # logger.debug(f"Key '{key}' not found in dictionary at path '{'.'.join(current_path_trace)}'. Returning default.")
                    return default
            else:  # Primitive type or list, cannot go deeper with attribute/key access
                # logger.debug(f"Cannot access key '{key}' in non-model/non-dict type ({type(obj)}) at path '{'.'.join(current_path_trace)}'. Returning default.")
                return default
        return obj

    def get_env(self, key, default=None):
        """Get value from environment variables."""
        return os.getenv(key, default)

    @property
    def search_config(self) -> SearchConfig:
        """Get search configuration as a Pydantic model."""
        return self.settings.search

    @property
    def url_validation_config(self) -> URLValidationConfig:
        """Get URL validation configuration as a Pydantic model."""
        return self.settings.url_validation

    @property
    def bm25_config(self) -> BM25Config:
        """Get BM25 configuration as a Pydantic model."""
        return self.settings.bm25

    @property
    def scraping_config(self) -> ScrapingConfig:
        """Get scraping configuration as a Pydantic model."""
        return self.settings.scraping

    @property
    def logging_config(self) -> LoggingConfig:
        """Get logging configuration as a Pydantic model."""
        return self.settings.logging

# Create a singleton instance
config = Config()