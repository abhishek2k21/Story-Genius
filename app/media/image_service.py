"""
Image Service
Wraps the existing Imagen wrapper for image generation.
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


class ImageService:
    """
    Image generation service using Imagen.
    """
    
    def __init__(self):
        self._imagen = None
    
    def _get_imagen(self):
        """Lazy load Imagen wrapper."""
        if self._imagen is None:
            try:
                from story_genius.assets.imagen_wrapper import ImagenWrapper
                self._imagen = ImagenWrapper()
            except Exception as e:
                logger.error(f"Failed to initialize Imagen: {e}")
                raise
        return self._imagen
    
    def generate_image(
        self,
        prompt: str,
        output_path: str = None,
        scene_id: Optional[str] = None,
        style_prefix: str = ""
    ) -> str:
        """
        Generate image from prompt.
        
        Args:
            prompt: Visual description for image generation
            output_path: Optional output file path
            scene_id: Optional scene ID for naming
            style_prefix: Style prefix to add to prompt
            
        Returns:
            Path to generated image file
        """
        if not output_path:
            filename = f"image_{scene_id or uuid.uuid4()}.png"
            output_path = str(settings.MEDIA_DIR / filename)
        
        # Ensure directory exists
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        
        # Combine style prefix with prompt
        full_prompt = f"{style_prefix}, {prompt}" if style_prefix else prompt
        
        imagen = self._get_imagen()
        
        try:
            imagen.generate_image(full_prompt, output_path)
            logger.info(f"Generated image: {output_path}")
            return output_path
        except Exception as e:
            logger.error(f"Image generation failed: {e}")
            raise
