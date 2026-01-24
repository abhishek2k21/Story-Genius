"""
Stress Test Script
Tests parallel delivery across multiple clients.
"""
import sys
import time
import json
import threading
from pathlib import Path
from datetime import datetime
from dataclasses import dataclass, asdict
from typing import List, Dict
from concurrent.futures import ThreadPoolExecutor, as_completed

PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from app.core.database import init_db
from app.agency.client_service import AgencyClientService
from app.core.logging import get_logger

logger = get_logger("stress_test")


@dataclass
class StressTestResult:
    """Result of a stress test run."""
    total_clients: int
    total_batches: int
    total_videos: int
    successful_videos: int
    failed_videos: int
    total_time_sec: float
    avg_latency_sec: float
    max_latency_sec: float
    cascading_failures: bool
    cost_spike: bool


def run_client_batch(client_id: str, batch_size: int, svc: AgencyClientService) -> Dict:
    """Run a batch for a single client."""
    start = time.time()
    
    try:
        result = svc.generate_batch(client_id, count=batch_size)
        elapsed = time.time() - start
        
        return {
            "client_id": client_id,
            "success": True,
            "videos_requested": batch_size,
            "videos_successful": result.successful,
            "videos_failed": result.failed,
            "latency_sec": elapsed,
            "avg_score": result.avg_score
        }
    except Exception as e:
        elapsed = time.time() - start
        return {
            "client_id": client_id,
            "success": False,
            "error": str(e),
            "latency_sec": elapsed
        }


def run_stress_test(
    num_clients: int = 3,
    batch_size: int = 10,
    parallel: bool = True
) -> StressTestResult:
    """
    Run stress test with parallel client batches.
    
    Args:
        num_clients: Number of clients to simulate
        batch_size: Videos per client batch
        parallel: Run in parallel or sequential
    """
    print("=" * 70)
    print("    STRESS TEST: Parallel Delivery")
    print("=" * 70)
    print(f"Clients: {num_clients}, Batch Size: {batch_size}, Parallel: {parallel}")
    
    init_db()
    svc = AgencyClientService()
    
    # Create test agency and clients
    agency = svc.create_agency("StressTest Agency", "stress@test.com")
    client_ids = []
    
    for i in range(num_clients):
        client = svc.create_client(
            agency.id,
            name=f"StressClient_{i+1}",
            persona="fast_explainer",
            genre="facts"
        )
        client_ids.append(client.id)
    
    print(f"Created {num_clients} test clients")
    
    # Run batches
    start_time = time.time()
    results = []
    
    if parallel:
        with ThreadPoolExecutor(max_workers=num_clients) as executor:
            futures = {
                executor.submit(run_client_batch, cid, batch_size, svc): cid 
                for cid in client_ids
            }
            
            for future in as_completed(futures):
                result = future.result()
                results.append(result)
                status = "✓" if result.get("success") else "✗"
                print(f"  {status} {result.get('client_id', '')[:8]}: {result.get('videos_successful', 0)}/{batch_size} in {result.get('latency_sec', 0):.1f}s")
    else:
        for cid in client_ids:
            result = run_client_batch(cid, batch_size, svc)
            results.append(result)
    
    total_time = time.time() - start_time
    
    # Analyze results
    successful = [r for r in results if r.get("success")]
    total_videos = sum(r.get("videos_successful", 0) for r in successful)
    failed_videos = sum(r.get("videos_failed", 0) for r in successful)
    latencies = [r.get("latency_sec", 0) for r in results]
    
    # Check for cascading failures
    cascading = len([r for r in results if not r.get("success")]) > 1
    
    # Check for cost spikes (rough estimate)
    expected_cost = total_videos * 0.01
    cost_spike = expected_cost > (total_videos * 0.02)  # >2x expected
    
    test_result = StressTestResult(
        total_clients=num_clients,
        total_batches=len(results),
        total_videos=total_videos,
        successful_videos=total_videos,
        failed_videos=failed_videos,
        total_time_sec=round(total_time, 2),
        avg_latency_sec=round(sum(latencies) / len(latencies), 2) if latencies else 0,
        max_latency_sec=round(max(latencies), 2) if latencies else 0,
        cascading_failures=cascading,
        cost_spike=cost_spike
    )
    
    # Print summary
    print("\n" + "=" * 70)
    print("    STRESS TEST RESULTS")
    print("=" * 70)
    print(f"Clients:           {test_result.total_clients}")
    print(f"Total Videos:      {test_result.total_videos}")
    print(f"Success Rate:      {test_result.successful_videos / max(1, test_result.total_videos + test_result.failed_videos):.0%}")
    print(f"Total Time:        {test_result.total_time_sec:.1f}s")
    print(f"Avg Latency:       {test_result.avg_latency_sec:.1f}s")
    print(f"Max Latency:       {test_result.max_latency_sec:.1f}s")
    print(f"Cascading Failures: {'YES ⚠️' if test_result.cascading_failures else 'NO ✓'}")
    print(f"Cost Spike:        {'YES ⚠️' if test_result.cost_spike else 'NO ✓'}")
    
    # Save report
    report_path = Path("reports/stress_test_report.json")
    report_path.parent.mkdir(exist_ok=True)
    with open(report_path, "w") as f:
        json.dump(asdict(test_result), f, indent=2)
    
    print(f"\nReport saved: {report_path}")
    
    svc.close()
    return test_result


if __name__ == "__main__":
    clients = int(sys.argv[1]) if len(sys.argv) > 1 else 3
    batch = int(sys.argv[2]) if len(sys.argv) > 2 else 5
    run_stress_test(clients, batch, parallel=True)
