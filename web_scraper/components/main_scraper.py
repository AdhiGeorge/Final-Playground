from pathlib import Path
from urllib.parse import urljoin
from typing import List, Dict, Optional, Any
from playwright.sync_api import sync_playwright
from datetime import datetime
import json
import re
from bs4 import BeautifulSoup
from web_scraper.components.base_scraper import BaseScraper
from web_scraper.components.pdf_scraper import PDFScraper
from web_scraper.components.image_scraper import ImageScraper
from utils.config import config
from utils.logger import logger
from utils.results_storage import ResultsStorage
import random
import time
import json

class WebScraper(BaseScraper):
    def __init__(self):
        super().__init__()
        self.setup_directories()
        self.pdf_scraper = PDFScraper()
        self.image_scraper = ImageScraper()
        self.max_concurrent = config.get('scraping.max_concurrent', 5)
        self.rate_limit = config.get('scraping.rate_limit', {})
        self.query = None  # Will be set when scraping starts
        self.results_storage = None
        logger.info("WebScraper initialized with configuration")

    def set_query(self, query: str):
        """Set the query for this scraping session."""
        self.query = query
        if self.results_storage is None:
            self.results_storage = ResultsStorage(query=query, type_='scrape')

    def scrape(self, urls: List[str], mode: str = 'standard'):
        """Scrape multiple URLs with specified mode."""
        if not self.query:
            raise ValueError("Query must be set before scraping")
            
        if not urls:
            logger.error("No URLs provided for scraping")
            return
            
        # Set mode-specific scraping behavior
        scraping_config = config.get('scraping.modes', {}).get(mode, {})
        
        # Process URLs sequentially
        for url in urls:
            self.scrape_url(url, scraping_config)
        
        logger.info(f"Scraping completed for {len(urls)} URLs")

    def scrape_url(self, url: str, config: dict) -> None:
        """Scrape a single URL."""
        try:
            with sync_playwright() as playwright:
                browser = playwright.chromium.launch(headless=True)
                context = browser.new_context(
                    user_agent=random.choice(self.user_agents)
                )
                page = context.new_page()
                
                # Navigate and wait for load
                page.goto(url, wait_until='networkidle')
                
                # Get page content
                content = page.content()
                
                # Extract content
                extracted = self.extract_content(url, content)
                
                # Save results
                if extracted:
                    self.results_storage.save_metadata(url, extracted)
                    
                # Close browser
                browser.close()
                
        except Exception as e:
            logger.error(f"Error scraping {url}: {str(e)}")
            return {'url': url, 'error': str(e)}

    def extract_content(self, url: str, content: str) -> Dict:
        """Extract content from the page."""
        try:
            soup = BeautifulSoup(content, 'html.parser')
            
            # Extract basic page content
            title = soup.title.string if soup.title else "No title"
            description = self.extract_description(soup)
            
            # Extract links
            links = self.extract_links(soup, url)
            
            # Extract images
            images = self.image_scraper.extract_images(soup, url)
            
            # Extract PDFs
            pdfs = self.pdf_scraper.extract_pdfs(soup, url)
            
            return {
                'url': url,
                'title': title,
                'description': description,
                'links': links,
                'images': images,
                'pdfs': pdfs,
                'timestamp': datetime.now().isoformat()
            }
        except Exception as e:
            logger.error(f"Error extracting content from {url}: {str(e)}")
            return {'url': url, 'error': str(e)}

    def setup_directories(self):
        """Create necessary directories for storing scraped data."""
        base_dir = Path(self.config.get('directories.base', 'Data'))
        scrape_dir = base_dir / self.config.get('directories.scrape.base', 'Scraped_Results')
        scrape_dir.mkdir(parents=True, exist_ok=True)
        
        # Create subdirectories
        subdirs = self.config.get('directories.scrape', {})
        for subdir in subdirs.values():
            if subdir != 'base':
                (scrape_dir / subdir).mkdir(parents=True, exist_ok=True)
        
        logger.info(f"Created scraping directory structure at: {scrape_dir}")

    async def wait_for_rate_limit(self):
        """Wait according to rate limiting configuration."""
        delay = self.rate_limit.get('delay_between_requests', 1)
        await asyncio.sleep(delay)

    async def scrape_urls(self, urls: List[str], mode: str = 'standard'):
        """Scrape multiple URLs concurrently."""
        tasks = []
        for url in urls:
            tasks.append(self.scrape_url(url, mode))
            await self.wait_for_rate_limit()
            
            # Limit concurrent tasks
            if len(tasks) >= self.max_concurrent:
                await asyncio.gather(*tasks)
                tasks = []
        
        # Process remaining tasks
        if tasks:
            await asyncio.gather(*tasks)

    def scrape(self, urls: List[str], mode: str = 'standard'):
        """Main method to start scraping."""
        try:
            asyncio.run(self.scrape_urls(urls, mode))
        except Exception as e:
            logger.error(f"Failed to scrape: {str(e)}")
            raise
            return {'error': str(e)}

    def save_html(self, url: str, content: str) -> Path:
        """Save HTML content to file."""
        html_dir = Path(self.config['download_directory']) / self.config['subdirectories']['html']
        filename = f"{self.get_safe_filename(url)}.html"
        filepath = html_dir / filename
        
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(content)
        return filepath
        
    def save_metadata(self, url: str, data: Dict) -> str:
        """Save metadata using ResultsStorage."""
        return self.results_storage.save_scrape_results(url, data['html_file'], data)
        
    def extract_description(self, soup: BeautifulSoup) -> str:
        """Extract page description."""
        meta_desc = soup.find('meta', attrs={'name': 'description'})
        if meta_desc and 'content' in meta_desc.attrs:
            return meta_desc['content']
        return ''
        
    async def scrape_urls(self, urls: List[str], mode: str = 'standard'):
        """Scrape multiple URLs concurrently."""
        tasks = []
        for url in urls:
            tasks.append(self.scrape_url(url, mode))
            await self.wait_for_rate_limit()
            
            # Limit concurrent tasks
            if len(tasks) >= self.max_concurrent:
                await asyncio.gather(*tasks)
                tasks = []
        
        # Process remaining tasks
        if tasks:
            await asyncio.gather(*tasks)

    def scrape(self, urls: List[str], mode: str = 'standard'):
        """Main method to start scraping."""
        asyncio.run(self.scrape_urls(urls, mode))
