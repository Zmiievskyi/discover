# Web Crawler with AI Semantic Search

Modern web crawler with **ChromaDB + OpenAI embeddings** for powerful semantic search.



## ✨ Features

- 🕷️ **Advanced web crawler** - Stealth mode, authentication, domain-restricted crawling
- 🤖 **AI-powered semantic search** - OpenAI embeddings (`text-embedding-3-small`)
- 🗄️ **ChromaDB vector store** - Persistent storage for embeddings
- 🌍 **Multilingual** - Search in any language
- 🔒 **Security-first** - All secrets in `.env`, never in git
- 📦 **Modular** - Clean, testable, reusable components

## 🚀 Quick Start

### 1. Setup

```bash
# Activate virtual environment
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Configure (copy template and edit)
cp .env.example .env
nano .env  # Add your OPENAI_API_KEY
```

### 2. Crawl

```bash
python main.py
```

Crawls `BASE_URL` (from `.env`), generates embeddings, stores in ChromaDB.

### 3. Search

```bash
# Interactive mode
python search.py

# Single query
python search.py "find about security"
python search.py "security best practices"
```

## ⚙️ Configuration (`.env` file)

```bash
# Required
OPENAI_API_KEY=sk-your-key-here
BASE_URL=https://your-site.com/

# Optional
MAX_PAGES=50
STEALTH_MODE=true

# Authentication (if needed)
AUTH_TYPE=cookies
AUTH_COOKIES=JSESSIONID=abc;token=xyz
```

See `.env.example` for all options.

## 📁 Structure

```
discover/
├── app/
│   ├── crawler.py       # Web crawler
│   ├── database.py      # SQLite (optional)
│   ├── vector_store.py  # ChromaDB + OpenAI
│   └── config.py        # Config loader
├── main.py              # Crawl & index
├── search.py            # Semantic search
└── .env                 # Your config (NOT in git)
```

## 💰 Cost

- **$0.02 per 1M tokens** (OpenAI text-embedding-3-small)
- 50 pages ≈ **$0.001** (less than 1 cent!)

## 🔧 Advanced

### Authentication

**Cookies:**
```bash
AUTH_TYPE=cookies
AUTH_COOKIES=KEY1=VAL1;KEY2=VAL2
```

**Basic Auth:**
```bash
AUTH_TYPE=basic
AUTH_USERNAME=user
AUTH_PASSWORD=pass
```

### Change Model

```bash
# Fast & cheap (default)
OPENAI_EMBEDDING_MODEL=text-embedding-3-small

# Better quality
OPENAI_EMBEDDING_MODEL=text-embedding-3-large
```

## 📚 Use Cases

- Documentation search
- Multilingual queries
- Concept-based search (meaning, not keywords)
- RAG with LLMs

## 🛡️ Security

- ✅ Secrets in `.env`
- ✅ `.env` in `.gitignore`
- ❌ **Never commit `.env`!**

## 📖 Full Documentation

See [CLAUDE.md](./CLAUDE.md) for detailed architecture and development guide.

---

Built using ChromaDB, OpenAI, and Python
