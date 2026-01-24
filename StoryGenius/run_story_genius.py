from story_genius.engines.kids_story_engine import KidsStoryEngine
from story_genius.audio.edge_tts_module import EdgeTTSVoiceModule
from story_genius.llm.vertex_wrapper import VertexLLM
import os

def main():
    print("==========================================")
    print("   StoryGenius - Universal Content Studio")
    print("==========================================")
    
    # 1. Initialize
    print("\n[1/4] Initializing AI Cores...")
    llm = VertexLLM()
    
    # 2. Select Genre
    from story_genius.config.genre_presets import GENRE_PRESETS
    
    print("\n[2/4] Select Content Type:")
    for key, config in GENRE_PRESETS.items():
        print(f"  {key}. {config.name}")
        
    genre_choice = input("\nEnter Choice (1-10): ")
    if genre_choice not in GENRE_PRESETS:
        genre_choice = "1" # Default to Kids
    
    selected_genre = GENRE_PRESETS[genre_choice]
    print(f"Selected: {selected_genre.name}")
    
    # 3. Select Duration
    print("\n[3/4] Select Duration:")
    print("  1. Short (30s)")
    print("  2. Standard (60s)")
    print("  3. Extended (120s)")
    
    dur_choice = input("Enter Choice (1-3): ")
    scenes = 6 # Default
    if dur_choice == "1": scenes = 3
    elif dur_choice == "2": scenes = 6
    elif dur_choice == "3": scenes = 12
    
    # 4. Input Topic
    topic = input("\n[4/4] Enter Story Topic/Idea: ")
    if not topic: topic = "A surprise adventure"
    
    # Optional: Voice Override (Advanced)
    # user_voice = input(f"Voice [{selected_genre.default_voice}]: ")
    # if not user_voice: user_voice = selected_genre.default_voice
    
    # Initialize Engine
    print("\nStarting Production...")
    from story_genius.engines.universal_engine import UniversalStoryEngine
    
    voice = EdgeTTSVoiceModule(selected_genre.default_voice)
    engine = UniversalStoryEngine(llm, voice, selected_genre, duration_scenes=scenes)
    
    # Run
    print(f"Generative Engine Active: {selected_genre.name} | {scenes} Scenes | {topic}")
    for step, msg in engine.makeContent():
        print(f"{msg}")
        
    print(f"\nDONE. Output: {engine.get_video_output_path()}")

if __name__ == "__main__":
    main()
