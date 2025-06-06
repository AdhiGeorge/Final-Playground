from typing import List
import os
import sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from utils.config import config
from web_search.search.duckduckgo import DuckDuckGoSearch
from web_search.search.tavily import TavilySearch
from web_search.search.google import GoogleSearch
from utils.url_validator import URLValidator
from web_search.components.search_manager import SearchManager
from web_search.components.bm25 import BM25Scorer
from utils.logger import logger
from utils.results_storage import ResultsStorage

class WebSearcher:
    def __init__(self):
        """Initialize the web searcher with all components."""
        self.url_validator = URLValidator()
        self.search_engines = {
            "duckduckgo": DuckDuckGoSearch(),
            "tavily": TavilySearch(),
            "google": GoogleSearch()
        }
        
        # Initialize components
        self.search_manager = SearchManager(
            search_engines=self.search_engines,
            config=config.search_config
        )
        
        self.bm25_scorer = BM25Scorer(
            k1=config.bm25_config.get('k1', 1.2),
            b=config.bm25_config.get('b', 0.75)
        )
        
        # Initialize results storage with query parameter
        self.results_storage = None
        self.results_file = None  # Initialize results_file
        logger.info("WebSearcher initialized with all components")

    def search(self, query: str) -> List[str]:
        """Perform web search and return ranked results."""
        logger.info(f"Starting search for query: {query}")
        
        # Initialize ResultsStorage with query
        self.results_storage = ResultsStorage(query=query, type_='search')
        
        # Get raw search results
        """Perform web search and return ranked results."""
        logger.info(f"Starting search for query: {query}")
        
        # Get raw search results
        all_results = self.search_manager.perform_search(query)
        
        if not all_results:
            logger.warning(f"No results found for query: {query}")
            return []

        # Save results before validation
        results_file = self.results_storage.save_results(query, all_results)
        self.results_file = results_file  # Store the file path
        logger.info(f"Results saved to: {results_file}")

        # Validate URLs
        valid_results = []
        for url in all_results:
            if self.url_validator.validate_url(url):
                valid_results.append(url)

        # Get content for each URL
        url_contents = self._get_url_contents(valid_results)
        
        # Calculate BM25 scores
        scores = self.bm25_scorer.score(query, url_contents)
        
        # Combine URLs with their scores
        scored_results = list(zip(valid_results, scores))
        
        # Sort by score
        scored_results.sort(key=lambda x: x[1], reverse=True)
        
        # Save results with metadata
        metadata = {
            'search_engines': list(self.search_engines.keys()),
            'max_results': config.search_config.get('max_results', 10),
            'bm25_config': config.bm25_config
        }
        
        results_file = self.results_storage.save_results(
            query=query,
            results=[url for url, _ in scored_results],
            metadata=metadata
        )
        
        if results_file:
            logger.info(f"Search results saved to: {results_file}")
        
        # Return top results
        return [url for url, _ in scored_results[:config.search_config.get('max_results', 10)]]

    def _get_url_contents(self, urls: List[str]) -> List[str]:
        """Get content from URLs. This is a placeholder method that you'll need to implement."""
        logger.info(f"Getting content for {len(urls)} URLs")
        # TODO: Implement URL content fetching
        return ["" for _ in urls]

    def search(self, query: str) -> List[str]:
        """Perform web search and return ranked results."""
        # Get raw search results
        all_results = self.search_manager.perform_search(query)
        
        if not all_results:
            return []

        # Validate URLs
        valid_results = []
        for url in all_results:
            if self.url_validator.validate_url(url):
                valid_results.append(url)
                
                # If we have enough valid results, break early
                if len(valid_results) >= config.search_config.get('max_results', 10):
                    break

        # Get content for each URL (you'll need to implement this)
        url_contents = self._get_url_contents(valid_results)
        
        # Calculate BM25 scores
        scores = self.bm25_scorer.score(query, url_contents)
        
        # Combine URLs with their scores
        scored_results = list(zip(valid_results, scores))
        
        # Sort by score
        scored_results.sort(key=lambda x: x[1], reverse=True)
        
        # Return top results
        return [url for url, _ in scored_results[:config.search_config.get('max_results', 10)]]

    def _get_url_contents(self, urls: List[str]) -> List[str]:
        """Get content from URLs. This is a placeholder method that you'll need to implement."""
        # TODO: Implement actual URL content fetching
        # This could use aiohttp for async requests
        # For now, returning dummy content
        return ["dummy content" for _ in urls]

    def get_search_stats(self) -> dict:
        """Get current search configuration and statistics."""
        return {
            'max_results': self.max_results,
            'fallback_order': self.fallback_order,
            'search_engines': list(self.search_engines.keys())
        }
