from story_genius.core.abstract_engine import AbstractContentEngine
from story_genius.gui.voice_module import VoiceModule
from story_genius.assets.veo_wrapper import VeoWrapper
from story_genius.core.story_structure import StoryBoard
import json
import concurrent.futures
import os
from moviepy import AudioFileClip, VideoFileClip, concatenate_videoclips

class ThrillerEngine(AbstractContentEngine):
    def __init__(self, llm, voiceModule: VoiceModule):
        super().__init__(content_type="thriller_short", voiceModule=voiceModule)
        self.llm = llm
        self.veo = VeoWrapper()
        self.storyboard = StoryBoard()
        
        self.stepDict = {
            1: self.generate_storyboard,
            2: self.generate_assets_parallel,
            3: self.render_full_video
        }
        
    def generate_storyboard(self):
        print("Designing Thriller content...")
        # Prompt for 1 minute thriller short (Vertical 9:16 aspect ratio usually preferred for Shorts, 
        # but Veo generates landscape. We will crop or center later if needed. For now sticking to standard generation).
        
        prompt = """
        Create a 60-second suspense/thriller Youtube Short script.
        Theme: "The Midnight Caller" or a similar urban legend. 
        Style: Photorealistic, Dark, Cinematic, Suspenseful.
        Break it down into 6 sequential scenes.
        For each scene, provide:
        1. 'script': The narrator's line (Short, punchy, ominous).
        2. 'visual': A detailed visual description for AI video generation (Must encompass "Photorealistic", "Cinematic Lighting", "4k").
        
        Output valid JSON format:
        [
            {"script": "...", "visual": "..."},
            ...
        ]
        """
        try:
            response = self.llm.generate_content(prompt)
            response = response.replace("```json", "").replace("```", "").strip()
            data = json.loads(response)
            
            for item in data:
                self.storyboard.add_scene(item['script'], item['visual'])
                
            print(f"Thriller Storyboard created with {len(self.storyboard.scenes)} scenes.")
            
        except Exception as e:
            print(f"Storyboard Generation Error: {e}")
            # Fallback
            self.storyboard.add_scene("It was a dark night.", "Photorealistic street at night with a flickering street lamp, cinematic.")

    def generate_assets_parallel(self):
        print("Generating Thriller Assets (Audio + Video)...")
        scenes = self.storyboard.to_list()
        
        def process_scene(scene):
            print(f"Processing Scene {scene.id}...")
            
            # 1. Audio
            scene.audio_path = self.dynamicAssetDir + f"scene_{scene.id}_audio.mp3"
            self.voiceModule.generate_voice(scene.script, scene.audio_path)
            
            # 2. Video (Veo)
            scene.video_path = self.dynamicAssetDir + f"scene_{scene.id}_video.mp4"
            
            # Enforce Realism in Prompt
            veo_prompt = f"Cinematic, Photorealistic, 4k, Dark Atmosphere, {scene.visual_description}"
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
        print("Stitching Thriller Reel...")
        try:
            clips = []
            for scene in self.storyboard.to_list():
                if os.path.exists(scene.video_path) and os.path.exists(scene.audio_path):
                    video = VideoFileClip(scene.video_path)
                    audio = AudioFileClip(scene.audio_path)
                    
                    duration = audio.duration
                    
                    # Loop video if audio is longer
                    if duration > video.duration:
                         from math import ceil
                         n = ceil(duration / video.duration)
                         video = concatenate_videoclips([video]*n)
                         video = video.subclipped(0, duration) 
                    else:
                        video = video.subclipped(0, duration)
                    
                    video = video.with_audio(audio)
                    clips.append(video)
                else:
                    print(f"Missing assets for scene {scene.id}, skipping.")
            
            if clips:
                final_video = concatenate_videoclips(clips)
                output_filename = self.dynamicAssetDir + "final_thriller_short.mp4"
                final_video.write_videofile(output_filename, fps=24)
                self._video_output_path = output_filename
                print(f"FINAL THRILLER READY AT: {self._video_output_path}")
            else:
                print("No clips generated.")

        except Exception as e:
            print(f"Render Error: {e}")
            import traceback
            traceback.print_exc()
