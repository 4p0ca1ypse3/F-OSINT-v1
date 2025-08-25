"""
Keyword alerts module for F-OSINT DWv1
"""

import time
import threading
from typing import List, Dict, Any, Callable, Optional
from dataclasses import dataclass
from datetime import datetime, timedelta
from queue import Queue

from modules.google_dorking import GoogleDorking
from modules.darkweb_scanner import DarkWebScanner
from utils.networking import RateLimiter


@dataclass
class Alert:
    """Keyword alert"""
    alert_id: str
    keyword: str
    source: str
    content: str
    url: str
    timestamp: str
    severity: str = "low"
    confidence: float = 0.0
    
    def __post_init__(self):
        if not self.timestamp:
            self.timestamp = datetime.now().isoformat()


@dataclass
class MonitoringRule:
    """Monitoring rule for keyword alerts"""
    rule_id: str
    keywords: List[str]
    sources: List[str]
    frequency: int  # in minutes
    enabled: bool = True
    last_run: str = ""
    filters: Dict[str, Any] = None
    
    def __post_init__(self):
        if self.filters is None:
            self.filters = {}
        if not self.last_run:
            self.last_run = datetime.now().isoformat()


class KeywordAlerts:
    """Real-time keyword monitoring and alerting system"""
    
    def __init__(self):
        self.monitoring_rules: Dict[str, MonitoringRule] = {}
        self.alerts_queue = Queue()
        self.is_monitoring = False
        self.monitor_thread = None
        
        # Initialize OSINT modules
        self.google_dorking = GoogleDorking()
        self.darkweb_scanner = DarkWebScanner()
        
        # Rate limiters for different sources
        self.rate_limiters = {
            'google': RateLimiter(max_requests_per_minute=10),
            'darkweb': RateLimiter(max_requests_per_minute=5)
        }
        
        # Alert callbacks
        self.alert_callbacks: List[Callable[[Alert], None]] = []
        
        # Severity keywords
        self.severity_keywords = {
            'critical': ['hack', 'breach', 'leak', 'dump', 'stolen', 'password', 'database'],
            'high': ['vulnerability', 'exploit', 'attack', 'malware', 'threat'],
            'medium': ['security', 'risk', 'warning', 'suspicious'],
            'low': ['mention', 'reference', 'discussion']
        }
    
    def add_monitoring_rule(self, rule: MonitoringRule) -> bool:
        """Add a new monitoring rule"""
        try:
            self.monitoring_rules[rule.rule_id] = rule
            return True
        except Exception as e:
            print(f"Error adding monitoring rule: {e}")
            return False
    
    def remove_monitoring_rule(self, rule_id: str) -> bool:
        """Remove a monitoring rule"""
        try:
            if rule_id in self.monitoring_rules:
                del self.monitoring_rules[rule_id]
                return True
            return False
        except Exception as e:
            print(f"Error removing monitoring rule: {e}")
            return False
    
    def update_monitoring_rule(self, rule_id: str, updates: Dict[str, Any]) -> bool:
        """Update a monitoring rule"""
        try:
            if rule_id in self.monitoring_rules:
                rule = self.monitoring_rules[rule_id]
                for key, value in updates.items():
                    if hasattr(rule, key):
                        setattr(rule, key, value)
                return True
            return False
        except Exception as e:
            print(f"Error updating monitoring rule: {e}")
            return False
    
    def start_monitoring(self) -> bool:
        """Start real-time monitoring"""
        if self.is_monitoring:
            return False
        
        self.is_monitoring = True
        self.monitor_thread = threading.Thread(target=self._monitoring_loop, daemon=True)
        self.monitor_thread.start()
        return True
    
    def stop_monitoring(self):
        """Stop real-time monitoring"""
        self.is_monitoring = False
        if self.monitor_thread:
            self.monitor_thread.join(timeout=5)
    
    def _monitoring_loop(self):
        """Main monitoring loop"""
        while self.is_monitoring:
            try:
                current_time = datetime.now()
                
                for rule_id, rule in self.monitoring_rules.items():
                    if not rule.enabled:
                        continue
                    
                    # Check if it's time to run this rule
                    last_run = datetime.fromisoformat(rule.last_run)
                    if (current_time - last_run).total_seconds() >= rule.frequency * 60:
                        self._execute_monitoring_rule(rule)
                        rule.last_run = current_time.isoformat()
                
                # Sleep for a short interval
                time.sleep(30)
                
            except Exception as e:
                print(f"Error in monitoring loop: {e}")
                time.sleep(60)  # Sleep longer on error
    
    def _execute_monitoring_rule(self, rule: MonitoringRule):
        """Execute a single monitoring rule"""
        try:
            for keyword in rule.keywords:
                for source in rule.sources:
                    alerts = self._search_source(keyword, source, rule.filters)
                    
                    for alert in alerts:
                        # Check if this is a new alert
                        if self._is_new_alert(alert):
                            # Analyze and score the alert
                            alert = self._analyze_alert(alert)
                            
                            # Add to queue and trigger callbacks
                            self.alerts_queue.put(alert)
                            self._trigger_alert_callbacks(alert)
                    
                    # Rate limiting between searches
                    time.sleep(2)
        
        except Exception as e:
            print(f"Error executing monitoring rule {rule.rule_id}: {e}")
    
    def _search_source(self, keyword: str, source: str, filters: Dict[str, Any]) -> List[Alert]:
        """Search a specific source for keyword"""
        alerts = []
        
        try:
            if source == 'google':
                alerts = self._search_google(keyword, filters)
            elif source == 'darkweb':
                alerts = self._search_darkweb(keyword, filters)
            elif source == 'social_media':
                alerts = self._search_social_media(keyword, filters)
            elif source == 'paste_sites':
                alerts = self._search_paste_sites(keyword, filters)
        
        except Exception as e:
            print(f"Error searching {source} for {keyword}: {e}")
        
        return alerts
    
    def _search_google(self, keyword: str, filters: Dict[str, Any]) -> List[Alert]:
        """Search Google for keyword mentions"""
        alerts = []
        
        try:
            # Rate limiting
            self.rate_limiters['google'].wait_if_needed()
            
            # Build search query
            query = keyword
            if 'date_range' in filters:
                query += f" after:{filters['date_range']}"
            if 'site' in filters:
                query += f" site:{filters['site']}"
            
            # Search
            results = self.google_dorking.search(query, num_results=10)
            
            for result in results:
                alert = Alert(
                    alert_id=f"google_{hash(result.url)}_{int(time.time())}",
                    keyword=keyword,
                    source='google',
                    content=result.snippet,
                    url=result.url
                )
                alerts.append(alert)
        
        except Exception as e:
            print(f"Error searching Google for {keyword}: {e}")
        
        return alerts
    
    def _search_darkweb(self, keyword: str, filters: Dict[str, Any]) -> List[Alert]:
        """Search dark web for keyword mentions"""
        alerts = []
        
        try:
            # Rate limiting
            self.rate_limiters['darkweb'].wait_if_needed()
            
            # This would implement dark web search
            # For now, return empty list as it requires Tor setup
            pass
        
        except Exception as e:
            print(f"Error searching dark web for {keyword}: {e}")
        
        return alerts
    
    def _search_social_media(self, keyword: str, filters: Dict[str, Any]) -> List[Alert]:
        """Search social media for keyword mentions"""
        alerts = []
        
        try:
            # Search Twitter, Facebook, etc. using Google dorking
            platforms = ['twitter.com', 'facebook.com', 'linkedin.com', 'instagram.com']
            
            for platform in platforms:
                results = self.google_dorking.search_social_media(keyword, platform.split('.')[0], 5)
                
                for result in results:
                    alert = Alert(
                        alert_id=f"social_{platform}_{hash(result.url)}_{int(time.time())}",
                        keyword=keyword,
                        source=f'social_media_{platform}',
                        content=result.snippet,
                        url=result.url
                    )
                    alerts.append(alert)
        
        except Exception as e:
            print(f"Error searching social media for {keyword}: {e}")
        
        return alerts
    
    def _search_paste_sites(self, keyword: str, filters: Dict[str, Any]) -> List[Alert]:
        """Search paste sites for keyword mentions"""
        alerts = []
        
        try:
            # Search paste sites using Google dorking
            paste_sites = ['pastebin.com', 'paste.org', 'hastebin.com']
            
            for site in paste_sites:
                results = self.google_dorking.search(f'site:{site} "{keyword}"', 5)
                
                for result in results:
                    alert = Alert(
                        alert_id=f"paste_{site}_{hash(result.url)}_{int(time.time())}",
                        keyword=keyword,
                        source=f'paste_{site}',
                        content=result.snippet,
                        url=result.url
                    )
                    alerts.append(alert)
        
        except Exception as e:
            print(f"Error searching paste sites for {keyword}: {e}")
        
        return alerts
    
    def _analyze_alert(self, alert: Alert) -> Alert:
        """Analyze alert content and assign severity/confidence"""
        content_lower = alert.content.lower()
        keyword_lower = alert.keyword.lower()
        
        # Calculate confidence based on keyword prominence
        confidence = 0.5  # Base confidence
        
        if keyword_lower in content_lower:
            confidence += 0.3
        
        # Check for exact matches
        if alert.keyword in alert.content:
            confidence += 0.2
        
        # Determine severity based on content
        severity = 'low'  # Default
        
        for sev_level, keywords in self.severity_keywords.items():
            for sev_keyword in keywords:
                if sev_keyword in content_lower:
                    if sev_level == 'critical':
                        severity = 'critical'
                        confidence += 0.2
                        break
                    elif sev_level == 'high' and severity in ['low', 'medium']:
                        severity = 'high'
                        confidence += 0.15
                    elif sev_level == 'medium' and severity == 'low':
                        severity = 'medium'
                        confidence += 0.1
            
            if severity == 'critical':
                break
        
        alert.severity = severity
        alert.confidence = min(1.0, confidence)
        
        return alert
    
    def _is_new_alert(self, alert: Alert) -> bool:
        """Check if this is a new alert (not already processed)"""
        # This would check against a database of processed alerts
        # For now, always return True
        return True
    
    def _trigger_alert_callbacks(self, alert: Alert):
        """Trigger all registered alert callbacks"""
        for callback in self.alert_callbacks:
            try:
                callback(alert)
            except Exception as e:
                print(f"Error in alert callback: {e}")
    
    def add_alert_callback(self, callback: Callable[[Alert], None]):
        """Add an alert callback function"""
        self.alert_callbacks.append(callback)
    
    def remove_alert_callback(self, callback: Callable[[Alert], None]):
        """Remove an alert callback function"""
        if callback in self.alert_callbacks:
            self.alert_callbacks.remove(callback)
    
    def get_recent_alerts(self, hours: int = 24) -> List[Alert]:
        """Get alerts from the last N hours"""
        alerts = []
        cutoff_time = datetime.now() - timedelta(hours=hours)
        
        # Convert queue to list (this empties the queue)
        while not self.alerts_queue.empty():
            alert = self.alerts_queue.get()
            alert_time = datetime.fromisoformat(alert.timestamp)
            if alert_time >= cutoff_time:
                alerts.append(alert)
        
        return sorted(alerts, key=lambda x: x.timestamp, reverse=True)
    
    def get_alerts_by_severity(self, severity: str) -> List[Alert]:
        """Get alerts filtered by severity level"""
        all_alerts = self.get_recent_alerts(24 * 7)  # Last week
        return [alert for alert in all_alerts if alert.severity == severity]
    
    def get_monitoring_statistics(self) -> Dict[str, Any]:
        """Get monitoring statistics"""
        stats = {
            'total_rules': len(self.monitoring_rules),
            'active_rules': sum(1 for rule in self.monitoring_rules.values() if rule.enabled),
            'is_monitoring': self.is_monitoring,
            'alerts_in_queue': self.alerts_queue.qsize(),
            'rules_by_frequency': {}
        }
        
        # Group rules by frequency
        for rule in self.monitoring_rules.values():
            freq = rule.frequency
            if freq not in stats['rules_by_frequency']:
                stats['rules_by_frequency'][freq] = 0
            stats['rules_by_frequency'][freq] += 1
        
        return stats
    
    def create_monitoring_rule_from_template(self, template_name: str, keywords: List[str]) -> MonitoringRule:
        """Create monitoring rule from predefined templates"""
        templates = {
            'security_monitoring': {
                'sources': ['google', 'darkweb', 'paste_sites'],
                'frequency': 60,  # 1 hour
                'filters': {'date_range': '1d'}
            },
            'brand_monitoring': {
                'sources': ['google', 'social_media'],
                'frequency': 30,  # 30 minutes
                'filters': {}
            },
            'threat_intelligence': {
                'sources': ['darkweb', 'paste_sites'],
                'frequency': 120,  # 2 hours
                'filters': {}
            }
        }
        
        if template_name not in templates:
            raise ValueError(f"Unknown template: {template_name}")
        
        template = templates[template_name]
        
        rule = MonitoringRule(
            rule_id=f"{template_name}_{int(time.time())}",
            keywords=keywords,
            sources=template['sources'],
            frequency=template['frequency'],
            filters=template['filters']
        )
        
        return rule
    
    def export_alerts(self, alerts: List[Alert], format_type: str = 'json') -> str:
        """Export alerts in specified format"""
        if format_type == 'json':
            import json
            return json.dumps([{
                'alert_id': alert.alert_id,
                'keyword': alert.keyword,
                'source': alert.source,
                'content': alert.content,
                'url': alert.url,
                'timestamp': alert.timestamp,
                'severity': alert.severity,
                'confidence': alert.confidence
            } for alert in alerts], indent=2)
        
        elif format_type == 'csv':
            import csv
            import io
            
            output = io.StringIO()
            writer = csv.writer(output)
            
            # Header
            writer.writerow(['Alert ID', 'Keyword', 'Source', 'Content', 'URL', 'Timestamp', 'Severity', 'Confidence'])
            
            # Data
            for alert in alerts:
                writer.writerow([
                    alert.alert_id, alert.keyword, alert.source,
                    alert.content[:100] + '...' if len(alert.content) > 100 else alert.content,
                    alert.url, alert.timestamp, alert.severity, alert.confidence
                ])
            
            return output.getvalue()
        
        return ""