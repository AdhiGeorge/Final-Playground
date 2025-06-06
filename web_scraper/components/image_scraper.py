from typing import List, Dict, Optional
import aiohttp
import aiofiles
from PIL import Image
import io
from pathlib import Path
from bs4 import BeautifulSoup
from urllib.parse import urljoin
from web_scraper.components.base_scraper import BaseScraper
from utils.config import config
from utils.logger import logger

class ImageScraper(BaseScraper):
    def __init__(self):
        super().__init__()
        base_dir = Path(config.get('directories.base', 'Data'))
        scrape_dir = base_dir / config.get('directories.scrape.base', 'Scraped_Results')
        self.image_dir = scrape_dir / config.get('directories.scrape.images', 'images')
        self.image_dir.mkdir(parents=True, exist_ok=True)
        self.image_dir.mkdir(parents=True, exist_ok=True)
        
    async def extract_content(self, url: str, content: str) -> Dict:
        """Extract and download images from the page."""
        soup = BeautifulSoup(content, 'html.parser')
        image_links = self.extract_image_links(soup, url)
        
        results = []
        for img_url in image_links:
            img_path = self.image_dir / f"{self.get_safe_filename(img_url)}"
            if await self.download_image(img_url, img_path):
                results.append(str(img_path))
        
        return {
            'images': results,
            'count': len(results)
        }
        
    def extract_image_links(self, soup: BeautifulSoup, base_url: str) -> List[str]:
        """Extract image links from the page."""
        image_links = []
        for img in soup.find_all('img', src=True):
            src = img['src'].lower()
            if src.endswith(('.jpg', '.jpeg', '.png', '.gif')):
                image_links.append(urljoin(base_url, src))
        return image_links
        
    async def download_image(self, url: str, save_path: Path) -> bool:
        """Download and validate an image."""
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(url) as response:
                    if response.status == 200:
                        # Get image format from content type
                        content_type = response.headers.get('content-type', '').lower()
                        if 'image/' in content_type:
                            ext = content_type.split('/')[-1]
                        else:
                            ext = url.split('.')[-1].lower()
                            
                        # Save with correct extension
                        save_path = save_path.with_suffix(f'.{ext}')
                        
                        # Download and validate image
                        async with aiofiles.open(save_path, 'wb') as f:
                            while True:
                                chunk = await response.content.read(1024)
                                if not chunk:
                                    break
                                await f.write(chunk)
                        
                        # Validate image
                        try:
                            with Image.open(save_path) as img:
                                img.verify()
                            return True
                        except Exception:
                            logger.error(f"Invalid image file: {save_path}")
                            os.remove(save_path)
                            return False
                    return False
        except Exception as e:
            logger.error(f"Failed to download image {url}: {str(e)}")
            return False
