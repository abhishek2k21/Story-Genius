"""
Size Optimization
File size estimation and optimization.
"""
from typing import Dict, Optional, Tuple

from app.exports.models import QualityLevel, OptimizeFor
from app.exports.presets import get_preset, get_bitrate_for_resolution


def estimate_file_size(
    duration_seconds: float,
    video_bitrate_kbps: int,
    audio_bitrate_kbps: int = 128,
    overhead_percent: float = 5.0
) -> float:
    """Estimate file size in MB"""
    total_bitrate = video_bitrate_kbps + audio_bitrate_kbps
    size_bits = total_bitrate * 1000 * duration_seconds
    size_mb = size_bits / (8 * 1024 * 1024)
    size_mb *= (1 + overhead_percent / 100)
    return round(size_mb, 2)


def calculate_bitrate_for_size(
    target_size_mb: float,
    duration_seconds: float,
    audio_bitrate_kbps: int = 128,
    overhead_percent: float = 5.0
) -> int:
    """Calculate video bitrate for target file size"""
    # Remove overhead
    effective_size = target_size_mb / (1 + overhead_percent / 100)
    
    # Calculate total bitrate
    total_bits = effective_size * 8 * 1024 * 1024
    total_bitrate_kbps = total_bits / (duration_seconds * 1000)
    
    # Subtract audio
    video_bitrate = int(total_bitrate_kbps - audio_bitrate_kbps)
    
    return max(500, video_bitrate)  # Minimum 500 kbps


def get_size_reduction_strategies(
    current_size_mb: float,
    target_size_mb: float,
    current_settings: Dict
) -> list:
    """Get strategies to reduce file size"""
    strategies = []
    reduction_needed = (current_size_mb - target_size_mb) / current_size_mb * 100
    
    # Strategy 1: Use better compression codec
    if current_settings.get("codec") == "h264":
        strategies.append({
            "strategy": "use_h265",
            "description": "Switch to H.265 for 30-50% better compression",
            "estimated_reduction": 40
        })
    
    # Strategy 2: Reduce bitrate
    current_bitrate = current_settings.get("video_bitrate_kbps", 6000)
    if current_bitrate > 2000:
        strategies.append({
            "strategy": "reduce_bitrate",
            "description": f"Reduce bitrate from {current_bitrate} to {int(current_bitrate * 0.7)} kbps",
            "estimated_reduction": 30
        })
    
    # Strategy 3: Lower resolution
    current_res = current_settings.get("resolution", "1080p")
    res_options = {"2160p": "1440p", "1440p": "1080p", "1080p": "720p", "720p": "480p"}
    if current_res in res_options:
        strategies.append({
            "strategy": "lower_resolution",
            "description": f"Downscale from {current_res} to {res_options[current_res]}",
            "estimated_reduction": 50
        })
    
    # Strategy 4: Reduce framerate
    strategies.append({
        "strategy": "reduce_framerate",
        "description": "Reduce framerate from 30 to 24 fps",
        "estimated_reduction": 20
    })
    
    return strategies


def get_streaming_optimizations() -> Dict:
    """Get optimizations for streaming"""
    return {
        "faststart": True,  # moov atom at start
        "keyframe_interval": 2,  # seconds
        "fragmented": False,  # fMP4 for DASH/HLS
        "bitrate_mode": "vbr",  # Variable for quality
        "max_bitrate_ratio": 1.5  # Constrain VBR peaks
    }


def get_download_optimizations() -> Dict:
    """Get optimizations for download"""
    return {
        "faststart": True,
        "keyframe_interval": 5,  # Less frequent for smaller size
        "fragmented": False,
        "bitrate_mode": "crf",
        "max_bitrate_ratio": None
    }


def get_archive_optimizations() -> Dict:
    """Get optimizations for archival"""
    return {
        "faststart": False,  # Not needed
        "keyframe_interval": 10,
        "fragmented": False,
        "bitrate_mode": "crf",
        "max_bitrate_ratio": None,
        "preserve_metadata": True
    }


def validate_platform_limits(
    file_size_mb: float,
    duration_seconds: float,
    resolution: str,
    platform: str
) -> Tuple[bool, list]:
    """Validate export against platform limits"""
    from app.exports.presets import get_platform
    
    platform_preset = get_platform(platform)
    if not platform_preset:
        return True, []
    
    issues = []
    
    # Check file size
    if file_size_mb > platform_preset.max_file_size_mb:
        issues.append(f"File size {file_size_mb}MB exceeds {platform} limit of {platform_preset.max_file_size_mb}MB")
    
    # Check duration
    if duration_seconds > platform_preset.max_duration_seconds:
        issues.append(f"Duration {duration_seconds}s exceeds {platform} limit of {platform_preset.max_duration_seconds}s")
    
    return len(issues) == 0, issues


def auto_optimize_for_platform(
    duration_seconds: float,
    platform: str,
    quality: QualityLevel = QualityLevel.MEDIUM
) -> Dict:
    """Auto-calculate settings for platform"""
    from app.exports.presets import get_platform
    
    platform_preset = get_platform(platform)
    if not platform_preset:
        return {}
    
    # Calculate max bitrate to stay under size limit
    max_size = platform_preset.max_file_size_mb * 0.95  # 5% margin
    max_bitrate = calculate_bitrate_for_size(max_size, duration_seconds)
    
    # Get quality-based bitrate
    quality_bitrate = get_bitrate_for_resolution("1080p", quality)
    
    # Use lower of the two
    effective_bitrate = min(max_bitrate, quality_bitrate)
    
    return {
        "video_codec": platform_preset.video_codec,
        "audio_codec": platform_preset.audio_codec,
        "video_bitrate_kbps": effective_bitrate,
        "audio_bitrate_kbps": 128,
        "max_resolution": platform_preset.max_resolution,
        "estimated_size_mb": estimate_file_size(duration_seconds, effective_bitrate)
    }
