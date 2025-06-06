from typing import List
import requests
from tenacity import retry, stop_after_attempt, wait_exponential
from utils.config import config

class DuckDuckGoSearch:
    @retry(
        stop=stop_after_attempt(config.search_config.retry.max_attempts),
        wait=wait_exponential(
            multiplier=config.search_config.retry.wait_exponential_multiplier / 1000, # Convert ms to s for tenacity
            max=config.search_config.retry.wait_exponential_max / 1000 # Convert ms to s for tenacity
        )
    )
    def search(self, query: str, max_results: int = 10) -> List[str]:
        """Search using DuckDuckGo API."""
        try:
            url = f"https://api.duckduckgo.com/?q={query}&format=json"
            response = requests.get(url)
            response.raise_for_status()
            
            data = response.json()
            results = []
            
            # Extract URLs from related topics
            if 'RelatedTopics' in data:
                for topic in data['RelatedTopics']:
                    if 'FirstURL' in topic:
                        results.append(topic['FirstURL'])
                        if len(results) >= max_results:
                            break
            
            return results
            
        except requests.RequestException as e:
            raise Exception(f"DuckDuckGo search failed: {str(e)}")
