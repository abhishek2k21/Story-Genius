"""
Video Service
Handles video generation (Veo) and final video stitching (FFmpeg/MoviePy).
"""
import os
import uuid
import sys
from pathlib import Path
from typing import List, Optional

# Add StoryGenius to path
STORYGENIUS_PATH = Path(__file__).parent.parent.parent / "StoryGenius"
sys.path.insert(0, str(STORYGENIUS_PATH))

from app.core.config import settings
from app.core.models import Scene
from app.core.logging import get_logger

logger = get_logger(__name__)


class VideoService:
    """
    Video generation and stitching service.
    """
    
    def __init__(self):
        self._veo = None
    
    def _get_veo(self):
        """Lazy load Veo wrapper."""
        if self._veo is None:
            try:
                from story_genius.assets.veo_wrapper import VeoWrapper
                self._veo = VeoWrapper()
            except Exception as e:
                logger.error(f"Failed to initialize Veo: {e}")
                raise
        return self._veo
    
    def generate_video_clip(
        self,
        prompt: str,
        output_path: str = None,
        scene_id: Optional[str] = None,
        style_prefix: str = ""
    ) -> str:
        """
        Generate video clip from prompt using Veo.
        
        Args:
            prompt: Visual description for video generation
            output_path: Optional output file path
            scene_id: Optional scene ID for naming
            style_prefix: Style prefix to add to prompt
            
        Returns:
            Path to generated video file
        """
        if not output_path:
            filename = f"clip_{scene_id or uuid.uuid4()}.mp4"
            output_path = str(settings.MEDIA_DIR / filename)
        
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        
        full_prompt = f"{style_prefix}, {prompt}" if style_prefix else prompt
        
        veo = self._get_veo()
        
        try:
            veo.generate_video(full_prompt, output_path)
            logger.info(f"Generated video clip: {output_path}")
            return output_path
        except Exception as e:
            logger.error(f"Video clip generation failed: {e}")
            raise
    
    def stitch_video(
        self,
        scenes: List[Scene],
        output_path: str = None,
        job_id: Optional[str] = None
    ) -> str:
        """
        Stitch scene videos with audio into final video.
        
        Args:
            scenes: List of scenes with video_path and audio_path
            output_path: Optional output file path
            job_id: Optional job ID for naming
            
        Returns:
            Path to final stitched video
        """
        if not output_path:
            filename = f"final_{job_id or uuid.uuid4()}.mp4"
            output_path = str(settings.MEDIA_DIR / filename)
        
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        
        try:
            from moviepy import AudioFileClip, VideoFileClip, concatenate_videoclips, vfx
            
            clips = []
            
            for scene in scenes:
                if not scene.video_path or not os.path.exists(scene.video_path):
                    logger.warning(f"Missing video for scene {scene.id}")
                    continue
                    
                video = VideoFileClip(scene.video_path)
                
                # Add audio if available
                if scene.audio_path and os.path.exists(scene.audio_path):
                    audio = AudioFileClip(scene.audio_path)
                    duration = audio.duration
                    
                    # Sync video duration to audio
                    if duration > video.duration:
                        # Slow down video to match audio
                        factor = video.duration / duration
                        logger.info(f"Scene {scene.id}: Extending video {video.duration:.1f}s → {duration:.1f}s")
                        video = video.with_effects([vfx.MultiplySpeed(factor)])
                    else:
                        # Trim video to match audio
                        logger.info(f"Scene {scene.id}: Trimming video {video.duration:.1f}s → {duration:.1f}s")
                        video = video.subclipped(0, duration)
                    
                    video = video.with_audio(audio)
                
                clips.append(video)
            
            if not clips:
                raise ValueError("No valid clips to stitch")
            
            # Concatenate all clips
            final_video = concatenate_videoclips(clips)
            
            # Write to 9:16 vertical format
            final_video.write_videofile(
                output_path,
                fps=24,
                codec='libx264',
                audio_codec='aac'
            )
            
            logger.info(f"Stitched final video: {output_path}")
            return output_path
            
        except Exception as e:
            logger.error(f"Video stitching failed: {e}")
            raise
    
    def create_shorts_video(
        self,
        scenes: List[Scene],
        job_id: str,
        style_prefix: str = ""
    ) -> str:
        """
        Complete workflow: generate clips for each scene and stitch.
        
        Args:
            scenes: List of scenes with narration and visual prompts
            job_id: Job ID for naming
            style_prefix: Visual style prefix for Veo
            
        Returns:
            Path to final video
        """
        logger.info(f"Creating shorts video for job {job_id[:8]} with {len(scenes)} scenes")
        
        # Generate video clip for each scene (could be parallelized later)
        for scene in scenes:
            scene.video_path = self.generate_video_clip(
                prompt=scene.visual_prompt,
                scene_id=str(scene.id),
                style_prefix=style_prefix
            )
        
        # Stitch all clips together
        output_path = self.stitch_video(scenes, job_id=job_id)
        
        return output_path
