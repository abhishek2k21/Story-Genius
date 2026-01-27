"""
Export Encoder
Encoding execution and FFmpeg command building.
"""
from typing import Dict, List
from datetime import datetime
import uuid

from app.exports.models import ExportJob, ExportConfig, ExportStatus, BitrateMode
from app.exports.codecs import get_video_codec, get_audio_codec, get_container_for_codec
from app.exports.presets import get_preset, get_crf_for_quality
from app.exports.resolution import get_resolution


class Encoder:
    """Build and execute encoding commands"""
    
    def build_ffmpeg_command(
        self,
        input_path: str,
        output_path: str,
        config: ExportConfig
    ) -> List[str]:
        """Build FFmpeg command from config"""
        cmd = ["ffmpeg", "-y", "-i", input_path]
        
        # Video codec settings
        video_codec = get_video_codec(config.video_codec)
        if video_codec:
            cmd.extend(["-c:v", video_codec.encoder])
            
            # Apply preset defaults
            for key, value in video_codec.default_params.items():
                cmd.extend([f"-{key}", str(value)])
        
        # Quality settings
        preset = get_preset(config.quality_preset)
        if preset:
            if config.bitrate_mode == BitrateMode.CRF:
                crf = preset.crf_h264 if config.video_codec == "h264" else preset.crf_h265
                cmd.extend(["-crf", str(crf)])
            else:
                cmd.extend(["-b:v", f"{preset.video_bitrate_kbps}k"])
            
            cmd.extend(["-preset", preset.encoding_speed.value])
        
        # Resolution
        resolution = get_resolution(config.resolution)
        if resolution:
            cmd.extend(["-vf", f"scale={resolution.width}:{resolution.height}"])
        
        # Audio codec
        audio_codec = get_audio_codec(config.audio_codec)
        if audio_codec:
            cmd.extend(["-c:a", audio_codec.encoder])
            if preset:
                cmd.extend(["-b:a", f"{preset.audio_bitrate_kbps}k"])
        
        # Streaming optimization
        if config.optimize_for.value == "streaming":
            cmd.extend(["-movflags", "+faststart"])
        
        # Output
        cmd.append(output_path)
        
        return cmd
    
    def build_two_pass_commands(
        self,
        input_path: str,
        output_path: str,
        config: ExportConfig,
        passlog_prefix: str = "passlog"
    ) -> tuple:
        """Build two-pass encoding commands"""
        # First pass
        pass1 = ["ffmpeg", "-y", "-i", input_path]
        
        video_codec = get_video_codec(config.video_codec)
        if video_codec:
            pass1.extend(["-c:v", video_codec.encoder])
        
        preset = get_preset(config.quality_preset)
        if preset:
            pass1.extend(["-b:v", f"{preset.video_bitrate_kbps}k"])
            pass1.extend(["-preset", preset.encoding_speed.value])
        
        pass1.extend([
            "-pass", "1",
            "-passlogfile", passlog_prefix,
            "-an",  # No audio in first pass
            "-f", "null",
            "/dev/null" if True else "NUL"  # Windows: NUL
        ])
        
        # Second pass
        pass2 = ["ffmpeg", "-y", "-i", input_path]
        
        if video_codec:
            pass2.extend(["-c:v", video_codec.encoder])
        
        if preset:
            pass2.extend(["-b:v", f"{preset.video_bitrate_kbps}k"])
            pass2.extend(["-preset", preset.encoding_speed.value])
        
        pass2.extend([
            "-pass", "2",
            "-passlogfile", passlog_prefix
        ])
        
        # Audio in second pass
        audio_codec = get_audio_codec(config.audio_codec)
        if audio_codec:
            pass2.extend(["-c:a", audio_codec.encoder])
            if preset:
                pass2.extend(["-b:a", f"{preset.audio_bitrate_kbps}k"])
        
        # Resolution
        resolution = get_resolution(config.resolution)
        if resolution:
            pass2.extend(["-vf", f"scale={resolution.width}:{resolution.height}"])
        
        pass2.append(output_path)
        
        return pass1, pass2
    
    def get_output_extension(self, config: ExportConfig) -> str:
        """Get output file extension"""
        video_codec = get_video_codec(config.video_codec)
        return video_codec.file_extension if video_codec else ".mp4"
    
    def simulate_encode(self, job: ExportJob) -> Dict:
        """Simulate encoding (for testing)"""
        job.status = ExportStatus.ENCODING
        job.started_at = datetime.utcnow()
        job.current_stage = "encoding"
        job.progress = 50.0
        
        # Simulate completion
        job.status = ExportStatus.COMPLETED
        job.completed_at = datetime.utcnow()
        job.progress = 100.0
        
        output_file = f"export_{job.export_id}{self.get_output_extension(job.export_config)}"
        job.output_files = [output_file]
        job.file_sizes = {output_file: 50.0}  # Simulated 50MB
        
        return {
            "status": "completed",
            "output_files": job.output_files,
            "file_sizes": job.file_sizes
        }


encoder = Encoder()
