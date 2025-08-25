"""
Google dorking module for F-OSINT DWv1
"""

import time
import random
import re
from typing import List, Dict, Any, Optional
from dataclasses import dataclass
from datetime import datetime
from urllib.parse import quote_plus, urlparse

import requests
from bs4 import BeautifulSoup

from utils.networking import RateLimiter, safe_request, add_random_delay


@dataclass
class DorkResult:
    """Google dork search result"""
    title: str
    url: str
    snippet: str
    domain: str = ""
    timestamp: str = ""
    
    def __post_init__(self):
        if not self.domain:
            self.domain = urlparse(self.url).netloc
        if not self.timestamp:
            self.timestamp = datetime.now().isoformat()


class GoogleDorking:
    """Google dorking module for advanced OSINT queries"""
    
    def __init__(self, max_results: int = 100, delay: int = 2):
        self.max_results = max_results
        self.delay = delay
        self.rate_limiter = RateLimiter(max_requests_per_minute=20)
        self.session = requests.Session()
        
        # Set realistic headers
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.5',
            'Accept-Encoding': 'gzip, deflate',
            'DNT': '1',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1',
        })
        
        # Predefined dork templates
        self.dork_templates = {
            'file_types': {
                'pdf': 'filetype:pdf "{query}"',
                'doc': 'filetype:doc OR filetype:docx "{query}"',
                'xls': 'filetype:xls OR filetype:xlsx "{query}"',
                'ppt': 'filetype:ppt OR filetype:pptx "{query}"',
                'txt': 'filetype:txt "{query}"',
                'sql': 'filetype:sql "{query}"',
                'log': 'filetype:log "{query}"',
                'backup': 'filetype:bak OR filetype:backup "{query}"'
            },
            'sensitive_info': {
                'login_pages': 'inurl:login OR inurl:signin OR inurl:admin "{query}"',
                'config_files': 'filetype:conf OR filetype:config OR filetype:ini "{query}"',
                'database_dumps': 'filetype:sql OR "database dump" "{query}"',
                'api_keys': '"api_key" OR "api-key" OR "apikey" "{query}"',
                'passwords': 'filetype:txt "password" "{query}"',
                'emails': '@{query} filetype:txt OR filetype:pdf OR filetype:doc',
                'phone_numbers': '"{query}" phone OR mobile OR cell',
                'social_security': '"{query}" ssn OR "social security"'
            },
            'social_media': {
                'twitter': 'site:twitter.com "{query}"',
                'facebook': 'site:facebook.com "{query}"',
                'linkedin': 'site:linkedin.com "{query}"',
                'instagram': 'site:instagram.com "{query}"',
                'github': 'site:github.com "{query}"',
                'pastebin': 'site:pastebin.com "{query}"'
            },
            'vulnerabilities': {
                'directory_listing': 'intitle:"index of" "{query}"',
                'error_pages': 'intext:"error" OR intext:"warning" "{query}"',
                'debug_info': 'intext:"debug" OR intext:"trace" "{query}"',
                'version_info': 'intext:"version" OR intext:"build" "{query}"'
            },
            'domain_info': {
                'subdomains': 'site:{query} -www',
                'specific_site': 'site:{query}',
                'exclude_site': '"{query}" -site:{exclude}',
                'related_sites': 'related:{query}'
            }
        }
    
    def search(self, query: str, num_results: int = None, lang: str = 'en') -> List[DorkResult]:
        """Perform Google dork search"""
        if num_results is None:
            num_results = self.max_results
        
        results = []
        start = 0
        
        while len(results) < num_results:
            # Rate limiting
            self.rate_limiter.wait_if_needed()
            
            batch_results = self._search_batch(query, start, min(10, num_results - len(results)), lang)
            if not batch_results:
                break
            
            results.extend(batch_results)
            start += 10
            
            # Add delay between requests
            add_random_delay(self.delay, self.delay + 2)
        
        return results[:num_results]
    
    def _search_batch(self, query: str, start: int, num: int, lang: str) -> List[DorkResult]:
        """Search a batch of results"""
        url = "https://www.google.com/search"
        params = {
            'q': query,
            'start': start,
            'num': num,
            'hl': lang,
            'lr': f'lang_{lang}',
        }
        
        try:
            response = safe_request(url, session=self.session, params=params, timeout=15)
            if not response:
                return []
            
            soup = BeautifulSoup(response.text, 'html.parser')
            return self._parse_results(soup)
            
        except Exception as e:
            print(f"Error searching Google: {e}")
            return []
    
    def _parse_results(self, soup: BeautifulSoup) -> List[DorkResult]:
        """Parse Google search results"""
        results = []
        
        # Find result containers
        result_containers = soup.find_all('div', class_='g')
        
        for container in result_containers:
            try:
                # Extract title and URL
                title_element = container.find('h3')
                if not title_element:
                    continue
                
                link_element = title_element.parent
                if not link_element or not link_element.get('href'):
                    continue
                
                title = title_element.get_text()
                url = link_element['href']
                
                # Clean up URL
                if url.startswith('/url?'):
                    # Extract actual URL from Google redirect
                    import urllib.parse as urlparse
                    parsed = urlparse.parse_qs(urlparse.urlparse(url).query)
                    if 'q' in parsed:
                        url = parsed['q'][0]
                
                # Extract snippet
                snippet_element = container.find('span', {'data-ved': True})
                if not snippet_element:
                    snippet_element = container.find('div', class_='s')
                
                snippet = ""
                if snippet_element:
                    snippet = snippet_element.get_text()
                
                # Create result
                result = DorkResult(
                    title=title,
                    url=url,
                    snippet=snippet
                )
                results.append(result)
                
            except Exception as e:
                print(f"Error parsing result: {e}")
                continue
        
        return results
    
    def build_dork(self, category: str, subcategory: str, query: str, **kwargs) -> str:
        """Build a dork query from templates"""
        if category not in self.dork_templates:
            return query
        
        if subcategory not in self.dork_templates[category]:
            return query
        
        template = self.dork_templates[category][subcategory]
        
        # Replace placeholders
        if '{query}' in template:
            dork = template.format(query=query, **kwargs)
        else:
            dork = f"{template} {query}"
        
        return dork
    
    def search_file_type(self, query: str, file_type: str, num_results: int = None) -> List[DorkResult]:
        """Search for specific file types"""
        if file_type in self.dork_templates['file_types']:
            dork = self.build_dork('file_types', file_type, query)
        else:
            dork = f'filetype:{file_type} "{query}"'
        
        return self.search(dork, num_results)
    
    def search_sensitive_info(self, query: str, info_type: str, num_results: int = None) -> List[DorkResult]:
        """Search for sensitive information"""
        if info_type in self.dork_templates['sensitive_info']:
            dork = self.build_dork('sensitive_info', info_type, query)
        else:
            dork = query
        
        return self.search(dork, num_results)
    
    def search_social_media(self, query: str, platform: str, num_results: int = None) -> List[DorkResult]:
        """Search social media platforms"""
        if platform in self.dork_templates['social_media']:
            dork = self.build_dork('social_media', platform, query)
        else:
            dork = f'site:{platform}.com "{query}"'
        
        return self.search(dork, num_results)
    
    def search_domain(self, domain: str, search_type: str = 'specific_site', exclude_domain: str = None) -> List[DorkResult]:
        """Search domain-specific information"""
        if search_type in self.dork_templates['domain_info']:
            if search_type == 'exclude_site' and exclude_domain:
                dork = self.build_dork('domain_info', search_type, domain, exclude=exclude_domain)
            else:
                dork = self.build_dork('domain_info', search_type, domain)
        else:
            dork = f'site:{domain}'
        
        return self.search(dork)
    
    def search_vulnerabilities(self, query: str, vuln_type: str, num_results: int = None) -> List[DorkResult]:
        """Search for potential vulnerabilities"""
        if vuln_type in self.dork_templates['vulnerabilities']:
            dork = self.build_dork('vulnerabilities', vuln_type, query)
        else:
            dork = query
        
        return self.search(dork, num_results)
    
    def custom_dork(self, query: str, operators: Dict[str, str] = None) -> str:
        """Build custom dork with operators"""
        if not operators:
            return query
        
        dork_parts = [query]
        
        for operator, value in operators.items():
            if operator == 'site':
                dork_parts.append(f'site:{value}')
            elif operator == 'filetype':
                dork_parts.append(f'filetype:{value}')
            elif operator == 'inurl':
                dork_parts.append(f'inurl:{value}')
            elif operator == 'intitle':
                dork_parts.append(f'intitle:{value}')
            elif operator == 'intext':
                dork_parts.append(f'intext:{value}')
            elif operator == 'exclude_site':
                dork_parts.append(f'-site:{value}')
            elif operator == 'exclude_term':
                dork_parts.append(f'-{value}')
            elif operator == 'exact_phrase':
                dork_parts.append(f'"{value}"')
            elif operator == 'or_terms':
                if isinstance(value, list):
                    dork_parts.append(' OR '.join(value))
                else:
                    dork_parts.append(f'OR {value}')
            elif operator == 'wildcard':
                dork_parts.append(f'*{value}*')
        
        return ' '.join(dork_parts)
    
    def get_dork_templates(self) -> Dict[str, Dict[str, str]]:
        """Get available dork templates"""
        return self.dork_templates.copy()
    
    def analyze_results(self, results: List[DorkResult]) -> Dict[str, Any]:
        """Analyze dork search results"""
        if not results:
            return {}
        
        domains = {}
        file_extensions = {}
        total_results = len(results)
        
        for result in results:
            # Count domains
            domain = result.domain
            domains[domain] = domains.get(domain, 0) + 1
            
            # Extract file extensions
            url_path = urlparse(result.url).path
            if '.' in url_path:
                ext = url_path.split('.')[-1].lower()
                if len(ext) <= 4:  # Reasonable file extension length
                    file_extensions[ext] = file_extensions.get(ext, 0) + 1
        
        # Sort by frequency
        top_domains = sorted(domains.items(), key=lambda x: x[1], reverse=True)[:10]
        top_extensions = sorted(file_extensions.items(), key=lambda x: x[1], reverse=True)[:10]
        
        return {
            'total_results': total_results,
            'unique_domains': len(domains),
            'top_domains': top_domains,
            'file_types_found': top_extensions,
            'avg_snippet_length': sum(len(r.snippet) for r in results) / total_results if results else 0
        }