"""
Automated security testing with OWASP ZAP.
Performs spider scan and active scan against target API.
"""
from zapv2 import ZAPv2
import time
import sys
import os
from typing import List, Dict
import json


class SecurityTester:
    """OWASP ZAP security testing automation."""
    
    def __init__(self, target_url: str, zap_proxy: str = "http://localhost:8080"):
        """
        Initialize security tester.
        
        Args:
            target_url: Target URL to scan
            zap_proxy: ZAP proxy URL
        """
        self.target = target_url
        self.zap = ZAPv2(proxies={
            'http': zap_proxy,
            'https': zap_proxy
        })
        
        print(f"🔐 Initialized ZAP security tester")
        print(f"  Target: {target_url}")
        print(f"  ZAP Proxy: {zap_proxy}\n")
    
    def spider_scan(self) -> bool:
        """
        Spider scan to discover endpoints.
        
        Returns:
            True if successful
        """
        print(f"🕷️  Starting spider scan on {self.target}...")
        
        try:
            scan_id = self.zap.spider.scan(self.target)
            
            # Wait for spider to complete
            while int(self.zap.spider.status(scan_id)) < 100:
                progress = self.zap.spider.status(scan_id)
                print(f"  Spider progress: {progress}%")
                time.sleep(5)
            
            # Get results
            spider_results = self.zap.spider.results(scan_id)
            print(f"✅ Spider scan complete")
            print(f"  Found {len(spider_results)} URLs\n")
            
            return True
        
        except Exception as e:
            print(f"❌ Spider scan failed: {e}")
            return False
    
    def passive_scan_wait(self):
        """Wait for passive scan to complete."""
        print(f"⏳ Waiting for passive scan to complete...")
        
        while int(self.zap.pscan.records_to_scan) > 0:
            remaining = self.zap.pscan.records_to_scan
            print(f"  Passive scan: {remaining} records remaining")
            time.sleep(5)
        
        print(f"✅ Passive scan complete\n")
    
    def active_scan(self) -> bool:
        """
        Active vulnerability scan.
        
        Returns:
            True if successful
        """
        print(f"🔍 Starting active scan on {self.target}...")
        
        try:
            scan_id = self.zap.ascan.scan(self.target)
            
            # Wait for scan to complete
            while int(self.zap.ascan.status(scan_id)) < 100:
                progress = self.zap.ascan.status(scan_id)
                print(f"  Active scan progress: {progress}%")
                time.sleep(10)
            
            print(f"✅ Active scan complete\n")
            return True
        
        except Exception as e:
            print(f"❌ Active scan failed: {e}")
            return False
    
    def get_alerts(self) -> List[Dict]:
        """
        Get security alerts.
        
        Returns:
            List of alerts
        """
        return self.zap.core.alerts(baseurl=self.target)
    
    def analyze_alerts(self, alerts: List[Dict]) -> Dict:
        """
        Analyze and categorize alerts.
        
        Args:
            alerts: List of ZAP alerts
            
        Returns:
            Dictionary of categorized alerts
        """
        categorized = {
            'Critical': [],
            'High': [],
            'Medium': [],
            'Low': [],
            'Informational': []
        }
        
        for alert in alerts:
            risk = alert.get('risk', 'Informational')
            categorized[risk].append(alert)
        
        return categorized
    
    def generate_report(self, alerts: List[Dict]) -> bool:
        """
        Generate security report.
        
        Args:
            alerts: List of security alerts
            
        Returns:
            True if no high/critical vulnerabilities
        """
        print("\n" + "="*60)
        print("SECURITY SCAN REPORT")
        print("="*60 + "\n")
        
        # Categorize alerts
        categorized = self.analyze_alerts(alerts)
        
        # Print summary
        print(f"Target: {self.target}")
        print(f"Total Alerts: {len(alerts)}\n")
        
        print("Severity Breakdown:")
        for severity in ['Critical', 'High', 'Medium', 'Low', 'Informational']:
            count = len(categorized[severity])
            icon = "🚨" if severity in ['Critical', 'High'] else "⚠️" if severity == 'Medium' else "ℹ️"
            print(f"  {icon} {severity}: {count}")
        
        print()
        
        # Print Critical/High vulnerabilities
        if categorized['Critical'] or categorized['High']:
            print("="*60)
            print("CRITICAL & HIGH SEVERITY VULNERABILITIES")
            print("="*60 + "\n")
            
            for alert in categorized['Critical'] + categorized['High']:
                print(f"🚨 {alert['alert']}")
                print(f"  Risk: {alert['risk']}")
                print(f"  Confidence: {alert['confidence']}")
                print(f"  URL: {alert['url']}")
                print(f"  Description: {alert.get('description', 'N/A')[:150]}...")
                print(f"  Solution: {alert.get('solution', 'N/A')[:150]}...")
                print()
        
        # Generate JSON report
        report_file = "zap-security-report.json"
        with open(report_file, 'w') as f:
            json.dump({
                'target': self.target,
                'total_alerts': len(alerts),
                'severity_breakdown': {k: len(v) for k, v in categorized.items()},
                'alerts': alerts
            }, f, indent=2)
        
        print(f"📄 Full report saved to: {report_file}\n")
        
        # Determine pass/fail
        critical_high_count = len(categorized['Critical']) + len(categorized['High'])
        
        print("="*60)
        if critical_high_count > 0:
            print(f"❌ FAILED: {critical_high_count} critical/high vulnerabilities found")
            print("="*60)
            return False
        else:
            print(f"✅ PASSED: No critical/high vulnerabilities found")
            print("="*60)
            return True
    
    def run_full_scan(self) -> bool:
        """
        Run complete security scan.
        
        Returns:
            True if no critical/high vulnerabilities
        """
        print("="*60)
        print("AUTOMATED SECURITY TESTING")
        print("="*60 + "\n")
        
        # Spider scan
        if not self.spider_scan():
            return False
        
        # Wait for passive scan
        self.passive_scan_wait()
        
        # Active scan
        if not self.active_scan():
            return False
        
        # Get alerts
        alerts = self.get_alerts()
        
        # Generate report
        return self.generate_report(alerts)


if __name__ == "__main__":
    # Get target from environment or use default
    target_url = os.getenv('TARGET_URL', 'https://api.ytvideocreator.com')
    zap_proxy = os.getenv('ZAP_PROXY', 'http://localhost:8080')
    
    # Run security test
    tester = SecurityTester(target_url, zap_proxy)
    success = tester.run_full_scan()
    
    sys.exit(0 if success else 1)
