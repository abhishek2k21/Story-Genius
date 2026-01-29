"""
Storage Client
Local and cloud storage for media files.
"""
import os
import shutil
import uuid
from datetime import datetime
from pathlib import Path
from typing import BinaryIO, Optional

from src.core.exceptions import NotFoundError, StoryGeniusError
from src.core.logging import get_logger
from src.core.settings import settings

logger = get_logger(__name__)


class StorageClient:
    """
    Storage client for media files.

    Supports:
    - Local filesystem storage
    - S3-compatible storage (future)
    """

    def __init__(
        self,
        base_path: Path | None = None,
        s3_bucket: str | None = None,
    ):
        self.base_path = base_path or settings.media_dir
        self.s3_bucket = s3_bucket  # Future use
        self._ensure_dirs()

    def _ensure_dirs(self) -> None:
        """Create required directories."""
        for subdir in ["audio", "video", "images", "thumbnails", "temp"]:
            (self.base_path / subdir).mkdir(parents=True, exist_ok=True)

    def _generate_filename(self, extension: str, prefix: str = "") -> str:
        """Generate unique filename."""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        unique_id = str(uuid.uuid4())[:8]
        return f"{prefix}{timestamp}_{unique_id}.{extension}"

    # ========================
    # File Operations
    # ========================

    async def save_file(
        self,
        file: BinaryIO | bytes,
        category: str,
        filename: str | None = None,
        extension: str = "mp4",
    ) -> str:
        """
        Save a file to storage.

        Args:
            file: File content (bytes or file-like object)
            category: Subdirectory (audio, video, images, etc.)
            filename: Optional custom filename
            extension: File extension

        Returns:
            Relative path to saved file
        """
        if filename is None:
            filename = self._generate_filename(extension, f"{category}_")

        file_path = self.base_path / category / filename

        try:
            if isinstance(file, bytes):
                file_path.write_bytes(file)
            else:
                with open(file_path, "wb") as f:
                    shutil.copyfileobj(file, f)

            logger.info(f"Saved file: {file_path}")
            return str(file_path.relative_to(self.base_path))

        except Exception as e:
            raise StoryGeniusError(f"Failed to save file: {e}")

    async def get_file_path(self, relative_path: str) -> Path:
        """Get absolute path for a stored file."""
        full_path = self.base_path / relative_path
        if not full_path.exists():
            raise NotFoundError("File", relative_path)
        return full_path

    async def delete_file(self, relative_path: str) -> bool:
        """Delete a file from storage."""
        full_path = self.base_path / relative_path
        try:
            if full_path.exists():
                full_path.unlink()
                logger.info(f"Deleted file: {relative_path}")
                return True
            return False
        except Exception as e:
            logger.error(f"Failed to delete {relative_path}: {e}")
            return False

    async def file_exists(self, relative_path: str) -> bool:
        """Check if a file exists."""
        return (self.base_path / relative_path).exists()

    # ========================
    # Specialized Saves
    # ========================

    async def save_audio(
        self,
        content: bytes,
        scene_id: str | None = None,
    ) -> str:
        """Save audio file."""
        filename = f"audio_{scene_id or uuid.uuid4()}.mp3"
        return await self.save_file(content, "audio", filename, "mp3")

    async def save_video(
        self,
        content: bytes,
        job_id: str | None = None,
        is_clip: bool = False,
    ) -> str:
        """Save video file."""
        prefix = "clip" if is_clip else "final"
        filename = f"{prefix}_{job_id or uuid.uuid4()}.mp4"
        return await self.save_file(content, "video", filename, "mp4")

    async def save_image(
        self,
        content: bytes,
        scene_id: str | None = None,
    ) -> str:
        """Save image file."""
        filename = f"image_{scene_id or uuid.uuid4()}.png"
        return await self.save_file(content, "images", filename, "png")

    async def save_thumbnail(
        self,
        content: bytes,
        story_id: str | None = None,
    ) -> str:
        """Save thumbnail file."""
        filename = f"thumb_{story_id or uuid.uuid4()}.jpg"
        return await self.save_file(content, "thumbnails", filename, "jpg")

    # ========================
    # Cleanup
    # ========================

    async def cleanup_temp(self, max_age_hours: int = 24) -> int:
        """Clean up old temp files."""
        import time

        temp_dir = self.base_path / "temp"
        cutoff = time.time() - (max_age_hours * 3600)
        deleted = 0

        for file in temp_dir.glob("*"):
            if file.stat().st_mtime < cutoff:
                file.unlink()
                deleted += 1

        logger.info(f"Cleaned up {deleted} temp files")
        return deleted

    async def get_storage_stats(self) -> dict:
        """Get storage statistics."""
        stats = {}
        for subdir in ["audio", "video", "images", "thumbnails", "temp"]:
            dir_path = self.base_path / subdir
            files = list(dir_path.glob("*"))
            total_size = sum(f.stat().st_size for f in files if f.is_file())
            stats[subdir] = {
                "count": len(files),
                "size_mb": round(total_size / (1024 * 1024), 2),
            }
        return stats


# Singleton
_storage_client: StorageClient | None = None


def get_storage_client() -> StorageClient:
    """Get or create singleton Storage client."""
    global _storage_client
    if _storage_client is None:
        _storage_client = StorageClient()
    return _storage_client
