from story_genius.core.abstract_engine import AbstractContentEngine
from story_genius.gui.voice_module import VoiceModule
from story_genius.assets.veo_wrapper import VeoWrapper
from story_genius.core.story_structure import StoryBoard
from story_genius.config.genre_presets import GenreConfig
import json
import concurrent.futures
import os
from moviepy import AudioFileClip, VideoFileClip, concatenate_videoclips

class UniversalStoryEngine(AbstractContentEngine):
    def __init__(self, llm, voiceModule: VoiceModule, genre_config: GenreConfig, duration_scenes: int = 6, topic: str = ""):
        super().__init__(content_type=f"universal_{genre_config.id}", voiceModule=voiceModule)
        self.llm = llm
        self.veo = VeoWrapper()
        self.storyboard = StoryBoard()
        self.config = genre_config
        self.target_scenes = duration_scenes
        self.topic = topic  # Store the user's topic
        
        # Override output path suffix
        self.content_type = genre_config.output_suffix
        
        self.stepDict = {
            1: self.generate_storyboard,
            2: self.generate_assets_parallel,
            3: self.render_full_video
        }
        
    def generate_storyboard(self):
        print(f"Designing {self.config.name} content (Target: {self.target_scenes} scenes)...")
        
        # Determine total duration
        total_seconds = self.target_scenes * 10
        
        # Build topic instruction
        topic_instruction = f"\nTOPIC: {self.topic}\nCreate content specifically about: {self.topic}\n" if self.topic else ""
        
        prompt = f"""
        Create a {total_seconds}-second video script.
        Genre: {self.config.name}
        Style: {self.config.description}
        {topic_instruction}
        Task: {self.config.llm_prompt_style}
        
        IMPORTANT: The story MUST be about "{self.topic}". Every scene should relate to this topic.
        
        Break it down into {self.target_scenes} sequential scenes.
        For each scene, provide:
        1. 'script': The narrator's line (Keep it SHORT, max 15 words, approx 5-7 seconds).
        2. 'visual': A detailed visual description for AI video generation. MUST include the main subject ({self.topic}).
        
        Output valid JSON format:
        [
            {{"script": "...", "visual": "..."}},
            ...
        ]
        """
        try:
            response = self.llm.generate_content(prompt)
            response = response.replace("```json", "").replace("```", "").strip()
            data = json.loads(response)
            
            for item in data:
                self.storyboard.add_scene(item['script'], item['visual'])
                
            print(f"Storyboard created with {len(self.storyboard.scenes)} scenes.")
            
        except Exception as e:
            print(f"Storyboard Generation Error: {e}")
            self.storyboard.add_scene("Error in generation.", "Static error screen.")

    def generate_assets_parallel(self):
        print(f"Generating Assets for {self.config.id} (Audio + Video)...")
        scenes = self.storyboard.to_list()
        
        def process_scene(scene):
            print(f"Processing Scene {scene.id}...")
            
            # 1. Audio
            scene.audio_path = self.dynamicAssetDir + f"scene_{scene.id}_audio.mp3"
            self.voiceModule.generate_voice(scene.script, scene.audio_path)
            
            # 2. Video (Veo)
            scene.video_path = self.dynamicAssetDir + f"scene_{scene.id}_video.mp4"
            
            # Prefix the Veo prompt with the genre style
            veo_prompt = f"{self.config.veo_style_prefix}, {scene.visual_description}"
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
        print(f"Stitching {self.config.name} Video...")
        try:
            clips = []
            from moviepy import AudioFileClip, VideoFileClip, concatenate_videoclips, vfx
            
            for scene in self.storyboard.to_list():
                if os.path.exists(scene.video_path) and os.path.exists(scene.audio_path):
                    video = VideoFileClip(scene.video_path)
                    audio = AudioFileClip(scene.audio_path)
                    
                    # Sync Logic: Time Stretch (Smarter than Loop)
                    # We want video duration to MATCH audio duration exactly.
                    duration = audio.duration
                    
                    if duration > video.duration:
                         # Video is too short. Slow it down to fit.
                         # Factor < 1.0 means slow down.
                         factor = video.duration / duration
                         print(f"  - Scene {scene.id}: Extending video {video.duration}s -> {duration}s (Speed: {factor:.2f}x)")
                         video = video.with_effects([vfx.MultiplySpeed(factor)])
                    else:
                        # Video is too long. Trim it.
                        print(f"  - Scene {scene.id}: Trimming video {video.duration}s -> {duration}s")
                        video = video.subclipped(0, duration)
                    
                    video = video.with_audio(audio)
                    clips.append(video)
                else:
                    print(f"Missing assets for scene {scene.id}, skipping.")
            
            if clips:
                final_video = concatenate_videoclips(clips)
                output_filename = self.dynamicAssetDir + f"final_{self.config.output_suffix}.mp4"
                final_video.write_videofile(output_filename, fps=24)
                self._video_output_path = output_filename
                print(f"FINAL VIDEO READY AT: {self._video_output_path}")
            else:
                print("No clips generated.")

        except Exception as e:
            print(f"Render Error: {e}")
            import traceback
            traceback.print_exc()
