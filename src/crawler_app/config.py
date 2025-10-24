"""
Configuration settings for web crawler.
Contains default crawler parameters and authentication configuration.
"""

# Crawler settings
BASE_URL = "https://wiki.gcore.lu/"
MAX_PAGES = 50
DELAY = 2  # Base delay in seconds (becomes 2-6 seconds in stealth mode)
STEALTH_MODE = True
DATABASE_PATH = 'crawl_data.db'
OUTPUT_FILE = 'crawl_results.json'


# Authentication configuration
# IMPORTANT: For accessing protected sites like Confluence, authentication is required
#
# Option 1: Cookies (Recommended)
# To get cookies:
# 1. Open the site in browser and log in
# 2. Open DevTools (F12) -> Application/Storage -> Cookies
# 3. Copy required cookies (usually JSESSIONID and/or others)
#
# Option 2: Basic Auth (if supported)
# Option 3: Bearer token (if supported)

AUTH_CONFIG = None  # No authentication (for public sites)

# Uncomment and configure one of the options below:

# Cookie-based authentication:
AUTH_CONFIG = {
    'type': 'cookies',
    'cookies': {
        'JSESSIONID': '71F572ACA7F168D486482260A4E7C0E0',
        'croowd.token_key': '_0wiPRNuFIY5vZU7Z1oKngAAAAAAAIACYW50b24uem1paWV2c2t5aUBnY29yZS5sdQ'
    }
}

# Basic Auth example (uncomment to use):
# AUTH_CONFIG = {
#     'type': 'basic',
#     'username': 'your_username',
#     'password': 'your_password'
# }

# Bearer token example (uncomment to use):
# AUTH_CONFIG = {
#     'type': 'headers',
#     'headers': {
#         'Authorization': 'Bearer YOUR_TOKEN'
#     }
# }
