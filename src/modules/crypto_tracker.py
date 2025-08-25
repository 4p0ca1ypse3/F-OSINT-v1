"""
Cryptocurrency address tracker module for F-OSINT DWv1
"""

import re
import requests
from typing import List, Dict, Any, Optional
from dataclasses import dataclass
from datetime import datetime

from utils.networking import safe_request, RateLimiter


@dataclass
class CryptoTransaction:
    """Cryptocurrency transaction"""
    tx_hash: str
    amount: float
    from_address: str = ""
    to_address: str = ""
    timestamp: str = ""
    block_height: int = 0
    confirmations: int = 0


@dataclass
class CryptoAddress:
    """Cryptocurrency address information"""
    address: str
    currency: str
    balance: float = 0.0
    total_received: float = 0.0
    total_sent: float = 0.0
    transaction_count: int = 0
    first_seen: str = ""
    last_seen: str = ""
    transactions: List[CryptoTransaction] = None
    
    def __post_init__(self):
        if self.transactions is None:
            self.transactions = []


class CryptoTracker:
    """Cryptocurrency address tracker"""
    
    def __init__(self):
        self.rate_limiter = RateLimiter(max_requests_per_minute=30)
        self.session = requests.Session()
        
        # Address validation patterns
        self.address_patterns = {
            'bitcoin': {
                'legacy': re.compile(r'^[13][a-km-zA-HJ-NP-Z1-9]{25,34}$'),
                'segwit': re.compile(r'^bc1[a-z0-9]{39,59}$'),
                'segwit_nested': re.compile(r'^3[a-km-zA-HJ-NP-Z1-9]{25,34}$')
            },
            'ethereum': {
                'standard': re.compile(r'^0x[a-fA-F0-9]{40}$')
            },
            'litecoin': {
                'legacy': re.compile(r'^[LM3][a-km-zA-HJ-NP-Z1-9]{26,33}$'),
                'segwit': re.compile(r'^ltc1[a-z0-9]{39,59}$')
            },
            'monero': {
                'standard': re.compile(r'^4[0-9AB][1-9A-HJ-NP-Za-km-z]{93}$')
            }
        }
        
        # API endpoints (would need API keys in production)
        self.api_endpoints = {
            'bitcoin': 'https://blockstream.info/api',
            'ethereum': 'https://api.etherscan.io/api',
            'litecoin': 'https://api.blockcypher.com/v1/ltc/main'
        }
    
    def identify_currency(self, address: str) -> str:
        """Identify cryptocurrency type from address"""
        for currency, patterns in self.address_patterns.items():
            for pattern_name, pattern in patterns.items():
                if pattern.match(address):
                    return currency
        return 'unknown'
    
    def validate_address(self, address: str, currency: str = None) -> bool:
        """Validate cryptocurrency address"""
        if currency:
            if currency in self.address_patterns:
                patterns = self.address_patterns[currency]
                return any(pattern.match(address) for pattern in patterns.values())
        else:
            # Try to identify currency and validate
            identified_currency = self.identify_currency(address)
            return identified_currency != 'unknown'
        
        return False
    
    def track_bitcoin_address(self, address: str) -> CryptoAddress:
        """Track Bitcoin address"""
        crypto_addr = CryptoAddress(address=address, currency='bitcoin')
        
        if not self.validate_address(address, 'bitcoin'):
            return crypto_addr
        
        try:
            # Rate limiting
            self.rate_limiter.wait_if_needed()
            
            # Get address info from Blockstream API
            url = f"{self.api_endpoints['bitcoin']}/address/{address}"
            response = safe_request(url, session=self.session)
            
            if response and response.status_code == 200:
                data = response.json()
                
                crypto_addr.balance = data.get('chain_stats', {}).get('funded_txo_sum', 0) / 100000000  # Convert satoshis to BTC
                crypto_addr.total_received = data.get('chain_stats', {}).get('funded_txo_sum', 0) / 100000000
                crypto_addr.total_sent = data.get('chain_stats', {}).get('spent_txo_sum', 0) / 100000000
                crypto_addr.transaction_count = data.get('chain_stats', {}).get('tx_count', 0)
            
            # Get transactions
            self.rate_limiter.wait_if_needed()
            tx_url = f"{self.api_endpoints['bitcoin']}/address/{address}/txs"
            tx_response = safe_request(tx_url, session=self.session)
            
            if tx_response and tx_response.status_code == 200:
                tx_data = tx_response.json()
                
                for tx in tx_data[:10]:  # Limit to 10 most recent transactions
                    transaction = CryptoTransaction(
                        tx_hash=tx.get('txid', ''),
                        amount=0,  # Would need to calculate from inputs/outputs
                        timestamp=datetime.fromtimestamp(tx.get('status', {}).get('block_time', 0)).isoformat(),
                        block_height=tx.get('status', {}).get('block_height', 0),
                        confirmations=tx.get('status', {}).get('confirmed', False)
                    )
                    crypto_addr.transactions.append(transaction)
        
        except Exception as e:
            print(f"Error tracking Bitcoin address {address}: {e}")
        
        return crypto_addr
    
    def track_ethereum_address(self, address: str, api_key: str = None) -> CryptoAddress:
        """Track Ethereum address"""
        crypto_addr = CryptoAddress(address=address, currency='ethereum')
        
        if not self.validate_address(address, 'ethereum'):
            return crypto_addr
        
        try:
            # Rate limiting
            self.rate_limiter.wait_if_needed()
            
            # Get balance from Etherscan API
            params = {
                'module': 'account',
                'action': 'balance',
                'address': address,
                'tag': 'latest'
            }
            
            if api_key:
                params['apikey'] = api_key
            
            response = safe_request(self.api_endpoints['ethereum'], session=self.session, params=params)
            
            if response and response.status_code == 200:
                data = response.json()
                if data.get('status') == '1':
                    balance_wei = int(data.get('result', '0'))
                    crypto_addr.balance = balance_wei / 1e18  # Convert wei to ETH
            
            # Get transaction count
            self.rate_limiter.wait_if_needed()
            tx_params = {
                'module': 'proxy',
                'action': 'eth_getTransactionCount',
                'address': address,
                'tag': 'latest'
            }
            
            if api_key:
                tx_params['apikey'] = api_key
            
            tx_response = safe_request(self.api_endpoints['ethereum'], session=self.session, params=tx_params)
            
            if tx_response and tx_response.status_code == 200:
                tx_data = tx_response.json()
                if tx_data.get('result'):
                    crypto_addr.transaction_count = int(tx_data['result'], 16)
        
        except Exception as e:
            print(f"Error tracking Ethereum address {address}: {e}")
        
        return crypto_addr
    
    def track_multiple_addresses(self, addresses: List[str]) -> List[CryptoAddress]:
        """Track multiple cryptocurrency addresses"""
        results = []
        
        for address in addresses:
            currency = self.identify_currency(address)
            
            if currency == 'bitcoin':
                result = self.track_bitcoin_address(address)
            elif currency == 'ethereum':
                result = self.track_ethereum_address(address)
            else:
                result = CryptoAddress(address=address, currency=currency)
            
            results.append(result)
        
        return results
    
    def analyze_address_activity(self, crypto_addr: CryptoAddress) -> Dict[str, Any]:
        """Analyze cryptocurrency address activity"""
        analysis = {
            'address': crypto_addr.address,
            'currency': crypto_addr.currency,
            'activity_level': 'inactive',
            'risk_indicators': [],
            'notable_patterns': [],
            'privacy_score': 0,
            'recommendations': []
        }
        
        # Analyze transaction count
        if crypto_addr.transaction_count > 1000:
            analysis['activity_level'] = 'very_high'
        elif crypto_addr.transaction_count > 100:
            analysis['activity_level'] = 'high'
        elif crypto_addr.transaction_count > 10:
            analysis['activity_level'] = 'moderate'
        elif crypto_addr.transaction_count > 0:
            analysis['activity_level'] = 'low'
        
        # Analyze balance vs transaction volume
        if crypto_addr.total_received > 0:
            turnover_ratio = crypto_addr.total_sent / crypto_addr.total_received
            if turnover_ratio > 0.9:
                analysis['notable_patterns'].append('High transaction turnover')
            
            balance_ratio = crypto_addr.balance / crypto_addr.total_received
            if balance_ratio < 0.1:
                analysis['notable_patterns'].append('Low balance retention')
        
        # Risk indicators
        if crypto_addr.balance > 100:  # Large balance
            analysis['risk_indicators'].append('Large balance (potential high-value target)')
        
        if crypto_addr.transaction_count > 500:
            analysis['risk_indicators'].append('High transaction volume (potential commercial use)')
        
        # Privacy score (simplified)
        privacy_score = 50  # Base score
        
        if crypto_addr.transaction_count > 50:
            privacy_score -= 20  # Many transactions reduce privacy
        
        if len(analysis['risk_indicators']) > 0:
            privacy_score -= 15  # Risk indicators reduce privacy
        
        analysis['privacy_score'] = max(0, min(100, privacy_score))
        
        # Recommendations
        if crypto_addr.balance > 10:
            analysis['recommendations'].append('Consider using multiple addresses for better privacy')
        
        if crypto_addr.transaction_count > 100:
            analysis['recommendations'].append('High activity may compromise privacy')
        
        return analysis
    
    def search_related_addresses(self, address: str) -> List[str]:
        """Search for addresses related to the given address"""
        related = []
        
        # This would implement clustering algorithms to find related addresses
        # For now, return empty list as this requires complex analysis
        
        return related
    
    def get_address_tags(self, address: str) -> List[Dict[str, str]]:
        """Get known tags/labels for an address"""
        tags = []
        
        # This would query databases of known address tags
        # For now, return empty list
        
        return tags
    
    def monitor_address(self, address: str) -> bool:
        """Add address to monitoring list"""
        # This would add the address to a monitoring system
        # For now, just validate the address
        return self.validate_address(address)
    
    def export_results(self, addresses: List[CryptoAddress], format_type: str = 'json') -> str:
        """Export cryptocurrency tracking results"""
        if format_type == 'json':
            import json
            return json.dumps([{
                'address': addr.address,
                'currency': addr.currency,
                'balance': addr.balance,
                'total_received': addr.total_received,
                'total_sent': addr.total_sent,
                'transaction_count': addr.transaction_count,
                'first_seen': addr.first_seen,
                'last_seen': addr.last_seen
            } for addr in addresses], indent=2)
        
        elif format_type == 'csv':
            import csv
            import io
            
            output = io.StringIO()
            writer = csv.writer(output)
            
            # Header
            writer.writerow(['Address', 'Currency', 'Balance', 'Total Received', 'Total Sent', 'TX Count'])
            
            # Data
            for addr in addresses:
                writer.writerow([
                    addr.address, addr.currency, addr.balance,
                    addr.total_received, addr.total_sent, addr.transaction_count
                ])
            
            return output.getvalue()
        
        return ""