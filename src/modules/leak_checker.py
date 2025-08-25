"""
Leak checker module for F-OSINT DWv1
"""

import re
import hashlib
from typing import List, Dict, Any, Optional
from dataclasses import dataclass
from datetime import datetime

import requests
from utils.networking import safe_request, RateLimiter


@dataclass
class LeakResult:
    """Leak check result"""
    email: str
    breaches: List[Dict[str, Any]] = None
    pastes: List[Dict[str, Any]] = None
    checked_at: str = ""
    
    def __post_init__(self):
        if self.breaches is None:
            self.breaches = []
        if self.pastes is None:
            self.pastes = []
        if not self.checked_at:
            self.checked_at = datetime.now().isoformat()


class LeakChecker:
    """Email/Username/Phone leak checker"""
    
    def __init__(self):
        self.rate_limiter = RateLimiter(max_requests_per_minute=10)
        self.session = requests.Session()
        
        # Email validation regex
        self.email_pattern = re.compile(r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$')
        
        # Phone validation regex (simple international format)
        self.phone_pattern = re.compile(r'^\+?[\d\s\-\(\)]{7,15}$')
    
    def check_email_hibp(self, email: str, api_key: str = None) -> LeakResult:
        """Check email against Have I Been Pwned database"""
        result = LeakResult(email=email)
        
        if not self._validate_email(email):
            return result
        
        try:
            # Rate limiting
            self.rate_limiter.wait_if_needed()
            
            # Check breaches
            breaches_url = f"https://haveibeenpwned.com/api/v3/breachedaccount/{email}"
            headers = {
                'User-Agent': 'F-OSINT-DWv1',
                'hibp-api-key': api_key
            } if api_key else {'User-Agent': 'F-OSINT-DWv1'}
            
            response = safe_request(breaches_url, session=self.session, headers=headers)
            
            if response and response.status_code == 200:
                result.breaches = response.json()
            elif response and response.status_code == 404:
                result.breaches = []  # No breaches found
            
            # Check pastes (if API key available)
            if api_key:
                self.rate_limiter.wait_if_needed()
                pastes_url = f"https://haveibeenpwned.com/api/v3/pasteaccount/{email}"
                response = safe_request(pastes_url, session=self.session, headers=headers)
                
                if response and response.status_code == 200:
                    result.pastes = response.json()
                elif response and response.status_code == 404:
                    result.pastes = []  # No pastes found
            
        except Exception as e:
            print(f"Error checking HIBP for {email}: {e}")
        
        return result
    
    def check_email_local_database(self, email: str) -> LeakResult:
        """Check email against local breach database (placeholder)"""
        result = LeakResult(email=email)
        
        # This would interface with a local database of breaches
        # For now, return empty result
        return result
    
    def check_username_breaches(self, username: str) -> List[Dict[str, Any]]:
        """Check username against various breach databases"""
        results = []
        
        # Common domains to check username against
        common_domains = [
            'gmail.com', 'yahoo.com', 'hotmail.com', 'outlook.com',
            'protonmail.com', 'tutanota.com'
        ]
        
        for domain in common_domains:
            email = f"{username}@{domain}"
            if self._validate_email(email):
                result = self.check_email_hibp(email)
                if result.breaches:
                    results.append({
                        'email': email,
                        'username': username,
                        'domain': domain,
                        'breaches': result.breaches
                    })
        
        return results
    
    def check_phone_number(self, phone: str) -> Dict[str, Any]:
        """Check phone number for leaks (placeholder implementation)"""
        if not self._validate_phone(phone):
            return {'valid': False, 'message': 'Invalid phone number format'}
        
        # Normalize phone number
        normalized = re.sub(r'[^\d+]', '', phone)
        
        result = {
            'phone': phone,
            'normalized': normalized,
            'valid': True,
            'breaches': [],
            'social_media': [],
            'message': 'Phone number validation successful'
        }
        
        # This would check against phone number breach databases
        # Implementation would depend on available APIs/databases
        
        return result
    
    def bulk_check_emails(self, emails: List[str], api_key: str = None) -> List[LeakResult]:
        """Check multiple emails for breaches"""
        results = []
        
        for email in emails:
            if self._validate_email(email):
                result = self.check_email_hibp(email, api_key)
                results.append(result)
            else:
                results.append(LeakResult(email=email))
        
        return results
    
    def generate_email_variations(self, username: str, domains: List[str] = None) -> List[str]:
        """Generate possible email variations for a username"""
        if not domains:
            domains = [
                'gmail.com', 'yahoo.com', 'hotmail.com', 'outlook.com',
                'protonmail.com', 'tutanota.com', 'mail.com'
            ]
        
        variations = []
        
        # Basic variations
        for domain in domains:
            variations.append(f"{username}@{domain}")
        
        # Common number suffixes
        for i in range(10):
            for domain in domains[:3]:  # Limit to top 3 domains
                variations.append(f"{username}{i}@{domain}")
        
        # Dot variations
        if len(username) > 3:
            for domain in domains[:3]:
                variations.append(f"{username[:2]}.{username[2:]}@{domain}")
        
        return variations
    
    def search_breach_details(self, breach_name: str) -> Dict[str, Any]:
        """Get details about a specific breach"""
        try:
            url = f"https://haveibeenpwned.com/api/v3/breach/{breach_name}"
            response = safe_request(url, session=self.session)
            
            if response and response.status_code == 200:
                return response.json()
        except Exception as e:
            print(f"Error getting breach details for {breach_name}: {e}")
        
        return {}
    
    def analyze_breach_severity(self, breaches: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Analyze severity of breaches"""
        if not breaches:
            return {'severity': 'none', 'risk_score': 0}
        
        total_breaches = len(breaches)
        total_accounts = sum(breach.get('PwnCount', 0) for breach in breaches)
        
        # Check for sensitive data types
        sensitive_types = ['Passwords', 'Social security numbers', 'Credit cards', 'Phone numbers']
        sensitive_breaches = 0
        
        for breach in breaches:
            data_classes = breach.get('DataClasses', [])
            if any(sensitive in data_classes for sensitive in sensitive_types):
                sensitive_breaches += 1
        
        # Calculate risk score (0-100)
        risk_score = min(100, (total_breaches * 10) + (sensitive_breaches * 20))
        
        if risk_score >= 80:
            severity = 'critical'
        elif risk_score >= 60:
            severity = 'high'
        elif risk_score >= 40:
            severity = 'medium'
        elif risk_score >= 20:
            severity = 'low'
        else:
            severity = 'minimal'
        
        return {
            'severity': severity,
            'risk_score': risk_score,
            'total_breaches': total_breaches,
            'total_accounts_affected': total_accounts,
            'sensitive_breaches': sensitive_breaches
        }
    
    def _validate_email(self, email: str) -> bool:
        """Validate email format"""
        return bool(self.email_pattern.match(email))
    
    def _validate_phone(self, phone: str) -> bool:
        """Validate phone number format"""
        return bool(self.phone_pattern.match(phone))
    
    def export_results(self, results: List[LeakResult], format_type: str = 'json') -> str:
        """Export leak check results"""
        if format_type == 'json':
            import json
            return json.dumps([{
                'email': r.email,
                'breaches_count': len(r.breaches),
                'pastes_count': len(r.pastes),
                'breaches': r.breaches,
                'checked_at': r.checked_at
            } for r in results], indent=2)
        
        elif format_type == 'csv':
            import csv
            import io
            
            output = io.StringIO()
            writer = csv.writer(output)
            
            # Header
            writer.writerow(['Email', 'Breaches Count', 'Pastes Count', 'Risk Level', 'Checked At'])
            
            # Data
            for r in results:
                analysis = self.analyze_breach_severity(r.breaches)
                writer.writerow([
                    r.email, len(r.breaches), len(r.pastes),
                    analysis['severity'], r.checked_at
                ])
            
            return output.getvalue()
        
        return ""