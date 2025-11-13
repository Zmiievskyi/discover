# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This is a Python-based web crawling project with AI-powered semantic search:
1. **app/** - Modular web crawler with SQLite persistence, ChromaDB vector store, stealth mode, and authentication support
2. **main.py** - Entry point for crawling and indexing
3. **search.py** - Semantic search interface using ChromaDB and OpenAI embeddings

## Folder Structure

```
discover/
├── app/                      # Main crawler package
│   ├── __init__.py           # Package initialization, exports WebCrawler, CrawlDatabase, VectorStore
│   ├── database.py           # CrawlDatabase class (~150 lines) - SQLite storage
│   ├── crawler.py            # WebCrawler class (~345 lines) - Main crawler
│   ├── vector_store.py       # VectorStore class (~280 lines) - ChromaDB + OpenAI embeddings
│   └── config.py             # Configuration loader (~215 lines) - Reads from .env
├── main.py                   # Entry point (~90 lines) - Crawl & index
├── search.py                 # Semantic search script (~110 lines) - AI search interface
├── requirements.txt          # Python dependencies (ChromaDB, OpenAI, etc.)
├── .env.example              # Configuration template (copy to .env)
├── .env                      # Your actual configuration (NOT in git!)
├── .gitignore                # Git ignore rules (excludes .env, *.db, chroma_db/)
├── CLAUDE.md                 # This file
├── venv       /              # Virtual environment
├── crawl_results.json        # Output from crawling (JSON, gitignored)
├── crawl_data.db             # SQLite database (optional, gitignored)
└── chroma_db/                # ChromaDB vector store (persisted, gitignored)
```

## Python Environment Setup

**CRITICAL**: Always use virtual environment for this project:

```bash
# Activate virtual environment (MUST do this first!)
python3 -m venv venv
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Set up configuration (REQUIRED!)
cp .env.example .env
# Then edit .env and configure:
# - OPENAI_API_KEY (required for semantic search)
# - BASE_URL (target website to crawl)
# - AUTH_CONFIG (if crawling protected sites)
# - Other settings as needed
```

Never run Python commands without activating the virtual environment first.

**All configuration is now in `.env` file** - no hardcoded settings in code!

## Running the Crawler

### Web Crawler
```bash
python main.py
```
- Full-featured web crawler with modular architecture
- Features:
  - **ChromaDB vector store** with OpenAI embeddings for AI-powered semantic search
  - SQLite database persistence (crawl_data.db) - optional
  - Stealth mode with random delays and realistic browser headers
  - Multiple authentication methods (manual cookies, **auto-refresh cookies**, Basic Auth, Bearer tokens)
  - **Automatic cookie refresh** - detects expired auth and re-logs in automatically
  - Domain-restricted crawling
  - Configurable page limits and delays
  - Automatic embedding generation using OpenAI API (`text-embedding-3-small`)


### Semantic Search 
```bash
# Interactive search mode
python search.py

# Single query search
python search.py "find all about security"
python search.py "security best practices"
```
- Natural language queries in any language (Russian, English, etc.)
- AI-powered semantic search using OpenAI embeddings (not just keyword matching)
- Uses ChromaDB with `text-embedding-3-small` model (1536 dimensions)
- Returns top 5 most relevant pages with relevance scores
- Supports both interactive and command-line modes
- **Requires OpenAI API key** (set in `.env` file)

## Architecture

### Modular Structure 

**app/database.py** (~150 lines):
- `CrawlDatabase` class: SQLite database wrapper for storing crawled pages
- Key methods:
  - `_create_tables()`: Creates pages table with indexes
  - `page_exists()`: Check if URL already crawled
  - `save_page()`: Persist page data with metadata
  - `get_page()`, `get_all_pages()`: Retrieve stored pages
  - `search_pages()`: Full-text search in titles/content
  - `get_statistics()`: Database stats (total pages, characters, date range)

**app/crawler.py** (~345 lines):
- `WebCrawler` class: Main crawler implementation with session management and auto-refresh authentication
- Key methods:
  - `_setup_stealth_mode()`: Configures realistic browser headers, random User-Agent rotation
  - `_setup_auth()`: Supports Basic Auth, manual cookies, auto-refresh cookies, and Bearer tokens
  - `_login()`: Performs login POST request to get fresh cookies (for auto_cookies mode)
  - `_is_auth_expired()`: Detects expired authentication (401/403 or login redirects)
  - `_get_random_delay()`: Random delays (delay to delay*3) in stealth mode
  - `is_valid_url()`: Domain validation, excludes binary files (.pdf, images, archives)
  - `extract_links()`: Parses HTML links, converts relative to absolute URLs
  - `crawl_page()`: Fetches page, auto-retries with fresh cookies on auth failure, extracts text, queues new links
  - `crawl()`: Main loop with visited URL tracking and delay management
  - `save_results()`: Export to JSON

**app/config.py** (~215 lines):
- Configuration settings module that reads ALL settings from `.env` file
- No hardcoded values - everything configurable via environment variables
- Key features:
  - `load_dotenv()`: Loads `.env` file automatically
  - `get_bool()`, `get_int()`: Helper functions to parse env vars
  - `_build_auth_config()`: Builds auth config from env vars (supports manual cookies, auto-refresh cookies, Basic Auth, Bearer token)
  - `validate_config()`: Validates settings and shows warnings
  - `print_config()`: Debug function to display current configuration
- All variables loaded from environment:
  - `BASE_URL`: Target website
  - `MAX_PAGES`, `DELAY`, `STEALTH_MODE`: Crawler behavior
  - `DATABASE_PATH`, `OUTPUT_FILE`: Storage paths
  - `VECTOR_STORE_ENABLED`, `VECTOR_STORE_PATH`, `VECTOR_COLLECTION_NAME`: ChromaDB settings
  - `OPENAI_EMBEDDING_MODEL`: OpenAI embedding model
  - `AUTH_CONFIG`: Built from `AUTH_TYPE`, `AUTH_COOKIES`, `AUTH_USERNAME`, `AUTH_LOGIN_URL`, etc.

**app/vector_store.py** (~280 lines):
- `VectorStore` class: ChromaDB wrapper for semantic search with OpenAI embeddings
- Key features:
  - Automatic embedding generation using OpenAI API
  - Persistent storage with ChromaDB
  - Cosine similarity search
  - Multilingual support (works with Russian, English, etc.)
  - API key management via environment variables
- Key methods:
  - `_create_embedding()`: Generate embeddings via OpenAI API
  - `add_page()`: Add single page with auto-embedding
  - `add_pages_batch()`: Efficient batch insertion with progress tracking
  - `semantic_search()`: Natural language search with relevance scores
  - `delete_page()`, `clear_all()`: Maintenance operations
  - `get_statistics()`: Vector store stats
- Default model: `text-embedding-3-small` (1536-dim, $0.02/1M tokens, fast and cost-effective)
- Alternative models available: `text-embedding-3-large` (3072-dim, $0.13/1M tokens, better quality)

**app/__init__.py**:
- Package initialization file
- Exports `WebCrawler`, `CrawlDatabase`, `VectorStore`, and `config` for easy importing
- Defines package version (v1.1.0)

**main.py** (~90 lines):
- Entry point that orchestrates all components
- Imports from `app` package
- Creates crawler instance with config settings
- Runs crawl and saves results to JSON
- Automatically saves to ChromaDB vector store (if enabled)
- Optionally saves to SQLite database (commented out by default)
- Displays sample results and statistics

**search.py** (~110 lines):
- Semantic search interface for querying ChromaDB
- Two modes:
  - Interactive: Continuous search queries
  - Single query: Command-line argument search
- Pretty-prints results with relevance scores and previews
- Supports multilingual queries (Russian, English, etc.)

### Why This Refactoring?
- **Single Responsibility**: Each module has one clear purpose
- **File Length**: All files under 350 lines (well within best practices)
  - database.py: ~150 lines
  - crawler.py: ~345 lines (with auto-refresh authentication)
  - vector_store.py: ~280 lines (with OpenAI API integration)
  - config.py: ~215 lines (environment variable loader with validation and auto_cookies support)
  - main.py: ~90 lines
  - search.py: ~110 lines
- **Maintainability**: Easy to modify configuration without touching code (just edit `.env`)
- **Security**: All secrets in `.env` file, never committed to git
- **Testability**: Each module can be tested independently
- **Reusability**: `CrawlDatabase`, `WebCrawler`, and `VectorStore` can be used in other projects
- **Modern AI Features**: ChromaDB + OpenAI embeddings enable semantic search and RAG capabilities
- **Auto-Refresh Authentication**: Automatically handles cookie expiration for long-running crawls

## Configuration via .env File

**All project configuration is managed through the `.env` file** - no hardcoded settings!

### Setup
```bash
# 1. Copy the example file
cp .env.example .env

# 2. Edit .env with your settings
nano .env  # or use any text editor
```

### Environment Variables Reference

**OpenAI API (REQUIRED for semantic search):**
```bash
OPENAI_API_KEY=sk-your-api-key-here
# Get at: https://platform.openai.com/api-keys
```

**Crawler Settings:**
```bash
BASE_URL=https://wikipedia.org/        # Target website
MAX_PAGES=50                            # How many pages to crawl
DELAY=2                                 # Delay between requests (seconds)
STEALTH_MODE=true                       # Enable stealth mode (true/false)
```

**Storage Settings:**
```bash
DATABASE_PATH=crawl_data.db             # SQLite database (optional)
OUTPUT_FILE=crawl_results.json          # JSON output
```

**Vector Store (ChromaDB):**
```bash
VECTOR_STORE_ENABLED=true               # Enable semantic search
VECTOR_STORE_PATH=./chroma_db           # ChromaDB storage directory
VECTOR_COLLECTION_NAME=crawled_pages    # Collection name
OPENAI_EMBEDDING_MODEL=text-embedding-3-small  # Embedding model
```

**Authentication (choose one method):**

*Method 1: Manual Cookies*
```bash
AUTH_TYPE=cookies
AUTH_COOKIES=JSESSIONID=abc123;token=xyz789
# Format: KEY1=VALUE1;KEY2=VALUE2
# Note: Cookies won't refresh automatically - you need to update them manually
```

*Method 2: Auto-Refresh Cookies (NEW!)* ⭐
```bash
AUTH_TYPE=auto_cookies
AUTH_LOGIN_URL=https://your-site.com/login
AUTH_USERNAME=your_username
AUTH_PASSWORD=your_password

# Optional settings (with defaults):
AUTH_LOGIN_USERNAME_FIELD=username  # POST field name for username
AUTH_LOGIN_PASSWORD_FIELD=password  # POST field name for password
AUTH_COOKIES=JSESSIONID=initial_cookie  # Start with existing cookies (optional)
```

**How Auto-Refresh Works:**
- Automatically detects when cookies expire (401/403 responses or login page redirects)
- Performs login POST request using username/password to get fresh cookies
- Retries failed requests automatically with new cookies
- No manual cookie updates needed - perfect for long-running crawls!

**Perfect for:**
- Long-running crawls where session cookies may expire mid-crawl
- Sites with short session timeouts (< 1 hour)
- Automated scheduled crawls without manual intervention
- Development/testing where you don't want to constantly update cookies

**Example:**
```bash
# For a site with login at https://example.com/auth/login
AUTH_TYPE=auto_cookies
AUTH_LOGIN_URL=https://example.com/auth/login
AUTH_USERNAME=myuser@example.com
AUTH_PASSWORD=mypassword123
# Optional: If login form uses different field names
AUTH_LOGIN_USERNAME_FIELD=email  # instead of "username"
AUTH_LOGIN_PASSWORD_FIELD=pwd    # instead of "password"
```

*Method 3: Basic Auth*
```bash
AUTH_TYPE=basic
AUTH_USERNAME=your_username
AUTH_PASSWORD=your_password
```

*Method 4: Bearer Token*
```bash
AUTH_TYPE=headers
AUTH_BEARER_TOKEN=your_token_here
```

*No Authentication*
```bash
AUTH_TYPE=none
```

### Configuration Validation

The `config.py` module automatically validates settings when imported:
- Checks for required values (BASE_URL, OPENAI_API_KEY if vector store enabled)
- Validates ranges (MAX_PAGES >= 1, DELAY >= 0)
- Shows warnings for missing or invalid settings

To debug configuration, use:
```python
from app import config
config.print_config()  # Shows all current settings
```

## Code Quality Rules

- **File length**: Keep files 100-200 lines (max 300)
  - ✓ Modular structure follows this rule (all files < 350 lines)
- **Folder Organization**: Use proper package structure
  - ✓ Code organized in `app/` package (clean, simple structure)
- **All code in English only**: Code, comments, docstrings must be in English
  - ✓ All new modules use English
  - Original file had Russian comments (now fixed in new modules)
- **Single Responsibility Principle**: One class/function = one purpose
- **DRY**: Extract repeated code into functions
- **Descriptive naming**: Clear variable, function, and class names
- **Error handling**: Proper validation and exception handling

## Important Notes

### Security Best Practices
- ✅ **All sensitive data in `.env` file** - OpenAI API keys, auth cookies, credentials
- ✅ **`.gitignore` configured** - `.env` file will never be committed to git
- ✅ **`.env.example` provided** - Template with no real credentials
- ✅ **No hardcoded secrets** - All configuration loaded from environment variables
- **CRITICAL**: Never commit `.env` file or share it publicly!
- **IMPORTANT**: Rotate API keys if accidentally exposed

### Translation Status
- ✓ All modules in `app/` use English
- ✓ All documentation is in English
- ✓ All code comments and docstrings are in English

### Development Approach
- Act as a mentor: explain WHY, point out learning opportunities
- Politely correct significant English grammar mistakes
- Show both simple and advanced solutions when appropriate

## ChromaDB and Semantic Search with OpenAI

### What is This Stack?
This project uses **ChromaDB** (vector database) + **OpenAI Embeddings API** for AI-powered search:
- **ChromaDB**: Stores and searches document embeddings (numerical representations of text)
- **OpenAI embeddings**: State-of-the-art text embeddings (`text-embedding-3-small`)
- **Semantic search**: Find documents by meaning, not just keywords
- **Multilingual search**: Works with Russian, English, and other languages
- **RAG (Retrieval-Augmented Generation)**: Feed relevant documents to LLMs for better answers

### How It Works
1. **Indexing** (`main.py`):
   - Crawls pages and extracts text
   - Sends text to OpenAI API to generate embeddings (1536-dimensional vectors)
   - Stores embeddings in ChromaDB with metadata (URL, title, etc.)
   - Cost: ~$0.02 per 1 million tokens (very cheap!)

2. **Searching** (`search.py`):
   - Takes natural language query (e.g., "find all about security")
   - Converts query to embedding via OpenAI API
   - Finds most similar documents using cosine similarity
   - Returns ranked results with relevance scores

### Use Cases
- **Documentation search**: "How to configure authentication?"
- **Multilingual search**: Query in Russian, find English content (and vice versa)
- **Concept search**: "security best practices" finds related pages even without exact keywords
- **RAG integration**: Use with GPT/Claude to answer questions based on crawled content

### Configuration

**All configuration is in `.env` file:**

```bash
# 1. Copy the template
cp .env.example .env

# 2. Edit .env and configure
nano .env
```

**Required settings in `.env`:**
```bash
# OpenAI API key (REQUIRED!)
OPENAI_API_KEY=sk-your-key-here

# Target website to crawl
BASE_URL=https://your-site.com/

# Vector store settings
VECTOR_STORE_ENABLED=true
OPENAI_EMBEDDING_MODEL=text-embedding-3-small
```

**Embedding model options** (change in `.env`):
```bash
# Fast and cheap (default)
OPENAI_EMBEDDING_MODEL=text-embedding-3-small  # $0.02/1M tokens, 1536-dim

# Better quality, more expensive
OPENAI_EMBEDDING_MODEL=text-embedding-3-large  # $0.13/1M tokens, 3072-dim

# Legacy model
OPENAI_EMBEDDING_MODEL=text-embedding-ada-002  # $0.10/1M tokens, 1536-dim
```

See **Configuration via .env File** section above for all available options.

### Example Usage
```bash
# 1. Activate venv (CRITICAL!)
source venv/bin/activate

# 2. Install dependencies (first time only)
pip install -r requirements.txt

# 3. Set up OpenAI API key (REQUIRED!)
cp .env.example .env
# Edit .env and add: OPENAI_API_KEY=sk-your-key-here

# 4. Crawl and index pages (will generate embeddings via OpenAI API)
python main.py

# 5. Search interactively
python search.py

# 6. Single query search
python search.py "find all about security"
python search.py "how to configure cookies"
```

### Cost Estimation
For 50 pages with ~1000 words each:
- Tokens: ~50,000 tokens (50 pages × ~1000 words)
- Cost: **~$0.001** (less than 1 cent!)
- OpenAI embeddings are very affordable for most use cases

## Git Practices

- Always use semantic commit messages: `feat:`, `fix:`, `refactor:`, `docs:`
- Commit before major changes
- Track version changes for Docker images (though this project doesn't use Docker currently)