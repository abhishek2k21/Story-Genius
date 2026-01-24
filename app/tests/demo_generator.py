"""
Demo Batch Generator
Generates showcase content for demos, pitches, and pilots.
"""
import sys
import json
from pathlib import Path
from datetime import datetime
from typing import List, Dict

# Add project root
PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from app.core.database import init_db
from app.orchestrator.channel_service import ChannelService, PRESET_CHANNELS
from app.analytics.economics import EconomicsService
from app.core.logging import get_logger

logger = get_logger("demo_generator")


def generate_hero_demo(channel_id: str = "kids_fun_facts", num_videos: int = 5):
    """
    Generate a hero channel demo batch.
    
    Args:
        channel_id: Target channel
        num_videos: Number of videos to generate
    """
    print("=" * 70)
    print("    Creative AI Shorts - Hero Channel Demo Generator")
    print("=" * 70)
    
    init_db()
    
    channel_service = ChannelService()
    economics = EconomicsService()
    
    channel = channel_service.get_channel(channel_id)
    if not channel:
        print(f"Channel not found: {channel_id}")
        return
    
    print(f"\n📺 Channel: {channel.name}")
    print(f"   Persona: {channel.persona_id}")
    print(f"   Visual Style: {channel.visual_style_id}")
    print(f"   Platform: {channel.platform}")
    print(f"\n🎬 Generating {num_videos} showcase videos...\n")
    
    # Demo topics
    demo_topics = [
        "Did you know dinosaurs still walk among us?",
        "The secret superpower of everyday bananas",
        "Why the moon keeps following you",
        "The mystery of disappearing socks explained",
        "How ants build cities bigger than yours"
    ]
    
    results = []
    total_cost = 0
    
    for i, topic in enumerate(demo_topics[:num_videos]):
        print(f"\n[{i+1}/{num_videos}] {topic}")
        
        try:
            result = channel_service.generate_for_channel(channel_id, topic)
            results.append(result)
            
            # Track economics
            cost = economics.estimate_cost(result["job_id"])
            economics.estimate_value(result["job_id"], estimated_views=5000)
            total_cost += cost.total_cost
            
            if result["success"]:
                print(f"    ✅ Score: {result['score']:.2f} | Cost: ${cost.total_cost:.4f}")
            else:
                print(f"    ❌ Failed")
                
        except Exception as e:
            print(f"    ❌ Error: {e}")
    
    # Summary
    successful = [r for r in results if r.get("success")]
    
    print("\n" + "=" * 70)
    print("    DEMO BATCH SUMMARY")
    print("=" * 70)
    print(f"Channel:          {channel.name}")
    print(f"Videos Generated: {len(successful)}/{num_videos}")
    print(f"Avg Score:        {sum(r['score'] for r in successful)/len(successful):.2f}" if successful else "N/A")
    print(f"Total Cost:       ${total_cost:.4f}")
    print(f"Avg Cost/Video:   ${total_cost/len(successful):.4f}" if successful else "N/A")
    
    # Value proposition
    print("\n" + "-" * 70)
    print("VALUE PROPOSITION:")
    print(f"  💰 Cost per video:     ${total_cost/max(1, len(successful)):.4f}")
    print(f"  📈 Est. value (5K views): ${0.02 * len(successful):.2f}")
    print(f"  🚀 ROI potential:      {(0.02 * len(successful)) / max(0.01, total_cost):.0f}x")
    
    # Save demo report
    report = {
        "channel": channel.name,
        "timestamp": datetime.now().isoformat(),
        "videos": num_videos,
        "successful": len(successful),
        "total_cost": round(total_cost, 4),
        "results": results
    }
    
    report_path = Path("reports/demo_batch_report.json")
    report_path.parent.mkdir(exist_ok=True)
    with open(report_path, "w") as f:
        json.dump(report, f, indent=2)
    
    print(f"\n📄 Report saved: {report_path}")
    
    channel_service.close()
    

def generate_multi_channel_demo(idea: str = "Amazing animal facts"):
    """
    Generate same idea across multiple channels.
    """
    print("=" * 70)
    print("    Multi-Channel Demo")
    print("=" * 70)
    
    init_db()
    
    channel_service = ChannelService()
    
    print(f"\n💡 Idea: {idea}")
    print(f"📺 Channels: {len(PRESET_CHANNELS)}")
    
    result = channel_service.generate_multi_channel(
        idea=idea,
        max_channels=3
    )
    
    print(f"\n{'='*70}")
    print("RESULTS:")
    for r in result.channel_results:
        status = "✅" if r.get("success") else "❌"
        print(f"  {status} {r.get('channel_name', 'Unknown')}: Score {r.get('score', 0):.2f}")
    
    print(f"\nTotal time: {result.total_time_sec:.1f}s")
    print(f"Success rate: {result.successful_jobs}/{result.total_jobs}")
    
    channel_service.close()


def print_positioning():
    """Print the value proposition and positioning."""
    print("""
╔══════════════════════════════════════════════════════════════════════╗
║                    CREATIVE AI SHORTS PLATFORM                      ║
╠══════════════════════════════════════════════════════════════════════╣
║                                                                      ║
║  "We don't generate videos. We generate Shorts that PERFORM."       ║
║                                                                      ║
╠══════════════════════════════════════════════════════════════════════╣
║  WHAT MAKES US DIFFERENT:                                           ║
║                                                                      ║
║  ✅ Hook Intelligence    - 5 variants, LLM-scored, best wins        ║
║  ✅ Brand Personas       - Consistent voice across 100s of videos   ║
║  ✅ Emotion Curves       - Pacing engineered for retention          ║
║  ✅ Visual Branding      - Channel-level style consistency          ║
║  ✅ Platform Optimization- YouTube, Reels, TikTok specific rules    ║
║  ✅ A/B Testing Built-in - Test hooks before going live             ║
║  ✅ Real Metrics Loop    - System learns from actual performance    ║
║                                                                      ║
╠══════════════════════════════════════════════════════════════════════╣
║  UNIT ECONOMICS:                                                    ║
║                                                                      ║
║  Cost per video:    ~$0.01                                          ║
║  Time per video:    ~20 seconds                                     ║
║  ROI potential:     30-100x on ad revenue                           ║
║                                                                      ║
╠══════════════════════════════════════════════════════════════════════╣
║  USE CASES:                                                         ║
║                                                                      ║
║  🎯 Creator SaaS     - $29-99/mo for content creators               ║
║  🎯 Agency Backend   - White-label for video agencies               ║
║  🎯 Content Network  - Run 100 channels from one brain              ║
║  🎯 API Platform     - Sell video generation as infrastructure      ║
║                                                                      ║
╚══════════════════════════════════════════════════════════════════════╝
""")


if __name__ == "__main__":
    import sys
    
    if len(sys.argv) > 1:
        if sys.argv[1] == "multi":
            generate_multi_channel_demo()
        elif sys.argv[1] == "positioning":
            print_positioning()
        else:
            generate_hero_demo(sys.argv[1], 5)
    else:
        print_positioning()
        generate_hero_demo("kids_fun_facts", 3)
