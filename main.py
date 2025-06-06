from web_search.searcher import WebSearcher
from web_scraper.scraper_manager import ScraperManager
from utils.config import config
from utils.logger import logger
import json

def main():
    # Initialize components
    search_manager = WebSearcher()
    scraper_manager = ScraperManager()
    
    print("\nEnter your search query (or type 'exit' to quit):")
    
    while True:
        query = input("\n> ").strip()
        
        if query.lower() == 'exit':
            print("\nGoodbye!")
            break
        
        if not query:
            print("Please enter a valid search query.")
            continue
            
        try:
            # Search
            print(f"\nSearching for: {query}")
            search_results = search_manager.search(query)
            
            # Display results
            print("\nSearch Results:")
            for i, result in enumerate(search_results[:2], 1):
                print(f"\nResult {i}:")
                if isinstance(result, dict):
                    print(f"Title: {result.get('title', 'No title')}")
                    print(f"URL: {result.get('url', 'No URL')}")
                    print(f"Description: {result.get('description', 'No description')}")
                else:
                    print(f"URL: {result}")
            
            # Extract URLs for scraping
            urls = []
            for result in search_results[:2]:
                if isinstance(result, dict):
                    urls.append(result.get('url', ''))
                else:
                    urls.append(result)
            
            # Scrape
            print("\nStarting to scrape results...")
            scraper_manager.scrape(urls, mode='standard', query=query)
            
            print("\nScraping completed!")
            print("Results have been saved to the appropriate directories.")
            
        except Exception as e:
            logger.error(f"An error occurred: {str(e)}")
            print(f"\nAn error occurred: {str(e)}")

if __name__ == "__main__":
    main()