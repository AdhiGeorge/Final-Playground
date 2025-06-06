from typing import Dict, List, Any
from tenacity import retry, stop_after_attempt, wait_exponential
import logging
import os
from utils.logger import logger

class SearchManager:
    def __init__(self, search_engines: Dict[str, Any], config: Dict[str, Any]):
        """Initialize search manager with engines and configuration."""
        self.search_engines = search_engines
        self.max_results = config.get('max_results', 10)
        self.fallback_order = config.get('fallback_order', ['duckduckgo', 'tavily', 'google'])
        self.retry_config = config.get('retry', {})
        logger.info(f"Initialized SearchManager with max_results={self.max_results} and fallback_order={self.fallback_order}")

    def _get_retry_config(self):
        """Get retry configuration from config."""
        return {
            'stop': stop_after_attempt(self.retry_config.get('max_attempts', 3)),
            'wait': wait_exponential(
                multiplier=self.retry_config.get('wait_exponential_multiplier', 1000),
                max=self.retry_config.get('wait_exponential_max', 10000)
            )
        }

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1000, max=10000)
    )
    def _perform_search(self, query: str) -> List[str]:
        """Internal method to perform search."""
        logger.info(f"Starting search for query: {query}")
        all_results = []
        
        # Get results from all search engines
        for engine_name in self.fallback_order:
            try:
                logger.info(f"Searching with {engine_name}...")
                search_engine = self.search_engines[engine_name]
                
                # Skip Tavily if API key is not configured
                if engine_name == 'tavily':
                    if not os.getenv('TAVILY_API_KEY'):
                        logger.warning("Tavily API key not configured, skipping Tavily search")
                        continue
                
                urls = search_engine.search(query, self.max_results)
                
                if urls:
                    logger.info(f"Found {len(urls)} results from {engine_name}")
                    all_results.extend(urls)
                    
                    # If we have enough results, break early
                    if len(all_results) >= self.max_results * 2:
                        logger.info(f"Reached sufficient results ({len(all_results)}), stopping early")
                        break
            except Exception as e:
                logger.error(f"Search failed for {engine_name}: {str(e)}")
                continue
        
        logger.info(f"Total results collected: {len(all_results)}")
        return all_results

    def perform_search(self, query: str) -> List[str]:
        """Perform web search using configured fallback order."""
        retry_config = self._get_retry_config()
        return self._perform_search(query)

