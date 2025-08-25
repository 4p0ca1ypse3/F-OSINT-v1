"""
PGP key search module for F-OSINT DWv1
"""

import re
import requests
from typing import List, Dict, Any, Optional
from dataclasses import dataclass
from datetime import datetime

from utils.networking import safe_request, RateLimiter


@dataclass
class PGPKey:
    """PGP key information"""
    key_id: str
    user_ids: List[str] = None
    fingerprint: str = ""
    algorithm: str = ""
    key_size: int = 0
    creation_date: str = ""
    expiration_date: str = ""
    key_server: str = ""
    public_key: str = ""
    
    def __post_init__(self):
        if self.user_ids is None:
            self.user_ids = []


class PGPSearch:
    """PGP key search functionality"""
    
    def __init__(self):
        self.rate_limiter = RateLimiter(max_requests_per_minute=30)
        self.session = requests.Session()
        
        # Common PGP key servers
        self.key_servers = [
            'https://keys.openpgp.org',
            'https://keyserver.ubuntu.com',
            'https://pgp.mit.edu',
            'https://keys.gnupg.net'
        ]
        
        # Email pattern for validation
        self.email_pattern = re.compile(r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$')
    
    def search_by_email(self, email: str) -> List[PGPKey]:
        """Search for PGP keys by email address"""
        if not self._validate_email(email):
            return []
        
        all_keys = []
        
        for server in self.key_servers:
            try:
                keys = self._search_key_server(server, email, 'email')
                all_keys.extend(keys)
            except Exception as e:
                print(f"Error searching {server} for {email}: {e}")
        
        return self._deduplicate_keys(all_keys)
    
    def search_by_name(self, name: str) -> List[PGPKey]:
        """Search for PGP keys by name"""
        if not name or len(name) < 3:
            return []
        
        all_keys = []
        
        for server in self.key_servers:
            try:
                keys = self._search_key_server(server, name, 'name')
                all_keys.extend(keys)
            except Exception as e:
                print(f"Error searching {server} for {name}: {e}")
        
        return self._deduplicate_keys(all_keys)
    
    def search_by_key_id(self, key_id: str) -> List[PGPKey]:
        """Search for PGP keys by key ID"""
        if not key_id:
            return []
        
        # Clean key ID
        key_id = key_id.replace('0x', '').upper()
        
        all_keys = []
        
        for server in self.key_servers:
            try:
                keys = self._search_key_server(server, key_id, 'keyid')
                all_keys.extend(keys)
            except Exception as e:
                print(f"Error searching {server} for key ID {key_id}: {e}")
        
        return self._deduplicate_keys(all_keys)
    
    def _search_key_server(self, server: str, query: str, search_type: str) -> List[PGPKey]:
        """Search a specific key server"""
        keys = []
        
        # Rate limiting
        self.rate_limiter.wait_if_needed()
        
        # Different servers have different APIs
        if 'keys.openpgp.org' in server:
            keys = self._search_openpgp_org(query, search_type)
        elif 'keyserver.ubuntu.com' in server:
            keys = self._search_ubuntu_keyserver(query, search_type)
        elif 'pgp.mit.edu' in server:
            keys = self._search_mit_keyserver(query, search_type)
        else:
            # Generic HKP search
            keys = self._search_hkp_server(server, query, search_type)
        
        # Set key server for all found keys
        for key in keys:
            key.key_server = server
        
        return keys
    
    def _search_openpgp_org(self, query: str, search_type: str) -> List[PGPKey]:
        """Search keys.openpgp.org"""
        keys = []
        
        try:
            if search_type == 'email':
                # Search by email
                url = f"https://keys.openpgp.org/vks/v1/by-email/{query}"
            else:
                # General search not directly supported, return empty
                return keys
            
            response = safe_request(url, session=self.session)
            
            if response and response.status_code == 200:
                # Parse response (simplified)
                data = response.text
                if 'BEGIN PGP PUBLIC KEY' in data:
                    key = PGPKey(
                        key_id="unknown",
                        user_ids=[query] if search_type == 'email' else [],
                        public_key=data
                    )
                    keys.append(key)
        
        except Exception as e:
            print(f"Error searching keys.openpgp.org: {e}")
        
        return keys
    
    def _search_ubuntu_keyserver(self, query: str, search_type: str) -> List[PGPKey]:
        """Search keyserver.ubuntu.com"""
        keys = []
        
        try:
            # Ubuntu keyserver uses HKP protocol
            if search_type == 'email':
                search_query = query
            elif search_type == 'name':
                search_query = query
            elif search_type == 'keyid':
                search_query = f"0x{query}"
            else:
                search_query = query
            
            url = f"https://keyserver.ubuntu.com/pks/lookup"
            params = {
                'op': 'index',
                'search': search_query,
                'options': 'mr'  # Machine readable
            }
            
            response = safe_request(url, session=self.session, params=params)
            
            if response and response.status_code == 200:
                keys = self._parse_hkp_response(response.text)
        
        except Exception as e:
            print(f"Error searching Ubuntu keyserver: {e}")
        
        return keys
    
    def _search_mit_keyserver(self, query: str, search_type: str) -> List[PGPKey]:
        """Search pgp.mit.edu"""
        keys = []
        
        try:
            url = f"https://pgp.mit.edu/pks/lookup"
            params = {
                'op': 'index',
                'search': query
            }
            
            response = safe_request(url, session=self.session, params=params)
            
            if response and response.status_code == 200:
                keys = self._parse_mit_response(response.text)
        
        except Exception as e:
            print(f"Error searching MIT keyserver: {e}")
        
        return keys
    
    def _search_hkp_server(self, server: str, query: str, search_type: str) -> List[PGPKey]:
        """Generic HKP server search"""
        keys = []
        
        try:
            url = f"{server}/pks/lookup"
            params = {
                'op': 'index',
                'search': query,
                'options': 'mr'
            }
            
            response = safe_request(url, session=self.session, params=params)
            
            if response and response.status_code == 200:
                keys = self._parse_hkp_response(response.text)
        
        except Exception as e:
            print(f"Error searching HKP server {server}: {e}")
        
        return keys
    
    def _parse_hkp_response(self, response_text: str) -> List[PGPKey]:
        """Parse HKP machine-readable response"""
        keys = []
        current_key = None
        
        for line in response_text.split('\n'):
            line = line.strip()
            
            if line.startswith('pub:'):
                # Public key line
                parts = line.split(':')
                if len(parts) >= 6:
                    current_key = PGPKey(
                        key_id=parts[1],
                        algorithm=parts[2],
                        key_size=int(parts[3]) if parts[3].isdigit() else 0,
                        creation_date=parts[4],
                        expiration_date=parts[5] if parts[5] else ""
                    )
                    keys.append(current_key)
            
            elif line.startswith('uid:') and current_key:
                # User ID line
                parts = line.split(':')
                if len(parts) >= 2:
                    user_id = parts[1]
                    if user_id not in current_key.user_ids:
                        current_key.user_ids.append(user_id)
        
        return keys
    
    def _parse_mit_response(self, response_text: str) -> List[PGPKey]:
        """Parse MIT keyserver HTML response"""
        keys = []
        
        # This would require HTML parsing
        # For now, return empty list
        # In a real implementation, you'd use BeautifulSoup to parse the HTML
        
        return keys
    
    def get_public_key(self, key_id: str, server: str = None) -> str:
        """Retrieve full public key"""
        if not server:
            server = self.key_servers[0]  # Use first server as default
        
        try:
            self.rate_limiter.wait_if_needed()
            
            url = f"{server}/pks/lookup"
            params = {
                'op': 'get',
                'search': f"0x{key_id.replace('0x', '')}"
            }
            
            response = safe_request(url, session=self.session, params=params)
            
            if response and response.status_code == 200:
                return response.text
        
        except Exception as e:
            print(f"Error retrieving public key {key_id}: {e}")
        
        return ""
    
    def analyze_key_strength(self, key: PGPKey) -> Dict[str, Any]:
        """Analyze PGP key strength and security"""
        analysis = {
            'key_id': key.key_id,
            'strength': 'unknown',
            'algorithm_secure': False,
            'key_size_adequate': False,
            'expired': False,
            'recommendations': []
        }
        
        # Check algorithm
        if key.algorithm:
            if key.algorithm.upper() in ['RSA', 'DSA', 'ECDSA', 'EDDSA']:
                analysis['algorithm_secure'] = True
            else:
                analysis['recommendations'].append('Consider using RSA, ECDSA, or EdDSA algorithm')
        
        # Check key size
        if key.key_size:
            if key.algorithm.upper() == 'RSA' and key.key_size >= 2048:
                analysis['key_size_adequate'] = True
            elif key.algorithm.upper() in ['ECDSA', 'EDDSA'] and key.key_size >= 256:
                analysis['key_size_adequate'] = True
            else:
                analysis['recommendations'].append('Increase key size for better security')
        
        # Check expiration
        if key.expiration_date:
            try:
                exp_date = datetime.fromisoformat(key.expiration_date)
                if exp_date < datetime.now():
                    analysis['expired'] = True
                    analysis['recommendations'].append('Key has expired')
            except:
                pass
        
        # Overall strength assessment
        if analysis['algorithm_secure'] and analysis['key_size_adequate'] and not analysis['expired']:
            analysis['strength'] = 'strong'
        elif analysis['algorithm_secure'] and analysis['key_size_adequate']:
            analysis['strength'] = 'good'
        elif analysis['algorithm_secure']:
            analysis['strength'] = 'fair'
        else:
            analysis['strength'] = 'weak'
        
        return analysis
    
    def _deduplicate_keys(self, keys: List[PGPKey]) -> List[PGPKey]:
        """Remove duplicate keys based on key ID"""
        seen_keys = set()
        unique_keys = []
        
        for key in keys:
            if key.key_id not in seen_keys:
                seen_keys.add(key.key_id)
                unique_keys.append(key)
        
        return unique_keys
    
    def _validate_email(self, email: str) -> bool:
        """Validate email format"""
        return bool(self.email_pattern.match(email))
    
    def export_results(self, keys: List[PGPKey], format_type: str = 'json') -> str:
        """Export PGP search results"""
        if format_type == 'json':
            import json
            return json.dumps([{
                'key_id': k.key_id,
                'user_ids': k.user_ids,
                'fingerprint': k.fingerprint,
                'algorithm': k.algorithm,
                'key_size': k.key_size,
                'creation_date': k.creation_date,
                'expiration_date': k.expiration_date,
                'key_server': k.key_server
            } for k in keys], indent=2)
        
        elif format_type == 'csv':
            import csv
            import io
            
            output = io.StringIO()
            writer = csv.writer(output)
            
            # Header
            writer.writerow(['Key ID', 'User IDs', 'Algorithm', 'Key Size', 'Creation Date', 'Key Server'])
            
            # Data
            for k in keys:
                writer.writerow([
                    k.key_id, '; '.join(k.user_ids), k.algorithm,
                    k.key_size, k.creation_date, k.key_server
                ])
            
            return output.getvalue()
        
        return ""