"""
Semantic search script using ChromaDB vector store.
Demonstrates AI-powered search capabilities with natural language queries.
"""

from src.crawler_app import VectorStore, config
import sys


def print_search_results(results, query):
    """Pretty print search results"""
    print(f"\n{'=' * 80}")
    print(f"SEARCH RESULTS FOR: '{query}'")
    print(f"{'=' * 80}\n")

    if not results:
        print("No results found.")
        return

    for i, result in enumerate(results, 1):
        metadata = result['metadata']
        distance = result['distance']
        content_preview = result['content'][:300] + "..." if len(result['content']) > 300 else result['content']

        print(f"{i}. {metadata.get('title', 'No title')}")
        print(f"   URL: {metadata.get('url', 'N/A')}")
        print(f"   Relevance score: {1 - distance:.4f}")  # Convert distance to similarity
        print(f"   Preview: {content_preview}")
        print(f"   {'-' * 76}\n")


def interactive_search():
    """Interactive search mode"""
    print("=" * 80)
    print("SEMANTIC SEARCH - ChromaDB")
    print("=" * 80)
    print("\nLoading vector store...")

    # Initialize vector store
    vector_store = VectorStore(
        persist_directory=config.VECTOR_STORE_PATH,
        collection_name=config.VECTOR_COLLECTION_NAME,
        embedding_model=config.OPENAI_EMBEDDING_MODEL
    )

    stats = vector_store.get_statistics()
    print(f"\n✓ Vector store loaded")
    print(f"  Documents available: {stats['total_documents']}")

    if stats['total_documents'] == 0:
        print("\n❌ No documents in vector store!")
        print("   Run 'python main.py' first to crawl and index pages.\n")
        return

    print("\n" + "=" * 80)
    print("Enter your search queries (natural language)")
    print("Examples:")
    print("  - find all about security")
    print("  - security best practices")
    print("  - how to configure authentication")
    print("\nType 'quit' or 'exit' to stop")
    print("=" * 80)

    while True:
        try:
            query = input("\n🔍 Search query: ").strip()

            if query.lower() in ['quit', 'exit', 'q']:
                print("\n👋 Goodbye!\n")
                break

            if not query:
                continue

            # Perform semantic search
            results = vector_store.semantic_search(query, top_k=5)
            print_search_results(results, query)

        except KeyboardInterrupt:
            print("\n\n👋 Goodbye!\n")
            break
        except Exception as e:
            print(f"\n❌ Search error: {e}\n")


def single_query_search(query, top_k=5):
    """Search with a single query (for command-line usage)"""
    vector_store = VectorStore(
        persist_directory=config.VECTOR_STORE_PATH,
        collection_name=config.VECTOR_COLLECTION_NAME,
        embedding_model=config.OPENAI_EMBEDDING_MODEL
    )

    results = vector_store.semantic_search(query, top_k=top_k)
    print_search_results(results, query)


def main():
    """Main function"""
    # Check if query provided as command-line argument
    if len(sys.argv) > 1:
        query = ' '.join(sys.argv[1:])
        single_query_search(query)
    else:
        # Interactive mode
        interactive_search()


if __name__ == "__main__":
    main()
