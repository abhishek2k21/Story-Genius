"""
ElevenLabs TTS Client
Text-to-speech using ElevenLabs API (with EdgeTTS fallback).
"""
import asyncio
import os
from pathlib import Path
from typing import Optional

from src.core.exceptions import ExternalServiceError
from src.core.logging import get_logger
from src.core.settings import settings

logger = get_logger(__name__)


class ElevenLabsClient:
    """
    ElevenLabs TTS client with EdgeTTS fallback.

    Falls back to EdgeTTS (free) if ElevenLabs API key not configured.
    """

    # Popular ElevenLabs voice IDs
    VOICES = {
        "rachel": "21m00Tcm4TlvDq8ikWAM",  # Female, calm
        "adam": "pNInz6obpgDQGcFmaJgB",    # Male, deep
        "antoni": "ErXwobaYiN019PkySvjV",   # Male, warm
        "bella": "EXAVITQu4vr4xnSDxMaL",    # Female, soft
        "josh": "TxGEqnHWrfWFTfGW9XjX",     # Male, young
    }

    def __init__(self, api_key: str | None = None):
        self.api_key = api_key or os.environ.get("ELEVENLABS_API_KEY")
        self._client = None
        self._use_fallback = False

    def _ensure_client(self) -> None:
        """Initialize ElevenLabs client or set fallback mode."""
        if self._client is not None or self._use_fallback:
            return

        if self.api_key:
            try:
                from elevenlabs.client import ElevenLabs

                self._client = ElevenLabs(api_key=self.api_key)
                logger.info("ElevenLabs client initialized")
            except ImportError:
                logger.warning("ElevenLabs package not installed, using EdgeTTS fallback")
                self._use_fallback = True
            except Exception as e:
                logger.warning(f"ElevenLabs init failed: {e}, using EdgeTTS fallback")
                self._use_fallback = True
        else:
            logger.info("No ElevenLabs API key, using EdgeTTS fallback")
            self._use_fallback = True

    async def generate_speech(
        self,
        text: str,
        output_path: str,
        voice: str = "rachel",
        model: str = "eleven_turbo_v2",
    ) -> str:
        """
        Generate speech from text.

        Args:
            text: Text to convert to speech
            output_path: Path to save audio file
            voice: Voice name or ID
            model: ElevenLabs model to use

        Returns:
            Path to saved audio file
        """
        self._ensure_client()

        # Ensure output directory exists
        os.makedirs(os.path.dirname(output_path), exist_ok=True)

        if self._use_fallback:
            return await self._generate_with_edge_tts(text, output_path)

        try:
            return await self._generate_with_elevenlabs(text, output_path, voice, model)
        except Exception as e:
            logger.warning(f"ElevenLabs failed, falling back to EdgeTTS: {e}")
            return await self._generate_with_edge_tts(text, output_path)

    async def _generate_with_elevenlabs(
        self,
        text: str,
        output_path: str,
        voice: str,
        model: str,
    ) -> str:
        """Generate speech using ElevenLabs."""
        try:
            # Resolve voice name to ID
            voice_id = self.VOICES.get(voice.lower(), voice)

            def _generate():
                audio = self._client.generate(
                    text=text,
                    voice=voice_id,
                    model=model,
                )
                # Write audio to file
                with open(output_path, "wb") as f:
                    for chunk in audio:
                        f.write(chunk)
                return output_path

            result = await asyncio.get_event_loop().run_in_executor(None, _generate)
            logger.info(f"ElevenLabs generated: {output_path}")
            return result

        except Exception as e:
            raise ExternalServiceError("ElevenLabs", str(e), retryable=True)

    async def _generate_with_edge_tts(
        self,
        text: str,
        output_path: str,
        voice: str = "en-US-AriaNeural",
    ) -> str:
        """Generate speech using EdgeTTS (free fallback)."""
        try:
            import edge_tts

            communicate = edge_tts.Communicate(text, voice)
            await communicate.save(output_path)
            logger.info(f"EdgeTTS generated: {output_path}")
            return output_path

        except Exception as e:
            raise ExternalServiceError("EdgeTTS", str(e), retryable=True)

    async def list_voices(self) -> list[dict]:
        """List available voices."""
        self._ensure_client()

        if self._use_fallback:
            # Return EdgeTTS voices
            import edge_tts

            voices = await edge_tts.list_voices()
            return [
                {"name": v["ShortName"], "gender": v["Gender"], "locale": v["Locale"]}
                for v in voices
                if v["Locale"].startswith("en-")
            ][:10]

        try:
            def _list():
                return self._client.voices.get_all()

            voices = await asyncio.get_event_loop().run_in_executor(None, _list)
            return [
                {"id": v.voice_id, "name": v.name, "category": v.category}
                for v in voices.voices
            ]
        except Exception as e:
            raise ExternalServiceError("ElevenLabs", str(e))


# Singleton
_elevenlabs_client: ElevenLabsClient | None = None


def get_elevenlabs_client() -> ElevenLabsClient:
    """Get or create singleton ElevenLabs client."""
    global _elevenlabs_client
    if _elevenlabs_client is None:
        _elevenlabs_client = ElevenLabsClient()
    return _elevenlabs_client
