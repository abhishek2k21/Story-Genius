"""
Batch Test Script (Week 2)
Tests the intelligent creative system with 20 diverse jobs.
Logs hook types, personas, scores, and improvement metrics.
"""
import sys
import os
import json
from pathlib import Path
from datetime import datetime

# Add project root to path
PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from app.core.database import init_db
from app.orchestrator.service import OrchestratorService
from app.core.logging import get_logger

logger = get_logger("batch_test_v2")


def run_batch_test(num_jobs: int = 20):
    """
    Run Week 2 verification batch.
    """
    print("=" * 60)
    print("    Creative AI Shorts (Week 2) - Intelligent Batch Test")
    print("=" * 60)
    
    # Initialize database
    logger.info("Initializing database...")
    init_db()
    
    # Diverse test configurations
    base_configs = [
        {"platform": "youtube_shorts", "audience": "kids_india", "genre": "kids"},
        {"platform": "youtube_shorts", "audience": "genz_us", "genre": "facts"},
        {"platform": "instagram_reels", "audience": "motivation", "genre": "success"},
        {"platform": "tiktok", "audience": "genz", "genre": "thriller"},
        {"platform": "youtube_shorts", "audience": "children", "genre": "bedtime"}
    ]
    
    orchestrator = OrchestratorService()
    results = []
    
    try:
        start_time = datetime.now()
        
        for i in range(num_jobs):
            config = base_configs[i % len(base_configs)]
            config["duration"] = 30
            
            print(f"\n{'='*60}")
            print(f"  Job {i+1}/{num_jobs}: {config['genre']} for {config['audience']}")
            print(f"{'='*60}")
            
            try:
                # Create job
                job = orchestrator.create_job(config)
                print(f"  Job ID: {job.id}")
                
                # Run job
                success = orchestrator.start_job(job.id)
                
                # Get final status
                final_job = orchestrator.get_job(job.id)
                
                metric = {
                    "job_id": job.id,
                    "config": config,
                    "success": success,
                    "score": final_job.total_score if final_job else 0,
                    "retries": final_job.retry_count if final_job else 0
                }
                results.append(metric)
                
                status_icon = "✅" if success else "❌"
                score_display = f"{final_job.total_score:.2f}" if final_job and final_job.total_score else "N/A"
                print(f"  {status_icon} Result: {score_display} (Retries: {final_job.retry_count})")
                    
            except Exception as e:
                logger.error(f"Job {i+1} failed: {e}")
                results.append({"success": False, "error": str(e)})
        
        duration = datetime.now() - start_time
        
        # --- Analysis ---
        successful = [r for r in results if r["success"]]
        avg_score = sum(r["score"] for r in successful) / len(successful) if successful else 0
        total_retries = sum(r["retries"] for r in successful)
        
        print("\n" + "=" * 60)
        print("    WEEK 2 PERFORMANCE METRICS")
        print("=" * 60)
        print(f"Total Jobs:      {len(results)}")
        print(f"Successful:      {len(successful)}")
        print(f"Avg Score:       {avg_score:.2f} (Target: >0.75)")
        print(f"Total Retries:   {total_retries}")
        print(f"Avg Retries/Job: {total_retries/len(successful):.2f}")
        print(f"Time Taken:      {duration}")
        
        # Week 1 Comparison (Approximate baseline)
        print("\nChange vs Week 1 Baseline:")
        print(f"Quality Delta:   {avg_score - 0.65:+.2f}")
        
        # Save detailed logs
        with open("reports/week2_batch_metrics.json", "w") as f:
            json.dump(results, f, indent=2)
            
        print("\nDetailed metrics saved to 'reports/week2_batch_metrics.json'")
        
    finally:
        orchestrator.close()


if __name__ == "__main__":
    count = int(sys.argv[1]) if len(sys.argv) > 1 else 20
    run_batch_test(count)
