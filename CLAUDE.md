# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This is a Python-based web crawling project with two implementations:
1. **crawl.py** - Simple Tavily API client for web crawling
2. **src/crawler_app/** - Modular web crawler with SQLite persistence, stealth mode, and authentication support
3. **legacy/local-crawl.py** - Original monolithic version (423 lines, kept for reference)

## Folder Structure

```
tavily/
├── src/
│   └── crawler_app/          # Main crawler package
│       ├── __init__.py        # Package initialization, exports WebCrawler, CrawlDatabase
│       ├── database.py        # CrawlDatabase class (~150 lines)
│       ├── crawler.py         # WebCrawler class (~250 lines)
│       └── config.py          # Configuration settings (~50 lines)
├── legacy/
│   └── local-crawl.py         # Original monolithic version (423 lines)
├── main.py                    # Entry point (~65 lines)
├── crawl.py                   # Simple Tavily API crawler
├── requirements.txt           # Python dependencies
├── CLAUDE.md                  # This file
├── venv_tavily/              # Virtual environment
└── crawl_results.json        # Output from crawling
```

## Python Environment Setup

**CRITICAL**: Always use virtual environment for this project:

```bash
# Activate virtual environment (MUST do this first!)
source venv_tavily/bin/activate

# Install dependencies
pip install -r requirements.txt
```

Never run Python commands without activating the virtual environment first.

## Running the Crawlers

### Simple Tavily API Crawler
```bash
python crawl.py
```
- Uses Tavily API for web crawling
- Configured for `https://paris-brest.be`
- Requires Tavily API key (currently embedded in code)

### Advanced Local Crawler (Modular Version)
```bash
python main.py
```
- Full-featured web crawler with modular architecture
- Features:
  - SQLite database persistence (crawl_data.db)
  - Stealth mode with random delays and realistic browser headers
  - Multiple authentication methods (cookies, Basic Auth, Bearer tokens)
  - Domain-restricted crawling
  - Configurable page limits and delays

**Legacy version**: `python legacy/local-crawl.py` (monolithic 423-line file, kept for reference)

## Architecture

### Modular Structure (Refactored)

**src/crawler_app/database.py** (~150 lines):
- `CrawlDatabase` class: SQLite database wrapper for storing crawled pages
- Key methods:
  - `_create_tables()`: Creates pages table with indexes
  - `page_exists()`: Check if URL already crawled
  - `save_page()`: Persist page data with metadata
  - `get_page()`, `get_all_pages()`: Retrieve stored pages
  - `search_pages()`: Full-text search in titles/content
  - `get_statistics()`: Database stats (total pages, characters, date range)

**src/crawler_app/crawler.py** (~250 lines):
- `WebCrawler` class: Main crawler implementation with session management
- Key methods:
  - `_setup_stealth_mode()`: Configures realistic browser headers, random User-Agent rotation
  - `_setup_auth()`: Supports Basic Auth, cookies, and Bearer tokens
  - `_get_random_delay()`: Random delays (delay to delay*3) in stealth mode
  - `is_valid_url()`: Domain validation, excludes binary files (.pdf, images, archives)
  - `extract_links()`: Parses HTML links, converts relative to absolute URLs
  - `crawl_page()`: Fetches page, extracts text (removes scripts/styles), queues new links
  - `crawl()`: Main loop with visited URL tracking and delay management
  - `save_results()`: Export to JSON

**src/crawler_app/config.py** (~50 lines):
- Configuration settings module
- Variables:
  - `BASE_URL`: Target website (default: `https://wiki.gcore.lu/`)
  - `MAX_PAGES`: Maximum pages to crawl (50)
  - `DELAY`: Base delay between requests (2 seconds)
  - `STEALTH_MODE`: Enable stealth mode (True)
  - `AUTH_CONFIG`: Authentication configuration (cookies, Basic Auth, or Bearer token)
  - `DATABASE_PATH`, `OUTPUT_FILE`: Storage paths

**src/crawler_app/__init__.py**:
- Package initialization file
- Exports `WebCrawler`, `CrawlDatabase`, and `config` for easy importing
- Defines package version

**main.py** (~65 lines):
- Entry point that orchestrates all components
- Imports from `src.crawler_app` package
- Creates crawler instance with config settings
- Runs crawl and saves results
- Optionally saves to database (commented out by default)
- Displays sample results

### Why This Refactoring?
- **Single Responsibility**: Each module has one clear purpose
- **File Length**: All files now under 300 lines (database: ~150, crawler: ~250, config: ~50, main: ~65)
- **Maintainability**: Easy to modify configuration without touching crawler logic
- **Testability**: Each module can be tested independently
- **Reusability**: `CrawlDatabase` and `WebCrawler` can be used in other projects

## Code Quality Rules

- **File length**: Keep files 100-200 lines (max 300)
  - ✓ New modular structure follows this rule
  - Original `legacy/local-crawl.py` (423 lines) kept for reference
- **Folder Organization**: Use proper package structure
  - ✓ Code organized in `src/crawler_app/` package
  - ✓ Legacy code in `legacy/` folder
- **All code in English only**: Code, comments, docstrings must be in English
  - ✓ All new modules use English
  - Original file had Russian comments (now fixed in new modules)
- **Single Responsibility Principle**: One class/function = one purpose
- **DRY**: Extract repeated code into functions
- **Descriptive naming**: Clear variable, function, and class names
- **Error handling**: Proper validation and exception handling

## Important Notes

### Security Warning
- `crawl.py` contains embedded API key (line 4): `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`
- `src/crawler_app/config.py` contains hardcoded authentication cookies (lines 30-33)
- **TODO**: Move sensitive credentials to environment variables or `.env` file
- Add `.env` to `.gitignore` to prevent credential leaks

### Translation Status
- ✓ All new modules in `src/crawler_app/` use English
- Original `legacy/local-crawl.py` still has Russian comments (kept as reference)

### Development Approach
- Act as a mentor: explain WHY, point out learning opportunities
- Politely correct significant English grammar mistakes
- Show both simple and advanced solutions when appropriate

## Git Practices

- Always use semantic commit messages: `feat:`, `fix:`, `refactor:`, `docs:`
- Commit before major changes
- Track version changes for Docker images (though this project doesn't use Docker currently)