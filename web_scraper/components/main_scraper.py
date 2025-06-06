from pathlib import Path
from urllib.parse import urljoin
from typing import List, Dict, Optional, Any
from playwright.async_api import async_playwright, TimeoutError as PlaywrightTimeoutError
from datetime import datetime
import json
import re
from bs4 import BeautifulSoup
from web_scraper.components.base_scraper import BaseScraper 
from utils.config import config
from utils.logger import logger
from utils.results_storage import ResultsStorage
import random
import time
import asyncio
import aiofiles
import aiohttp
import pytesseract
from PIL import Image
import io

class WebScraper(BaseScraper):
    def __init__(self):
        self.query = None
        self.results_storage = None
        self.max_concurrent = config.settings.scraping.max_concurrent
        self.rate_limit_config = config.settings.scraping.rate_limit
        self.user_agents = config.settings.scraping.user_agents
        self.timeout = config.settings.scraping.timeout
        logger.info("WebScraper initialized.")

    async def set_query(self, query: str):
        """Set the current query and initialize storage"""
        logger.info(f"Setting query: {query}")
        self.query = query
        base_dir = Path(config.settings.directories.base) / self._sanitize_query(query)
        self.results_storage = ResultsStorage(base_dir, query)
        await self.results_storage.initialize()
        logger.info(f"Storage initialized for query: {query}")

    def _sanitize_query(self, query: str) -> str:
        """Convert query to safe directory name"""
        return "".join(c if c.isalnum() else "_" for c in query)

    async def scrape(self, urls: List[str]) -> List[Dict]:
        """Scrape a list of URLs with full feature support"""
        if not self.query or not self.results_storage:
            raise ValueError("Query and ResultsStorage must be set before scraping")
            
        # Ensure storage is ready
        if not await self.results_storage.is_ready():
            raise RuntimeError("Results storage is not ready")
        
        results = []
        
        # Scrape first N URLs fully based on config
        top_n = min(config.settings.search.scrape_top_n, len(urls))
        
        try:
            async with async_playwright() as playwright:
                browser = await playwright.chromium.launch()
                context = await browser.new_context()
                
                for i, url in enumerate(urls):
                    try:
                        result = {"url": url, "success": False}
                        
                        # Basic scraping for all URLs
                        page = await context.new_page()
                        timeout_seconds = self.timeout / 1000
                        response = await page.goto(url, timeout=timeout_seconds * 1000)
                        
                        if response.status >= 400:
                            result["error"] = f"HTTP {response.status}"
                            results.append(result)
                            continue
                        
                        content_type = response.headers.get("content-type", "")
                        
                        # Handle PDFs
                        if "pdf" in content_type.lower() and config.settings.scraping.save_pdfs:
                            pdf_content = await response.body()
                            await self.results_storage.save_scraped_content(
                                url, "pdf", pdf_content, {"content_type": "pdf"}
                            )
                            result["pdf_saved"] = True
                        
                        # Full scraping for top N URLs
                        if i < top_n:
                            html = await page.content()
                            
                            # Save HTML
                            if config.settings.scraping.save_html:
                                await self.results_storage.save_scraped_content(
                                    url, "html", html, {"content_type": "html"}
                                )
                            
                            # Extract and save text
                            if config.settings.scraping.save_text:
                                soup = BeautifulSoup(html, "html.parser")
                                text = soup.get_text(" ", strip=True)
                                await self.results_storage.save_scraped_content(
                                    url, "text", text, {"content_type": "text"}
                                )
                            
                            # Capture screenshots of formulas
                            if config.settings.scraping.capture_formulas:
                                math_elements = await page.query_selector_all("math, .math, .equation")
                                for j, element in enumerate(math_elements):
                                    screenshot = await element.screenshot(
                                        type="png",
                                        quality=config.settings.scraping.formula_screenshot_quality
                                    )
                                    await self.results_storage.save_scraped_content(
                                        url, "formula", screenshot, 
                                        {"formula_index": j, "content_type": "formula"}
                                    )
                            
                            # Save images
                            if config.settings.scraping.save_images:
                                images = await page.query_selector_all("img")
                                for img in images:
                                    try:
                                        src = await img.get_attribute("src")
                                        if src and src.startswith(('http', 'https')):
                                            async with aiohttp.ClientSession() as session:
                                                async with session.get(src) as resp:
                                                    img_data = await resp.read()
                                                    await self.results_storage.save_scraped_content(
                                                        url, "image", img_data,
                                                        {"src": src, "content_type": resp.content_type}
                                                    )
                                    except Exception as e:
                                        logger.error(f"Failed to save image from {url}: {e}")
                        
                        result["success"] = True
                        results.append(result)
                        
                    except Exception as e:
                        logger.error(f"Failed to scrape {url}: {e}")
                        results.append({"url": url, "error": str(e), "success": False})
                    finally:
                        await page.close()
                
                await context.close()
                await browser.close()
        except Exception as e:
            logger.error(f"Error in scrape: {e}")
            raise
        
        return results

    async def extract_content(self, url: str, html_content: str) -> Dict:  
        try:
            soup = BeautifulSoup(html_content, 'html.parser')
            title = soup.title.string.strip() if soup.title and soup.title.string else 'No title found'
            description = self._extract_description(soup)
            
            links = self._extract_links(soup, url)
            images = [] 
            pdfs = []   

            return {
                'title': title,
                'description': description,
                'links': links,
                'images': images,
                'pdfs': pdfs,
            }
        except Exception as e:
            logger.error(f"Error extracting content for {url}: {e}", exc_info=True)
            return {'error': f'Failed to extract content: {e}'}

    def _extract_description(self, soup: BeautifulSoup) -> str:
        meta_desc = soup.find('meta', attrs={'name': 'description'})
        if meta_desc and meta_desc.get('content'):
            return meta_desc['content'].strip()
        
        meta_og_desc = soup.find('meta', property='og:description')
        if meta_og_desc and meta_og_desc.get('content'):
            return meta_og_desc['content'].strip()
        
        first_p = soup.find('p')
        if first_p and first_p.get_text():
            text = first_p.get_text().strip()
            if 50 < len(text) < 300: 
                return text
        return 'No description found'

    def _extract_links(self, soup: BeautifulSoup, base_url: str) -> List[str]:
        links = set()
        for a_tag in soup.find_all('a', href=True):
            href = a_tag['href']
            if href and not href.startswith('#') and not href.startswith('javascript:'):
                full_url = urljoin(base_url, href)
                links.add(full_url)
        return list(links)

    async def _wait_for_rate_limit(self):
        delay = self.rate_limit_config.delay_between_requests
        if delay > 0:
            await asyncio.sleep(delay)

    async def scrape_with_full_features(self, urls: List[str]) -> List[Dict]:
        """Scrape a list of URLs."""
        if not self.results_storage:
            raise ValueError("ResultsStorage not initialized")
            
        # Ensure directories are ready
        await self.results_storage._ensure_directories_ready()
        
        if not await self.results_storage.is_ready():
            raise RuntimeError("Failed to initialize storage directories")

        if not self.query:
            logger.error("Query not set. Call set_query() first.")
            raise ValueError("Query must be set via set_query() before scraping.")

        if not urls:
            logger.warning("No URLs provided for scraping.")
            return []

        scraping_mode_settings = getattr(config.settings.scraping.modes, 'standard', None)
        if scraping_mode_settings is None:
            logger.warning(f"Invalid scraping mode 'standard'. Falling back to default settings.")
            scraping_mode_settings = config.settings.scraping.modes
        
        scraping_params = scraping_mode_settings
        
        tasks = []
        scraped_results_aggregate: List[Dict] = []

        logger.info(f"Starting scrape for {len(urls)} URLs with mode 'standard' for query: '{self.query}'.")

        semaphore = asyncio.Semaphore(self.max_concurrent)

        for url_to_scrape in urls:
            task = asyncio.create_task(self._scrape_url_with_semaphore(semaphore, url_to_scrape, scraping_params))
            tasks.append(task)
        
        results_batch = await asyncio.gather(*tasks, return_exceptions=True)
        scraped_results_aggregate.extend(self._process_batch_results(results_batch, urls))
        
        successful_scrapes = sum(1 for r in scraped_results_aggregate if not r.get('error'))
        logger.info(f"Scraping completed for query: '{self.query}'. Successfully scraped: {successful_scrapes}, Failed: {len(scraped_results_aggregate) - successful_scrapes} out of {len(urls)} URLs.")
        return scraped_results_aggregate

    def _process_batch_results(self, results_batch: List[Any], original_urls: List[str]) -> List[Dict]:
        processed = []
        for i, res in enumerate(results_batch):
            if isinstance(res, Exception):
                logger.error(f"Exception during scraping URL {original_urls[i]}: {res}", exc_info=True)
                processed.append({'url': original_urls[i], 'error': str(res)})
            elif res is None: 
                logger.error(f"Scraping returned None for URL {original_urls[i]}")
                processed.append({'url': original_urls[i], 'error': 'Scraping returned None'})
            else:
                processed.append(res)
        return processed

    async def _scrape_url_with_semaphore(self, semaphore: asyncio.Semaphore, url: str, scraping_params: Dict) -> Dict:
        async with semaphore:
            await self._wait_for_rate_limit()
            return await self.scrape_url(url, scraping_params)

    async def scrape_url(self, url: str, scraping_params: Dict) -> Dict:
        if url.lower().endswith('.pdf'):
            logger.warning(f"Skipping PDF scraping for {url}")
            return {'url': url, 'error': 'PDF scraping not supported'}
            
        if not self.query or not self.results_storage:
            logger.error("ResultsStorage not available in scrape_url. This indicates a programming error.")
            return {'url': url, 'error': 'ResultsStorage not initialized'}

        try:
            async with async_playwright() as playwright:
                browser = await playwright.chromium.launch(headless=True)
                context = await browser.new_context(user_agent=random.choice(self.user_agents))
                page = await context.new_page()
                
                try:
                    timeout_seconds = self.timeout / 1000
                    logger.info(f"Navigating to {url} with timeout {timeout_seconds}s")
                    await page.goto(url, timeout=timeout_seconds * 1000)  # Playwright uses ms
                    
                    html_content = await page.content()
                    
                    # Save HTML content
                    save_result = await self.results_storage.save_scraped_content(url, "html", html_content)
                    if not save_result:
                        return {'url': url, 'error': 'Failed to save HTML content'}
                    
                    extracted_data = await self.extract_content(url, html_content)
                    
                    metadata = {
                        'url': url,
                        'query': self.query,
                        'timestamp': datetime.now().isoformat(),
                        'scraping_mode_params': scraping_params,
                        'html_file_path': str(save_result),
                        **extracted_data
                    }
                    
                    await self.results_storage.save_scrape_metadata(url, metadata)
                    
                    return {
                        'url': url,
                        'status': 'success',
                        'html_file': str(save_result),
                        **extracted_data
                    }
                finally:
                    await browser.close()
        except Exception as e:
            logger.error(f"Error scraping {url}: {str(e)}")
            return {'url': url, 'error': str(e)}
