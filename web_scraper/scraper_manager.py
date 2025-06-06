from typing import List
from web_scraper.components.main_scraper import WebScraper
from web_search.searcher import WebSearcher
from utils.config import config
import logging
import asyncio
from utils.logger import logger

class ScraperManager:
    def __init__(self):
        """Initialize the scraper manager."""
        self.scraper = WebScraper()
        self.searcher = WebSearcher()
        logger.info("ScraperManager initialized")

    def validate_urls(self, urls: List[str]) -> List[str]:
        """Validate URLs before scraping."""
        valid_urls = []
        for url in urls:
            try:
                # Basic URL validation
                if url.startswith('http://') or url.startswith('https://'):
                    valid_urls.append(url)
                else:
                    logger.warning(f"Invalid URL format: {url}")
            except Exception as e:
                logger.error(f"Error validating URL {url}: {str(e)}")
        return valid_urls

    def get_search_results(self, query: str, num_results: int = 2) -> List[str]:
        """Get search results for a query."""
        try:
            results = self.searcher.search(query)
            return results[:num_results] if results else []
        except Exception as e:
            logger.error(f"Search failed: {str(e)}")
            return []

    async def scrape(self, urls: List[str], mode: str = 'standard', query: str = None):
        """Scrape the provided URLs."""
        try:
            valid_urls = self.validate_urls(urls)
            if not valid_urls:
                logger.error("No valid URLs to scrape")
                return

            if query:
                self.scraper.set_query(query)
            # If query is None here, WebScraper.scrape will raise an error if its own query isn't set.
            # This is the desired behavior: query must be set on WebScraper before scraping.
            
            logger.info(f"Starting to scrape {len(valid_urls)} URLs for query: '{query if query else self.scraper.query}'")
            await self.scraper.scrape(valid_urls, mode)
            logger.info(f"Scraping completed for query: '{query if query else self.scraper.query}'")
        except Exception as e:
            logger.error(f"Scraping failed for query '{query if query else self.scraper.query}': {str(e)}")
            raise

    async def scrape_from_query(self, query: str, mode: str = 'standard'):
        """Scrape URLs from search results."""
        try:
            urls = self.get_search_results(query) # This remains sync for now
            if not urls:
                logger.error(f"No search results found for query: '{query}'")
                return

            logger.info(f"Found {len(urls)} URLs from search results for query: '{query}'. Starting scraping.")
            # Pass the query to self.scrape, which will then call self.scraper.set_query(query)
            await self.scrape(urls, mode, query=query)
            # Logging for completion is now handled within the awaited self.scrape method
            
        except Exception as e:
            logger.error(f"Scraping from query '{query}' failed: {str(e)}")
            raise
