"""
Week 13 - Path 1 Thinking Loop Test
Demonstrates the full thinking pipeline:
Idea → Assumptions → Counter-Arguments → Second-Order Effects → Depth Score → Synthesis
"""
import sys
import json
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from app.intelligence.assumptions import get_assumption_extractor
from app.intelligence.counter import get_counter_engine
from app.intelligence.second_order import get_second_order_checker
from app.intelligence.depth_scorer import get_depth_scorer
from app.intelligence.synthesis import get_synthesis_engine


def run_path1_loop(idea: str, verbose: bool = True) -> dict:
    """
    Run the complete Path 1 thinking loop on an idea.
    
    Steps:
    1. Extract hidden assumptions
    2. Generate counter-arguments
    3. Analyze second-order effects
    4. Score idea depth
    5. Synthesize a stronger version
    
    Args:
        idea: Raw idea to analyze and refine
        verbose: Print detailed output
        
    Returns:
        Complete analysis result
    """
    print("\n" + "="*70)
    print("🧠 PATH 1 THINKING LOOP - Week 13")
    print("="*70)
    print(f"\n📝 INPUT IDEA:\n{idea}")
    print("\n" + "-"*70)
    
    result = {"input_idea": idea}
    
    # Step 1: Extract Assumptions
    print("\n🔍 STEP 1: EXTRACTING HIDDEN ASSUMPTIONS...")
    extractor = get_assumption_extractor()
    assumptions = extractor.extract_assumptions(idea)
    result["assumptions"] = assumptions.to_dict()
    
    if verbose:
        print("\n  Hidden Assumptions Found:")
        for i, a in enumerate(assumptions.assumptions, 1):
            conf = assumptions.confidence_scores.get(a, 0.5)
            print(f"    {i}. {a} (confidence: {conf:.0%})")
        if assumptions.fragile_assumptions:
            print("\n  ⚠️ Most Fragile Assumptions:")
            for a in assumptions.fragile_assumptions:
                print(f"    - {a}")
    
    # Step 2: Generate Counter-Arguments
    print("\n" + "-"*70)
    print("\n⚔️ STEP 2: GENERATING COUNTER-ARGUMENTS...")
    counter_engine = get_counter_engine()
    counters = counter_engine.generate_counter_arguments(idea)
    result["counters"] = counters.to_dict()
    
    if verbose:
        print("\n  Counter-Arguments:")
        for i, c in enumerate(counters.counter_arguments, 1):
            print(f"    {i}. {c}")
        print(f"\n  💀 Strongest Counter:\n    \"{counters.strongest_counter}\"")
        print(f"\n  🎯 Survival Likelihood: {counters.survival_likelihood:.0%}")
    
    # Step 3: Analyze Second-Order Effects
    print("\n" + "-"*70)
    print("\n🌊 STEP 3: ANALYZING SECOND-ORDER EFFECTS...")
    so_checker = get_second_order_checker()
    second_order = so_checker.analyze_second_order_effects(idea)
    result["second_order"] = second_order.to_dict()
    
    if verbose:
        print("\n  What Happens After Success:")
        for i, effect in enumerate(second_order.second_order_effects, 1):
            print(f"    {i}. {effect}")
        print("\n  ➕ Positive Effects:")
        for p in second_order.positive_effects:
            print(f"    + {p}")
        print("\n  ➖ Negative Effects:")
        for n in second_order.negative_effects:
            print(f"    - {n}")
        print(f"\n  📊 Long-Term Risk Score: {second_order.long_term_risk_score:.0%}")
        print(f"\n  👥 Audience Conditioning:\n    \"{second_order.audience_conditioning}\"")
    
    # Step 4: Score Idea Depth
    print("\n" + "-"*70)
    print("\n📊 STEP 4: SCORING IDEA DEPTH...")
    scorer = get_depth_scorer()
    depth_score = scorer.score_idea_depth(idea)
    result["depth_score"] = depth_score.to_dict()
    
    if verbose:
        print("\n  Depth Score Breakdown:")
        print(f"    📖 Conceptual Depth:   {depth_score.depth:.0%}")
        print(f"    🛡️ Robustness:         {depth_score.robustness:.0%}")
        print(f"    ✨ Novelty:            {depth_score.novelty:.0%}")
        print(f"    📈 Long-Term Value:    {depth_score.long_term_value:.0%}")
        print(f"\n    ⭐ OVERALL SCORE:      {depth_score.overall_score:.0%}")
        print(f"\n    💬 Explanation:\n    \"{depth_score.rank_explanation}\"")
    
    # Step 5: Synthesize Stronger Idea
    print("\n" + "-"*70)
    print("\n🔧 STEP 5: SYNTHESIZING STRONGER IDEA...")
    synthesizer = get_synthesis_engine()
    synthesis = synthesizer.synthesize_stronger_idea(
        original=idea,
        assumptions=assumptions.assumptions,
        counters=counters.counter_arguments,
        second_order=second_order.second_order_effects
    )
    result["synthesis"] = synthesis.to_dict()
    
    if verbose:
        print("\n  ✅ REFINED IDEA:")
        print(f"    \"{synthesis.refined_idea}\"")
        print("\n  Improvements Made:")
        for imp in synthesis.improvements_made:
            print(f"    ✓ {imp}")
        print(f"\n  💪 Confidence Boost: +{synthesis.confidence_boost:.0%}")
    
    # Final Summary
    print("\n" + "="*70)
    print("📋 FINAL SUMMARY")
    print("="*70)
    print(f"\n  Original Idea:  {idea[:60]}...")
    print(f"  Depth Score:    {depth_score.overall_score:.0%}")
    print(f"  Survival Rate:  {counters.survival_likelihood:.0%}")
    print(f"  Long-Term Risk: {second_order.long_term_risk_score:.0%}")
    print(f"\n  🚀 Refined Output:")
    print(f"    \"{synthesis.refined_idea}\"")
    print("\n" + "="*70)
    
    return result


def run_batch_ideas(ideas: list) -> list:
    """Run Path 1 loop on multiple ideas and rank them."""
    print("\n" + "="*70)
    print("🎯 BATCH IDEA ANALYSIS - Running 5 Ideas Through the Loop")
    print("="*70)
    
    results = []
    for i, idea in enumerate(ideas, 1):
        print(f"\n\n>>> ANALYZING IDEA {i}/{len(ideas)} <<<")
        result = run_path1_loop(idea, verbose=True)
        results.append(result)
    
    # Rank by depth score
    print("\n\n" + "="*70)
    print("🏆 FINAL RANKING BY DEPTH SCORE")
    print("="*70)
    
    ranked = sorted(results, key=lambda r: r["depth_score"]["overall_score"], reverse=True)
    for i, r in enumerate(ranked, 1):
        score = r["depth_score"]["overall_score"]
        idea = r["input_idea"][:50]
        print(f"\n  #{i}: {score:.0%} - \"{idea}...\"")
        print(f"      Refined: \"{r['synthesis']['refined_idea'][:60]}...\"")
    
    return ranked


if __name__ == "__main__":
    # Sample ideas for testing
    test_ideas = [
        "Short-form curiosity hooks work best for kids educational content.",
        "Using extreme cliffhangers will maximize video retention.",
        "AI-generated voices are indistinguishable from human narration now.",
        "Posting 3 shorts per day is the optimal frequency for channel growth.",
        "Thumbnail faces with exaggerated expressions always get more clicks."
    ]
    
    print("\n🚀 WEEK 13 - PATH 1 THINKING MODULES TEST")
    print("Testing the complete idea refinement pipeline\n")
    
    # Option 1: Test single idea
    print("\n" + "="*70)
    print("SINGLE IDEA TEST")
    print("="*70)
    single_result = run_path1_loop(test_ideas[0])
    
    # Option 2: Run batch with all 5 ideas
    print("\n\n")
    batch_results = run_batch_ideas(test_ideas)
    
    # Save results to file
    output_file = Path(__file__).parent / "path1_test_results.json"
    with open(output_file, "w") as f:
        json.dump(batch_results, f, indent=2)
    
    print(f"\n\n📁 Results saved to: {output_file}")
    print("\n✅ Week 13 Path 1 Modules Test Complete!")
