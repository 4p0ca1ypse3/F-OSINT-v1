"""
Dark web scanner module for F-OSINT DWv1
"""

import re
import time
import threading
from urllib.parse import urljoin, urlparse
from typing import List, Dict, Any, Optional, Set
from dataclasses import dataclass
from datetime import datetime

import requests
from bs4 import BeautifulSoup

from utils.networking import TorSession, is_onion_url, add_random_delay
from core.tor_handler import get_tor_handler


@dataclass
class ScanResult:
    """Dark web scan result"""
    url: str
    title: str = ""
    content: str = ""
    links: List[str] = None
    forms: List[Dict[str, Any]] = None
    emails: List[str] = None
    status_code: int = 0
    error: str = ""
    timestamp: str = ""
    
    def __post_init__(self):
        if self.links is None:
            self.links = []
        if self.forms is None:
            self.forms = []
        if self.emails is None:
            self.emails = []
        if not self.timestamp:
            self.timestamp = datetime.now().isoformat()


class DarkWebScanner:
    """Dark web scanner for .onion sites"""
    
    def __init__(self, max_depth: int = 3, timeout: int = 60):
        self.max_depth = max_depth
        self.timeout = timeout
        self.tor_handler = get_tor_handler()
        self.session = None
        self.visited_urls: Set[str] = set()
        self.results: List[ScanResult] = []
        self.is_scanning = False
        
        # Email regex pattern
        self.email_pattern = re.compile(r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b')
        
        # Common interesting keywords for content analysis
        self.keywords = [
            'marketplace', 'market', 'shop', 'store', 'buy', 'sell',
            'forum', 'board', 'discussion', 'community',
            'leak', 'database', 'dump', 'breach', 'hack',
            'drugs', 'weapons', 'counterfeit', 'fraud',
            'bitcoin', 'cryptocurrency', 'payment', 'escrow',
            'login', 'register', 'account', 'profile'
        ]
    
    def start_scan(self, urls: List[str], callback=None) -> bool:
        """Start scanning dark web sites"""
        if self.is_scanning:
            return False
        
        # Ensure Tor is running
        if not self.tor_handler.is_tor_running():
            success = self.tor_handler.start_tor()
            if not success:
                return False
        
        self.session = self.tor_handler.get_session()
        if not self.session:
            return False
        
        self.is_scanning = True
        self.visited_urls.clear()
        self.results.clear()
        
        # Start scanning in separate thread
        def scan_thread():
            try:
                for url in urls:
                    if not self.is_scanning:
                        break
                    self._scan_recursive(url, 0, callback)
            finally:
                self.is_scanning = False
        
        threading.Thread(target=scan_thread, daemon=True).start()
        return True
    
    def stop_scan(self):
        """Stop the scanning process"""
        self.is_scanning = False
    
    def _scan_recursive(self, url: str, depth: int, callback=None):
        """Recursively scan a URL and its links"""
        if depth > self.max_depth or not self.is_scanning:
            return
        
        if url in self.visited_urls:
            return
        
        self.visited_urls.add(url)
        
        # Scan the current URL
        result = self._scan_url(url)
        self.results.append(result)
        
        if callback:
            callback(result)
        
        # If successful, scan linked .onion URLs
        if result.status_code == 200 and result.links:
            for link in result.links:
                if is_onion_url(link) and link not in self.visited_urls:
                    add_random_delay(1, 3)  # Avoid overwhelming the network
                    if self.is_scanning:
                        self._scan_recursive(link, depth + 1, callback)
    
    def _scan_url(self, url: str) -> ScanResult:
        """Scan a single URL"""
        result = ScanResult(url=url)
        
        try:
            # Make request through Tor
            response = self.session.get(url, timeout=self.timeout, allow_redirects=True)
            result.status_code = response.status_code
            
            if response.status_code == 200:
                # Parse HTML content
                soup = BeautifulSoup(response.text, 'html.parser')
                
                # Extract title
                title_tag = soup.find('title')
                if title_tag:
                    result.title = title_tag.get_text().strip()
                
                # Extract text content
                result.content = soup.get_text()[:5000]  # Limit content size
                
                # Extract links
                result.links = self._extract_links(soup, url)
                
                # Extract forms
                result.forms = self._extract_forms(soup)
                
                # Extract emails
                result.emails = self._extract_emails(response.text)
                
        except requests.exceptions.RequestException as e:
            result.error = f"Request error: {str(e)}"
        except Exception as e:
            result.error = f"Unexpected error: {str(e)}"
        
        return result
    
    def _extract_links(self, soup: BeautifulSoup, base_url: str) -> List[str]:
        """Extract all links from the page"""
        links = []
        
        for tag in soup.find_all(['a', 'link'], href=True):
            href = tag['href']
            
            # Convert relative URLs to absolute
            full_url = urljoin(base_url, href)
            
            # Only include .onion URLs
            if is_onion_url(full_url):
                links.append(full_url)
        
        return list(set(links))  # Remove duplicates
    
    def _extract_forms(self, soup: BeautifulSoup) -> List[Dict[str, Any]]:
        """Extract forms from the page"""
        forms = []
        
        for form in soup.find_all('form'):
            form_data = {
                'action': form.get('action', ''),
                'method': form.get('method', 'GET').upper(),
                'fields': []
            }
            
            # Extract form fields
            for input_tag in form.find_all(['input', 'textarea', 'select']):
                field = {
                    'type': input_tag.get('type', 'text'),
                    'name': input_tag.get('name', ''),
                    'placeholder': input_tag.get('placeholder', ''),
                    'required': input_tag.has_attr('required')
                }
                form_data['fields'].append(field)
            
            forms.append(form_data)
        
        return forms
    
    def _extract_emails(self, text: str) -> List[str]:
        """Extract email addresses from text"""
        emails = self.email_pattern.findall(text)
        return list(set(emails))  # Remove duplicates
    
    def analyze_content(self, result: ScanResult) -> Dict[str, Any]:
        """Analyze scanned content for interesting information"""
        analysis = {
            'keywords_found': [],
            'potential_marketplace': False,
            'has_login_form': False,
            'has_registration_form': False,
            'email_count': len(result.emails),
            'link_count': len(result.links),
            'form_count': len(result.forms),
            'content_length': len(result.content),
            'suspicious_indicators': []
        }
        
        content_lower = result.content.lower()
        
        # Check for keywords
        for keyword in self.keywords:
            if keyword in content_lower:
                analysis['keywords_found'].append(keyword)
        
        # Analyze potential marketplace
        marketplace_indicators = ['buy', 'sell', 'price', 'payment', 'escrow', 'vendor']
        marketplace_count = sum(1 for indicator in marketplace_indicators if indicator in content_lower)
        if marketplace_count >= 3:
            analysis['potential_marketplace'] = True
        
        # Analyze forms
        for form in result.forms:
            field_names = [field.get('name', '').lower() for field in form['fields']]
            
            # Check for login form
            if any(name in ['username', 'email', 'login'] for name in field_names) and \
               any(name in ['password', 'pass'] for name in field_names):
                analysis['has_login_form'] = True
            
            # Check for registration form
            if any(name in ['register', 'signup', 'email'] for name in field_names):
                analysis['has_registration_form'] = True
        
        # Check for suspicious indicators
        suspicious_words = ['hack', 'crack', 'stolen', 'leaked', 'dump', 'breach']
        for word in suspicious_words:
            if word in content_lower:
                analysis['suspicious_indicators'].append(word)
        
        return analysis
    
    def get_results(self) -> List[ScanResult]:
        """Get scan results"""
        return self.results.copy()
    
    def get_results_summary(self) -> Dict[str, Any]:
        """Get summary of scan results"""
        if not self.results:
            return {}
        
        successful_scans = [r for r in self.results if r.status_code == 200]
        total_links = sum(len(r.links) for r in self.results)
        total_emails = sum(len(r.emails) for r in self.results)
        total_forms = sum(len(r.forms) for r in self.results)
        
        return {
            'total_scanned': len(self.results),
            'successful_scans': len(successful_scans),
            'failed_scans': len(self.results) - len(successful_scans),
            'total_links_found': total_links,
            'total_emails_found': total_emails,
            'total_forms_found': total_forms,
            'unique_domains': len(set(urlparse(r.url).netloc for r in self.results))
        }
    
    def export_results(self, format_type: str = 'json') -> str:
        """Export results in specified format"""
        if format_type == 'json':
            import json
            return json.dumps([{
                'url': r.url,
                'title': r.title,
                'status_code': r.status_code,
                'links_count': len(r.links),
                'emails_count': len(r.emails),
                'forms_count': len(r.forms),
                'timestamp': r.timestamp,
                'error': r.error
            } for r in self.results], indent=2)
        
        elif format_type == 'csv':
            import csv
            import io
            
            output = io.StringIO()
            writer = csv.writer(output)
            
            # Header
            writer.writerow(['URL', 'Title', 'Status Code', 'Links', 'Emails', 'Forms', 'Timestamp', 'Error'])
            
            # Data
            for r in self.results:
                writer.writerow([
                    r.url, r.title, r.status_code, len(r.links),
                    len(r.emails), len(r.forms), r.timestamp, r.error
                ])
            
            return output.getvalue()
        
        return ""