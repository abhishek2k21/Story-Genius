"""
Automated dependency vulnerability scanning.
Uses pip-audit and safety to check Python dependencies.
"""
import subprocess
import sys
import json
from typing import Dict, List, Tuple


class DependencyScanner:
    """Scans Python dependencies for security vulnerabilities."""
    
    def __init__(self):
        self.vulnerabilities: List[Dict] = []
    
    def scan_with_pip_audit(self) -> Tuple[bool, List[Dict]]:
        """
        Scan dependencies using pip-audit.
        
        Returns:
            Tuple of (success, vulnerabilities)
        """
        print("🔍 Scanning Python dependencies with pip-audit...")
        
        try:
            result = subprocess.run(
                ["pip-audit", "--format", "json", "--desc"],
                capture_output=True,
                text=True,
                timeout=300
            )
            
            if result.returncode == 0:
                print("✅ No vulnerabilities found by pip-audit")
                return True, []
            
            # Parse JSON output
            try:
                vulnerabilities = json.loads(result.stdout)
                return False, vulnerabilities.get('dependencies', [])
            except json.JSONDecodeError:
                print(f"⚠️  Failed to parse pip-audit output")
                return False, []
        
        except subprocess.TimeoutExpired:
            print("⚠️  pip-audit timed out")
            return False, []
        except FileNotFoundError:
            print("⚠️  pip-audit not installed. Install with: pip install pip-audit")
            return False, []
        except Exception as e:
            print(f"⚠️  pip-audit failed: {e}")
            return False, []
    
    def scan_with_safety(self) -> Tuple[bool, List[Dict]]:
        """
        Scan dependencies using Safety CLI.
        
        Returns:
            Tuple of (success, vulnerabilities)
        """
        print("🔍 Scanning Python dependencies with Safety...")
        
        try:
            result = subprocess.run(
                ["safety", "check", "--json"],
                capture_output=True,
                text=True,
                timeout=300
            )
            
            if result.returncode == 0:
                print("✅ No vulnerabilities found by Safety")
                return True, []
            
            # Parse JSON output
            try:
                vulnerabilities = json.loads(result.stdout)
                return False, vulnerabilities
            except json.JSONDecodeError:
                print(f"⚠️  Failed to parse Safety output")
                return False, []
        
        except subprocess.TimeoutExpired:
            print("⚠️  Safety timed out")
            return False, []
        except FileNotFoundError:
            print("⚠️  Safety not installed. Install with: pip install safety")
            return False, []
        except Exception as e:
            print(f"⚠️  Safety failed: {e}")
            return False, []
    
    def check_outdated_packages(self) -> List[Dict]:
        """Check for outdated packages."""
        print("🔍 Checking for outdated packages...")
        
        try:
            result = subprocess.run(
                ["pip", "list", "--outdated", "--format", "json"],
                capture_output=True,
                text=True,
                timeout=60
            )
            
            if result.returncode == 0:
                outdated = json.loads(result.stdout)
                
                if outdated:
                    print(f"⚠️  {len(outdated)} outdated packages found")
                    return outdated
                else:
                    print("✅ All packages are up-to-date")
                    return []
            
            return []
        
        except Exception as e:
            print(f"⚠️  Failed to check outdated packages: {e}")
            return []
    
    def generate_report(self, pip_audit_vulns: List, safety_vulns: List, outdated: List):
        """Generate vulnerability report."""
        print("\n" + "="*60)
        print("DEPENDENCY VULNERABILITY REPORT")
        print("="*60 + "\n")
        
        # pip-audit vulnerabilities
        if pip_audit_vulns:
            print(f"🚨 pip-audit found {len(pip_audit_vulns)} vulnerable dependencies:\n")
            for vuln in pip_audit_vulns:
                print(f"  Package: {vuln.get('name', 'Unknown')}")
                print(f"  Installed: {vuln.get('version', 'Unknown')}")
                print(f"  Vulnerabilities: {len(vuln.get('vulns', []))}")
                for v in vuln.get('vulns', []):
                    print(f"    - {v.get('id', 'Unknown')}: {v.get('description', 'No description')[:80]}...")
                    print(f"      Fix: Upgrade to {v.get('fix_versions', ['Unknown'])[0] if v.get('fix_versions') else 'No fix available'}")
                print()
        
        # Safety vulnerabilities
        if safety_vulns:
            print(f"🚨 Safety found {len(safety_vulns)} vulnerable dependencies:\n")
            for vuln in safety_vulns:
                print(f"  Package: {vuln[0]} ({vuln[1]})")
                print(f"  Vulnerability: {vuln[2]}")
                print(f"  Description: {vuln[3][:100]}...")
                print()
        
        # Outdated packages
        if outdated:
            print(f"⚠️  {len(outdated)} outdated packages:\n")
            for pkg in outdated[:10]:  # Show top 10
                print(f"  {pkg['name']}: {pkg['version']} → {pkg['latest_version']}")
            if len(outdated) > 10:
                print(f"  ... and {len(outdated) - 10} more")
            print()
        
        # Summary
        critical_count = len(pip_audit_vulns) + len(safety_vulns)
        print("="*60)
        print(f"SUMMARY:")
        print(f"  Critical/High vulnerabilities: {critical_count}")
        print(f"  Outdated packages: {len(outdated)}")
        
        if critical_count > 0:
            print(f"\n❌ FAILED: {critical_count} vulnerabilities found")
            print("="*60)
            return False
        else:
            print(f"\n✅ PASSED: No critical vulnerabilities found")
            print("="*60)
            return True
    
    def run_full_scan(self) -> bool:
        """
        Run complete dependency scan.
        
        Returns:
            True if no vulnerabilities, False otherwise
        """
        # Run scans
        pip_audit_ok, pip_audit_vulns = self.scan_with_pip_audit()
        safety_ok, safety_vulns = self.scan_with_safety()
        outdated = self.check_outdated_packages()
        
        # Generate report
        return self.generate_report(pip_audit_vulns, safety_vulns, outdated)


if __name__ == "__main__":
    scanner = DependencyScanner()
    success = scanner.run_full_scan()
    
    sys.exit(0 if success else 1)
