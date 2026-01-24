"""
Batch Test Script for Creative AI Shorts Platform
Tests the end-to-end pipeline with multiple jobs.
"""
import sys
import os
from pathlib import Path

# Add project root to path
PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from app.core.database import init_db
from app.orchestrator.service import OrchestratorService
from app.core.logging import get_logger

logger = get_logger("batch_test")


def run_batch_test(num_jobs: int = 5):
    """
    Run a batch of test jobs to verify the platform.
    
    Args:
        num_jobs: Number of jobs to create and run
    """
    print("=" * 60)
    print("    Creative AI Shorts Platform - Batch Test")
    print("=" * 60)
    
    # Initialize database
    logger.info("Initializing database...")
    init_db()
    
    # Test configurations
    test_configs = [
        {"platform": "youtube_shorts", "audience": "kids_india", "duration": 30, "genre": "kids"},
        {"platform": "youtube_shorts", "audience": "genz_us", "duration": 25, "genre": "motivation"},
        {"platform": "instagram_reels", "audience": "kids_india", "duration": 30, "genre": "comedy"},
        {"platform": "youtube_shorts", "audience": "kids_india", "duration": 35, "genre": "bedtime"},
        {"platform": "tiktok", "audience": "genz_us", "duration": 30, "genre": "scifi"},
    ]
    
    orchestrator = OrchestratorService()
    results = []
    
    try:
        for i, config in enumerate(test_configs[:num_jobs]):
            print(f"\n{'='*60}")
            print(f"  Job {i+1}/{num_jobs}: {config['genre']} for {config['audience']}")
            print(f"{'='*60}")
            
            try:
                # Create job
                job = orchestrator.create_job(config)
                logger.info(f"Created job: {job.id}")
                
                # Run job
                success = orchestrator.start_job(job.id)
                
                # Get final status
                final_job = orchestrator.get_job(job.id)
                
                results.append({
                    "job_id": job.id,
                    "config": config,
                    "success": success,
                    "status": final_job.status.value if final_job else "unknown",
                    "score": final_job.total_score if final_job else None
                })
                
                status_icon = "✅" if success else "❌"
                print(f"{status_icon} Job {job.id[:8]}: {final_job.status.value if final_job else 'unknown'}")
                if final_job and final_job.total_score:
                    print(f"   Score: {final_job.total_score}")
                    
            except Exception as e:
                logger.error(f"Job {i+1} failed: {e}")
                results.append({
                    "job_id": None,
                    "config": config,
                    "success": False,
                    "status": "error",
                    "error": str(e)
                })
        
        # Summary
        print("\n" + "=" * 60)
        print("    BATCH TEST RESULTS")
        print("=" * 60)
        
        successful = sum(1 for r in results if r["success"])
        print(f"\nTotal Jobs: {len(results)}")
        print(f"Successful: {successful}")
        print(f"Failed: {len(results) - successful}")
        
        # Best scores
        scored = [r for r in results if r.get("score")]
        if scored:
            sorted_by_score = sorted(scored, key=lambda x: x["score"], reverse=True)
            print("\n🏆 Top 3 Best Outputs:")
            for i, r in enumerate(sorted_by_score[:3]):
                print(f"  {i+1}. Job {r['job_id'][:8]} - Score: {r['score']}")
        
        return results
        
    finally:
        orchestrator.close()


if __name__ == "__main__":
    num = int(sys.argv[1]) if len(sys.argv) > 1 else 5
    run_batch_test(num)
