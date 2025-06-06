import os
import yaml
from dotenv import load_dotenv
from pathlib import Path

class Config:
    def __init__(self):
        # Get the root directory (parent of utils)
        current_dir = Path(__file__).parent
        root_dir = current_dir.parent
        
        # Load environment variables
        env_path = root_dir / ".env"
        load_dotenv(env_path)
        
        # Load YAML config
        config_path = root_dir / "config.yaml"
        if not config_path.exists():
            raise FileNotFoundError(f"Configuration file not found at {config_path}")
            
        with open(config_path, 'r') as f:
            self.yaml_config = yaml.safe_load(f)

    def get(self, key, default=None):
        """Get value from YAML config using dot notation."""
        keys = key.split('.')
        current = self.yaml_config
        for k in keys:
            if isinstance(current, dict) and k in current:
                current = current[k]
            else:
                return default
        return current

    def get_env(self, key, default=None):
        """Get value from environment variables."""
        return os.getenv(key, default)

    @property
    def search_config(self):
        """Get search configuration."""
        return self.get('search')

    @property
    def url_validation_config(self):
        """Get URL validation configuration."""
        return self.get('url_validation')

    @property
    def bm25_config(self):
        """Get BM25 configuration."""
        return self.get('bm25')

# Create a singleton instance
config = Config()