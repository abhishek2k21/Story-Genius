"""
Freesound API Client
Sound effects from Freesound.org.
"""
import asyncio
import os
from pathlib import Path
from typing import Optional

import httpx

from src.core.logging import get_logger
from src.core.settings import settings
from src.core.usage_logging import log_usage

logger = get_logger(__name__)

# Freesound API (free tier: 60 requests/minute)
FREESOUND_API_URL = "https://freesound.org/apiv2"


class FreesoundClient:
    """Client for Freesound.org API."""

    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key or getattr(settings, "freesound_api_key", None)
        self._client: Optional[httpx.AsyncClient] = None

    async def _get_client(self) -> httpx.AsyncClient:
        if not self._client:
            self._client = httpx.AsyncClient(
                base_url=FREESOUND_API_URL,
                timeout=30.0,
            )
        return self._client

    async def close(self):
        if self._client:
            await self._client.aclose()
            self._client = None

    async def search_sounds(
        self,
        query: str,
        duration_min: float = 0,
        duration_max: float = 30,
        license_filter: str = "Attribution",
        page_size: int = 10,
    ) -> list[dict]:
        """
        Search for sound effects.

        Args:
            query: Search query (e.g., "explosion", "footsteps")
            duration_min: Minimum duration in seconds
            duration_max: Maximum duration in seconds
            license_filter: License type filter
            page_size: Number of results

        Returns:
            List of sound info dicts
        """
        if not self.api_key:
            logger.warning("Freesound API key not configured")
            return []

        client = await self._get_client()

        try:
            response = await client.get(
                "/search/text/",
                params={
                    "token": self.api_key,
                    "query": query,
                    "filter": f"duration:[{duration_min} TO {duration_max}]",
                    "license": license_filter,
                    "page_size": page_size,
                    "fields": "id,name,description,duration,previews,license,username",
                },
            )
            response.raise_for_status()
            data = response.json()

            log_usage(
                service="freesound",
                operation="search",
                success=True,
                query=query,
                results=len(data.get("results", [])),
            )

            return data.get("results", [])

        except Exception as e:
            logger.error(f"Freesound search failed: {e}")
            log_usage(
                service="freesound",
                operation="search",
                success=False,
                error=str(e),
            )
            return []

    async def download_sound(
        self,
        sound_id: int,
        output_path: str,
        quality: str = "preview-hq-mp3",
    ) -> Optional[str]:
        """
        Download a sound effect.

        Args:
            sound_id: Freesound sound ID
            output_path: Path to save the file
            quality: Preview quality (preview-hq-mp3, preview-lq-mp3)

        Returns:
            Path to downloaded file or None
        """
        if not self.api_key:
            return None

        client = await self._get_client()

        try:
            # Get sound info with previews
            info_response = await client.get(
                f"/sounds/{sound_id}/",
                params={
                    "token": self.api_key,
                    "fields": "id,name,previews",
                },
            )
            info_response.raise_for_status()
            info = info_response.json()

            # Get preview URL
            preview_url = info.get("previews", {}).get(quality)
            if not preview_url:
                logger.warning(f"No {quality} preview for sound {sound_id}")
                return None

            # Download file
            download_response = await client.get(preview_url)
            download_response.raise_for_status()

            # Save file
            output = Path(output_path)
            output.parent.mkdir(parents=True, exist_ok=True)
            output.write_bytes(download_response.content)

            log_usage(
                service="freesound",
                operation="download",
                success=True,
                sound_id=sound_id,
            )

            return str(output)

        except Exception as e:
            logger.error(f"Freesound download failed: {e}")
            log_usage(
                service="freesound",
                operation="download",
                success=False,
                error=str(e),
            )
            return None

    async def get_sounds_for_scene(
        self,
        scene_description: str,
        max_sounds: int = 3,
    ) -> list[dict]:
        """
        Get relevant sound effects for a scene.

        Extracts keywords from description and searches Freesound.
        """
        # Simple keyword extraction
        keywords = self._extract_sfx_keywords(scene_description)

        if not keywords:
            return []

        sounds = []
        for keyword in keywords[:max_sounds]:
            results = await self.search_sounds(keyword, page_size=1)
            if results:
                sounds.append({
                    "keyword": keyword,
                    "sound": results[0],
                })

        return sounds

    def _extract_sfx_keywords(self, text: str) -> list[str]:
        """Extract potential SFX keywords from text."""
        # Common SFX keywords to look for
        sfx_words = {
            "explosion", "crash", "thunder", "rain", "wind", "fire",
            "footsteps", "door", "car", "engine", "water", "splash",
            "ambient", "city", "forest", "ocean", "birds", "crowd",
            "whoosh", "swoosh", "impact", "hit", "punch", "sword",
            "magic", "sparkle", "alarm", "bell", "clock", "phone",
        }

        text_lower = text.lower()
        found = []

        for word in sfx_words:
            if word in text_lower:
                found.append(word)

        return found


# Singleton client
_client: Optional[FreesoundClient] = None


def get_freesound_client() -> FreesoundClient:
    """Get Freesound client singleton."""
    global _client
    if _client is None:
        _client = FreesoundClient()
    return _client
