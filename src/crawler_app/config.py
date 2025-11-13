"""
Configuration settings for web crawler.
All settings are loaded from environment variables (.env file).
"""

import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()


def get_bool(env_var: str, default: bool = False) -> bool:
    """Parse boolean from environment variable"""
    value = os.getenv(env_var, str(default)).lower()
    return value in ('true', '1', 'yes', 'on')


def get_int(env_var: str, default: int = 0) -> int:
    """Parse integer from environment variable"""
    try:
        return int(os.getenv(env_var, default))
    except (ValueError, TypeError):
        return default


# =============================================================================
# CRAWLER SETTINGS
# =============================================================================
BASE_URL = os.getenv('BASE_URL', 'https://wiki.gcore.lu/')
MAX_PAGES = get_int('MAX_PAGES', 50)
DELAY = get_int('DELAY', 2)
STEALTH_MODE = get_bool('STEALTH_MODE', True)
DATABASE_PATH = os.getenv('DATABASE_PATH', 'crawl_data.db')
OUTPUT_FILE = os.getenv('OUTPUT_FILE', 'crawl_results.json')


# =============================================================================
# VECTOR STORE SETTINGS (ChromaDB with OpenAI embeddings)
# =============================================================================
VECTOR_STORE_ENABLED = get_bool('VECTOR_STORE_ENABLED', True)
VECTOR_STORE_PATH = os.getenv('VECTOR_STORE_PATH', './chroma_db')
VECTOR_COLLECTION_NAME = os.getenv('VECTOR_COLLECTION_NAME', 'crawled_pages')

# OpenAI Embeddings API settings
OPENAI_EMBEDDING_MODEL = os.getenv('OPENAI_EMBEDDING_MODEL', 'text-embedding-3-small')
# Alternative OpenAI models:
# - 'text-embedding-3-large' (3072-dim, $0.13/1M tokens, better quality)
# - 'text-embedding-ada-002' (1536-dim, $0.10/1M tokens, legacy model)

# IMPORTANT: Set OPENAI_API_KEY in .env file
# Get your API key at: https://platform.openai.com/api-keys


# =============================================================================
# AUTHENTICATION CONFIGURATION
# =============================================================================
def _build_auth_config():
    """
    Build authentication configuration from environment variables.

    Returns:
        dict or None: Authentication configuration based on AUTH_TYPE
    """
    auth_type = os.getenv('AUTH_TYPE', 'none').lower()

    if auth_type == 'none':
        return None

    elif auth_type == 'cookies':
        # Parse cookies from format: KEY1=VALUE1;KEY2=VALUE2
        cookies_str = os.getenv('AUTH_COOKIES', '')
        if not cookies_str:
            return None

        cookies = {}
        for cookie in cookies_str.split(';'):
            if '=' in cookie:
                key, value = cookie.strip().split('=', 1)
                cookies[key] = value

        return {
            'type': 'cookies',
            'cookies': cookies
        }

    elif auth_type == 'auto_cookies':
        # Auto-refresh cookies using login endpoint
        username = os.getenv('AUTH_USERNAME')
        password = os.getenv('AUTH_PASSWORD')
        login_url = os.getenv('AUTH_LOGIN_URL')

        if not all([username, password, login_url]):
            print("Warning: auto_cookies requires AUTH_USERNAME, AUTH_PASSWORD, and AUTH_LOGIN_URL")
            return None

        # Optional login form field names (defaults to standard names)
        username_field = os.getenv('AUTH_LOGIN_USERNAME_FIELD', 'username')
        password_field = os.getenv('AUTH_LOGIN_PASSWORD_FIELD', 'password')

        # Optional: Parse initial cookies if provided
        initial_cookies_str = os.getenv('AUTH_COOKIES', '')
        initial_cookies = {}
        if initial_cookies_str:
            for cookie in initial_cookies_str.split(';'):
                if '=' in cookie:
                    key, value = cookie.strip().split('=', 1)
                    initial_cookies[key] = value

        return {
            'type': 'auto_cookies',
            'username': username,
            'password': password,
            'login_url': login_url,
            'username_field': username_field,
            'password_field': password_field,
            'initial_cookies': initial_cookies if initial_cookies else None
        }

    elif auth_type == 'basic':
        username = os.getenv('AUTH_USERNAME')
        password = os.getenv('AUTH_PASSWORD')

        if not username or not password:
            return None

        return {
            'type': 'basic',
            'username': username,
            'password': password
        }

    elif auth_type == 'headers':
        bearer_token = os.getenv('AUTH_BEARER_TOKEN')

        if not bearer_token:
            return None

        return {
            'type': 'headers',
            'headers': {
                'Authorization': f'Bearer {bearer_token}'
            }
        }

    else:
        print(f"Warning: Unknown AUTH_TYPE '{auth_type}'. Using no authentication.")
        return None


AUTH_CONFIG = _build_auth_config()


# =============================================================================
# CONFIGURATION VALIDATION
# =============================================================================
def validate_config():
    """
    Validate configuration settings.
    Prints warnings for missing or invalid values.
    """
    warnings = []

    if not BASE_URL:
        warnings.append("⚠️  BASE_URL is not set!")

    if VECTOR_STORE_ENABLED and not os.getenv('OPENAI_API_KEY'):
        warnings.append("⚠️  OPENAI_API_KEY is not set! Vector store will not work.")
        warnings.append("   Get your key at: https://platform.openai.com/api-keys")

    if MAX_PAGES < 1:
        warnings.append(f"⚠️  MAX_PAGES is {MAX_PAGES}, should be >= 1")

    if DELAY < 0:
        warnings.append(f"⚠️  DELAY is {DELAY}, should be >= 0")

    if warnings:
        print("\n" + "=" * 80)
        print("CONFIGURATION WARNINGS")
        print("=" * 80)
        for warning in warnings:
            print(warning)
        print("=" * 80 + "\n")


# =============================================================================
# CONFIGURATION DISPLAY
# =============================================================================
def print_config():
    """Print current configuration (for debugging)"""
    print("\n" + "=" * 80)
    print("CURRENT CONFIGURATION")
    print("=" * 80)
    print(f"BASE_URL: {BASE_URL}")
    print(f"MAX_PAGES: {MAX_PAGES}")
    print(f"DELAY: {DELAY}")
    print(f"STEALTH_MODE: {STEALTH_MODE}")
    print(f"DATABASE_PATH: {DATABASE_PATH}")
    print(f"OUTPUT_FILE: {OUTPUT_FILE}")
    print(f"VECTOR_STORE_ENABLED: {VECTOR_STORE_ENABLED}")
    print(f"VECTOR_STORE_PATH: {VECTOR_STORE_PATH}")
    print(f"VECTOR_COLLECTION_NAME: {VECTOR_COLLECTION_NAME}")
    print(f"OPENAI_EMBEDDING_MODEL: {OPENAI_EMBEDDING_MODEL}")
    print(f"OPENAI_API_KEY: {'✓ Set' if os.getenv('OPENAI_API_KEY') else '✗ Not set'}")

    if AUTH_CONFIG:
        print(f"AUTH_CONFIG: {AUTH_CONFIG.get('type', 'unknown')}")
    else:
        print("AUTH_CONFIG: None")

    print("=" * 80 + "\n")


# Validate configuration on import
validate_config()
