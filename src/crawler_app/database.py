"""
Database module for web crawler.
Handles SQLite storage and retrieval of crawled pages.
"""

import sqlite3
import json
from datetime import datetime


class CrawlDatabase:
    """Class for working with SQLite database"""

    def __init__(self, db_path='crawl_data.db'):
        """
        Initialize database connection

        Args:
            db_path: Path to SQLite database file
        """
        self.db_path = db_path
        self.conn = sqlite3.connect(db_path)
        self.cursor = self.conn.cursor()
        self._create_tables()
        print(f"✓ Database connected: {db_path}")

    def _create_tables(self):
        """Create tables if they don't exist"""
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

        # Create indexes for fast lookups
        self.cursor.execute('''
            CREATE INDEX IF NOT EXISTS idx_url ON pages(url)
        ''')
        self.cursor.execute('''
            CREATE INDEX IF NOT EXISTS idx_crawled_at ON pages(crawled_at)
        ''')

        self.conn.commit()

    def page_exists(self, url):
        """Check if page exists in database"""
        self.cursor.execute('SELECT id FROM pages WHERE url = ?', (url,))
        return self.cursor.fetchone() is not None

    def save_page(self, url, title, content, links_count=0, metadata=None):
        """
        Save page to database

        Args:
            url: Page URL
            title: Page title
            content: Full page text
            links_count: Number of links on page
            metadata: Additional metadata (dictionary)
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
            print(f"Database save error: {e}")
            return False

    def get_page(self, url):
        """Get page by URL"""
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
        """Get all pages from database"""
        query = 'SELECT url, title, text_length, crawled_at FROM pages ORDER BY crawled_at DESC'
        if limit:
            query += f' LIMIT {limit}'

        self.cursor.execute(query)
        return self.cursor.fetchall()

    def search_pages(self, search_term):
        """Search pages by keyword in title or content"""
        self.cursor.execute('''
            SELECT url, title, text_length, crawled_at
            FROM pages
            WHERE title LIKE ? OR content LIKE ?
            ORDER BY crawled_at DESC
        ''', (f'%{search_term}%', f'%{search_term}%'))

        return self.cursor.fetchall()

    def get_statistics(self):
        """Get database statistics"""
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
        """Close database connection"""
        self.conn.close()
        print("✓ Database closed")
