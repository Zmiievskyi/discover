#!/usr/bin/env python3
"""
Пример использования AI-поиска по скравленным страницам

Этот скрипт показывает как искать информацию в скравленных данных
используя семантический поиск ChromaDB.
"""

from local_crawl import CrawlDatabase, ChromaVectorDB

def main():
    # Подключаемся к существующим базам данных
    print("Подключение к базам данных...")

    try:
        # SQLite для полных данных
        sqlite_db = CrawlDatabase('crawl_data.db')

        # ChromaDB для AI-поиска
        vector_db = ChromaVectorDB(collection_name='wiki_gcore')

        print(f"\n✓ Подключено к базам данных")
        print(f"  SQLite: {sqlite_db.get_statistics()['total_pages']} страниц")
        print(f"  ChromaDB: {vector_db.get_count()} embeddings")

    except Exception as e:
        print(f"❌ Ошибка подключения: {e}")
        print("Убедитесь что краулинг был выполнен хотя бы один раз")
        return

    # Интерактивный поиск
    print("\n" + "="*80)
    print("AI-ПОИСК ПО СКРАВЛЕННЫМ СТРАНИЦАМ")
    print("="*80)
    print("\nВведите запрос на любом языке (или 'exit' для выхода)")
    print("Примеры:")
    print("  - как настроить VPN")
    print("  - документация по безопасности")
    print("  - marketing strategies")

    while True:
        print("\n" + "-"*80)
        query = input("\n🔍 Поиск: ").strip()

        if not query or query.lower() in ['exit', 'quit', 'q']:
            print("Выход...")
            break

        # Семантический поиск в ChromaDB
        print(f"\nИщем: '{query}'...")
        results = vector_db.search(query, n_results=5)

        if not results:
            print("❌ Ничего не найдено")
            continue

        print(f"\n✓ Найдено {len(results)} релевантных страниц:\n")

        # Показываем результаты
        for i, result in enumerate(results, 1):
            url = result['url']
            metadata = result['metadata']
            distance = result.get('distance', 0)
            relevance = (1 - distance) * 100 if distance else 100

            print(f"{i}. {metadata.get('title', 'Без заголовка')}")
            print(f"   URL: {url}")
            print(f"   Релевантность: {relevance:.1f}%")

            # Получаем полный контент из SQLite
            page_data = sqlite_db.get_page(url)
            if page_data:
                print(f"   Размер: {page_data['text_length']:,} символов")
                # Показываем первые 200 символов
                preview = page_data['content'][:200].replace('\n', ' ')
                print(f"   Превью: {preview}...")
            print()

        # Спрашиваем, показать ли полный контент
        choice = input("Показать полный контент страницы? (введите номер или Enter для продолжения): ").strip()

        if choice.isdigit():
            idx = int(choice) - 1
            if 0 <= idx < len(results):
                url = results[idx]['url']
                page_data = sqlite_db.get_page(url)
                if page_data:
                    print("\n" + "="*80)
                    print(f"ПОЛНЫЙ КОНТЕНТ: {page_data['title']}")
                    print("="*80)
                    print(f"\nURL: {page_data['url']}")
                    print(f"Дата краулинга: {page_data['crawled_at']}")
                    print(f"Размер: {page_data['text_length']:,} символов")
                    print("\nКОНТЕНТ:")
                    print("-"*80)
                    print(page_data['content'])
                    print("-"*80)

    print("\n✓ Работа завершена")
    sqlite_db.close()


if __name__ == "__main__":
    main()
