"""
Web crawler module.
Implements web crawling with stealth mode and authentication support.
"""

import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlparse
import time
import json
import random


class WebCrawler:
    def __init__(self, base_url, max_pages=100, delay=1, stealth_mode=False, auth=None):
        """
        Initialize web crawler

        Args:
            base_url: Starting URL for crawling
            max_pages: Maximum number of pages to process
            delay: Delay between requests in seconds (used as minimum delay in stealth mode)
            stealth_mode: Enable stealth mode (random delays, realistic headers)
            auth: Authentication configuration dictionary, for example:
                  {'type': 'basic', 'username': 'user', 'password': 'pass'}
                  or
                  {'type': 'cookies', 'cookies': {'session': 'token'}}
        """
        self.base_url = base_url
        self.max_pages = max_pages
        self.delay = delay
        self.stealth_mode = stealth_mode
        self.visited_urls = set()
        self.to_visit = [base_url]
        self.results = []
        self.auth = auth

        # Create session to preserve cookies
        self.session = requests.Session()

        # Configure stealth mode
        if stealth_mode:
            self._setup_stealth_mode()

        # Configure authentication
        if auth:
            self._setup_auth(auth)

        # Get domain to ensure we stay on same site
        parsed = urlparse(base_url)
        self.domain = f"{parsed.scheme}://{parsed.netloc}"

    def _setup_stealth_mode(self):
        """Configure stealth mode for undetectable crawling"""
        # Realistic User-Agent strings from popular browsers
        user_agents = [
            # Chrome on Windows
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            # Chrome on Mac
            'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            # Firefox on Windows
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:121.0) Gecko/20100101 Firefox/121.0',
            # Firefox on Mac
            'Mozilla/5.0 (Macintosh; Intel Mac OS X 10.15; rv:121.0) Gecko/20100101 Firefox/121.0',
            # Safari on Mac
            'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.2 Safari/605.1.15',
            # Edge on Windows
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36 Edg/120.0.0.0'
        ]

        # Select random User-Agent
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

        print(f"✓ Stealth mode activated")
        print(f"  User-Agent: {self.session.headers['User-Agent'][:80]}...")
        print(f"  Random delay: {self.delay}-{self.delay * 3} sec")

    def _setup_auth(self, auth):
        """Configure authentication"""
        auth_type = auth.get('type')

        if auth_type == 'basic':
            # HTTP Basic Authentication
            from requests.auth import HTTPBasicAuth
            self.session.auth = HTTPBasicAuth(auth['username'], auth['password'])
            print("✓ Basic Auth configured")

        elif auth_type == 'cookies':
            # Cookie-based authentication
            self.session.cookies.update(auth['cookies'])
            print("✓ Cookies added")

        elif auth_type == 'headers':
            # Header-based authentication (e.g., Bearer token)
            self.session.headers.update(auth['headers'])
            print("✓ Authentication headers added")

    def _get_random_delay(self):
        """Return random delay for stealth mode"""
        if self.stealth_mode:
            # Random delay from delay to delay*3
            min_delay = self.delay
            max_delay = self.delay * 3
            return random.uniform(min_delay, max_delay)
        else:
            return self.delay

    def is_valid_url(self, url):
        """Check if URL is valid and belongs to same domain"""
        parsed = urlparse(url)

        # Check if it's HTTP/HTTPS
        if parsed.scheme not in ['http', 'https']:
            return False

        # Check if it's the same domain
        url_domain = f"{parsed.scheme}://{parsed.netloc}"
        if url_domain != self.domain:
            return False

        # Ignore binary files
        excluded_extensions = ['.pdf', '.jpg', '.jpeg', '.png', '.gif', '.zip', '.rar', '.doc', '.docx', '.xls', '.xlsx']
        if any(url.lower().endswith(ext) for ext in excluded_extensions):
            return False

        return True

    def extract_links(self, soup, current_url):
        """Extract all links from page"""
        links = []
        for link in soup.find_all('a', href=True):
            href = link['href']

            # Convert relative links to absolute
            full_url = urljoin(current_url, href)

            # Remove fragments (#)
            full_url = full_url.split('#')[0]

            if self.is_valid_url(full_url):
                links.append(full_url)

        return links

    def crawl_page(self, url):
        """Crawl a single page"""
        try:
            print(f"Processing: {url}")
            response = self.session.get(url, timeout=10)
            response.raise_for_status()

            soup = BeautifulSoup(response.content, 'html.parser')

            # Extract text
            # Remove script and style elements
            for script in soup(["script", "style"]):
                script.decompose()

            text = soup.get_text()
            # Clean text from extra whitespace
            lines = (line.strip() for line in text.splitlines())
            chunks = (phrase.strip() for line in lines for phrase in line.split("  "))
            text = '\n'.join(chunk for chunk in chunks if chunk)

            # Save result
            self.results.append({
                'url': url,
                'title': soup.title.string if soup.title else '',
                'text': text[:1000],  # First 1000 characters
                'text_length': len(text)
            })

            # Extract links for further crawling
            links = self.extract_links(soup, url)

            # Add new links to queue
            for link in links:
                if link not in self.visited_urls and link not in self.to_visit:
                    self.to_visit.append(link)

            return True

        except Exception as e:
            print(f"Error processing {url}: {str(e)}")
            return False

    def crawl(self):
        """Main crawling method"""
        print(f"Starting crawl: {self.base_url}")
        print(f"Maximum pages: {self.max_pages}")
        print("-" * 80)

        while self.to_visit and len(self.visited_urls) < self.max_pages:
            url = self.to_visit.pop(0)

            if url in self.visited_urls:
                continue

            self.visited_urls.add(url)
            self.crawl_page(url)

            # Delay between requests (random in stealth mode)
            delay = self._get_random_delay()
            if self.stealth_mode:
                print(f"⏳ Pause {delay:.1f} sec...")
            time.sleep(delay)

        print("-" * 80)
        print(f"Crawl completed!")
        print(f"Pages processed: {len(self.visited_urls)}")
        print(f"Results collected: {len(self.results)}")

        return self.results

    def save_results(self, filename='crawl_results.json'):
        """Save results to JSON file"""
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(self.results, f, ensure_ascii=False, indent=2)
        print(f"Results saved to {filename}")
