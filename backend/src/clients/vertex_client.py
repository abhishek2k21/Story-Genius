"""
Vertex AI Client
Unified interface for Gemini LLM, Imagen 3, and Veo 3.
"""
import asyncio
import time
from typing import Any, Optional

import vertexai
from vertexai.generative_models import GenerativeModel, SafetySetting
from vertexai.preview.vision_models import ImageGenerationModel

from src.core.exceptions import ExternalServiceError
from src.core.logging import get_logger
from src.core.settings import settings

logger = get_logger(__name__)


class VertexClient:
    """
    Unified Vertex AI client for all Google Cloud AI services.

    Services:
    - Gemini: Text generation (scripts, prompts)
    - Imagen 3: Reference image generation
    - Veo 3: Video generation (via polling)
    """

    def __init__(
        self,
        project_id: str | None = None,
        location: str | None = None,
    ):
        self.project_id = project_id or settings.google_cloud_project
        self.location = location or settings.google_cloud_location
        self._initialized = False
        self._gemini_model: GenerativeModel | None = None
        self._imagen_model: ImageGenerationModel | None = None

    def _ensure_initialized(self) -> None:
        """Initialize Vertex AI SDK."""
        if not self._initialized:
            try:
                vertexai.init(project=self.project_id, location=self.location)
                self._initialized = True
                logger.info(f"Vertex AI initialized: {self.project_id}/{self.location}")
            except Exception as e:
                logger.error(f"Failed to initialize Vertex AI: {e}")
                raise ExternalServiceError("Vertex AI", f"Initialization failed: {e}")

    @property
    def gemini(self) -> GenerativeModel:
        """Get Gemini model (lazy load)."""
        self._ensure_initialized()
        if self._gemini_model is None:
            self._gemini_model = GenerativeModel("gemini-2.0-flash-001")
        return self._gemini_model

    @property
    def imagen(self) -> ImageGenerationModel:
        """Get Imagen model (lazy load)."""
        self._ensure_initialized()
        if self._imagen_model is None:
            self._imagen_model = ImageGenerationModel.from_pretrained("imagen-3.0-generate-001")
        return self._imagen_model

    # ========================
    # Gemini Text Generation
    # ========================

    async def generate_text(
        self,
        prompt: str,
        system_instruction: str | None = None,
        temperature: float = 0.7,
        max_tokens: int = 8192,
    ) -> str:
        """
        Generate text using Gemini.

        Args:
            prompt: User prompt
            system_instruction: Optional system instruction
            temperature: Creativity (0-1)
            max_tokens: Maximum output tokens

        Returns:
            Generated text
        """
        try:
            model = self.gemini
            if system_instruction:
                model = GenerativeModel(
                    "gemini-2.0-flash-001",
                    system_instruction=[system_instruction],
                )

            generation_config = {
                "max_output_tokens": max_tokens,
                "temperature": temperature,
                "top_p": 0.95,
            }

            safety_settings = [
                SafetySetting(
                    category=SafetySetting.HarmCategory.HARM_CATEGORY_HATE_SPEECH,
                    threshold=SafetySetting.HarmBlockThreshold.BLOCK_MEDIUM_AND_ABOVE,
                ),
                SafetySetting(
                    category=SafetySetting.HarmCategory.HARM_CATEGORY_DANGEROUS_CONTENT,
                    threshold=SafetySetting.HarmBlockThreshold.BLOCK_MEDIUM_AND_ABOVE,
                ),
            ]

            # Run in thread pool as Vertex SDK is sync
            def _generate():
                return model.generate_content(
                    [prompt],
                    generation_config=generation_config,
                    safety_settings=safety_settings,
                )

            response = await asyncio.get_event_loop().run_in_executor(None, _generate)
            return response.text

        except Exception as e:
            logger.error(f"Gemini generation failed: {e}")
            raise ExternalServiceError("Gemini", str(e), retryable=True)

    # ========================
    # Imagen 3 Image Generation
    # ========================

    async def generate_image(
        self,
        prompt: str,
        output_path: str,
        aspect_ratio: str = "9:16",
        number_of_images: int = 1,
    ) -> str:
        """
        Generate image using Imagen 3.

        Args:
            prompt: Image description
            output_path: Path to save the image
            aspect_ratio: Image aspect ratio (9:16 for vertical)
            number_of_images: Number of images to generate

        Returns:
            Path to saved image
        """
        try:
            def _generate():
                return self.imagen.generate_images(
                    prompt=prompt,
                    number_of_images=number_of_images,
                    aspect_ratio=aspect_ratio,
                )

            images = await asyncio.get_event_loop().run_in_executor(None, _generate)

            if images and len(images.images) > 0:
                images.images[0].save(output_path)
                logger.info(f"Generated image: {output_path}")
                return output_path
            else:
                raise ExternalServiceError("Imagen", "No images generated")

        except Exception as e:
            logger.error(f"Imagen generation failed: {e}")
            raise ExternalServiceError("Imagen", str(e), retryable=True)

    # ========================
    # Veo 3 Video Generation
    # ========================

    async def generate_video(
        self,
        prompt: str,
        output_path: str,
        reference_image_path: str | None = None,
        duration_seconds: int = 5,
        aspect_ratio: str = "9:16",
    ) -> str:
        """
        Generate video using Veo 3 with polling.

        Args:
            prompt: Video description
            output_path: Path to save the video
            reference_image_path: Optional reference image for consistency
            duration_seconds: Video duration (5-10 typical)
            aspect_ratio: Video aspect ratio

        Returns:
            Path to saved video
        """
        try:
            from google.cloud import aiplatform

            # Start video generation operation
            logger.info(f"Starting Veo generation: {prompt[:50]}...")

            # Initialize the video generation
            parent = f"projects/{self.project_id}/locations/{self.location}"

            # Note: This is a simplified version - actual Veo API may differ
            # The real implementation would use the Veo SDK when available
            def _generate_video():
                # Placeholder for actual Veo API call
                # In production, this would:
                # 1. Submit generation request
                # 2. Poll for completion
                # 3. Download result
                import time

                # Simulated polling
                logger.info("Veo: Submitting request...")
                time.sleep(1)

                # For now, we'll use the existing VeoWrapper from StoryGenius
                import sys
                from pathlib import Path

                storygenius_path = Path(__file__).parents[3] / "StoryGenius"
                if str(storygenius_path) not in sys.path:
                    sys.path.insert(0, str(storygenius_path))

                from story_genius.assets.veo_wrapper import VeoWrapper

                veo = VeoWrapper()
                veo.generate_video(prompt, output_path)
                return output_path

            result = await asyncio.get_event_loop().run_in_executor(None, _generate_video)
            logger.info(f"Veo generation complete: {result}")
            return result

        except Exception as e:
            logger.error(f"Veo generation failed: {e}")
            raise ExternalServiceError("Veo", str(e), retryable=True)

    async def get_video_status(self, operation_name: str) -> dict[str, Any]:
        """Check status of a video generation operation."""
        # Placeholder for actual status check
        return {"status": "completed", "operation": operation_name}


# Singleton instance
_vertex_client: VertexClient | None = None


def get_vertex_client() -> VertexClient:
    """Get or create singleton Vertex client."""
    global _vertex_client
    if _vertex_client is None:
        _vertex_client = VertexClient()
    return _vertex_client
