from typing import List, Optional
import re
from urllib.parse import urlparse
from utils.config import config
import logging
from utils.logger import logger

class URLValidator:
    def __init__(self):
        """Initialize URL validator with configuration."""
        self.allowed_domains = config.url_validation_config.allowed_domains
        self.blocked_domains = config.url_validation_config.blocked_domains
        self.blocked_extensions = config.url_validation_config.blocked_extensions
        self.max_content_size = config.url_validation_config.max_content_size
        self.allow_video_urls = config.url_validation_config.allow_video_urls
        self.allow_auth_required = config.url_validation_config.allow_auth_required
        self.logger = logging.getLogger('search_system')
        logger.info("URLValidator initialized with configuration")

    def is_allowed_domain(self, url: str) -> bool:
        """Check if the URL's domain matches any allowed domain pattern."""
        try:
            domain = urlparse(url).netloc
            
            # Check exact matches first
            if domain in self.allowed_domains:
                return True
                
            # Check for wildcard patterns (*.com, *.org)
            for pattern in self.allowed_domains:
                if pattern.startswith('*'):
                    # Remove leading * and trailing . if present
                    pattern = pattern.lstrip('*').rstrip('.')
                    if domain.endswith(pattern):
                        return True
            
            return False
        except Exception as e:
            self.logger.warning(f"Error checking domain for URL {url}: {str(e)}")
            return False

    def validate_url(self, url: str) -> bool:
        """Validate a URL based on configuration."""
        try:
            parsed = urlparse(url)
            
            # Check domain restrictions
            if self.allowed_domains and not self.is_allowed_domain(url):
                logger.warning(f"Domain not allowed: {url}")
                return False

            # Check blocked domains
            if self.blocked_domains and parsed.hostname in self.blocked_domains:
                logger.warning(f"Domain blocked: {url}")
                return False

            # Check file extensions
            if self.blocked_extensions:
                path = parsed.path.lower()
                if any(path.endswith(ext) for ext in self.blocked_extensions):
                    logger.warning(f"URL blocked due to extension: {url}")
                    return False

            # Check authentication requirements
            if self.allow_auth_required:
                if parsed.username or parsed.password:
                    logger.warning(f"URL requires authentication: {url}")
                    return False

            return True
        except Exception as e:
            logger.error(f"URL validation failed for {url}: {str(e)}")
            return False

    def validate_urls(self, urls: List[str]) -> List[str]:
        """Validate a list of URLs and return valid ones."""
        valid_urls = []
        for url in urls:
            if self.validate_url(url):
                valid_urls.append(url)
            else:
                logger.info(f"URL rejected: {url}")
        return valid_urls

    def _is_valid_format(self, url: str) -> bool:
        """Check if URL has a valid format."""
        url_regex = re.compile(
            r'^(?:http|ftp)s?://'  # http:// or https://
            r'(?:(?:[A-Z0-9](?:[A-Z0-9-]{0,61}[A-Z0-9])?\.)+(?:[A-Z]{2,6}\.?|[A-Z0-9-]{2,}\.?)|'  # domain...
            r'localhost|'  # localhost...
            r'\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})'  # ...or ip
            r'(?::\d+)?'  # optional port
            r'(?:/?|[/?]\S+)$', re.IGNORECASE
        )
        return url_regex.match(url) is not None

    def _is_video_url(self, parsed_url) -> bool:
        """Check if URL is likely a video URL."""
        video_extensions = ['.mp4', '.avi', '.mkv', '.mov', '.wmv']
        return any(parsed_url.path.lower().endswith(ext) for ext in video_extensions)

    def _requires_auth(self, parsed_url) -> bool:
        """Check if URL requires authentication."""
        return parsed_url.username or parsed_url.password
