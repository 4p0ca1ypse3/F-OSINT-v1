"""
Networking utilities for F-OSINT DWv1
"""

import requests
import socket
import socks
from urllib.parse import urlparse
import time
import random
from typing import Optional, Dict, Any


class TorSession:
    """Tor-enabled HTTP session"""
    
    def __init__(self, proxy_host='127.0.0.1', proxy_port=9050):
        self.proxy_host = proxy_host
        self.proxy_port = proxy_port
        self.session = requests.Session()
        
        # Configure session for Tor
        self.session.proxies = {
            'http': f'socks5h://{proxy_host}:{proxy_port}',
            'https': f'socks5h://{proxy_host}:{proxy_port}'
        }
        
        # Set realistic headers
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; rv:109.0) Gecko/20100101 Firefox/115.0',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.5',
            'Accept-Encoding': 'gzip, deflate',
            'DNT': '1',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1',
        })
    
    def get(self, url, **kwargs):
        """GET request through Tor"""
        return self.session.get(url, **kwargs)
    
    def post(self, url, **kwargs):
        """POST request through Tor"""
        return self.session.post(url, **kwargs)
    
    def check_tor_connection(self) -> bool:
        """Check if Tor connection is working"""
        try:
            response = self.get('https://check.torproject.org/api/ip', timeout=10)
            data = response.json()
            return data.get('IsTor', False)
        except:
            return False
    
    def get_tor_ip(self) -> Optional[str]:
        """Get current Tor IP address"""
        try:
            response = self.get('https://httpbin.org/ip', timeout=10)
            data = response.json()
            return data.get('origin')
        except:
            return None


def check_tor_service(host='127.0.0.1', port=9050) -> bool:
    """Check if Tor service is running"""
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(5)
        result = sock.connect_ex((host, port))
        sock.close()
        return result == 0
    except:
        return False


def is_onion_url(url: str) -> bool:
    """Check if URL is a .onion address"""
    parsed = urlparse(url)
    return parsed.hostname and parsed.hostname.endswith('.onion')


def is_valid_url(url: str) -> bool:
    """Check if URL is valid"""
    try:
        result = urlparse(url)
        return all([result.scheme, result.netloc])
    except:
        return False


def get_domain_from_url(url: str) -> Optional[str]:
    """Extract domain from URL"""
    try:
        parsed = urlparse(url)
        return parsed.netloc
    except:
        return None


def add_random_delay(min_seconds=1, max_seconds=3):
    """Add random delay to avoid rate limiting"""
    delay = random.uniform(min_seconds, max_seconds)
    time.sleep(delay)


class RateLimiter:
    """Simple rate limiter"""
    
    def __init__(self, max_requests_per_minute=30):
        self.max_requests = max_requests_per_minute
        self.requests = []
    
    def can_make_request(self) -> bool:
        """Check if request can be made within rate limit"""
        now = time.time()
        # Remove requests older than 1 minute
        self.requests = [req_time for req_time in self.requests if now - req_time < 60]
        
        return len(self.requests) < self.max_requests
    
    def make_request(self):
        """Record a request"""
        self.requests.append(time.time())
    
    def wait_if_needed(self):
        """Wait if rate limit is exceeded"""
        if not self.can_make_request():
            # Wait until we can make a request
            oldest_request = min(self.requests)
            wait_time = 60 - (time.time() - oldest_request)
            if wait_time > 0:
                time.sleep(wait_time + 1)


def safe_request(url, method='GET', session=None, timeout=30, **kwargs):
    """Make a safe HTTP request with error handling"""
    try:
        if session is None:
            session = requests.Session()
        
        if method.upper() == 'GET':
            response = session.get(url, timeout=timeout, **kwargs)
        elif method.upper() == 'POST':
            response = session.post(url, timeout=timeout, **kwargs)
        else:
            raise ValueError(f"Unsupported HTTP method: {method}")
        
        response.raise_for_status()
        return response
        
    except requests.exceptions.RequestException as e:
        print(f"Request error for {url}: {e}")
        return None
    except Exception as e:
        print(f"Unexpected error for {url}: {e}")
        return None