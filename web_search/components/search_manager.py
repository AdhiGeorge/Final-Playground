from typing import Dict, List, Any
from tenacity import retry, stop_after_attempt, wait_exponential, Retrying # Added Retrying
import logging
import os
from utils.logger import logger
from utils.config_models import SearchConfig # Added import

class SearchManager:
    def __init__(self, search_engines: Dict[str, Any], config_model: SearchConfig): # Changed 'config' to 'config_model' and type
        """Initialize search manager with engines and configuration."""
        self.search_engines = search_engines
        self.config_model = config_model # Store the Pydantic model
        self.max_results = self.config_model.max_results # Use direct attribute access
        self.fallback_order = self.config_model.fallback_order # Use direct attribute access
        # self.retry_config is no longer needed as we use self.config_model.retry directly
        logger.info(f"Initialized SearchManager with max_results={self.max_results} and fallback_order={self.fallback_order}")


    # @retry decorator removed, _get_retry_config removed.
    def _perform_search(self, query: str) -> List[str]:
        """Internal method to perform search."""
        logger.info(f"Starting search for query: {query}")
        all_results = []
        
        # Get results from all search engines
        for engine_name in self.fallback_order:
            try:
                logger.info(f"Searching with {engine_name}...")
                search_engine = self.search_engines[engine_name]
                
                # API key checks are now done in individual search engine __init__ methods.
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
        """Perform web search using configured fallback order and retry logic."""
        retry_settings = self.config_model.retry
        
        # Convert milliseconds to seconds for tenacity
        wait_multiplier_seconds = retry_settings.wait_exponential_multiplier / 1000.0
        wait_max_seconds = retry_settings.wait_exponential_max / 1000.0

        for attempt in Retrying(
            stop=stop_after_attempt(retry_settings.max_attempts),
            wait=wait_exponential(multiplier=wait_multiplier_seconds, max=wait_max_seconds),
            reraise=True # Reraise the last exception if all attempts fail
        ):
            with attempt:
                # The 'attempt' object can be used to log attempt numbers if needed
                # logger.debug(f"Search attempt {attempt.retry_state.attempt_number} for query: {query}")
                return self._perform_search(query)
        return [] # Should not be reached if reraise=True, but as a fallback

