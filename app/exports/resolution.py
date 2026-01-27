"""
Resolution Handling
Multi-resolution export support.
"""
from typing import Dict, List, Optional
from app.exports.models import Resolution


# Standard resolutions (16:9)
RESOLUTIONS_169 = {
    "360p": Resolution("360p", "360p", 640, 360, "16:9", "SD"),
    "480p": Resolution("480p", "480p", 854, 480, "16:9", "SD"),
    "720p": Resolution("720p", "720p", 1280, 720, "16:9", "HD"),
    "1080p": Resolution("1080p", "1080p", 1920, 1080, "16:9", "Full HD"),
    "1440p": Resolution("1440p", "1440p", 2560, 1440, "16:9", "2K"),
    "2160p": Resolution("2160p", "2160p", 3840, 2160, "16:9", "4K")
}

# Vertical resolutions (9:16)
RESOLUTIONS_916 = {
    "480p_v": Resolution("480p_v", "480p Vertical", 480, 854, "9:16", "SD Vertical"),
    "720p_v": Resolution("720p_v", "720p Vertical", 720, 1280, "9:16", "HD Vertical"),
    "1080p_v": Resolution("1080p_v", "1080p Vertical", 1080, 1920, "9:16", "Full HD Vertical")
}

# Square resolutions (1:1)
RESOLUTIONS_11 = {
    "480p_sq": Resolution("480p_sq", "480p Square", 480, 480, "1:1", "Square"),
    "720p_sq": Resolution("720p_sq", "720p Square", 720, 720, "1:1", "Square"),
    "1080p_sq": Resolution("1080p_sq", "1080p Square", 1080, 1080, "1:1", "Square")
}

# All resolutions
ALL_RESOLUTIONS = {**RESOLUTIONS_169, **RESOLUTIONS_916, **RESOLUTIONS_11}


# Scaling methods
SCALING_METHODS = {
    "bilinear": {"ffmpeg_flag": "bilinear", "quality": "lower", "speed": "fast"},
    "bicubic": {"ffmpeg_flag": "bicubic", "quality": "good", "speed": "medium"},
    "lanczos": {"ffmpeg_flag": "lanczos", "quality": "high", "speed": "slow"},
    "spline": {"ffmpeg_flag": "spline", "quality": "high", "speed": "slow"}
}


def get_resolution(preset_id: str) -> Optional[Resolution]:
    """Get resolution by preset ID"""
    return ALL_RESOLUTIONS.get(preset_id)


def list_resolutions(aspect_ratio: str = None) -> List[Resolution]:
    """List resolutions, optionally filtered by aspect ratio"""
    resolutions = list(ALL_RESOLUTIONS.values())
    
    if aspect_ratio:
        resolutions = [r for r in resolutions if r.aspect_ratio == aspect_ratio]
    
    return sorted(resolutions, key=lambda r: r.width * r.height)


def get_resolution_bitrate_multiplier(resolution: str) -> float:
    """Get bitrate multiplier for resolution"""
    multipliers = {
        "360p": 0.3, "480p": 0.5, "720p": 1.0,
        "1080p": 2.0, "1440p": 3.5, "2160p": 6.0,
        "480p_v": 0.5, "720p_v": 1.0, "1080p_v": 2.0,
        "480p_sq": 0.4, "720p_sq": 0.8, "1080p_sq": 1.5
    }
    return multipliers.get(resolution, 1.0)


def scale_to_resolution(
    source_width: int,
    source_height: int,
    target_resolution: str,
    maintain_aspect: bool = True
) -> Dict:
    """Calculate scaled dimensions"""
    target = get_resolution(target_resolution)
    if not target:
        return {"width": source_width, "height": source_height}
    
    if maintain_aspect:
        source_aspect = source_width / source_height
        target_aspect = target.width / target.height
        
        if source_aspect > target_aspect:
            # Wider than target - fit to width
            width = target.width
            height = int(width / source_aspect)
        else:
            # Taller than target - fit to height
            height = target.height
            width = int(height * source_aspect)
        
        # Ensure even dimensions
        width = width - (width % 2)
        height = height - (height % 2)
    else:
        width = target.width
        height = target.height
    
    return {"width": width, "height": height}


def get_adaptive_package_resolutions(source_resolution: str) -> List[str]:
    """Get resolutions for adaptive streaming package"""
    res = get_resolution(source_resolution)
    if not res:
        return ["720p", "480p"]
    
    # Include source and lower resolutions
    order = ["2160p", "1440p", "1080p", "720p", "480p", "360p"]
    
    try:
        idx = order.index(source_resolution)
        return order[idx:]
    except ValueError:
        return ["720p", "480p"]
