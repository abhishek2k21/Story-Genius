"""
Video Format Configuration Module
Handles all platform-specific video requirements for YT Shorts, Reels, TikTok, etc.
"""
from enum import Enum
from dataclasses import dataclass
from typing import Tuple, List, Dict


class Platform(str, Enum):
    """Supported video platforms"""
    YOUTUBE_SHORTS = "youtube_shorts"
    INSTAGRAM_REELS = "instagram_reels"
    TIKTOK = "tiktok"
    YOUTUBE_LONG = "youtube_long"
    INSTAGRAM_POST = "instagram_post"


@dataclass
class VideoFormat:
    """Video format specification for a platform"""
    platform: Platform
    aspect_ratio: Tuple[int, int]  # (width, height) ratio
    resolution: Tuple[int, int]  # (width, height) pixels
    max_duration: int  # seconds
    recommended_duration: Tuple[int, int]  # (min, max) seconds
    fps: int
    safe_zone: Dict[str, int]  # margins for text/UI elements


# Platform-specific video formats
VIDEO_FORMATS: Dict[Platform, VideoFormat] = {
    Platform.YOUTUBE_SHORTS: VideoFormat(
        platform=Platform.YOUTUBE_SHORTS,
        aspect_ratio=(9, 16),
        resolution=(1080, 1920),
        max_duration=60,
        recommended_duration=(15, 60),
        fps=30,
        safe_zone={"top": 150, "bottom": 200, "left": 50, "right": 50}
    ),
    Platform.INSTAGRAM_REELS: VideoFormat(
        platform=Platform.INSTAGRAM_REELS,
        aspect_ratio=(9, 16),
        resolution=(1080, 1920),
        max_duration=90,
        recommended_duration=(15, 30),
        fps=30,
        safe_zone={"top": 120, "bottom": 250, "left": 40, "right": 40}
    ),
    Platform.TIKTOK: VideoFormat(
        platform=Platform.TIKTOK,
        aspect_ratio=(9, 16),
        resolution=(1080, 1920),
        max_duration=180,
        recommended_duration=(15, 60),
        fps=30,
        safe_zone={"top": 100, "bottom": 150, "left": 40, "right": 40}
    ),
    Platform.YOUTUBE_LONG: VideoFormat(
        platform=Platform.YOUTUBE_LONG,
        aspect_ratio=(16, 9),
        resolution=(1920, 1080),
        max_duration=43200,  # 12 hours
        recommended_duration=(480, 900),  # 8-15 mins
        fps=30,
        safe_zone={"top": 60, "bottom": 60, "left": 80, "right": 80}
    ),
    Platform.INSTAGRAM_POST: VideoFormat(
        platform=Platform.INSTAGRAM_POST,
        aspect_ratio=(1, 1),
        resolution=(1080, 1080),
        max_duration=60,
        recommended_duration=(15, 60),
        fps=30,
        safe_zone={"top": 80, "bottom": 100, "left": 40, "right": 40}
    ),
}


def get_format(platform: Platform) -> VideoFormat:
    """Get video format for a platform"""
    return VIDEO_FORMATS.get(platform)


def get_all_short_formats() -> List[VideoFormat]:
    """Get all vertical (9:16) short-form formats"""
    return [f for f in VIDEO_FORMATS.values() if f.aspect_ratio == (9, 16)]


def get_format_by_name(name: str) -> VideoFormat:
    """Get format by platform name string"""
    try:
        platform = Platform(name)
        return get_format(platform)
    except ValueError:
        return None


def list_all_platforms() -> List[str]:
    """List all available platform names"""
    return [p.value for p in Platform]
