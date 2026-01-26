"""
Multi-Platform Batch Processor
Enables generating same content for multiple platforms concurrently.
"""
import asyncio
from concurrent.futures import ThreadPoolExecutor
from typing import List, Dict
import os
import uuid
from app.core.video_formats import Platform, get_format
from app.services.video_processor import FormatAwareVideoProcessor
from app.core.logging import get_logger

logger = get_logger(__name__)


class MultiPlatformBatchProcessor:
    """Processes videos for multiple platforms concurrently"""
    
    def __init__(self, max_workers: int = 3, output_dir: str = ".story_assets/videos"):
        self.executor = ThreadPoolExecutor(max_workers=max_workers)
        self.output_dir = output_dir
        os.makedirs(output_dir, exist_ok=True)
    
    async def process_for_all_platforms(
        self,
        source_video_path: str,
        platforms: List[Platform],
        job_id: str
    ) -> Dict[str, dict]:
        """
        Process single source video for multiple platforms concurrently
        
        Args:
            source_video_path: Path to source video
            platforms: List of target platforms
            job_id: Unique job identifier
        
        Returns:
            Dictionary of results per platform
        """
        results = {}
        tasks = []
        
        logger.info(f"Starting batch processing for {len(platforms)} platforms")
        
        for platform in platforms:
            task = asyncio.get_event_loop().run_in_executor(
                self.executor,
                self._process_single_platform,
                source_video_path,
                platform,
                job_id
            )
            tasks.append((platform, task))
        
        for platform, task in tasks:
            try:
                result = await task
                results[platform.value] = result
                logger.info(f"Completed processing for {platform.value}")
            except Exception as e:
                logger.error(f"Failed processing for {platform.value}: {e}")
                results[platform.value] = {
                    "success": False,
                    "error": str(e)
                }
        
        return results
    
    def _process_single_platform(
        self,
        source_path: str,
        platform: Platform,
        job_id: str
    ) -> dict:
        """
        Process video for a single platform
        
        Args:
            source_path: Path to source video
            platform: Target platform
            job_id: Job identifier
        
        Returns:
            Processing result
        """
        from moviepy.editor import VideoFileClip
        
        video_format = get_format(platform)
        processor = FormatAwareVideoProcessor(video_format)
        
        # Create output path
        output_filename = f"{job_id}_{platform.value}.mp4"
        output_path = os.path.join(self.output_dir, output_filename)
        
        # Load and process
        clip = VideoFileClip(source_path)
        processed = processor.resize_clip_to_format(clip)
        
        # Trim to platform max if needed
        if processed.duration > video_format.max_duration:
            processed = processed.subclip(0, video_format.max_duration)
        
        # Export
        processed.write_videofile(
            output_path,
            fps=video_format.fps,
            codec='libx264',
            audio_codec='aac',
            preset='medium',
            logger=None
        )
        
        # Cleanup
        clip.close()
        processed.close()
        
        # Get file size
        file_size = os.path.getsize(output_path)
        
        return {
            "success": True,
            "output_path": output_path,
            "platform": platform.value,
            "resolution": f"{video_format.resolution[0]}x{video_format.resolution[1]}",
            "file_size_mb": round(file_size / (1024 * 1024), 2)
        }
    
    def cleanup(self):
        """Shutdown executor"""
        self.executor.shutdown(wait=False)


async def process_multi_platform_video(
    job_id: str,
    source_video_path: str,
    platforms: List[str],
    duration: int = None
) -> Dict:
    """
    Background task for multi-platform processing
    
    Args:
        job_id: Unique job ID
        source_video_path: Path to source video
        platforms: List of platform names
        duration: Optional target duration
    
    Returns:
        Processing results
    """
    logger.info(f"Starting multi-platform batch job {job_id}")
    
    # Convert platform names to enums
    platform_enums = [Platform(p) for p in platforms]
    
    # Process for all platforms
    processor = MultiPlatformBatchProcessor()
    
    try:
        results = await processor.process_for_all_platforms(
            source_video_path=source_video_path,
            platforms=platform_enums,
            job_id=job_id
        )
        
        logger.info(f"Batch job {job_id} completed")
        return results
        
    finally:
        processor.cleanup()
