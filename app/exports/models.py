"""
Export Models
Data structures for export jobs, codecs, and presets.
"""
from typing import Dict, List, Optional
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
import uuid


class ExportStatus(str, Enum):
    QUEUED = "queued"
    PREPARING = "preparing"
    ENCODING = "encoding"
    OPTIMIZING = "optimizing"
    FINALIZING = "finalizing"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class QualityLevel(str, Enum):
    DRAFT = "draft"
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    ULTRA = "ultra"


class BitrateMode(str, Enum):
    CBR = "cbr"
    VBR = "vbr"
    CRF = "crf"
    ABR = "abr"


class EncodingSpeed(str, Enum):
    ULTRAFAST = "ultrafast"
    FAST = "fast"
    MEDIUM = "medium"
    SLOW = "slow"
    VERYSLOW = "veryslow"


class OptimizeFor(str, Enum):
    STREAMING = "streaming"
    DOWNLOAD = "download"
    ARCHIVE = "archive"


@dataclass
class VideoCodec:
    """Video codec definition"""
    codec_id: str
    name: str
    encoder: str
    container: str
    file_extension: str
    compatibility: List[str] = field(default_factory=list)
    quality_range: Dict = field(default_factory=dict)
    default_params: Dict = field(default_factory=dict)
    
    def to_dict(self) -> Dict:
        return {
            "codec_id": self.codec_id,
            "name": self.name,
            "encoder": self.encoder,
            "container": self.container,
            "file_extension": self.file_extension,
            "compatibility": self.compatibility
        }


@dataclass
class AudioCodec:
    """Audio codec definition"""
    codec_id: str
    name: str
    encoder: str
    bitrate_range: Dict = field(default_factory=lambda: {"min": 64, "max": 320})
    sample_rates: List[int] = field(default_factory=lambda: [44100, 48000])
    
    def to_dict(self) -> Dict:
        return {
            "codec_id": self.codec_id,
            "name": self.name,
            "encoder": self.encoder,
            "bitrate_range": self.bitrate_range
        }


@dataclass
class Resolution:
    """Resolution definition"""
    preset_id: str
    name: str
    width: int
    height: int
    aspect_ratio: str
    common_name: str
    
    def to_dict(self) -> Dict:
        return {
            "preset_id": self.preset_id,
            "name": self.name,
            "width": self.width,
            "height": self.height,
            "aspect_ratio": self.aspect_ratio,
            "common_name": self.common_name
        }


@dataclass
class QualityPreset:
    """Quality preset definition"""
    preset_id: str
    name: str
    description: str
    target_quality: QualityLevel
    video_bitrate_kbps: int
    audio_bitrate_kbps: int
    crf_h264: int
    crf_h265: int
    encoding_speed: EncodingSpeed
    file_size_priority: bool = False
    is_system: bool = False
    
    def to_dict(self) -> Dict:
        return {
            "preset_id": self.preset_id,
            "name": self.name,
            "description": self.description,
            "target_quality": self.target_quality.value,
            "video_bitrate_kbps": self.video_bitrate_kbps,
            "audio_bitrate_kbps": self.audio_bitrate_kbps,
            "encoding_speed": self.encoding_speed.value,
            "is_system": self.is_system
        }


@dataclass
class ExportConfig:
    """Export configuration"""
    video_codec: str = "h264"
    audio_codec: str = "aac"
    resolution: str = "1080p"
    quality_preset: str = "medium"
    bitrate_mode: BitrateMode = BitrateMode.CRF
    target_size_mb: Optional[float] = None
    two_pass: bool = False
    optimize_for: OptimizeFor = OptimizeFor.STREAMING
    custom_settings: Dict = field(default_factory=dict)
    
    def to_dict(self) -> Dict:
        return {
            "video_codec": self.video_codec,
            "audio_codec": self.audio_codec,
            "resolution": self.resolution,
            "quality_preset": self.quality_preset,
            "bitrate_mode": self.bitrate_mode.value,
            "target_size_mb": self.target_size_mb,
            "two_pass": self.two_pass,
            "optimize_for": self.optimize_for.value
        }


@dataclass
class ExportJob:
    """Export job model"""
    export_id: str
    user_id: str
    source_id: str
    export_config: ExportConfig
    status: ExportStatus = ExportStatus.QUEUED
    progress: float = 0.0
    current_stage: str = ""
    output_files: List[str] = field(default_factory=list)
    file_sizes: Dict = field(default_factory=dict)
    error_message: str = ""
    webhook_url: str = ""
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    created_at: datetime = field(default_factory=datetime.utcnow)
    
    def to_dict(self) -> Dict:
        return {
            "export_id": self.export_id,
            "source_id": self.source_id,
            "status": self.status.value,
            "progress": round(self.progress, 1),
            "current_stage": self.current_stage,
            "output_files": self.output_files,
            "file_sizes": self.file_sizes,
            "error_message": self.error_message,
            "created_at": self.created_at.isoformat()
        }


@dataclass
class PlatformPreset:
    """Platform-specific export settings"""
    platform_id: str
    name: str
    video_codec: str
    audio_codec: str
    max_resolution: Dict
    max_file_size_mb: int
    max_duration_seconds: int
    recommended_settings: Dict = field(default_factory=dict)
    
    def to_dict(self) -> Dict:
        return {
            "platform_id": self.platform_id,
            "name": self.name,
            "video_codec": self.video_codec,
            "audio_codec": self.audio_codec,
            "max_resolution": self.max_resolution,
            "max_file_size_mb": self.max_file_size_mb,
            "max_duration_seconds": self.max_duration_seconds
        }


def create_export_id() -> str:
    return str(uuid.uuid4())
