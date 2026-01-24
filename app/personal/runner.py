"""
Personal Runner
One-button output with speed mode and playbook execution.
"""
import sys
import time
from pathlib import Path
from datetime import datetime
from typing import List, Dict, Optional

PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from app.core.database import init_db
from app.personal.control_config import load_config, PersonalConfig
from app.personal.playbooks import PlaybookEngine
from app.personal.taste_memory import TasteMemory
from app.orchestrator.service import OrchestratorService
from app.core.logging import get_logger

logger = get_logger("personal_runner")


class PersonalRunner:
    """
    One-button execution for personal mode.
    Generate → Filter → Rank → Review winners only.
    """
    
    def __init__(self):
        self.config = load_config()
        self.playbooks = PlaybookEngine()
        self.taste = TasteMemory()
        self.orchestrator = OrchestratorService()
    
    def run(
        self,
        playbook_id: str = None,
        ideas: int = 5,
        topic: str = None,
        speed_mode: bool = None
    ) -> Dict:
        """
        One-button run: playbook + ideas → winners.
        
        Args:
            playbook_id: Which playbook to use
            ideas: How many to generate
            topic: Optional specific topic
            speed_mode: Override config speed mode
            
        Returns:
            Results with winners
        """
        print("\n" + "=" * 60)
        print("  🚀 PERSONAL RUNNER")
        print("=" * 60)
        
        init_db()
        
        # Get playbook
        playbook_id = playbook_id or self.config.active_playbook or "viral_fact"
        playbook = self.playbooks.get(playbook_id)
        
        if not playbook:
            print(f"  ❌ Playbook not found: {playbook_id}")
            return {"error": "Playbook not found"}
        
        print(f"  📘 Playbook: {playbook.name}")
        print(f"  🎯 Ideas: {ideas}")
        
        # Speed mode
        is_speed = speed_mode if speed_mode is not None else self.config.speed_mode
        if is_speed:
            print("  ⚡ Speed Mode: ON")
        
        # Generate batch
        start = time.time()
        results = []
        winners = []
        
        for i in range(ideas):
            try:
                # Build config from playbook
                job_config = self.playbooks.to_job_config(playbook_id)
                if topic:
                    job_config["topic"] = topic
                
                # Speed mode adjustments
                if is_speed:
                    job_config["duration"] = min(job_config.get("duration", 30), 20)
                    job_config["max_retries"] = 1
                
                job = self.orchestrator.create_job(job_config)
                success = self.orchestrator.start_job(job.id)
                final_job = self.orchestrator.get_job(job.id)
                
                result = {
                    "job_id": job.id,
                    "success": success,
                    "score": final_job.total_score if final_job else 0
                }
                results.append(result)
                
                # Check if winner
                if success and result["score"] >= self.config.min_quality_score:
                    winners.append(result)
                    print(f"  ✓ Idea {i+1}: Score {result['score']:.2f} ⭐")
                elif success:
                    print(f"  ○ Idea {i+1}: Score {result['score']:.2f}")
                else:
                    print(f"  ✗ Idea {i+1}: Failed")
                    
            except Exception as e:
                print(f"  ✗ Idea {i+1}: Error - {e}")
                results.append({"success": False, "error": str(e)})
        
        elapsed = time.time() - start
        
        # Summary
        print("\n" + "-" * 60)
        print("  RESULTS")
        print("-" * 60)
        print(f"  Total: {len(results)}")
        print(f"  Winners: {len(winners)} ⭐")
        print(f"  Time: {elapsed:.1f}s")
        
        if winners:
            print(f"\n  🏆 TOP WINNER: {winners[0]['job_id'][:8]} (Score: {winners[0]['score']:.2f})")
        
        return {
            "playbook": playbook_id,
            "total": len(results),
            "winners": winners,
            "time_sec": round(elapsed, 1)
        }
    
    def quick_run(self, count: int = 3):
        """Quick run with defaults."""
        return self.run(ideas=count, speed_mode=True)
    
    def rate_last(self, rating: int, feedback: str = ""):
        """Rate the last generated output."""
        # Would get last job from session
        logger.info(f"Rated last output: {rating}/5")
        self.taste.rate("last", rating, feedback)
    
    def close(self):
        self.orchestrator.close()


def run_cli():
    """CLI for personal runner."""
    import sys
    
    playbook = sys.argv[1] if len(sys.argv) > 1 else "viral_fact"
    ideas = int(sys.argv[2]) if len(sys.argv) > 2 else 3
    
    runner = PersonalRunner()
    runner.run(playbook, ideas, speed_mode=True)
    runner.close()


if __name__ == "__main__":
    run_cli()
