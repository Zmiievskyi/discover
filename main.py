"""
Main entry point for web crawler application.
Orchestrates crawler, database, and configuration.
"""

from src.crawler_app import WebCrawler, CrawlDatabase, config


def main():
    """Main function to run the web crawler"""
    print("=" * 80)
    print("WEB CRAWLER")
    print("=" * 80)
    print()

    # Create and run crawler
    crawler = WebCrawler(
        base_url=config.BASE_URL,
        max_pages=config.MAX_PAGES,
        delay=config.DELAY,
        stealth_mode=config.STEALTH_MODE,
        auth=config.AUTH_CONFIG
    )

    # Start crawling
    results = crawler.crawl()

    # Save results to JSON
    crawler.save_results(config.OUTPUT_FILE)

    # Optionally: Save to database
    # Uncomment the lines below to also save to SQLite database
    # db = CrawlDatabase(config.DATABASE_PATH)
    # for result in results:
    #     db.save_page(
    #         url=result['url'],
    #         title=result['title'],
    #         content=result['text'],
    #         links_count=0
    #     )
    # stats = db.get_statistics()
    # print(f"\nDatabase statistics:")
    # print(f"  Total pages: {stats['total_pages']}")
    # print(f"  Total characters: {stats['total_characters']}")
    # db.close()

    # Display sample results
    print("\nSample crawled pages:")
    for i, result in enumerate(results[:5], 1):
        print(f"{i}. {result['title']} - {result['url']}")

    print()
    print("=" * 80)
    print("CRAWL COMPLETED SUCCESSFULLY")
    print("=" * 80)


if __name__ == "__main__":
    main()
