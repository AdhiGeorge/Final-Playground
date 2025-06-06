import json
import os
import asyncio
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Optional, Union
import aiofiles
import aiofiles.os
from pydantic import BaseModel, HttpUrl
from utils.config import config
from utils.logger import logger

class SearchResultModel(BaseModel):
    query: str
    urls: List[HttpUrl]
    timestamp: str
    metadata: Optional[Dict] = None

class ResultsStorage:
    def __init__(self, base_dir: Path, query: str):
        self.base_dir = base_dir
        self.query = query
        
        # Initialize directory paths
        self.search_results_dir = self.base_dir / "Search_Results"
        self.scraped_results_dir = self.base_dir / "Scraped_Results"
        
        # Scraped content subdirectories
        self.scrape_html_dir = self.scraped_results_dir / "html"
        self.scrape_pdf_dir = self.scraped_results_dir / "pdfs"
        self.scrape_image_dir = self.scraped_results_dir / "images"
        self.scrape_text_dir = self.scraped_results_dir / "text"
        self.scrape_formula_dir = self.scraped_results_dir / "formulas"
        self.scrape_meta_dir = self.scraped_results_dir / "metadata"
        
        # Track initialization state
        self._initialized = False
    
    async def initialize(self):
        """Initialize storage directories"""
        logger.info(f"Initializing storage for query: {self.query}")
        if not self._initialized:
            await self._ensure_directories_ready()
            self._initialized = True
            logger.info(f"Storage initialized successfully for query: {self.query}")
    
    async def is_ready(self) -> bool:
        """Check if storage is ready for use"""
        logger.debug(f"Checking storage readiness for query: {self.query}")
        if not self._initialized:
            await self.initialize()
            
        try:
            # Verify all directories exist and are writable
            test_file = self.base_dir / "test_write.tmp"
            async with aiofiles.open(test_file, "w") as f:
                await f.write("test")
            test_file.unlink()
            
            ready = all([
                self.search_results_dir.exists(),
                self.scrape_html_dir.exists(),
                self.scrape_pdf_dir.exists(),
                self.scrape_image_dir.exists(),
                self.scrape_text_dir.exists(),
                self.scrape_formula_dir.exists(),
                self.scrape_meta_dir.exists()
            ])
            
            logger.debug(f"Storage readiness check completed: {ready}")
            return ready
            
        except Exception as e:
            logger.error(f"Storage readiness check failed: {e}")
            return False
    
    async def _ensure_directories_ready(self) -> None:
        """Create all required directories"""
        logger.info(f"Creating storage directories for query: {self.query}")
        try:
            for directory in [
                self.search_results_dir,
                self.scrape_html_dir,
                self.scrape_pdf_dir,
                self.scrape_image_dir,
                self.scrape_text_dir,
                self.scrape_formula_dir,
                self.scrape_meta_dir
            ]:
                directory.mkdir(parents=True, exist_ok=True)
            logger.info(f"Successfully created storage directories for query: {self.query}")
        except Exception as e:
            logger.error(f"Failed to create directories: {e}")
            raise RuntimeError(f"Could not initialize storage: {e}")
    
    async def save_search_results(self, query: str, results: List[str]) -> Optional[str]:
        """Save search results to JSON"""
        try:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"query_results_{timestamp}.json"
            filepath = self.search_results_dir / filename
            
            result_data = SearchResultModel(
                query=query,
                urls=results,
                timestamp=timestamp
            )
            
            async with aiofiles.open(filepath, "w", encoding="utf-8") as f:
                await f.write(result_data.model_dump_json(indent=2))
                
            return str(filepath)
        except Exception as e:
            logger.error(f"Failed to save search results: {e}")
            return None

    async def save_scraped_content(self, url: str, content_type: str, content: Union[str, bytes], metadata: Optional[Dict] = None) -> bool:
        """Unified method to save all scraped content types"""
        try:
            # Get the appropriate directory
            content_dir = {
                "html": self.scrape_html_dir,
                "pdf": self.scrape_pdf_dir,
                "image": self.scrape_image_dir,
                "text": self.scrape_text_dir,
                "formula": self.scrape_formula_dir
            }.get(content_type)
            
            if not content_dir:
                logger.error(f"Unknown content type: {content_type}")
                return False
            
            # Save content
            filename = f"{self._get_safe_filename(url)}.{content_type}"
            filepath = content_dir / filename
            
            async with aiofiles.open(filepath, "wb" if isinstance(content, bytes) else "w", encoding="utf-8") as f:
                await f.write(content)
            
            # Save metadata if provided
            if metadata:
                meta_filename = f"{self._get_safe_filename(url)}_metadata.json"
                meta_filepath = self.scrape_meta_dir / meta_filename
                async with aiofiles.open(meta_filepath, "w", encoding="utf-8") as f:
                    await f.write(json.dumps({
                        "url": url,
                        "content_type": content_type,
                        "timestamp": datetime.now().isoformat(),
                        **metadata
                    }, indent=2))
            
            return True
        except Exception as e:
            logger.error(f"Failed to save {content_type} content from {url}: {e}")
            return False

    def _get_safe_filename(self, text: str) -> str:
        """Convert URL to safe filename"""
        safe = text.replace("://", "_").replace("/", "_").replace("?", "_").replace("=", "_")
        return "".join(c for c in safe if c.isalnum() or c in ('_', '-', '.')).strip()[:200]

    def _sanitize_query(self, query: str) -> str:
        return "".join(c for c in query if c.isalnum() or c in (' ', '_', '-')).strip().replace(' ', '_')
