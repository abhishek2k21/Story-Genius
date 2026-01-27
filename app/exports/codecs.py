"""
Codec Definitions
Video and audio codec configurations.
"""
from typing import Dict, List, Optional
from app.exports.models import VideoCodec, AudioCodec


# Video Codecs
VIDEO_CODECS = {
    "h264": VideoCodec(
        codec_id="h264",
        name="H.264/AVC",
        encoder="libx264",
        container="mp4",
        file_extension=".mp4",
        compatibility=["youtube", "instagram", "tiktok", "twitter", "web"],
        quality_range={"crf_min": 0, "crf_max": 51, "default_crf": 23},
        default_params={"preset": "medium", "profile": "high", "level": "4.1"}
    ),
    "h265": VideoCodec(
        codec_id="h265",
        name="H.265/HEVC",
        encoder="libx265",
        container="mp4",
        file_extension=".mp4",
        compatibility=["youtube", "web"],
        quality_range={"crf_min": 0, "crf_max": 51, "default_crf": 25},
        default_params={"preset": "medium"}
    ),
    "vp9": VideoCodec(
        codec_id="vp9",
        name="VP9",
        encoder="libvpx-vp9",
        container="webm",
        file_extension=".webm",
        compatibility=["youtube", "web"],
        quality_range={"crf_min": 0, "crf_max": 63, "default_crf": 32},
        default_params={"deadline": "good", "cpu-used": 2}
    ),
    "av1": VideoCodec(
        codec_id="av1",
        name="AV1",
        encoder="libaom-av1",
        container="mp4",
        file_extension=".mp4",
        compatibility=["youtube", "web"],
        quality_range={"crf_min": 0, "crf_max": 63, "default_crf": 30},
        default_params={"cpu-used": 4}
    ),
    "prores": VideoCodec(
        codec_id="prores",
        name="ProRes",
        encoder="prores_ks",
        container="mov",
        file_extension=".mov",
        compatibility=["professional"],
        quality_range={"profile_min": 0, "profile_max": 5},
        default_params={"profile": 3}  # ProRes 422 HQ
    )
}


# Audio Codecs
AUDIO_CODECS = {
    "aac": AudioCodec(
        codec_id="aac",
        name="AAC",
        encoder="aac",
        bitrate_range={"min": 64, "max": 320}
    ),
    "mp3": AudioCodec(
        codec_id="mp3",
        name="MP3",
        encoder="libmp3lame",
        bitrate_range={"min": 64, "max": 320}
    ),
    "opus": AudioCodec(
        codec_id="opus",
        name="Opus",
        encoder="libopus",
        bitrate_range={"min": 32, "max": 512}
    ),
    "pcm": AudioCodec(
        codec_id="pcm",
        name="PCM (Lossless)",
        encoder="pcm_s16le",
        bitrate_range={"min": 1411, "max": 1411}
    ),
    "flac": AudioCodec(
        codec_id="flac",
        name="FLAC",
        encoder="flac",
        bitrate_range={"min": 500, "max": 1500}
    )
}


# Container formats
CONTAINERS = {
    "mp4": {
        "name": "MP4",
        "extension": ".mp4",
        "video_codecs": ["h264", "h265", "av1"],
        "audio_codecs": ["aac", "mp3"],
        "features": ["streaming", "chapters", "metadata"]
    },
    "mov": {
        "name": "QuickTime",
        "extension": ".mov",
        "video_codecs": ["h264", "h265", "prores"],
        "audio_codecs": ["aac", "pcm"],
        "features": ["professional", "timecode"]
    },
    "webm": {
        "name": "WebM",
        "extension": ".webm",
        "video_codecs": ["vp9", "av1"],
        "audio_codecs": ["opus"],
        "features": ["web", "streaming"]
    },
    "mkv": {
        "name": "Matroska",
        "extension": ".mkv",
        "video_codecs": ["h264", "h265", "vp9", "av1"],
        "audio_codecs": ["aac", "opus", "flac"],
        "features": ["subtitles", "chapters", "all_codecs"]
    }
}


def get_video_codec(codec_id: str) -> Optional[VideoCodec]:
    """Get video codec by ID"""
    return VIDEO_CODECS.get(codec_id)


def get_audio_codec(codec_id: str) -> Optional[AudioCodec]:
    """Get audio codec by ID"""
    return AUDIO_CODECS.get(codec_id)


def list_video_codecs() -> List[VideoCodec]:
    """List all video codecs"""
    return list(VIDEO_CODECS.values())


def list_audio_codecs() -> List[AudioCodec]:
    """List all audio codecs"""
    return list(AUDIO_CODECS.values())


def is_codec_compatible(video_codec: str, platform: str) -> bool:
    """Check codec-platform compatibility"""
    codec = VIDEO_CODECS.get(video_codec)
    if not codec:
        return False
    return platform in codec.compatibility


def get_container_for_codec(codec_id: str) -> str:
    """Get default container for codec"""
    codec = VIDEO_CODECS.get(codec_id)
    return codec.container if codec else "mp4"


def validate_codec_container(video_codec: str, container: str) -> bool:
    """Validate codec works with container"""
    cont = CONTAINERS.get(container)
    if not cont:
        return False
    return video_codec in cont["video_codecs"]
