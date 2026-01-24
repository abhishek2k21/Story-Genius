"""
Audio Service
Wraps the existing EdgeTTS voice module for audio generation.
"""
import os
import uuid
import sys
from pathlib import Path
from typing import Optional

# Add StoryGenius to path
STORYGENIUS_PATH = Path(__file__).parent.parent.parent / "StoryGenius"
sys.path.insert(0, str(STORYGENIUS_PATH))

from app.core.config import settings
from app.core.logging import get_logger

logger = get_logger(__name__)


class AudioService:
    """
    Audio generation service using EdgeTTS.
    """
    
    def __init__(self, voice: str = None):
        """
        Initialize audio service.
        
        Args:
            voice: TTS voice ID (default: settings.DEFAULT_VOICE)
        """
        self.voice = voice or settings.DEFAULT_VOICE
        self._voice_module = None
    
    def _get_voice_module(self):
        """Lazy load voice module."""
        if self._voice_module is None:
            try:
                from story_genius.audio.edge_tts_module import EdgeTTSVoiceModule
                self._voice_module = EdgeTTSVoiceModule(self.voice)
            except Exception as e:
                logger.error(f"Failed to initialize voice module: {e}")
                raise
        return self._voice_module
    
    def generate_audio(
        self,
        text: str,
        output_path: str = None,
        scene_id: Optional[str] = None
    ) -> str:
        """
        Generate audio from text using TTS.
        
        Args:
            text: Narration text to convert to speech
            output_path: Optional output file path
            scene_id: Optional scene ID for naming
            
        Returns:
            Path to generated audio file
        """
        if not output_path:
            filename = f"audio_{scene_id or uuid.uuid4()}.mp3"
            output_path = str(settings.MEDIA_DIR / filename)
        
        # Ensure directory exists
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        
        voice_module = self._get_voice_module()
        
        try:
            voice_module.generate_voice(text, output_path)
            logger.info(f"Generated audio: {output_path}")
            return output_path
        except Exception as e:
            logger.error(f"Audio generation failed: {e}")
            raise
    
    def set_voice(self, voice_id: str):
        """Change the TTS voice."""
        self.voice = voice_id
        self._voice_module = None  # Reset to reload with new voice
