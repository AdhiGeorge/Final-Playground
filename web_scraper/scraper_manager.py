from typing import List
from web_scraper.components.main_scraper import WebScraper
from web_search.searcher import WebSearcher
from utils.config import config
import logging
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

    def scrape(self, urls: List[str], mode: str = 'standard', query: str = None):
        """Scrape the provided URLs."""
        try:
            valid_urls = self.validate_urls(urls)
            if not valid_urls:
                logger.error("No valid URLs to scrape")
                return

            if query:
                self.scraper.set_query(query)
            
            logger.info(f"Starting to scrape {len(valid_urls)} URLs")
            self.scraper.scrape(valid_urls, mode)
            logger.info("Scraping completed")
        except Exception as e:
            logger.error(f"Scraping failed: {str(e)}")
            raise

    def scrape_from_query(self, query: str, mode: str = 'standard'):
        """Scrape URLs from search results."""
        try:
            urls = self.get_search_results(query)
            if not urls:
                logger.error("No search results found")
                return

            logger.info(f"Scraping {len(urls)} URLs from search results")
            self.scrape(urls, mode)
            logger.info("Scraping completed")
            
        except Exception as e:
            logger.error(f"Scraping from query failed: {str(e)}")
            raise
