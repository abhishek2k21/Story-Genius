"""
Thumbnail Generation Utilities
Auto-generate video thumbnails with MoviePy.
"""
from pathlib import Path
from typing import Optional, Tuple

from pydantic import BaseModel, Field


class ThumbnailConfig(BaseModel):
    """Configuration for thumbnail generation."""
    width: int = Field(1280, ge=320, le=3840)
    height: int = Field(720, ge=180, le=2160)
    frame_position: float = Field(0.3, ge=0.0, le=1.0, description="Relative position (0-1)")
    quality: int = Field(90, ge=50, le=100)
    format: str = "jpeg"


def generate_thumbnail(
    video_path: str,
    output_path: str,
    config: Optional[ThumbnailConfig] = None,
) -> str:
    """
    Generate thumbnail from video.

    Args:
        video_path: Input video path
        output_path: Output thumbnail path
        config: Thumbnail configuration

    Returns:
        Output thumbnail path
    """
    from PIL import Image
    from moviepy import VideoFileClip

    config = config or ThumbnailConfig()

    video = VideoFileClip(video_path)

    # Calculate frame time
    frame_time = video.duration * config.frame_position

    # Extract frame
    frame = video.get_frame(frame_time)
    video.close()

    # Convert to PIL Image
    img = Image.fromarray(frame)

    # Resize maintaining aspect ratio
    img = resize_with_aspect(img, config.width, config.height)

    # Save
    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    if config.format.lower() in ["jpeg", "jpg"]:
        img.save(str(output_path), "JPEG", quality=config.quality)
    else:
        img.save(str(output_path), config.format.upper())

    return str(output_path)


def resize_with_aspect(
    img,
    target_width: int,
    target_height: int,
) -> "Image":
    """
    Resize image maintaining aspect ratio, cropping if needed.

    Args:
        img: PIL Image
        target_width: Target width
        target_height: Target height

    Returns:
        Resized PIL Image
    """
    from PIL import Image

    # Calculate aspect ratios
    img_ratio = img.width / img.height
    target_ratio = target_width / target_height

    if img_ratio > target_ratio:
        # Image is wider - crop sides
        new_width = int(img.height * target_ratio)
        left = (img.width - new_width) // 2
        img = img.crop((left, 0, left + new_width, img.height))
    else:
        # Image is taller - crop top/bottom
        new_height = int(img.width / target_ratio)
        top = (img.height - new_height) // 2
        img = img.crop((0, top, img.width, top + new_height))

    # Resize to target
    return img.resize((target_width, target_height), Image.Resampling.LANCZOS)


def generate_thumbnail_grid(
    video_path: str,
    output_path: str,
    grid_size: Tuple[int, int] = (3, 3),
    thumb_size: Tuple[int, int] = (320, 180),
) -> str:
    """
    Generate a grid of thumbnails from video.

    Args:
        video_path: Input video path
        output_path: Output image path
        grid_size: (columns, rows)
        thumb_size: Size of each thumbnail

    Returns:
        Output image path
    """
    from PIL import Image
    from moviepy import VideoFileClip

    video = VideoFileClip(video_path)
    cols, rows = grid_size
    total = cols * rows

    # Calculate frame times
    times = [video.duration * (i + 1) / (total + 1) for i in range(total)]

    # Create grid image
    grid_width = cols * thumb_size[0]
    grid_height = rows * thumb_size[1]
    grid_img = Image.new("RGB", (grid_width, grid_height))

    for i, t in enumerate(times):
        frame = video.get_frame(t)
        img = Image.fromarray(frame)
        img = resize_with_aspect(img, thumb_size[0], thumb_size[1])

        x = (i % cols) * thumb_size[0]
        y = (i // cols) * thumb_size[1]
        grid_img.paste(img, (x, y))

    video.close()

    # Save
    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    grid_img.save(str(output_path), "JPEG", quality=90)

    return str(output_path)


def extract_frames(
    video_path: str,
    output_dir: str,
    num_frames: int = 10,
    format: str = "jpeg",
) -> list[str]:
    """
    Extract multiple frames from video.

    Args:
        video_path: Input video path
        output_dir: Output directory
        num_frames: Number of frames to extract
        format: Image format

    Returns:
        List of frame paths
    """
    from PIL import Image
    from moviepy import VideoFileClip

    video = VideoFileClip(video_path)
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    # Calculate frame times
    times = [video.duration * (i + 1) / (num_frames + 1) for i in range(num_frames)]

    paths = []
    for i, t in enumerate(times):
        frame = video.get_frame(t)
        img = Image.fromarray(frame)

        ext = "jpg" if format.lower() == "jpeg" else format.lower()
        path = output_dir / f"frame_{i:03d}.{ext}"

        if format.lower() in ["jpeg", "jpg"]:
            img.save(str(path), "JPEG", quality=90)
        else:
            img.save(str(path), format.upper())

        paths.append(str(path))

    video.close()
    return paths
