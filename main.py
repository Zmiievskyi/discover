"""
Main entry point for web crawler application.
Orchestrates crawler, database, and configuration.
"""

from src.crawler_app import WebCrawler, CrawlDatabase, VectorStore, config


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

    # Save to ChromaDB vector store for semantic search
    if config.VECTOR_STORE_ENABLED:
        print("\n" + "=" * 80)
        print("SAVING TO VECTOR STORE (ChromaDB)")
        print("=" * 80)

        vector_store = VectorStore(
            persist_directory=config.VECTOR_STORE_PATH,
            collection_name=config.VECTOR_COLLECTION_NAME,
            embedding_model=config.OPENAI_EMBEDDING_MODEL
        )

        # Convert results to format for batch insertion
        pages_to_add = [
            {
                'url': result['url'],
                'title': result['title'],
                'content': result['text']
            }
            for result in results
        ]

        vector_store.add_pages_batch(pages_to_add)

        vs_stats = vector_store.get_statistics()
        print(f"\nVector store statistics:")
        print(f"  Total documents: {vs_stats['total_documents']}")
        print(f"  Collection: {vs_stats['collection_name']}")
        print(f"  Path: {vs_stats['persist_directory']}")
        print("\n✓ Use 'python search.py' for semantic search")

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
