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
import asyncio
import aiohttp

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
            config_model=config.settings.search  # Changed 'config' to 'config_model'
        )
        
        self.bm25_scorer = BM25Scorer(
            k1=config.settings.bm25.k1,
            b=config.settings.bm25.b
        )
        
        # Initialize results storage with query parameter
        self.results_storage = None
        self.results_file = None  # Initialize results_file
        logger.info("WebSearcher initialized with all components")

    async def search(self, query: str) -> List[str]:
        """Perform web search and return ranked results."""
        logger.info(f"Starting search for query: {query}")
        from pathlib import Path
        base_dir = Path(config.settings.directories.base) / "_".join(query.split())
        self.results_storage = ResultsStorage(base_dir, query)
        
        # Get raw search results
        all_results = self.search_manager.perform_search(query)
        
        if not all_results:
            logger.warning(f"No results found for query: {query}")
            return []

        # Validate URLs
        valid_results = []
        for url in all_results:
            if self.url_validator.validate_url(url):
                valid_results.append(url)
                
                # If we have enough valid results, break early
                if len(valid_results) >= config.settings.search.max_results:
                    break

        # Get content for each URL
        url_contents = await self._get_url_contents(valid_results)
        
        # Calculate BM25 scores
        scores = self.bm25_scorer.score(query, url_contents)
        
        # Combine URLs with their scores
        scored_results = list(zip(valid_results, scores))
        
        # Sort by score
        scored_results.sort(key=lambda x: x[1], reverse=True)

        metadata = {
            'search_engines': list(self.search_engines.keys()),
            'max_results': config.settings.search.max_results,
            'bm25_config': {
                'k1': config.settings.bm25.k1,
                'b': config.settings.bm25.b
            }
        }
        results_file_path = await self.results_storage.save_search_results(
            query=query,
            results=[url for url, _ in scored_results],
            metadata=metadata
        )
        if results_file_path:
            logger.info(f"Search results saved to: {results_file_path}")

        return [url for url, _ in scored_results[:config.settings.search.max_results]]

    async def _fetch_single_url(self, session: aiohttp.ClientSession, url: str) -> str:
        """Helper to fetch content from a single URL asynchronously."""
        try:
            headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'}
            # Use timeout from config
            request_timeout = config.settings.url_validation.url_fetch_request_timeout
            async with session.get(url, headers=headers, allow_redirects=True, timeout=aiohttp.ClientTimeout(total=request_timeout)) as response:
                response.raise_for_status() # Raise an exception for HTTP errors 4xx/5xx
                if 'text/html' in response.headers.get('Content-Type', '').lower() or \
                   'text/plain' in response.headers.get('Content-Type', '').lower():
                    # Consider using BeautifulSoup here for cleaner text extraction from HTML
                    return await response.text()
                else:
                    logger.warning(f"Skipping non-text content for {url} (Content-Type: {response.headers.get('Content-Type')})")
                    return ""
        except aiohttp.ClientError as e:
            logger.error(f"aiohttp.ClientError fetching {url}: {str(e)}")
            return ""
        except asyncio.TimeoutError:
            logger.error(f"Timeout error fetching {url} after {request_timeout} seconds.")
            return ""
        except Exception as e:
            logger.error(f"Unexpected error fetching {url}: {str(e)}")
            return ""

    async def _get_url_contents(self, urls: List[str]) -> List[str]:
        """Get content from URLs asynchronously using aiohttp."""
        contents = []
        # Overall timeout for the ClientSession, can be configured
        session_timeout_total = config.settings.url_validation.url_fetch_session_timeout_total
        conn_timeout = config.settings.url_validation.url_fetch_connection_timeout
        
        timeout = aiohttp.ClientTimeout(total=session_timeout_total, connect=conn_timeout)
        
        async with aiohttp.ClientSession(timeout=timeout) as session:
            tasks = [self._fetch_single_url(session, url) for url in urls]
            results = await asyncio.gather(*tasks, return_exceptions=True)
            
            for i, result in enumerate(results):
                if isinstance(result, Exception):
                    # Errors are already logged in _fetch_single_url
                    contents.append("") 
                else:
                    contents.append(result)
        return contents

    def get_search_stats(self) -> dict:
        """Get current search configuration and statistics."""
        # Note: self.max_results and self.fallback_order were not defined on WebSearcher instance.
        # Assuming these should come from config or SearchManager if they were intended to be dynamic.
        # For now, directly accessing from config for consistency.
        return {
            'max_results': config.settings.search.max_results,
            'fallback_order': config.settings.search.fallback_order,
            'search_engines': list(self.search_engines.keys())
        }
        