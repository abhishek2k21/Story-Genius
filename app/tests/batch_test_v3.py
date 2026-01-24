"""
Batch Test Script (Week 3)
Tests the complete platform with all Week 3 features.
Includes timing, cost estimation, and scale metrics.
"""
import sys
import os
import json
import time
from pathlib import Path
from datetime import datetime
from dataclasses import dataclass, asdict
from typing import List, Dict

# Add project root to path
PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from app.core.database import init_db
from app.orchestrator.service import OrchestratorService
from app.core.logging import get_logger

logger = get_logger("batch_test_v3")


@dataclass
class JobMetrics:
    """Metrics for a single job."""
    job_id: str
    success: bool
    score: float
    retries: int
    duration_sec: float
    persona: str = ""
    visual_style: str = ""
    hook_type: str = ""
    error: str = ""


@dataclass
class BatchMetrics:
    """Aggregate metrics for a batch."""
    total_jobs: int
    successful_jobs: int
    failed_jobs: int
    avg_score: float
    avg_duration_sec: float
    total_retries: int
    total_time_sec: float
    estimated_cost_usd: float  # Rough estimate
    

def estimate_cost(num_llm_calls: int, num_tts_calls: int) -> float:
    """
    Rough cost estimation per job.
    - LLM calls: ~$0.001 per call (Gemini Flash)
    - TTS calls: ~$0.0004 per call (Edge TTS is free, but for estimation)
    """
    llm_cost = num_llm_calls * 0.001
    tts_cost = num_tts_calls * 0.0004
    return round(llm_cost + tts_cost, 4)


def run_batch_test(num_jobs: int = 20):
    """
    Run Week 3 production-ready batch test.
    """
    print("=" * 70)
    print("    Creative AI Shorts (Week 3) - Scale & Cost Batch Test")
    print("=" * 70)
    
    # Initialize database
    logger.info("Initializing database...")
    init_db()
    
    # Test configurations with diverse settings
    test_configs = [
        {"platform": "youtube_shorts", "audience": "kids_india", "genre": "kids", "duration": 30},
        {"platform": "youtube_shorts", "audience": "genz_us", "genre": "facts", "duration": 28},
        {"platform": "instagram_reels", "audience": "motivation", "genre": "success", "duration": 25},
        {"platform": "tiktok", "audience": "genz", "genre": "thriller", "duration": 30},
        {"platform": "youtube_shorts", "audience": "children", "genre": "bedtime", "duration": 32},
        {"platform": "youtube_shorts", "audience": "kids", "genre": "mythology", "duration": 30},
        {"platform": "instagram_reels", "audience": "genz_us", "genre": "comedy", "duration": 20},
        {"platform": "youtube_shorts", "audience": "educational", "genre": "history", "duration": 33},
    ]
    
    orchestrator = OrchestratorService()
    job_metrics: List[JobMetrics] = []
    
    try:
        batch_start = time.time()
        
        for i in range(num_jobs):
            config = test_configs[i % len(test_configs)]
            
            print(f"\n{'='*70}")
            print(f"  Job {i+1}/{num_jobs}: {config['genre']} | {config['audience']} | {config['platform']}")
            print(f"{'='*70}")
            
            job_start = time.time()
            
            try:
                # Create job
                job = orchestrator.create_job(config)
                print(f"  Job ID: {job.id[:8]}")
                
                # Run job
                success = orchestrator.start_job(job.id)
                
                job_duration = time.time() - job_start
                
                # Get final status
                final_job = orchestrator.get_job(job.id)
                
                metric = JobMetrics(
                    job_id=job.id,
                    success=success,
                    score=final_job.total_score if final_job and final_job.total_score else 0,
                    retries=final_job.retry_count if final_job else 0,
                    duration_sec=round(job_duration, 2)
                )
                job_metrics.append(metric)
                
                status_icon = "✅" if success else "❌"
                print(f"  {status_icon} Score: {metric.score:.2f} | Time: {metric.duration_sec:.1f}s | Retries: {metric.retries}")
                    
            except Exception as e:
                job_duration = time.time() - job_start
                logger.error(f"Job {i+1} failed: {e}")
                job_metrics.append(JobMetrics(
                    job_id="",
                    success=False,
                    score=0,
                    retries=0,
                    duration_sec=round(job_duration, 2),
                    error=str(e)
                ))
        
        batch_duration = time.time() - batch_start
        
        # --- Calculate Aggregate Metrics ---
        successful = [m for m in job_metrics if m.success]
        failed = [m for m in job_metrics if not m.success]
        
        avg_score = sum(m.score for m in successful) / len(successful) if successful else 0
        avg_duration = sum(m.duration_sec for m in job_metrics) / len(job_metrics)
        total_retries = sum(m.retries for m in job_metrics)
        
        # Estimate costs (rough)
        # Assume ~8 LLM calls per job, 6 TTS calls per job
        llm_calls_per_job = 8
        tts_calls_per_job = 6
        total_cost = estimate_cost(
            num_llm_calls=len(successful) * llm_calls_per_job,
            num_tts_calls=len(successful) * tts_calls_per_job
        )
        
        batch = BatchMetrics(
            total_jobs=len(job_metrics),
            successful_jobs=len(successful),
            failed_jobs=len(failed),
            avg_score=round(avg_score, 3),
            avg_duration_sec=round(avg_duration, 2),
            total_retries=total_retries,
            total_time_sec=round(batch_duration, 2),
            estimated_cost_usd=total_cost
        )
        
        # --- Print Summary ---
        print("\n" + "=" * 70)
        print("    WEEK 3 BATCH PERFORMANCE METRICS")
        print("=" * 70)
        print(f"Total Jobs:        {batch.total_jobs}")
        print(f"Successful:        {batch.successful_jobs}")
        print(f"Failed:            {batch.failed_jobs}")
        print(f"Success Rate:      {batch.successful_jobs/batch.total_jobs*100:.1f}%")
        print(f"")
        print(f"Avg Quality Score: {batch.avg_score:.3f}")
        print(f"Avg Job Duration:  {batch.avg_duration_sec:.1f}s")
        print(f"Total Retries:     {batch.total_retries}")
        print(f"Total Batch Time:  {batch.total_time_sec:.1f}s ({batch.total_time_sec/60:.1f} min)")
        print(f"")
        print(f"Estimated Cost:    ${batch.estimated_cost_usd:.4f}")
        print(f"Cost per Short:    ${batch.estimated_cost_usd/max(1, batch.successful_jobs):.4f}")
        
        # Week comparison
        print("\n" + "-" * 70)
        print("IMPROVEMENT vs Week 2:")
        print(f"  Avg Score:        {batch.avg_score:.3f} (Week 2: ~0.78)")
        print(f"  Quality Delta:    {batch.avg_score - 0.78:+.3f}")
        
        # Save detailed report
        report = {
            "batch_metrics": asdict(batch),
            "job_metrics": [asdict(m) for m in job_metrics],
            "timestamp": datetime.now().isoformat()
        }
        
        report_path = Path("reports/week3_batch_metrics.json")
        report_path.parent.mkdir(exist_ok=True)
        with open(report_path, "w") as f:
            json.dump(report, f, indent=2)
        
        print(f"\nDetailed report saved to: {report_path}")
        
        return batch
        
    finally:
        orchestrator.close()


if __name__ == "__main__":
    count = int(sys.argv[1]) if len(sys.argv) > 1 else 20
    run_batch_test(count)
