import asyncio
from pathlib import Path
import logging
from utils.logger import logger
from web_scraper.components.main_scraper import WebScraper

from web_search.searcher import WebSearcher

async def main():
    """Main application loop"""
    scraper = WebScraper()
    web_searcher = WebSearcher()
    
    while True:
        try:
            query = input("\nEnter your search query (or type 'exit' to quit):\n\n> ")
            
            if query.lower() == 'exit':
                print("\nGoodbye!\n")
                break
                
            print(f"\nSearching for: {query}")
            logger.info(f"Starting search for query: {query}")
            
            # Set query and initialize storage
            await scraper.set_query(query)
            
            # Get real search results
            search_results = await web_searcher.search(query)
            if not search_results:
                print("\nNo search results found. Try a different query.")
                continue
            
            # Scrape results
            scrape_results = await scraper.scrape(search_results)
            
            # Display summary
            success_count = sum(1 for r in scrape_results if r.get("success"))
            print(f"\nScraping completed! Successfully scraped {success_count}/{len(search_results)} URLs.")
            
        except Exception as e:
            logger.error(f"Error in main loop: {e}")
            print(f"\nAn error occurred: {e}")
            continue

if __name__ == "__main__":
    asyncio.run(main())