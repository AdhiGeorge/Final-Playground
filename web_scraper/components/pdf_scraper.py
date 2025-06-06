from typing import List, Dict, Optional
import aiohttp
import aiofiles
from pathlib import Path
from bs4 import BeautifulSoup
from urllib.parse import urljoin
from web_scraper.components.base_scraper import BaseScraper
from utils.config import config
from utils.logger import logger

class PDFScraper(BaseScraper):
    def __init__(self):
        super().__init__()
        base_dir = Path(config.scraping_config.directories.base)
        scrape_dir = base_dir / config.scraping_config.directories.scrape.base
        self.pdf_dir = scrape_dir / config.scraping_config.directories.scrape.pdfs
        # Directory creation is handled by WebScraper.setup_directories
        
    async def extract_content(self, url: str, content: str) -> Dict:
        """Extract and download PDFs from the page."""
        soup = BeautifulSoup(content, 'html.parser')
        pdf_links = self.extract_pdf_links(soup, url)
        
        results = []
        for pdf_url in pdf_links:
            pdf_path = self.pdf_dir / f"{self.get_safe_filename(pdf_url)}.pdf"
            if await self.download_file(pdf_url, pdf_path):
                results.append(str(pdf_path))
        
        return {
            'pdfs': results,
            'count': len(results)
        }
        
    def extract_pdf_links(self, soup: BeautifulSoup, base_url: str) -> List[str]:
        """Extract PDF links from the page."""
        pdf_links = []
        for link in soup.find_all('a', href=True):
            href = link['href'].lower()
            if href.endswith('.pdf'):
                pdf_links.append(urljoin(base_url, href))
        return pdf_links
        
    async def download_file(self, url: str, save_path: Path) -> bool:
        """Download a PDF file."""
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(url) as response:
                    if response.status == 200:
                        async with aiofiles.open(save_path, 'wb') as f:
                            while True:
                                chunk = await response.content.read(1024)
                                if not chunk:
                                    break
                                await f.write(chunk)
                        return True
                    return False
        except Exception as e:
            logger.error(f"Failed to download PDF {url}: {str(e)}")
            return False
