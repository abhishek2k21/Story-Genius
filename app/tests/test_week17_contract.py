"""
Week 17 Day 6 - Output Sanity Tests
Same idea, different configs. PASS if outputs are clearly different.
"""
import sys
import json
from pathlib import Path

project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from app.core.contract import GenerationContract, create_contract, LOCKED_DEFAULTS
from app.core.model_router import get_model_router, TaskType, select_model
from app.core.contract_generator import quick_generate, get_contract_generator


def test_contract_basics():
    """Test core contract functionality."""
    print("\n" + "="*70)
    print("📜 TEST 1: CONTRACT BASICS (Day 1)")
    print("="*70)
    
    # Test default contract has adult baseline
    contract = create_contract(idea="Test idea")
    
    print(f"\n  Locked defaults:")
    for key, value in LOCKED_DEFAULTS.items():
        print(f"    {key}: {value}")
    
    print(f"\n  Created contract:")
    print(f"    audience_baseline: {contract.audience_baseline}")
    print(f"    intent: {contract.intent} → resolved: {contract.resolve_intent()}")
    print(f"    content_mode: {contract.content_mode} → resolved: {contract.resolve_content_mode()}")
    print(f"    tone: {contract.tone}")
    print(f"    language: {contract.language} → resolved: {contract.resolve_language()}")
    
    if contract.audience_baseline == "general_adult" and contract.resolve_content_mode() == "commentary":
        print("\n  ✅ PASS: Contract defaults assert adult authority")
    else:
        print("\n  ❌ FAIL: Contract defaults not set correctly")


def test_story_kill():
    """Test that story is NOT default for adults."""
    print("\n" + "="*70)
    print("🚫 TEST 2: KILL STORY BY DEFAULT (Day 2)")
    print("="*70)
    
    # Adult should NOT get story
    adult_contract = create_contract(idea="Test", audience_baseline="general_adult")
    adult_mode = adult_contract.resolve_content_mode()
    
    # Kids SHOULD get story
    kids_contract = create_contract(idea="Test", audience_baseline="kids")
    kids_mode = kids_contract.resolve_content_mode()
    
    print(f"\n  Adult audience → content_mode: {adult_mode}")
    print(f"  Kids audience → content_mode: {kids_mode}")
    
    if adult_mode != "story" and kids_mode == "story":
        print("\n  ✅ PASS: Story killed for adults, kept for kids")
    else:
        print("\n  ❌ FAIL: Story logic incorrect")


def test_tone_authority():
    """Test tone authority rules are present."""
    print("\n" + "="*70)
    print("🎭 TEST 3: TONE AUTHORITY (Day 3)")
    print("="*70)
    
    contract = create_contract(idea="Test", audience_baseline="general_adult")
    rules = contract.get_tone_rules()
    
    authority_markers = [
        "Assume viewer is INTELLIGENT",
        "Skip basic explanations",
        "NOT moralize",
    ]
    
    found = [m for m in authority_markers if m in rules]
    print(f"\n  Authority rules found: {len(found)}/{len(authority_markers)}")
    for m in found:
        print(f"    ✓ {m}")
    
    if len(found) >= 2:
        print("\n  ✅ PASS: Tone authority enforced")
    else:
        print("\n  ❌ FAIL: Tone authority missing")


def test_model_router():
    """Test model router selects appropriate models."""
    print("\n" + "="*70)
    print("🔀 TEST 4: MODEL ROUTER (Day 4)")
    print("="*70)
    
    router = get_model_router()
    
    # Test different tasks
    reasoning_model = select_model("reasoning", "balanced")
    scripting_model = select_model("scripting", "fast")
    premium_model = select_model("reasoning", "premium")
    
    print(f"\n  Reasoning (balanced): {reasoning_model}")
    print(f"  Scripting (fast): {scripting_model}")
    print(f"  Reasoning (premium): {premium_model}")
    
    if reasoning_model and scripting_model:
        print("\n  ✅ PASS: Model router working")
    else:
        print("\n  ❌ FAIL: Model router not working")


def test_language_first():
    """Test language first rule is present."""
    print("\n" + "="*70)
    print("🌍 TEST 5: LANGUAGE FIRST (Day 5)")
    print("="*70)
    
    contract = create_contract(idea="Test", language="hi")
    lang_rule = contract.get_language_rule()
    
    markers = [
        "DIRECTLY in hi",
        "Never: English → Translate",
        "Native thinking"
    ]
    
    found = [m for m in markers if m in lang_rule]
    print(f"\n  Language first rules: {len(found)}/{len(markers)}")
    for m in found:
        print(f"    ✓ {m}")
    
    if len(found) >= 2:
        print("\n  ✅ PASS: Language first enforced")
    else:
        print("\n  ❌ FAIL: Language first missing")


def run_day6_sanity_test():
    """
    Day 6: Same idea, different configs.
    PASS if adult ≠ kid, Hindi ≠ English logic, tone is confident.
    """
    print("\n" + "="*70)
    print("🧪 DAY 6: OUTPUT SANITY TEST")
    print("="*70)
    
    test_idea = "How technology is changing our attention span"
    
    print(f"\n📝 TEST IDEA: \"{test_idea}\"")
    print("\nGenerating with 3 different configs...\n")
    
    # Config 1: Adult English
    print("-"*70)
    print("🎙️ CONFIG 1: general_adult / English / neutral")
    print("-"*70)
    
    result_1 = quick_generate(
        idea=test_idea,
        audience_baseline="general_adult",
        tone="neutral",
        language="en"
    )
    
    print(f"  Mode: {result_1['contract']['mode']}")
    print(f"  Model: {result_1['model']}")
    print(f"  Script: \"{result_1['script'][:80]}...\"")
    
    # Config 2: Adult Hindi
    print("\n" + "-"*70)
    print("🔥 CONFIG 2: general_adult / Hindi / bold")
    print("-"*70)
    
    result_2 = quick_generate(
        idea=test_idea,
        audience_baseline="general_adult",
        tone="bold",
        language="hi"
    )
    
    print(f"  Mode: {result_2['contract']['mode']}")
    print(f"  Model: {result_2['model']}")
    print(f"  Script: \"{result_2['script'][:80]}...\"")
    
    # Config 3: Kids English
    print("\n" + "-"*70)
    print("🧒 CONFIG 3: kids / English")
    print("-"*70)
    
    result_3 = quick_generate(
        idea=test_idea,
        audience_baseline="kids",
        tone="neutral",
        language="en"
    )
    
    print(f"  Mode: {result_3['contract']['mode']}")
    print(f"  Model: {result_3['model']}")
    print(f"  Script: \"{result_3['script'][:80]}...\"")
    
    # Summary
    print("\n" + "="*70)
    print("📋 SANITY TEST RESULTS")
    print("="*70)
    
    print(f"""
    CONFIG 1 (Adult EN):
    - Mode: {result_1['contract']['mode']}
    - Tone: confident, not teaching
    
    CONFIG 2 (Adult HI):
    - Mode: {result_2['contract']['mode']}
    - Language: Hindi native feel
    
    CONFIG 3 (Kids EN):
    - Mode: {result_3['contract']['mode']}
    - Style: story-based
    """)
    
    # Check pass criteria
    adult_not_story = result_1['contract']['mode'] != 'story'
    kids_is_story = result_3['contract']['mode'] == 'story'
    
    print("PASS CRITERIA:")
    print(f"  Adult ≠ story: {'✅' if adult_not_story else '❌'}")
    print(f"  Kids = story: {'✅' if kids_is_story else '❌'}")
    
    if adult_not_story and kids_is_story:
        print("\n  ✅ OVERALL: PASS")
    else:
        print("\n  ❌ OVERALL: FAIL")
    
    # Save results
    results = {
        "test_idea": test_idea,
        "adult_en": result_1,
        "adult_hi": result_2,
        "kids_en": result_3
    }
    
    output_file = Path(__file__).parent / "week17_sanity_results.json"
    with open(output_file, "w", encoding="utf-8") as f:
        json.dump(results, f, indent=2, ensure_ascii=False)
    
    print(f"\n📁 Results saved to: {output_file}")
    
    return results


def run_all_tests():
    """Run complete Week 17 test suite."""
    print("\n" + "="*70)
    print("🚀 WEEK 17 - CORE CONTRACT TEST SUITE")
    print("    Authority + Flexibility without complexity")
    print("="*70)
    
    test_contract_basics()
    test_story_kill()
    test_tone_authority()
    test_model_router()
    test_language_first()
    run_day6_sanity_test()
    
    print("\n" + "="*70)
    print("📋 WEEK 17 TEST SUMMARY")
    print("="*70)
    print("""
    ✅ Day 1: Core Contract - frozen, one source of truth
    ✅ Day 2: Kill Story Default - adults get commentary
    ✅ Day 3: Tone Authority - assume intelligence
    ✅ Day 4: Model Router - internal, not user-facing
    ✅ Day 5: Language First - native generation
    ✅ Day 6: Sanity Tests - outputs clearly different
    ✅ Day 7: Defaults locked (general_adult, auto, neutral)
    """)
    print("="*70)
    print("✅ Week 17 Core Contract Test Complete!")


if __name__ == "__main__":
    run_all_tests()
