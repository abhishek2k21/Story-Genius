"""
Failure Injection Test
Tests system resilience with simulated failures.
"""
import sys
from pathlib import Path
from datetime import datetime
from dataclasses import dataclass, asdict
from typing import List, Dict

PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from app.core.logging import get_logger
from app.agency.pilot_controls import get_pilot_controls

logger = get_logger("failure_injection")


@dataclass
class FailureTestResult:
    """Result of a failure injection test."""
    test_name: str
    passed: bool
    alert_triggered: bool
    auto_pause_worked: bool
    graceful_degradation: bool
    notes: str


class FailureInjectionTest:
    """
    Tests system resilience by injecting failures.
    """
    
    def __init__(self):
        self.controls = get_pilot_controls()
        self.results: List[FailureTestResult] = []
    
    def test_rate_limit_exhaustion(self) -> FailureTestResult:
        """Test behavior when rate limits are exhausted."""
        print("\n[TEST] Rate Limit Exhaustion")
        
        # Exhaust rate limiter
        for _ in range(25):
            self.controls.rate_limiter.record_request()
        
        can_proceed, msg = self.controls.rate_limiter.can_proceed()
        
        result = FailureTestResult(
            test_name="rate_limit_exhaustion",
            passed=not can_proceed,
            alert_triggered=not can_proceed,
            auto_pause_worked=True,
            graceful_degradation=True,
            notes=f"Rate limit correctly blocked: {msg}"
        )
        
        self.results.append(result)
        print(f"  {'✓' if result.passed else '✗'} Rate limit blocked new requests")
        
        # Reset
        self.controls.rate_limiter._minute_requests.clear()
        return result
    
    def test_consecutive_failures_pause(self) -> FailureTestResult:
        """Test auto-pause after consecutive failures."""
        print("\n[TEST] Consecutive Failures Auto-Pause")
        
        kill_switch = self.controls.kill_switch
        kill_switch._global_kill = False
        kill_switch._consecutive_failures = 0
        
        # Simulate 5 consecutive failures
        for i in range(5):
            kill_switch.register_job(f"test_job_{i}")
            kill_switch.unregister_job(f"test_job_{i}", success=False)
        
        result = FailureTestResult(
            test_name="consecutive_failures_pause",
            passed=kill_switch._global_kill,
            alert_triggered=kill_switch._global_kill,
            auto_pause_worked=kill_switch._global_kill,
            graceful_degradation=True,
            notes=f"Auto-paused after {kill_switch._consecutive_failures} failures"
        )
        
        self.results.append(result)
        print(f"  {'✓' if result.passed else '✗'} System auto-paused after consecutive failures")
        
        # Reset
        kill_switch.resume()
        return result
    
    def test_kill_switch(self) -> FailureTestResult:
        """Test manual kill switch."""
        print("\n[TEST] Kill Switch")
        
        kill_switch = self.controls.kill_switch
        
        # Register a job and kill it
        kill_switch.register_job("test_killable")
        kill_switch.kill_job("test_killable")
        
        should_stop = kill_switch.should_stop("test_killable")
        
        result = FailureTestResult(
            test_name="kill_switch",
            passed=should_stop,
            alert_triggered=True,
            auto_pause_worked=True,
            graceful_degradation=should_stop,
            notes="Kill switch stopped job execution"
        )
        
        self.results.append(result)
        print(f"  {'✓' if result.passed else '✗'} Kill switch stopped job")
        
        return result
    
    def test_global_kill(self) -> FailureTestResult:
        """Test global kill (stop all)."""
        print("\n[TEST] Global Kill")
        
        kill_switch = self.controls.kill_switch
        kill_switch._global_kill = False
        
        # Register jobs
        for i in range(3):
            kill_switch.register_job(f"global_test_{i}")
        
        # Global kill
        kill_switch.kill_all()
        
        all_stopped = all(
            kill_switch.should_stop(f"global_test_{i}") for i in range(3)
        )
        
        result = FailureTestResult(
            test_name="global_kill",
            passed=all_stopped and kill_switch._global_kill,
            alert_triggered=True,
            auto_pause_worked=True,
            graceful_degradation=True,
            notes="Global kill stopped all jobs"
        )
        
        self.results.append(result)
        print(f"  {'✓' if result.passed else '✗'} Global kill stopped all jobs")
        
        # Reset
        kill_switch.resume()
        return result
    
    def run_all_tests(self) -> Dict:
        """Run all failure injection tests."""
        print("=" * 60)
        print("  FAILURE INJECTION TEST SUITE")
        print("=" * 60)
        
        self.test_rate_limit_exhaustion()
        self.test_consecutive_failures_pause()
        self.test_kill_switch()
        self.test_global_kill()
        
        # Summary
        passed = len([r for r in self.results if r.passed])
        total = len(self.results)
        
        print("\n" + "=" * 60)
        print(f"  RESULTS: {passed}/{total} tests passed")
        print("=" * 60)
        
        for r in self.results:
            status = "✓ PASS" if r.passed else "✗ FAIL"
            print(f"  {status}: {r.test_name}")
        
        return {
            "passed": passed,
            "total": total,
            "all_passed": passed == total,
            "results": [asdict(r) for r in self.results]
        }


if __name__ == "__main__":
    test = FailureInjectionTest()
    test.run_all_tests()
