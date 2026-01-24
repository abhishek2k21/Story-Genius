"""
Path 1 to Content Generation - End-to-End Pipeline
Runs Path 1 thinking loop → Takes synthesized idea → Generates video content.
"""
import sys
import json
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from app.intelligence.path1_runner import Path1Runner, Path1Mode, TrustThresholds


def run_path1_to_generation(raw_ideas: list, auto_generate: bool = False):
    """
    Complete pipeline: Path 1 thinking → Synthesized idea → Content generation.
    
    Args:
        raw_ideas: List of raw content ideas
        auto_generate: If True, automatically trigger content generation
        
    Returns:
        The best refined idea ready for generation
    """
    print("\n" + "="*70)
    print("🧠 PATH 1 → CONTENT GENERATION PIPELINE")
    print("="*70)
    
    # Step 1: Run Path 1 on all ideas
    print("\n📝 STEP 1: Running Path 1 Thinking Loop...")
    print(f"   Analyzing {len(raw_ideas)} raw ideas...\n")
    
    runner = Path1Runner(mode=Path1Mode.VERBOSE)
    
    results = []
    for i, idea in enumerate(raw_ideas, 1):
        print(f"\n--- Idea {i}/{len(raw_ideas)} ---")
        print(f"Original: \"{idea}\"")
        result = runner.analyze(idea)
        results.append(result)
        
        print(f"Status: {result.status.value.upper()}")
        print(f"Depth Score: {result.depth_score:.0%}")
        if result.red_flags:
            print(f"⚠️ Red Flags: {len(result.red_flags)}")
            for rf in result.red_flags[:2]:
                print(f"   → {rf.flag_type}: {rf.reason[:50]}...")
        print(f"✨ Refined: \"{result.refined_idea[:80]}...\"")
    
    # Step 2: Select the best idea
    print("\n" + "-"*70)
    print("\n🏆 STEP 2: Selecting Best Idea...")
    
    # Filter out dangerous/rejected ideas
    viable = [r for r in results if r.status.value not in ['danger', 'rejected']]
    
    if not viable:
        print("⚠️ No ideas passed the safety filter. Using highest-scoring anyway...")
        viable = sorted(results, key=lambda r: r.depth_score, reverse=True)
    else:
        viable = sorted(viable, key=lambda r: r.depth_score, reverse=True)
    
    best = viable[0]
    
    print(f"\n✅ SELECTED IDEA:")
    print(f"   Original:  \"{best.idea}\"")
    print(f"   Refined:   \"{best.refined_idea}\"")
    print(f"   Score:     {best.depth_score:.0%}")
    print(f"   Status:    {best.status.value.upper()}")
    
    # Step 3: Feed into content generation
    print("\n" + "-"*70)
    print("\n🎬 STEP 3: Content Generation Ready")
    print(f"\n   The synthesized idea is ready to feed into StoryGenius:")
    print(f"   \"{best.refined_idea}\"")
    
    if auto_generate:
        print("\n🚀 Starting content generation...")
        run_content_generation(best.refined_idea)
    else:
        print("\n📋 To generate content, run:")
        print(f"   python StoryGenius/run_story_genius.py")
        print(f"   And use this topic: \"{best.refined_idea[:50]}...\"")
    
    return best


def run_content_generation(refined_idea: str, genre: str = "1", scenes: int = 3):
    """
    Run the actual content generation with the refined idea.
    
    Args:
        refined_idea: The Path 1 synthesized idea
        genre: Genre preset (1 = Kids)
        scenes: Number of scenes (3 = 30s)
    """
    print("\n" + "="*70)
    print("🎬 CONTENT GENERATION")
    print("="*70)
    
    # Change to StoryGenius directory for imports
    import os
    story_genius_path = project_root / "StoryGenius"
    sys.path.insert(0, str(story_genius_path))
    os.chdir(story_genius_path)
    
    try:
        from story_genius.engines.universal_engine import UniversalStoryEngine
        from story_genius.audio.edge_tts_module import EdgeTTSVoiceModule
        from story_genius.llm.vertex_wrapper import VertexLLM
        from story_genius.config.genre_presets import GENRE_PRESETS
        
        print(f"\n[1/4] Topic from Path 1: \"{refined_idea[:60]}...\"")
        
        # Initialize
        print("\n[2/4] Initializing AI Cores...")
        llm = VertexLLM()
        
        # Get genre config
        selected_genre = GENRE_PRESETS.get(genre, GENRE_PRESETS["1"])
        print(f"   Genre: {selected_genre.name}")
        
        # Initialize voice and engine
        voice = EdgeTTSVoiceModule(selected_genre.default_voice)
        engine = UniversalStoryEngine(llm, voice, selected_genre, duration_scenes=scenes)
        
        # Inject the refined idea into the engine's prompt
        # We modify the config's llm_prompt_style to include our topic
        original_style = selected_genre.llm_prompt_style
        selected_genre.llm_prompt_style = f"{original_style}\n\nTOPIC/THEME: {refined_idea}"
        
        print(f"\n[3/4] Generating {scenes} scenes for: {selected_genre.name}")
        print(f"   Injected Topic: \"{refined_idea[:50]}...\"")
        
        # Run generation
        print("\n[4/4] Running content pipeline...\n")
        for step, msg in engine.makeContent():
            print(f"   {msg}")
        
        output_path = engine.get_video_output_path()
        print(f"\n✅ CONTENT GENERATED!")
        print(f"   Output: {output_path}")
        
        return output_path
        
    except Exception as e:
        print(f"\n❌ Generation failed: {e}")
        import traceback
        traceback.print_exc()
        return None


if __name__ == "__main__":
    # Sample ideas to test the full pipeline
    raw_ideas = [
        "A curious Indian kid discovers a magical flute that brings animals to life.",
        "Short-form hooks that use extreme cliffhangers for maximum retention.",
        "Educational content about dinosaurs that makes learning fun for kids.",
    ]
    
    print("\n🚀 PATH 1 → GENERATION DEMO")
    print("Testing end-to-end: Raw ideas → Path 1 analysis → Content creation\n")
    
    # Run Path 1 and get the best synthesized idea
    best_result = run_path1_to_generation(raw_ideas, auto_generate=False)
    
    # Ask user if they want to generate
    print("\n" + "="*70)
    user_input = input("\n🎬 Generate content with this idea? (y/n): ").strip().lower()
    
    if user_input == 'y':
        run_content_generation(best_result.refined_idea, genre="1", scenes=3)
    else:
        print("\n📋 Saved refined idea for later use.")
        # Save to file for later
        output_file = Path(__file__).parent / "path1_to_gen_output.json"
        with open(output_file, "w") as f:
            json.dump({
                "original_idea": best_result.idea,
                "refined_idea": best_result.refined_idea,
                "depth_score": best_result.depth_score,
                "status": best_result.status.value
            }, f, indent=2)
        print(f"   Saved to: {output_file}")
    
    print("\n✅ Pipeline complete!")
