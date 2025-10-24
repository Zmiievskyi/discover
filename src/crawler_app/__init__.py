"""
Web Crawler Application Package

A modular web crawler with SQLite persistence, stealth mode, and authentication support.
"""

from .crawler import WebCrawler
from .database import CrawlDatabase
from . import config

__version__ = '1.0.0'
__all__ = ['WebCrawler', 'CrawlDatabase', 'config']
