from abc import ABC, abstractmethod
from typing import List, Dict, Optional
import aiohttp
from bs4 import BeautifulSoup
import logging
from urllib.parse import urljoin
import random
from utils.config import config
from utils.logger import logger
import asyncio

class BaseScraper(ABC):
    def __init__(self):
        """Initialize base scraper with configuration."""
        self.scraping_config = config.settings.scraping
        self.headers = self.scraping_config.headers
        self.user_agents = self.scraping_config.user_agents
        
    def get_headers(self) -> Dict[str, str]:
        """Get headers with random user agent"""
        headers = self.headers.copy()
        if self.user_agents:
            headers["User-Agent"] = random.choice(self.user_agents)
        return headers
        
    async def delay_request(self):
        """Delay between requests based on rate limit config"""
        delay = self.scraping_config.rate_limit.delay_between_requests
        if delay > 0:
            await asyncio.sleep(delay)
            
    @abstractmethod
    async def extract_content(self, url: str, content: str) -> Dict:
        """Extract content from the page."""
        pass
        
    async def get_page_content(self, url: str) -> Optional[str]:
        """Get page content with proper headers and user agent rotation."""
        try:
            headers = self.get_headers()
            
            async with aiohttp.ClientSession() as session:
                async with session.get(url, headers=headers, timeout=self.scraping_config.timeout) as response:
                    if response.status == 200:
                        return await response.text()
                    return None
        except Exception as e:
            logger.error(f"Error fetching {url}: {str(e)}")
            return None
            
    def get_safe_filename(self, url: str) -> str:
        """Create a safe filename from URL."""
        return url.replace('://', '_').replace('/', '_').replace('.', '_').replace(':', '_')[:255]
        
    def extract_links(self, soup: BeautifulSoup, base_url: str) -> List[str]:
        """Extract all links from the page."""
        links = []
        for link in soup.find_all('a', href=True):
            href = link['href']
            if href.startswith('http') or href.startswith('//'):
                links.append(href)
            elif href.startswith('/'):
                links.append(urljoin(base_url, href))
        return links
