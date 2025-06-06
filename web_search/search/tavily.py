from typing import List
import requests
from tenacity import retry, stop_after_attempt, wait_exponential
from utils.config import config
import os

class TavilySearch:
    def __init__(self):
        self.api_key = os.getenv('TAVILY_API_KEY')
        if not self.api_key:
            raise ValueError("TAVILY_API_KEY not found in environment variables")

    @retry(
        stop=stop_after_attempt(config.search_config.retry.max_attempts),
        wait=wait_exponential(
            multiplier=config.search_config.retry.wait_exponential_multiplier / 1000, # Convert ms to s for tenacity
            max=config.search_config.retry.wait_exponential_max / 1000 # Convert ms to s for tenacity
        )
    )
    def search(self, query: str, max_results: int = 10) -> List[str]:
        """Search using Tavily API."""
        try:
            url = "https://api.tavily.com/search"
            params = {
                "q": query,
                "api_key": self.api_key,
                "limit": max_results
            }
            
            response = requests.get(url, params=params)
            response.raise_for_status()
            
            data = response.json()
            results = []
            
            if 'data' in data and 'results' in data['data']:
                for result in data['data']['results']:
                    if 'url' in result:
                        results.append(result['url'])
                        if len(results) >= max_results:
                            break
            
            return results
            
        except requests.RequestException as e:
            raise Exception(f"Tavily search failed: {str(e)}")
