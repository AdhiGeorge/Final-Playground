from typing import List
import requests
from tenacity import retry, stop_after_attempt, wait_exponential
from utils.config import config
import os

class GoogleSearch:
    def __init__(self):
        self.api_key = os.getenv('GOOGLE_API_KEY')
        self.cse_id = os.getenv('GOOGLE_CSE_ID')
        if not self.api_key or not self.cse_id:
            raise ValueError("GOOGLE_API_KEY or GOOGLE_CSE_ID not found in environment variables")

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, max=10)
    )
    def search(self, query: str, max_results: int = 10) -> List[str]:
        """Search using Google Custom Search API."""
        try:
            url = "https://www.googleapis.com/customsearch/v1"
            params = {
                "key": self.api_key,
                "cx": self.cse_id,
                "q": query,
                "num": max_results
            }
            
            response = requests.get(url, params=params)
            response.raise_for_status()
            
            data = response.json()
            results = []
            
            if 'items' in data:
                for item in data['items']:
                    if 'link' in item:
                        results.append(item['link'])
                        if len(results) >= max_results:
                            break
            
            return results
            
        except requests.RequestException as e:
            raise Exception(f"Google search failed: {str(e)}")
