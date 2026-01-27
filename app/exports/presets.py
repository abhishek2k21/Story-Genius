"""
Quality Presets
Predefined quality configurations.
"""
from typing import Dict, List, Optional
from app.exports.models import QualityPreset, QualityLevel, EncodingSpeed, PlatformPreset


# Quality Presets
QUALITY_PRESETS = {
    "draft": QualityPreset(
        preset_id="draft",
        name="Draft",
        description="Quick preview, lowest quality",
        target_quality=QualityLevel.DRAFT,
        video_bitrate_kbps=1500,
        audio_bitrate_kbps=96,
        crf_h264=28,
        crf_h265=30,
        encoding_speed=EncodingSpeed.ULTRAFAST,
        is_system=True
    ),
    "low": QualityPreset(
        preset_id="low",
        name="Low",
        description="Mobile viewing, low bandwidth",
        target_quality=QualityLevel.LOW,
        video_bitrate_kbps=3000,
        audio_bitrate_kbps=128,
        crf_h264=26,
        crf_h265=28,
        encoding_speed=EncodingSpeed.FAST,
        is_system=True
    ),
    "medium": QualityPreset(
        preset_id="medium",
        name="Medium",
        description="Standard web delivery",
        target_quality=QualityLevel.MEDIUM,
        video_bitrate_kbps=6000,
        audio_bitrate_kbps=192,
        crf_h264=23,
        crf_h265=25,
        encoding_speed=EncodingSpeed.MEDIUM,
        is_system=True
    ),
    "high": QualityPreset(
        preset_id="high",
        name="High",
        description="High quality streaming",
        target_quality=QualityLevel.HIGH,
        video_bitrate_kbps=12000,
        audio_bitrate_kbps=256,
        crf_h264=20,
        crf_h265=22,
        encoding_speed=EncodingSpeed.SLOW,
        is_system=True
    ),
    "ultra": QualityPreset(
        preset_id="ultra",
        name="Ultra",
        description="Professional quality",
        target_quality=QualityLevel.ULTRA,
        video_bitrate_kbps=30000,
        audio_bitrate_kbps=320,
        crf_h264=17,
        crf_h265=19,
        encoding_speed=EncodingSpeed.VERYSLOW,
        is_system=True
    ),
    "social_quick": QualityPreset(
        preset_id="social_quick",
        name="Social Media Quick",
        description="Fast export for social platforms",
        target_quality=QualityLevel.MEDIUM,
        video_bitrate_kbps=5000,
        audio_bitrate_kbps=128,
        crf_h264=24,
        crf_h265=26,
        encoding_speed=EncodingSpeed.FAST,
        file_size_priority=True,
        is_system=True
    ),
    "web_optimized": QualityPreset(
        preset_id="web_optimized",
        name="Web Optimized",
        description="Optimized for web streaming",
        target_quality=QualityLevel.MEDIUM,
        video_bitrate_kbps=4000,
        audio_bitrate_kbps=128,
        crf_h264=24,
        crf_h265=26,
        encoding_speed=EncodingSpeed.MEDIUM,
        file_size_priority=True,
        is_system=True
    ),
    "archive": QualityPreset(
        preset_id="archive",
        name="Archive",
        description="High quality for archival",
        target_quality=QualityLevel.HIGH,
        video_bitrate_kbps=15000,
        audio_bitrate_kbps=256,
        crf_h264=18,
        crf_h265=20,
        encoding_speed=EncodingSpeed.SLOW,
        is_system=True
    )
}


# Platform Presets
PLATFORM_PRESETS = {
    "youtube": PlatformPreset(
        platform_id="youtube",
        name="YouTube",
        video_codec="h264",
        audio_codec="aac",
        max_resolution={"width": 3840, "height": 2160},
        max_file_size_mb=256000,
        max_duration_seconds=43200,
        recommended_settings={"bitrate": 12000, "fps": 30}
    ),
    "instagram_reels": PlatformPreset(
        platform_id="instagram_reels",
        name="Instagram Reels",
        video_codec="h264",
        audio_codec="aac",
        max_resolution={"width": 1080, "height": 1920},
        max_file_size_mb=4000,
        max_duration_seconds=90,
        recommended_settings={"bitrate": 5000, "fps": 30}
    ),
    "tiktok": PlatformPreset(
        platform_id="tiktok",
        name="TikTok",
        video_codec="h264",
        audio_codec="aac",
        max_resolution={"width": 1080, "height": 1920},
        max_file_size_mb=287,
        max_duration_seconds=180,
        recommended_settings={"bitrate": 4000, "fps": 30}
    ),
    "twitter": PlatformPreset(
        platform_id="twitter",
        name="Twitter/X",
        video_codec="h264",
        audio_codec="aac",
        max_resolution={"width": 1920, "height": 1200},
        max_file_size_mb=512,
        max_duration_seconds=140,
        recommended_settings={"bitrate": 6000, "fps": 30}
    ),
    "linkedin": PlatformPreset(
        platform_id="linkedin",
        name="LinkedIn",
        video_codec="h264",
        audio_codec="aac",
        max_resolution={"width": 1920, "height": 1080},
        max_file_size_mb=5000,
        max_duration_seconds=600,
        recommended_settings={"bitrate": 8000, "fps": 30}
    )
}


def get_preset(preset_id: str) -> Optional[QualityPreset]:
    """Get quality preset by ID"""
    return QUALITY_PRESETS.get(preset_id)


def list_presets() -> List[QualityPreset]:
    """List all quality presets"""
    return list(QUALITY_PRESETS.values())


def get_platform(platform_id: str) -> Optional[PlatformPreset]:
    """Get platform preset by ID"""
    return PLATFORM_PRESETS.get(platform_id)


def list_platforms() -> List[PlatformPreset]:
    """List all platform presets"""
    return list(PLATFORM_PRESETS.values())


def get_crf_for_quality(quality: QualityLevel, codec: str = "h264") -> int:
    """Get CRF value for quality level"""
    crf_map = {
        QualityLevel.DRAFT: {"h264": 28, "h265": 30},
        QualityLevel.LOW: {"h264": 26, "h265": 28},
        QualityLevel.MEDIUM: {"h264": 23, "h265": 25},
        QualityLevel.HIGH: {"h264": 20, "h265": 22},
        QualityLevel.ULTRA: {"h264": 17, "h265": 19}
    }
    return crf_map.get(quality, {}).get(codec, 23)


def get_bitrate_for_resolution(resolution: str, quality: QualityLevel) -> int:
    """Get bitrate for resolution and quality"""
    base_bitrate = {
        QualityLevel.DRAFT: 1500,
        QualityLevel.LOW: 3000,
        QualityLevel.MEDIUM: 6000,
        QualityLevel.HIGH: 12000,
        QualityLevel.ULTRA: 30000
    }
    
    resolution_multiplier = {
        "480p": 0.5,
        "720p": 1.0,
        "1080p": 2.0,
        "1440p": 3.5,
        "2160p": 6.0
    }
    
    base = base_bitrate.get(quality, 6000)
    mult = resolution_multiplier.get(resolution, 1.0)
    
    return int(base * mult)
