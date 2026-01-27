"""
Export Service
Main export management.
"""
from typing import Dict, List, Optional, Tuple
from datetime import datetime
import threading

from app.exports.models import (
    ExportJob, ExportConfig, ExportStatus, BitrateMode, OptimizeFor,
    create_export_id
)
from app.exports.codecs import list_video_codecs, list_audio_codecs, get_video_codec
from app.exports.presets import list_presets, list_platforms, get_preset, get_platform
from app.exports.resolution import list_resolutions, get_resolution
from app.exports.size import estimate_file_size, calculate_bitrate_for_size, auto_optimize_for_platform
from app.exports.encoder import encoder


class ExportService:
    """Main export service"""
    
    _instance = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._jobs: Dict[str, ExportJob] = {}
            cls._instance._lock = threading.Lock()
        return cls._instance
    
    def create_export(
        self,
        user_id: str,
        source_id: str,
        video_codec: str = "h264",
        audio_codec: str = "aac",
        resolution: str = "1080p",
        quality_preset: str = "medium",
        bitrate_mode: str = "crf",
        target_size_mb: float = None,
        two_pass: bool = False,
        optimize_for: str = "streaming",
        webhook_url: str = "",
        custom_settings: Dict = None
    ) -> Tuple[Optional[ExportJob], str]:
        """Create export job"""
        
        # Validate codec
        if not get_video_codec(video_codec):
            return None, f"Invalid video codec: {video_codec}"
        
        # Validate resolution
        if not get_resolution(resolution):
            return None, f"Invalid resolution: {resolution}"
        
        # Validate preset
        if not get_preset(quality_preset):
            return None, f"Invalid quality preset: {quality_preset}"
        
        config = ExportConfig(
            video_codec=video_codec,
            audio_codec=audio_codec,
            resolution=resolution,
            quality_preset=quality_preset,
            bitrate_mode=BitrateMode(bitrate_mode),
            target_size_mb=target_size_mb,
            two_pass=two_pass,
            optimize_for=OptimizeFor(optimize_for),
            custom_settings=custom_settings or {}
        )
        
        job = ExportJob(
            export_id=create_export_id(),
            user_id=user_id,
            source_id=source_id,
            export_config=config,
            webhook_url=webhook_url
        )
        
        with self._lock:
            self._jobs[job.export_id] = job
        
        # Start processing (simulated)
        encoder.simulate_encode(job)
        
        return job, "Export created"
    
    def create_multi_export(
        self,
        user_id: str,
        source_id: str,
        exports: List[Dict],
        naming_pattern: str = "{name}_{resolution}",
        parallel: bool = False
    ) -> Tuple[List[ExportJob], str]:
        """Create multiple exports"""
        jobs = []
        
        for export_config in exports:
            job, msg = self.create_export(
                user_id=user_id,
                source_id=source_id,
                **export_config
            )
            if job:
                jobs.append(job)
        
        return jobs, f"Created {len(jobs)} exports"
    
    def get_export(self, export_id: str, user_id: str) -> Optional[ExportJob]:
        """Get export job"""
        job = self._jobs.get(export_id)
        if job and job.user_id == user_id:
            return job
        return None
    
    def list_exports(self, user_id: str, status: ExportStatus = None) -> List[ExportJob]:
        """List user's exports"""
        jobs = [j for j in self._jobs.values() if j.user_id == user_id]
        
        if status:
            jobs = [j for j in jobs if j.status == status]
        
        return sorted(jobs, key=lambda j: j.created_at, reverse=True)
    
    def cancel_export(self, export_id: str, user_id: str) -> Tuple[bool, str]:
        """Cancel export"""
        job = self.get_export(export_id, user_id)
        if not job:
            return False, "Export not found"
        
        if job.status in [ExportStatus.COMPLETED, ExportStatus.FAILED, ExportStatus.CANCELLED]:
            return False, f"Cannot cancel: {job.status.value}"
        
        job.status = ExportStatus.CANCELLED
        return True, "Export cancelled"
    
    def estimate_export(
        self,
        duration_seconds: float,
        video_codec: str,
        resolution: str,
        quality_preset: str
    ) -> Dict:
        """Estimate export size and time"""
        preset = get_preset(quality_preset)
        if not preset:
            return {"error": "Invalid preset"}
        
        from app.exports.resolution import get_resolution_bitrate_multiplier
        mult = get_resolution_bitrate_multiplier(resolution)
        effective_bitrate = int(preset.video_bitrate_kbps * mult)
        
        size_mb = estimate_file_size(
            duration_seconds,
            effective_bitrate,
            preset.audio_bitrate_kbps
        )
        
        # Estimate encoding time (rough)
        speed_mult = {
            "ultrafast": 1, "fast": 2, "medium": 4, "slow": 8, "veryslow": 16
        }
        mult = speed_mult.get(preset.encoding_speed.value, 4)
        estimated_time = duration_seconds * mult / 10  # Rough estimate
        
        return {
            "estimated_size_mb": size_mb,
            "estimated_time_seconds": round(estimated_time, 1),
            "effective_bitrate_kbps": effective_bitrate,
            "codec": video_codec,
            "resolution": resolution
        }
    
    def get_platform_settings(self, platform: str, duration_seconds: float) -> Dict:
        """Get optimized settings for platform"""
        return auto_optimize_for_platform(duration_seconds, platform)
    
    def get_codecs(self) -> Dict:
        """Get available codecs"""
        return {
            "video": [c.to_dict() for c in list_video_codecs()],
            "audio": [c.to_dict() for c in list_audio_codecs()]
        }
    
    def get_presets(self) -> List[Dict]:
        """Get quality presets"""
        return [p.to_dict() for p in list_presets()]
    
    def get_resolutions(self, aspect_ratio: str = None) -> List[Dict]:
        """Get resolutions"""
        return [r.to_dict() for r in list_resolutions(aspect_ratio)]
    
    def get_platforms(self) -> List[Dict]:
        """Get platform presets"""
        return [p.to_dict() for p in list_platforms()]


export_service = ExportService()
