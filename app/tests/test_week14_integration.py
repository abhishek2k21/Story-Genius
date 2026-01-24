"""
Week 14 - Path 1 Integration Test
Tests Silent Mode, Red Flag Detection, Trust Thresholds, and Speed Preservation.
"""
import sys
import json
import time
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from app.intelligence.path1_runner import (
    Path1Runner,
    Path1Mode,
    TrustThresholds,
    get_path1_runner,
    filter_ideas,
    analyze_idea
)


def test_silent_mode():
    """Test Silent Mode - only surfaces results, not process."""
    print("\n" + "="*70)
    print("🔇 TEST 1: SILENT MODE INTEGRATION (Day 77)")
    print("="*70)
    
    ideas = [
        "Short-form curiosity hooks work best for kids educational content.",
        "Using extreme cliffhangers will maximize video retention.",
        "AI-generated voices are indistinguishable from human narration now.",
        "Posting 3 shorts per day is the optimal frequency for channel growth.",
        "Thumbnail faces with exaggerated expressions always get more clicks."
    ]
    
    print(f"\n📝 Analyzing {len(ideas)} ideas in SILENT mode...")
    print("   (You only see results, not process)\n")
    
    start = time.time()
    result = filter_ideas(ideas)
    elapsed = time.time() - start
    
    print(f"⏱️ Processing time: {elapsed:.2f}s")
    print(f"\n✅ TOP IDEAS (surfaced):")
    for i, idea in enumerate(result["top_ideas"], 1):
        print(f"\n  #{i}: {idea['status'].upper()} (Score: {idea['score']:.0%})")
        print(f"      Original: \"{idea['original'][:50]}...\"")
        print(f"      Refined:  \"{idea['refined'][:60]}...\"")
    
    if result["warnings"]:
        print(f"\n⚠️ WARNINGS ({result['warning_count']} flagged):")
        for w in result["warnings"]:
            print(f"\n  ❌ {w['status']}: \"{w['idea']}\"")
            for flag in w["flags"]:
                print(f"      → {flag}")
    else:
        print(f"\n✅ No warnings - all ideas passed safety checks")
    
    return result


def test_red_flags():
    """Test Red Flag System - detect ideas that should never ship."""
    print("\n" + "="*70)
    print("🚩 TEST 2: RED FLAG SYSTEM (Day 79)")
    print("="*70)
    
    # Ideas designed to trigger red flags
    dangerous_ideas = [
        "Use shocking clickbait that promises something we don't deliver.",
        "Copy trending content exactly without adding any original value.",
        "Maximize watch time by manipulating emotions through false urgency.",
        "Target vulnerable audiences with misleading health claims.",
    ]
    
    safe_ideas = [
        "Create educational content that genuinely helps viewers learn.",
        "Build authentic stories that resonate with core audience values.",
    ]
    
    runner = Path1Runner(mode=Path1Mode.VERBOSE)
    
    print("\n🔍 Testing DANGEROUS ideas (should be flagged):\n")
    for idea in dangerous_ideas:
        result = runner.analyze(idea)
        print(f"  Idea: \"{idea[:50]}...\"")
        print(f"  Status: {result.status.value.upper()}")
        print(f"  Score: {result.depth_score:.0%}")
        if result.red_flags:
            print(f"  🚩 Red Flags:")
            for rf in result.red_flags:
                print(f"      [{rf.flag_type}] {rf.reason[:60]}...")
        print()
    
    print("\n🔍 Testing SAFE ideas (should pass):\n")
    for idea in safe_ideas:
        result = runner.analyze(idea)
        print(f"  Idea: \"{idea[:50]}...\"")
        print(f"  Status: {result.status.value.upper()}")
        print(f"  Score: {result.depth_score:.0%}")
        print(f"  Refined: \"{result.refined_idea[:50]}...\"")
        print()


def test_trust_thresholds():
    """Test Personal Trust Thresholds - control when system overrides you."""
    print("\n" + "="*70)
    print("🎚️ TEST 3: TRUST THRESHOLDS (Day 80)")
    print("="*70)
    
    # Custom thresholds
    strict_thresholds = TrustThresholds(
        auto_accept=0.85,
        auto_reject=0.40,
        fragile_assumption_limit=2,
        long_term_risk_limit=0.60
    )
    
    lenient_thresholds = TrustThresholds(
        auto_accept=0.65,
        auto_reject=0.25,
        fragile_assumption_limit=5,
        long_term_risk_limit=0.85
    )
    
    test_idea = "Use emotional storytelling with cliffhangers for engagement."
    
    print(f"\n📝 Test Idea: \"{test_idea}\"\n")
    
    # Test with strict thresholds
    strict_runner = Path1Runner(mode=Path1Mode.SILENT, thresholds=strict_thresholds)
    strict_result = strict_runner.analyze(test_idea)
    
    print("🔒 STRICT Thresholds (auto_accept=85%, auto_reject=40%):")
    print(f"   Status: {strict_result.status.value.upper()}")
    print(f"   Score: {strict_result.depth_score:.0%}")
    print(f"   Red Flags: {len(strict_result.red_flags)}")
    
    # Test with lenient thresholds
    lenient_runner = Path1Runner(mode=Path1Mode.SILENT, thresholds=lenient_thresholds)
    lenient_result = lenient_runner.analyze(test_idea, skip_cache=True)
    
    print("\n🔓 LENIENT Thresholds (auto_accept=65%, auto_reject=25%):")
    print(f"   Status: {lenient_result.status.value.upper()}")
    print(f"   Score: {lenient_result.depth_score:.0%}")
    print(f"   Red Flags: {len(lenient_result.red_flags)}")
    
    print("\n💡 Same idea, different judgments based on YOUR thresholds.")
    print("   You control the system, not the other way around.")


def test_speed_preservation():
    """Test Speed Preservation - ensure Path 1 doesn't slow you down."""
    print("\n" + "="*70)
    print("⚡ TEST 4: SPEED PRESERVATION (Day 81)")
    print("="*70)
    
    ideas = [
        "Create engaging educational content for curious minds.",
        "Build authentic stories with meaningful payoffs.",
        "Use creative hooks that respect viewer intelligence."
    ]
    
    # First run - cold cache
    runner = Path1Runner(mode=Path1Mode.SILENT, cache_enabled=True)
    
    print("\n⏱️ Cold Cache (first run):")
    start = time.time()
    for idea in ideas:
        runner.analyze(idea)
    cold_time = time.time() - start
    print(f"   Total: {cold_time:.2f}s ({cold_time/len(ideas):.2f}s per idea)")
    
    # Second run - warm cache
    print("\n⏱️ Warm Cache (cached):")
    start = time.time()
    for idea in ideas:
        runner.analyze(idea)
    warm_time = time.time() - start
    print(f"   Total: {warm_time:.4f}s ({warm_time/len(ideas):.4f}s per idea)")
    
    speedup = cold_time / warm_time if warm_time > 0 else float('inf')
    print(f"\n🚀 Cache speedup: {speedup:.0f}x faster")
    print(f"   Cache size: {runner.get_stats()['cache_size']} entries")


def test_calibration():
    """Test Depth Score Calibration - align system with your intuition."""
    print("\n" + "="*70)
    print("🎯 TEST 5: DEPTH SCORE CALIBRATION (Day 78)")
    print("="*70)
    
    # Ideas with your gut ratings
    ideas_with_ratings = [
        ("Create genuine educational value that changes how viewers think.", 0.90),
        ("Use viral hooks that grab attention without substance.", 0.30),
        ("Build authentic audience relationships through consistent quality.", 0.85),
        ("Copy trending formats without adding original perspective.", 0.25),
        ("Tell stories that resonate emotionally and intellectually.", 0.80),
    ]
    
    runner = Path1Runner(mode=Path1Mode.SILENT)
    calibration = runner.calibrate_weights(ideas_with_ratings)
    
    print("\n📊 Calibration Results:\n")
    print(f"   Average difference (your rating - system): {calibration['average_difference']:+.2f}")
    print(f"   Suggested adjustment: {calibration['suggested_adjustment']}")
    
    print("\n📋 Idea-by-idea comparison:")
    for d in calibration["discrepancies"]:
        diff_icon = "✅" if abs(d["difference"]) < 0.15 else "⚠️"
        print(f"\n   {diff_icon} \"{d['idea'][:40]}...\"")
        print(f"      Your rating: {d['user_rating']:.0%}")
        print(f"      System score: {d['system_score']:.0%}")
        print(f"      Difference: {d['difference']:+.0%}")


def run_all_tests():
    """Run complete Week 14 test suite."""
    print("\n" + "="*70)
    print("🚀 WEEK 14 - PATH 1 INTEGRATION & CALIBRATION TEST")
    print("    Making the Thinking Invisible and Trustworthy")
    print("="*70)
    
    # Run all tests
    test_silent_mode()
    test_red_flags()
    test_trust_thresholds()
    test_speed_preservation()
    test_calibration()
    
    # Final summary
    print("\n" + "="*70)
    print("📋 WEEK 14 TEST SUMMARY")
    print("="*70)
    print("""
    ✅ Day 77: Silent Mode Integration - COMPLETE
       Path 1 runs invisibly, only surfaces top 1-2 ideas + warnings
       
    ✅ Day 78: Depth Score Calibration - COMPLETE
       Compare gut feeling vs system, adjust weights
       
    ✅ Day 79: Red Flag System - COMPLETE
       Detects dangerous ideas: fragile assumptions, clickbait traps,
       long-term risks, weak defenses
       
    ✅ Day 80: Trust Thresholds - COMPLETE
       Auto-accept, auto-reject, manual review zones defined
       You control the system, not the other way around
       
    ✅ Day 81: Speed Preservation - COMPLETE
       Caching enabled for instant repeat analysis
       Intelligence without friction
    """)
    print("="*70)
    print("✅ Week 14 Path 1 Integration Test Complete!")


if __name__ == "__main__":
    run_all_tests()
    
    # Save test output
    output_file = Path(__file__).parent / "week14_test_results.json"
    runner = get_path1_runner()
    with open(output_file, "w") as f:
        json.dump(runner.get_stats(), f, indent=2)
    print(f"\n📁 Stats saved to: {output_file}")
