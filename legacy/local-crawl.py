import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlparse
import time
import json
import random
import sqlite3
from datetime import datetime

try:
    import chromadb
    from chromadb.config import Settings
    CHROMADB_AVAILABLE = True
except ImportError:
    CHROMADB_AVAILABLE = False
    print("⚠️ ChromaDB не установлен. Для AI-поиска установите: pip install chromadb")


class ChromaVectorDB:
    """Класс для работы с ChromaDB (векторная база для AI-поиска)"""

    def __init__(self, collection_name='crawled_pages', persist_directory='./chroma_db'):
        """
        Инициализация ChromaDB

        Args:
            collection_name: Имя коллекции для хранения embeddings
            persist_directory: Директория для сохранения данных
        """
        if not CHROMADB_AVAILABLE:
            raise ImportError("ChromaDB не установлен. Установите: pip install chromadb")

        self.client = chromadb.PersistentClient(path=persist_directory)

        # Получаем или создаем коллекцию
        try:
            self.collection = self.client.get_collection(name=collection_name)
            print(f"✓ ChromaDB коллекция '{collection_name}' загружена")
        except:
            self.collection = self.client.create_collection(
                name=collection_name,
                metadata={"description": "Web crawling results with semantic search"}
            )
            print(f"✓ ChromaDB коллекция '{collection_name}' создана")

    def add_page(self, url, title, content, metadata=None):
        """
        Добавляет страницу в векторную базу

        Args:
            url: URL страницы (используется как ID)
            title: Заголовок страницы
            content: Полный текст страницы
            metadata: Дополнительные метаданные
        """
        try:
            # Создаем текст для эмбеддинга (title + content)
            text_for_embedding = f"{title}\n\n{content}"

            # Подготавливаем метаданные
            meta = {
                'url': url,
                'title': title,
                'content_length': len(content)
            }
            if metadata:
                meta.update(metadata)

            # Добавляем в ChromaDB
            # ChromaDB автоматически создаст embedding используя встроенную модель
            self.collection.add(
                documents=[text_for_embedding],
                metadatas=[meta],
                ids=[url]  # URL как уникальный ID
            )
            return True
        except Exception as e:
            print(f"Ошибка добавления в ChromaDB: {e}")
            return False

    def search(self, query, n_results=5):
        """
        Семантический поиск по запросу

        Args:
            query: Текстовый запрос
            n_results: Количество результатов

        Returns:
            Список результатов с метаданными
        """
        try:
            results = self.collection.query(
                query_texts=[query],
                n_results=n_results
            )

            # Форматируем результаты
            formatted_results = []
            if results['ids'] and len(results['ids'][0]) > 0:
                for i in range(len(results['ids'][0])):
                    formatted_results.append({
                        'url': results['ids'][0][i],
                        'metadata': results['metadatas'][0][i] if results['metadatas'] else {},
                        'distance': results['distances'][0][i] if results['distances'] else None,
                        'document': results['documents'][0][i] if results['documents'] else None
                    })

            return formatted_results
        except Exception as e:
            print(f"Ошибка поиска в ChromaDB: {e}")
            return []

    def get_count(self):
        """Получает количество документов в коллекции"""
        return self.collection.count()

    def delete_all(self):
        """Удаляет все документы из коллекции"""
        try:
            self.client.delete_collection(self.collection.name)
            print(f"✓ Коллекция '{self.collection.name}' удалена")
            return True
        except Exception as e:
            print(f"Ошибка удаления коллекции: {e}")
            return False


class CrawlDatabase:
    """Класс для работы с SQLite базой данных"""

    def __init__(self, db_path='crawl_data.db'):
        """
        Инициализация базы данных

        Args:
            db_path: Путь к файлу базы данных SQLite
        """
        self.db_path = db_path
        self.conn = sqlite3.connect(db_path)
        self.cursor = self.conn.cursor()
        self._create_tables()
        print(f"✓ База данных подключена: {db_path}")

    def _create_tables(self):
        """Создает таблицы если их нет"""
        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS pages (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                url TEXT UNIQUE NOT NULL,
                title TEXT,
                content TEXT,
                text_length INTEGER,
                links_count INTEGER,
                crawled_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                metadata TEXT
            )
        ''')

        # Создаем индексы для быстрого поиска
        self.cursor.execute('''
            CREATE INDEX IF NOT EXISTS idx_url ON pages(url)
        ''')
        self.cursor.execute('''
            CREATE INDEX IF NOT EXISTS idx_crawled_at ON pages(crawled_at)
        ''')

        self.conn.commit()

    def page_exists(self, url):
        """Проверяет, существует ли страница в базе"""
        self.cursor.execute('SELECT id FROM pages WHERE url = ?', (url,))
        return self.cursor.fetchone() is not None

    def save_page(self, url, title, content, links_count=0, metadata=None):
        """
        Сохраняет страницу в базу данных

        Args:
            url: URL страницы
            title: Заголовок страницы
            content: Полный текст страницы
            links_count: Количество ссылок на странице
            metadata: Дополнительные метаданные (словарь)
        """
        try:
            text_length = len(content)
            metadata_json = json.dumps(metadata) if metadata else None

            self.cursor.execute('''
                INSERT OR REPLACE INTO pages
                (url, title, content, text_length, links_count, metadata, crawled_at)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            ''', (url, title, content, text_length, links_count, metadata_json, datetime.now()))

            self.conn.commit()
            return True
        except Exception as e:
            print(f"Ошибка сохранения в БД: {e}")
            return False

    def get_page(self, url):
        """Получает страницу по URL"""
        self.cursor.execute('''
            SELECT url, title, content, text_length, links_count, crawled_at, metadata
            FROM pages WHERE url = ?
        ''', (url,))

        row = self.cursor.fetchone()
        if row:
            return {
                'url': row[0],
                'title': row[1],
                'content': row[2],
                'text_length': row[3],
                'links_count': row[4],
                'crawled_at': row[5],
                'metadata': json.loads(row[6]) if row[6] else None
            }
        return None

    def get_all_pages(self, limit=None):
        """Получает все страницы из базы"""
        query = 'SELECT url, title, text_length, crawled_at FROM pages ORDER BY crawled_at DESC'
        if limit:
            query += f' LIMIT {limit}'

        self.cursor.execute(query)
        return self.cursor.fetchall()

    def search_pages(self, search_term):
        """Поиск страниц по ключевому слову в заголовке или контенте"""
        self.cursor.execute('''
            SELECT url, title, text_length, crawled_at
            FROM pages
            WHERE title LIKE ? OR content LIKE ?
            ORDER BY crawled_at DESC
        ''', (f'%{search_term}%', f'%{search_term}%'))

        return self.cursor.fetchall()

    def get_statistics(self):
        """Получает статистику по базе данных"""
        self.cursor.execute('SELECT COUNT(*) FROM pages')
        total_pages = self.cursor.fetchone()[0]

        self.cursor.execute('SELECT SUM(text_length) FROM pages')
        total_chars = self.cursor.fetchone()[0] or 0

        self.cursor.execute('SELECT MIN(crawled_at), MAX(crawled_at) FROM pages')
        date_range = self.cursor.fetchone()

        return {
            'total_pages': total_pages,
            'total_characters': total_chars,
            'first_crawl': date_range[0],
            'last_crawl': date_range[1]
        }

    def close(self):
        """Закрывает соединение с базой данных"""
        self.conn.close()
        print("✓ База данных закрыта")


class WebCrawler:
    def __init__(self, base_url, max_pages=100, delay=1, stealth_mode=False, auth=None,
                 use_database=True, db_path='crawl_data.db',
                 use_chromadb=False, chroma_collection='crawled_pages'):
        """
        Инициализация краулера

        Args:
            base_url: Начальный URL для краулинга
            max_pages: Максимальное количество страниц для обработки (None = без ограничений)
            delay: Задержка между запросами в секундах (при stealth_mode используется как минимальная задержка)
            stealth_mode: Включить стелс-режим (случайные задержки, реалистичные заголовки)
            auth: Словарь с данными для авторизации
            use_database: Использовать SQLite для сохранения результатов
            db_path: Путь к файлу базы данных SQLite
            use_chromadb: Использовать ChromaDB для AI-поиска
            chroma_collection: Имя коллекции ChromaDB
        """
        self.base_url = base_url
        self.max_pages = max_pages
        self.delay = delay
        self.stealth_mode = stealth_mode
        self.visited_urls = set()
        self.to_visit = [base_url]
        self.results = []
        self.auth = auth
        self.use_database = use_database
        self.use_chromadb = use_chromadb

        # Инициализация SQLite базы данных
        self.db = None
        if use_database:
            self.db = CrawlDatabase(db_path)

        # Инициализация ChromaDB
        self.vector_db = None
        if use_chromadb:
            if not CHROMADB_AVAILABLE:
                print("⚠️ ChromaDB не установлен, продолжаем без AI-поиска")
                self.use_chromadb = False
            else:
                try:
                    self.vector_db = ChromaVectorDB(collection_name=chroma_collection)
                except Exception as e:
                    print(f"⚠️ Ошибка инициализации ChromaDB: {e}")
                    self.use_chromadb = False

        # Создаем сессию для сохранения cookies
        self.session = requests.Session()

        # Настраиваем стелс-режим
        if stealth_mode:
            self._setup_stealth_mode()

        # Настраиваем авторизацию
        if auth:
            self._setup_auth(auth)

        # Получаем домен для проверки, что остаемся на том же сайте
        parsed = urlparse(base_url)
        self.domain = f"{parsed.scheme}://{parsed.netloc}"

    def _setup_stealth_mode(self):
        """Настраивает стелс-режим для незаметного краулинга"""
        # Реалистичные User-Agent строки популярных браузеров
        user_agents = [
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:121.0) Gecko/20100101 Firefox/121.0',
            'Mozilla/5.0 (Macintosh; Intel Mac OS X 10.15; rv:121.0) Gecko/20100101 Firefox/121.0',
            'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.2 Safari/605.1.15',
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36 Edg/120.0.0.0'
        ]

        # Выбираем случайный User-Agent
        self.session.headers.update({
            'User-Agent': random.choice(user_agents),
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.9,ru;q=0.8',
            'Accept-Encoding': 'gzip, deflate, br',
            'DNT': '1',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1',
            'Sec-Fetch-Dest': 'document',
            'Sec-Fetch-Mode': 'navigate',
            'Sec-Fetch-Site': 'none',
            'Sec-Fetch-User': '?1',
            'Cache-Control': 'max-age=0'
        })

        print(f"✓ Стелс-режим активирован")
        print(f"  User-Agent: {self.session.headers['User-Agent'][:80]}...")
        print(f"  Случайная задержка: {self.delay}-{self.delay * 3} сек")

    def _setup_auth(self, auth):
        """Настраивает авторизацию"""
        auth_type = auth.get('type')

        if auth_type == 'basic':
            from requests.auth import HTTPBasicAuth
            self.session.auth = HTTPBasicAuth(auth['username'], auth['password'])
            print("✓ Настроена Basic Auth")

        elif auth_type == 'cookies':
            self.session.cookies.update(auth['cookies'])
            print("✓ Добавлены cookies")

        elif auth_type == 'headers':
            self.session.headers.update(auth['headers'])
            print("✓ Добавлены заголовки авторизации")

    def _get_random_delay(self):
        """Возвращает случайную задержку для стелс-режима"""
        if self.stealth_mode:
            min_delay = self.delay
            max_delay = self.delay * 3
            return random.uniform(min_delay, max_delay)
        else:
            return self.delay

    def is_valid_url(self, url):
        """Проверяет, валидный ли URL и принадлежит ли он тому же домену"""
        parsed = urlparse(url)

        if parsed.scheme not in ['http', 'https']:
            return False

        url_domain = f"{parsed.scheme}://{parsed.netloc}"
        if url_domain != self.domain:
            return False

        excluded_extensions = ['.pdf', '.jpg', '.jpeg', '.png', '.gif', '.zip', '.rar', '.doc', '.docx', '.xls', '.xlsx']
        if any(url.lower().endswith(ext) for ext in excluded_extensions):
            return False

        return True

    def extract_links(self, soup, current_url):
        """Извлекает все ссылки со страницы"""
        links = []
        for link in soup.find_all('a', href=True):
            href = link['href']
            full_url = urljoin(current_url, href)
            full_url = full_url.split('#')[0]

            if self.is_valid_url(full_url):
                links.append(full_url)

        return links

    def crawl_page(self, url):
        """Краулит одну страницу"""
        try:
            print(f"Обработка: {url}")
            response = self.session.get(url, timeout=10)
            response.raise_for_status()

            soup = BeautifulSoup(response.content, 'html.parser')

            # Извлекаем текст
            for script in soup(["script", "style"]):
                script.decompose()

            text = soup.get_text()
            lines = (line.strip() for line in text.splitlines())
            chunks = (phrase.strip() for line in lines for phrase in line.split("  "))
            text = '\n'.join(chunk for chunk in chunks if chunk)

            title = soup.title.string if soup.title else ''

            # Извлекаем ссылки для дальнейшего краулинга
            links = self.extract_links(soup, url)

            # Сохраняем в память
            self.results.append({
                'url': url,
                'title': title,
                'text': text[:1000],
                'text_length': len(text)
            })

            # Сохраняем в базу данных
            parsed = urlparse(url)
            metadata = {
                'domain': f"{parsed.scheme}://{parsed.netloc}",
                'path': parsed.path,
                'links_count': len(links)
            }

            if self.db:
                self.db.save_page(url, title, text, len(links), metadata)
                print(f"  💾 SQLite: Сохранено (текста: {len(text)} символов)")

            # Сохраняем в ChromaDB для AI-поиска
            if self.vector_db:
                self.vector_db.add_page(url, title, text, metadata)
                print(f"  🧠 ChromaDB: Embedding создан")

            # Добавляем новые ссылки в очередь
            for link in links:
                if link not in self.visited_urls and link not in self.to_visit:
                    self.to_visit.append(link)

            return True

        except Exception as e:
            print(f"Ошибка при обработке {url}: {str(e)}")
            return False

    def crawl(self):
        """Основной метод краулинга"""
        print(f"Начинаем краулинг: {self.base_url}")
        if self.max_pages:
            print(f"Максимум страниц: {self.max_pages}")
        else:
            print(f"Максимум страниц: БЕЗ ОГРАНИЧЕНИЙ ♾️")
        print("-" * 80)

        while self.to_visit and (self.max_pages is None or len(self.visited_urls) < self.max_pages):
            url = self.to_visit.pop(0)

            if url in self.visited_urls:
                continue

            self.visited_urls.add(url)
            self.crawl_page(url)

            # Задержка между запросами (случайная в стелс-режиме)
            delay = self._get_random_delay()
            if self.stealth_mode:
                print(f"⏳ Пауза {delay:.1f} сек...")
            time.sleep(delay)

        print("-" * 80)
        print(f"Краулинг завершен!")
        print(f"Обработано страниц: {len(self.visited_urls)}")
        print(f"Собрано результатов: {len(self.results)}")

        # Показываем статистику из базы данных
        if self.db:
            stats = self.db.get_statistics()
            print(f"\n📊 Статистика SQLite:")
            print(f"  Всего страниц: {stats['total_pages']}")
            print(f"  Всего символов: {stats['total_characters']:,}")
            if stats['first_crawl']:
                print(f"  Первый краулинг: {stats['first_crawl']}")
                print(f"  Последний краулинг: {stats['last_crawl']}")

        if self.vector_db:
            print(f"\n🧠 Статистика ChromaDB:")
            print(f"  Всего embeddings: {self.vector_db.get_count()}")

        return self.results

    def search(self, query, n_results=5):
        """
        Семантический поиск по скравленным страницам (требует ChromaDB)

        Args:
            query: Текстовый запрос на любом языке
            n_results: Количество результатов

        Returns:
            Список найденных страниц с полной информацией из SQLite
        """
        if not self.vector_db:
            print("⚠️ ChromaDB не включен. Используйте use_chromadb=True при создании краулера")
            return []

        print(f"\n🔍 Поиск: '{query}'")
        print("-" * 80)

        # Ищем в ChromaDB
        vector_results = self.vector_db.search(query, n_results)

        if not vector_results:
            print("Ничего не найдено")
            return []

        # Достаем полные данные из SQLite
        full_results = []
        for i, result in enumerate(vector_results, 1):
            url = result['url']
            print(f"\n{i}. {result['metadata'].get('title', 'Без заголовка')}")
            print(f"   URL: {url}")
            print(f"   Релевантность: {1 - result['distance']:.2%}" if result['distance'] else "")

            # Получаем полный контент из SQLite
            if self.db:
                page_data = self.db.get_page(url)
                if page_data:
                    full_results.append(page_data)
                    print(f"   Текста: {page_data['text_length']:,} символов")

        return full_results

    def save_results(self, filename='crawl_results.json'):
        """Сохраняет результаты в JSON файл"""
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(self.results, f, ensure_ascii=False, indent=2)
        print(f"Результаты сохранены в {filename}")

    def close(self):
        """Закрывает соединения"""
        if self.db:
            self.db.close()


if __name__ == "__main__":
    # Настройки краулера
    base_url = "https://wiki.gcore.lu/"

    auth_config = {
        'type': 'cookies',
        'cookies': {
            'JSESSIONID': '71F572ACA7F168D486482260A4E7C0E0',
            'croowd.token_key': '_0wiPRNuFIY5vZU7Z1oKngAAAAAAAIACYW50b24uem1paWV2c2t5aUBnY29yZS5sdQ'
        }
    }

    # Создаем и запускаем краулер
    crawler = WebCrawler(
        base_url=base_url,
        max_pages=None,  # БЕЗ ОГРАНИЧЕНИЙ! Скравлит все доступные страницы
        delay=2,  # Базовая задержка 2 секунды (в стелс-режиме будет 2-6 сек)
        stealth_mode=True,  # ВКЛЮЧЕН СТЕЛС-РЕЖИМ
        auth=auth_config,  # Передаем конфигурацию авторизации
        use_database=True,  # ВКЛЮЧЕНА база данных SQLite
        db_path='crawl_data.db',  # Имя файла базы данных
        use_chromadb=True,  # ВКЛЮЧЕНА ChromaDB для AI-поиска
        chroma_collection='wiki_gcore'  # Имя коллекции ChromaDB
    )

    try:
        results = crawler.crawl()
        crawler.save_results()

        # Пример AI-поиска (раскомментируйте чтобы использовать)
        # print("\n" + "="*80)
        # print("ПРИМЕР AI-ПОИСКА")
        # print("="*80)
        # search_results = crawler.search("как настроить VPN", n_results=3)
        # if search_results:
        #     print(f"\nНайдено {len(search_results)} релевантных страниц")

    finally:
        crawler.close()

    # Выводим краткую статистику
    print("\nПримеры найденных страниц:")
    for i, result in enumerate(results[:5], 1):
        print(f"{i}. {result['title']} - {result['url']}")