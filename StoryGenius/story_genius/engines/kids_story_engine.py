from story_genius.core.abstract_engine import AbstractContentEngine
from story_genius.gui.voice_module import VoiceModule
import os

from story_genius.assets.veo_wrapper import VeoWrapper

from story_genius.assets.veo_wrapper import VeoWrapper
from story_genius.core.story_structure import StoryBoard
import json
import concurrent.futures
import time
import os

class KidsStoryEngine(AbstractContentEngine):
    def __init__(self, llm, voiceModule: VoiceModule):
        super().__init__(content_type="kids_story", voiceModule=voiceModule)
        self.llm = llm
        self.veo = VeoWrapper()
        self.storyboard = StoryBoard()
        
        self.stepDict = {
            1: self.generate_storyboard,
            2: self.generate_assets_parallel,
            3: self.render_full_video
        }
        
    def generate_storyboard(self):
        print("Designing story content (Storyboard)...")
        # Prompt for 1 minute story (approx 4-5 scenes of 8-10 seconds)
        # Theme: Indian kid
        # Prompt for 2 minute story (approx 12 scenes of 10 seconds)
        # Theme: Indian kid, Hinglish language
        prompt = """
        Create a 120-second kids' story about an Indian boy named 'Aarav' and his friends.
        Language: Hinglish (Mix of English and Hindi). Use simple Hindi words naturally (like 'dost', 'khelna', 'chalo', 'mazza aaya').
        Break it down into 12 sequential scenes.
        For each scene, provide:
        1. 'script': The narrator's line in Hinglish (approx 20-30 words, 10 seconds).
        2. 'visual': A detailed visual description for AI video generation (Keep it descriptive: "Aarav and friends playing cricket in a dusty maidan, sunset light...").
        
        Output valid JSON format:
        [
            {"script": "...", "visual": "..."},
            ...
        ]
        """
        try:
            response = self.llm.generate_content(prompt)
            # Simple cleanup for JSON parsing if LLM adds backticks
            response = response.replace("```json", "").replace("```", "").strip()
            data = json.loads(response)
            
            for item in data:
                self.storyboard.add_scene(item['script'], item['visual'])
                
            print(f"Storyboard created with {len(self.storyboard.scenes)} scenes.")
            
        except Exception as e:
            print(f"Storyboard Generation Error: {e}")
            # Fallback
            self.storyboard.add_scene("Aarav found a flute.", "A cute Indian boy holding a wooden flute in a village.")
            self.storyboard.add_scene("He played a tune.", "The boy playing the flute under a banyan tree.")

    def generate_assets_parallel(self):
        print("Generating Assets in Parallel (Audio + Video)...")
        
        scenes = self.storyboard.to_list()
        
        # We can run Audio gen in parallel and Video gen in parallel.
        # Video is blocking/slow, so threading helps if APIs allow concurrency.
        # Since we use 'google-genai' with a client instance, usage might be thread-safe or we create new clients.
        # VeoWrapper uses one client. Ideally we might want instances per thread or just rely on its thread-safety.
        
        def process_scene(scene):
            print(f"Processing Scene {scene.id}...")
            
            # 1. Audio
            scene.audio_path = self.dynamicAssetDir + f"scene_{scene.id}_audio.mp3"
            self.voiceModule.generate_voice(scene.script, scene.audio_path)
            
            # 2. Video (Veo)
            scene.video_path = self.dynamicAssetDir + f"scene_{scene.id}_video.mp4"
            # Enhance prompt with consistent character description if not present?
            # User asked for 'doubly linked list type things' for context awareness.
            # We can prepend previous scene context if needed, but Veo is clip-based.
            # We trust the storyboard visual prompt.
            
            veo_prompt = f"Animation, {scene.visual_description}, 4k, disney style"
            self.veo.generate_video(veo_prompt, scene.video_path)
            
            return scene

        with concurrent.futures.ThreadPoolExecutor(max_workers=4) as executor:
            futures = [executor.submit(process_scene, scene) for scene in scenes]
            for future in concurrent.futures.as_completed(futures):
                try:
                    s = future.result()
                    print(f"Scene {s.id} assets ready.")
                except Exception as e:
                    print(f"Scene processing failed: {e}")

    def render_full_video(self):
        print("Stitching final video...")
        try:
            from moviepy import AudioFileClip, VideoFileClip, concatenate_videoclips


            clips = []
            for scene in self.storyboard.to_list():
                if os.path.exists(scene.video_path) and os.path.exists(scene.audio_path):
                    # Load Video
                    video = VideoFileClip(scene.video_path)
                    
                    # Load Audio
                    audio = AudioFileClip(scene.audio_path)
                    
                    # Sync Logic:
                    # If audio is longer, we loop video or hold last frame?
                    # Veo clips are ~8s. Script might be 8s.
                    # Best: Loop video to match audio duration.
                    
                    duration = audio.duration
                    
                    # Loop video using vfx (Safe for v1 and v2 potentially, or manual)
                    # Simple repetition logic:
                    if duration > video.duration:
                         # Calculate n_loops
                         from math import ceil
                         n = ceil(duration / video.duration)
                         video = concatenate_videoclips([video]*n)
                         video = video.subclipped(0, duration) # Trim to exact audio length
                    else:
                        video = video.subclipped(0, duration)
                    
                    video = video.with_audio(audio)
                    clips.append(video)
                else:
                    print(f"Missing assets for scene {scene.id}, skipping.")
            
            if clips:
                final_video = concatenate_videoclips(clips)
                output_filename = self.dynamicAssetDir + "final_story_movie.mp4"
                final_video.write_videofile(output_filename, fps=24)
                self._video_output_path = output_filename
                print(f"FINAL MOVIE READY AT: {self._video_output_path}")
            else:
                print("No clips generated.")

        except Exception as e:
            print(f"Render Error: {e}")
            import traceback
            traceback.print_exc()
