import json
import os
from datetime import datetime
from pathlib import Path
from utils.config import config
from utils.logger import logger

class ResultsStorage:
    def __init__(self, query: str, type_='search'):
        """Initialize results storage with configuration."""
        self.config = config
        self.type = type_  # 'search' or 'scrape'
        self.query = query
        
        # Get base directory
        base_dir = Path(self.config.get('directories.base', 'Data'))
        
        # Create query-based directory
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        safe_query = self._sanitize_query(query)
        query_dir_name = f"{timestamp}_{safe_query}"
        self.query_dir = base_dir / query_dir_name
        
        # Create query directory
        self.query_dir.mkdir(parents=True, exist_ok=True)
        
        # Set subdirectories based on type
        if self.type == 'search':
            results_dir = self.config.get('directories.search.results', 'Search_Results')
            self.results_dir = self.query_dir / results_dir
        else:  # scrape
            scrape_base = self.config.get('directories.scrape.base', 'Scraped_Results')
            self.results_dir = self.query_dir / scrape_base
        
        # Create subdirectories if they don't exist
        if self.type == 'scrape':
            scrape_subdirs = self.config.get('directories.scrape', {})
            for subdir in scrape_subdirs.values():
                if subdir != scrape_base:  # Skip base directory
                    (self.results_dir / subdir).mkdir(parents=True, exist_ok=True)
        
        logger.info(f"ResultsStorage initialized for {self.type} with query directory: {self.query_dir}")

    def _sanitize_query(self, query: str) -> str:
        """Sanitize query string for use in directory name."""
        return query.lower().replace(' ', '_').replace('/', '_').replace('?', '').replace('=', '_')[:50]

    def save_results(self, results: list, metadata: dict = None) -> str:
        """Save search results to a JSON file."""
        filename = "search_results.json"
        filepath = self.results_dir / filename

        result_data = {
            'query': self.query,
            'timestamp': datetime.now().isoformat(),
            'results': results
        }

        if metadata:
            result_data['metadata'] = metadata

        try:
            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(result_data, f, ensure_ascii=False, indent=2)
            logger.info(f"Search results saved to: {filepath}")
            return str(filepath)
        except Exception as e:
            logger.error(f"Failed to save search results: {str(e)}")
            return None

        result_data = {
            'query': query,
            'timestamp': timestamp,
            'results': results
        }

        if metadata:
            result_data['metadata'] = metadata

        try:
            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(result_data, f, ensure_ascii=False, indent=2)
            logger.info(f"Search results saved to: {filepath}")
            return str(filepath)
        except Exception as e:
            logger.error(f"Failed to save search results: {str(e)}")
            return None

    def save_scrape_results(self, url: str, content: str, metadata: dict = None) -> str:
        """Save scrape results to appropriate files."""
        if self.type != 'scrape':
            raise ValueError("This method is only for scrape results")
            
        # Save HTML
        html_filename = f"{self._get_safe_filename(url)}.html"
        html_path = self.results_dir / self.subdirs['html'] / html_filename
        try:
            with open(html_path, 'w', encoding='utf-8') as f:
                f.write(content)
        except Exception as e:
            logger.error(f"Failed to save HTML: {str(e)}")
            
        # Save metadata
        meta_filename = f"{self._get_safe_filename(url)}.json"
        meta_path = self.results_dir / self.subdirs['logs'] / meta_filename
        try:
            with open(meta_path, 'w', encoding='utf-8') as f:
                json.dump(metadata, f, ensure_ascii=False, indent=2)
            logger.info(f"Scrape metadata saved to: {meta_path}")
            return str(meta_path)
        except Exception as e:
            logger.error(f"Failed to save scrape metadata: {str(e)}")
            return None

    def _get_safe_filename(self, url: str) -> str:
        """Create a safe filename from URL."""
        return url.replace('://', '_').replace('/', '_').replace('.', '_').replace(':', '_')[:255]

    def load_results(self, filename: str) -> dict:
        """Load search results from a JSON file."""
        filepath = self.results_dir / filename
        if not filepath.exists():
            logger.error(f"Results file not found: {filepath}")
            return None

        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            logger.error(f"Failed to load results from {filepath}: {str(e)}")
            return None

    def get_latest_results(self) -> dict:
        """Get the most recent results file."""
        files = list(self.results_dir.glob('*.json'))
        if not files:
            logger.warning("No results files found")
            return None
            
        latest_file = max(files, key=os.path.getctime)
        return self.load_results(latest_file.name)
