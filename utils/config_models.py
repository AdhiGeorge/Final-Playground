from pydantic import BaseModel, Field, HttpUrl
from typing import List, Optional, Dict
from pydantic.types import PositiveInt, confloat
import random

# Basic configuration models
class DirectoryConfig(BaseModel):
    base: str = "Data"

class SearchRetryConfig(BaseModel):
    max_attempts: PositiveInt = 3
    wait_exponential_multiplier: PositiveInt = 1000  # ms
    wait_exponential_max: PositiveInt = 10000        # ms
    delay: PositiveInt = 1
    include_metadata: bool = True

class SearchConfig(BaseModel):
    max_results: int = 10
    scrape_top_n: int = 2
    fallback_order: List[str] = ["duckduckgo", "tavily", "google"]
    timeout: PositiveInt = 30
    retry: SearchRetryConfig = Field(default_factory=SearchRetryConfig)

# Rate limiting and proxy
class RateLimitConfig(BaseModel):
    requests_per_minute: PositiveInt = 60
    delay_between_requests: confloat(ge=0) = 1

class ProxyConfig(BaseModel):
    enabled: bool = False
    type: str = "http"
    host: Optional[str] = ""
    port: Optional[PositiveInt] = 8080
    username: Optional[str] = ""
    password: Optional[str] = ""

# Scraping configuration
class ScrapingModesConfig(BaseModel):
    standard: Dict = Field(default_factory=dict)
    deep: Dict = Field(default_factory=dict)

class ScrapingConfig(BaseModel):
    max_concurrent: PositiveInt = 5
    timeout: PositiveInt = 30000
    modes: ScrapingModesConfig = Field(default_factory=ScrapingModesConfig)
    rate_limit: RateLimitConfig = Field(default_factory=RateLimitConfig)
    proxy: ProxyConfig = Field(default_factory=ProxyConfig)
    headers: Dict[str, str] = Field(default_factory=lambda: {
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
        "Accept-Language": "en-US,en;q=0.5",
        "Accept-Encoding": "gzip, deflate, br"
    })
    save_html: bool = True
    save_text: bool = True
    save_pdfs: bool = True
    save_images: bool = True
    capture_formulas: bool = True
    formula_screenshot_quality: int = 90
    user_agents: List[str] = Field(default_factory=lambda: [
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36"
    ])

# Other configurations
class URLValidationConfig(BaseModel):
    allowed_domains: List[str] = Field(default_factory=list)
    blocked_domains: List[str] = Field(default_factory=list)
    blocked_extensions: List[str] = Field(default_factory=lambda: ['.exe', '.zip', '.rar'])
    max_content_size: int = 10485760  # 10MB
    allow_video_urls: bool = False
    allow_auth_required: bool = False
    url_fetch_session_timeout_total: int = 60  # seconds

class BM25Config(BaseModel):
    k1: confloat(gt=0) = 1.2
    b: confloat(ge=0, le=1) = 0.75

class LoggingConfig(BaseModel):
    level: str = "INFO"
    format: str = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    file: Optional[str] = None

class CircuitBreakerConfig(BaseModel):
    fail_max: PositiveInt = 5
    reset_timeout: PositiveInt = 60

# Main application config
class AppConfig(BaseModel):
    directories: DirectoryConfig = Field(default_factory=DirectoryConfig)
    search: SearchConfig = Field(default_factory=SearchConfig)
    scraping: ScrapingConfig = Field(default_factory=ScrapingConfig)
    url_validation: URLValidationConfig = Field(default_factory=URLValidationConfig)
    bm25: BM25Config = Field(default_factory=BM25Config)
    logging: LoggingConfig = Field(default_factory=LoggingConfig)
    circuit_breaker: CircuitBreakerConfig = Field(default_factory=CircuitBreakerConfig)
