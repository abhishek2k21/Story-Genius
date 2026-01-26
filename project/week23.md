CTO Analysis & Week 23 Plan - Story Genius
📊 Quick Project Assessment
After reviewing your repository and reports (Week 1-22), here's where you stand:

✅ What's Working
Video generation pipeline functional
Local PostgreSQL setup
Basic architecture established
Core backend foundations in place
⚠️ Critical Gaps for YT/Reels Creators
Gap Area	Impact	Priority
No aspect ratio support (9:16, 16:9, 1:1)	Creators can't post directly	🔴 HIGH
Missing template system	Slow content creation	🔴 HIGH
No batch processing	One video at a time = slow	🟡 MEDIUM
No trending audio/hooks integration	Less viral potential	🟡 MEDIUM
No analytics/performance tracking	Creators fly blind	🟠 MEDIUM
No direct platform export	Extra manual steps	🟡 MEDIUM
📅 Week 23 Plan: Multi-Format Video Architecture
🎯 Week Goal
Implement multi-aspect ratio support + video format presets for YT Shorts, Reels & TikTok

Day 1-2: Video Format Configuration System
What to do:
Create a format configuration module that handles all platform requirements.

How to do it:

# backend/app/core/video_formats.py

from enum import Enum
from dataclasses import dataclass
from typing import Tuple, Optional

class Platform(Enum):
    YOUTUBE_SHORTS = "youtube_shorts"
    INSTAGRAM_REELS = "instagram_reels"
    TIKTOK = "tiktok"
    YOUTUBE_LONG = "youtube_long"
    INSTAGRAM_POST = "instagram_post"

@dataclass
class VideoFormat:
    platform: Platform
    aspect_ratio: Tuple[int, int]  # (width, height)
    resolution: Tuple[int, int]
    max_duration: int  # seconds
    recommended_duration: Tuple[int, int]  # (min, max) seconds
    fps: int
    safe_zone: dict  # margins for text/UI elements

VIDEO_FORMATS = {
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
}

def get_format(platform: Platform) -> VideoFormat:
    return VIDEO_FORMATS.get(platform)

def get_all_short_formats() -> list:
    return [f for f in VIDEO_FORMATS.values() if f.aspect_ratio == (9, 16)]
Day 2-3: Database Schema Update
What to do:
Add platform/format support to your video projects table.

How to do it:

-- migrations/week23_video_formats.sql

-- Add enum type for platforms
CREATE TYPE video_platform AS ENUM (
    'youtube_shorts',
    'instagram_reels', 
    'tiktok',
    'youtube_long',
    'instagram_post'
);

-- Add format columns to video_projects table
ALTER TABLE video_projects 
ADD COLUMN target_platform video_platform DEFAULT 'youtube_shorts',
ADD COLUMN aspect_ratio VARCHAR(10) DEFAULT '9:16',
ADD COLUMN resolution_width INT DEFAULT 1080,
ADD COLUMN resolution_height INT DEFAULT 1920,
ADD COLUMN target_duration INT DEFAULT 30,
ADD COLUMN safe_zone_config JSONB DEFAULT '{}';

-- Create platform presets table for custom user presets
CREATE TABLE user_format_presets (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID REFERENCES users(id),
    preset_name VARCHAR(100) NOT NULL,
    base_platform video_platform,
    custom_resolution_width INT,
    custom_resolution_height INT,
    custom_safe_zone JSONB,
    is_default BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

-- Index for quick preset lookups
CREATE INDEX idx_user_presets ON user_format_presets(user_id, is_default);
Run migration:

psql -U your_user -d storygenius -f migrations/week23_video_formats.sql
Day 3-4: Video Processor Format Handler
What to do:
Modify your video generation pipeline to handle different formats.

How to do it:

# backend/app/services/video_processor.py

from moviepy.editor import VideoFileClip, CompositeVideoClip, ColorClip
from app.core.video_formats import VideoFormat, Platform, get_format
from typing import Optional
import os

class FormatAwareVideoProcessor:
    def __init__(self, video_format: VideoFormat):
        self.format = video_format
        self.width = video_format.resolution[0]
        self.height = video_format.resolution[1]
        self.safe_zone = video_format.safe_zone
        
    def resize_clip_to_format(self, clip: VideoFileClip) -> VideoFileClip:
        """Resize and crop clip to target format with smart cropping"""
        
        clip_aspect = clip.w / clip.h
        target_aspect = self.width / self.height
        
        if clip_aspect > target_aspect:
            # Clip is wider - crop sides
            new_width = int(clip.h * target_aspect)
            x_center = clip.w // 2
            x1 = x_center - new_width // 2
            clip = clip.crop(x1=x1, x2=x1 + new_width)
        else:
            # Clip is taller - crop top/bottom
            new_height = int(clip.w / target_aspect)
            y_center = clip.h // 2
            y1 = y_center - new_height // 2
            clip = clip.crop(y1=y1, y2=y1 + new_height)
        
        # Resize to exact resolution
        return clip.resize((self.width, self.height))
    
    def create_background_canvas(self, duration: float) -> ColorClip:
        """Create background canvas for compositing"""
        return ColorClip(
            size=(self.width, self.height),
            color=(0, 0, 0),
            duration=duration
        )
    
    def get_safe_text_position(self, position: str = "bottom") -> tuple:
        """Get text position within safe zone"""
        
        if position == "top":
            return ("center", self.safe_zone["top"])
        elif position == "bottom":
            return ("center", self.height - self.safe_zone["bottom"])
        elif position == "center":
            return ("center", "center")
        else:
            return ("center", self.height - self.safe_zone["bottom"])
    
    def validate_duration(self, duration: float) -> dict:
        """Validate video duration against platform limits"""
        
        result = {
            "valid": True,
            "duration": duration,
            "warnings": []
        }
        
        if duration > self.format.max_duration:
            result["valid"] = False
            result["warnings"].append(
                f"Duration {duration}s exceeds max {self.format.max_duration}s"
            )
        
        min_rec, max_rec = self.format.recommended_duration
        if duration < min_rec:
            result["warnings"].append(
                f"Duration below recommended minimum {min_rec}s"
            )
        elif duration > max_rec:
            result["warnings"].append(
                f"Duration above recommended maximum {max_rec}s"
            )
            
        return result


def process_video_for_platform(
    input_path: str,
    output_path: str,
    platform: Platform,
    target_duration: Optional[int] = None
) -> dict:
    """Main function to process video for specific platform"""
    
    video_format = get_format(platform)
    processor = FormatAwareVideoProcessor(video_format)
    
    # Load original clip
    clip = VideoFileClip(input_path)
    
    # Validate duration
    duration_check = processor.validate_duration(
        target_duration or clip.duration
    )
    
    # Resize to format
    processed_clip = processor.resize_clip_to_format(clip)
    
    # Trim if needed
    if target_duration and target_duration < processed_clip.duration:
        processed_clip = processed_clip.subclip(0, target_duration)
    
    # Export
    processed_clip.write_videofile(
        output_path,
        fps=video_format.fps,
        codec='libx264',
        audio_codec='aac',
        preset='medium',
        threads=4
    )
    
    # Cleanup
    clip.close()
    processed_clip.close()
    
    return {
        "success": True,
        "output_path": output_path,
        "format": video_format.platform.value,
        "resolution": f"{video_format.resolution[0]}x{video_format.resolution[1]}",
        "duration_validation": duration_check
    }
Day 4-5: API Endpoint Updates
What to do:
Add format selection to your video generation API.

How to do it:

# backend/app/api/v1/video_generation.py

from fastapi import APIRouter, HTTPException, BackgroundTasks
from pydantic import BaseModel, Field
from typing import Optional, List
from enum import Enum
from app.core.video_formats import Platform, get_format
from app.services.video_processor import process_video_for_platform

router = APIRouter(prefix="/video", tags=["Video Generation"])

class PlatformChoice(str, Enum):
    youtube_shorts = "youtube_shorts"
    instagram_reels = "instagram_reels"
    tiktok = "tiktok"
    youtube_long = "youtube_long"

class VideoGenerationRequest(BaseModel):
    story_id: str
    target_platforms: List[PlatformChoice] = Field(
        default=[PlatformChoice.youtube_shorts],
        description="Target platforms for video export"
    )
    duration: Optional[int] = Field(
        default=30,
        ge=5,
        le=180,
        description="Target duration in seconds"
    )
    
class VideoGenerationResponse(BaseModel):
    job_id: str
    status: str
    target_platforms: List[str]
    estimated_time: int

@router.post("/generate", response_model=VideoGenerationResponse)
async def generate_video(
    request: VideoGenerationRequest,
    background_tasks: BackgroundTasks
):
    """Generate video for multiple platforms"""
    
    # Validate platforms
    formats_info = []
    for platform in request.target_platforms:
        fmt = get_format(Platform(platform.value))
        
        # Check duration compatibility
        if request.duration > fmt.max_duration:
            raise HTTPException(
                status_code=400,
                detail=f"Duration {request.duration}s exceeds {platform.value} max of {fmt.max_duration}s"
            )
        formats_info.append(fmt)
    
    # Create job
    job_id = create_generation_job(
        story_id=request.story_id,
        platforms=[p.value for p in request.target_platforms],
        duration=request.duration
    )
    
    # Queue background processing
    background_tasks.add_task(
        process_multi_platform_video,
        job_id=job_id,
        story_id=request.story_id,
        platforms=request.target_platforms,
        duration=request.duration
    )
    
    return VideoGenerationResponse(
        job_id=job_id,
        status="queued",
        target_platforms=[p.value for p in request.target_platforms],
        estimated_time=len(request.target_platforms) * 60  # rough estimate
    )

@router.get("/formats")
async def get_available_formats():
    """Get all available video formats with specs"""
    
    from app.core.video_formats import VIDEO_FORMATS
    
    return {
        platform.value: {
            "aspect_ratio": f"{fmt.aspect_ratio[0]}:{fmt.aspect_ratio[1]}",
            "resolution": f"{fmt.resolution[0]}x{fmt.resolution[1]}",
            "max_duration": fmt.max_duration,
            "recommended_duration": {
                "min": fmt.recommended_duration[0],
                "max": fmt.recommended_duration[1]
            },
            "fps": fmt.fps
        }
        for platform, fmt in VIDEO_FORMATS.items()
    }
Day 5-6: Multi-Platform Batch Processor
What to do:
Enable generating same content for multiple platforms in one go.

How to do it:

# backend/app/services/batch_processor.py

import asyncio
from concurrent.futures import ThreadPoolExecutor
from typing import List, Dict
import os
from app.core.video_formats import Platform, get_format
from app.services.video_processor import FormatAwareVideoProcessor
from moviepy.editor import VideoFileClip
import uuid

class MultiPlatformBatchProcessor:
    def __init__(self, max_workers: int = 3):
        self.executor = ThreadPoolExecutor(max_workers=max_workers)
        self.output_dir = "outputs/videos"
        
    async def process_for_all_platforms(
        self,
        source_video_path: str,
        platforms: List[Platform],
        job_id: str
    ) -> Dict[str, dict]:
        """Process single source for multiple platforms concurrently"""
        
        results = {}
        tasks = []
        
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
            except Exception as e:
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
        """Process video for a single platform"""
        
        video_format = get_format(platform)
        processor = FormatAwareVideoProcessor(video_format)
        
        # Create output path
        output_filename = f"{job_id}_{platform.value}.mp4"
        output_path = os.path.join(self.output_dir, output_filename)
        
        # Ensure output directory exists
        os.makedirs(self.output_dir, exist_ok=True)
        
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
            preset='medium'
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


# Background task function
async def process_multi_platform_video(
    job_id: str,
    story_id: str,
    platforms: List,
    duration: int
):
    """Background task for multi-platform processing"""
    
    from app.services.story_to_video import generate_base_video
    from app.db.crud import update_job_status, save_video_outputs
    
    try:
        # Update status
        await update_job_status(job_id, "processing")
        
        # Generate base video from story
        base_video_path = await generate_base_video(story_id, duration)
        
        # Process for all platforms
        processor = MultiPlatformBatchProcessor()
        platform_enums = [Platform(p.value) for p in platforms]
        
        results = await processor.process_for_all_platforms(
            source_video_path=base_video_path,
            platforms=platform_enums,
            job_id=job_id
        )
        
        # Save results to DB
        await save_video_outputs(job_id, results)
        await update_job_status(job_id, "completed")
        
    except Exception as e:
        await update_job_status(job_id, "failed", error=str(e))
        raise
Day 6-7: Testing & Integration
What to do:
Test the complete flow and add integration tests.

How to do it:

# tests/test_video_formats.py

import pytest
from app.core.video_formats import Platform, get_format, VIDEO_FORMATS

class TestVideoFormats:
    
    def test_all_platforms_have_formats(self):
        """Ensure all platforms have defined formats"""
        for platform in Platform:
            fmt = get_format(platform)
            assert fmt is not None
            assert fmt.resolution[0] > 0
            assert fmt.resolution[1] > 0
    
    def test_shorts_aspect_ratios(self):
        """All short-form should be 9:16"""
        short_platforms = [
            Platform.YOUTUBE_SHORTS,
            Platform.INSTAGRAM_REELS,
            Platform.TIKTOK
        ]
        for platform in short_platforms:
            fmt = get_format(platform)
            assert fmt.aspect_ratio == (9, 16)
    
    def test_safe_zones_defined(self):
        """All formats should have safe zones"""
        for platform, fmt in VIDEO_FORMATS.items():
            assert "top" in fmt.safe_zone
            assert "bottom" in fmt.safe_zone
            assert fmt.safe_zone["top"] >= 0
            assert fmt.safe_zone["bottom"] >= 0


# tests/test_video_processor.py

import pytest
from app.services.video_processor import FormatAwareVideoProcessor
from app.core.video_formats import Platform, get_format

class TestVideoProcessor:
    
    @pytest.fixture
    def shorts_processor(self):
        fmt = get_format(Platform.YOUTUBE_SHORTS)
        return FormatAwareVideoProcessor(fmt)
    
    def test_duration_validation_valid(self, shorts_processor):
        result = shorts_processor.validate_duration(30)
        assert result["valid"] == True
        assert len(result["warnings"]) == 0
    
    def test_duration_validation_exceeds_max(self, shorts_processor):
        result = shorts_processor.validate_duration(90)  # Shorts max is 60
        assert result["valid"] == False
    
    def test_safe_text_positions(self, shorts_processor):
        bottom_pos = shorts_processor.get_safe_text_position("bottom")
        assert bottom_pos[0] == "center"
        assert bottom_pos[1] > 0
Run tests:

cd backend
pytest tests/test_video_formats.py -v
pytest tests/test_video_processor.py -v
📋 Week 23 Deliverables Checklist
Task	File(s)	Status
Video formats config	backend/app/core/video_formats.py	⬜
DB migration	migrations/week23_video_formats.sql	⬜
Format-aware processor	backend/app/services/video_processor.py	⬜
Updated API endpoints	backend/app/api/v1/video_generation.py	⬜
Batch processor	backend/app/services/batch_processor.py	⬜
Unit tests	tests/test_video_*.py	⬜
Integration test	Manual testing	⬜
🎯 Success Criteria for Week 23
✅ Can generate video in 9:16 format (Shorts/Reels/TikTok)
✅ Can generate video in 16:9 format (YouTube Long)
✅ Single story → multiple platform exports in one API call
✅ Safe zones respected for text overlays
✅ Duration validation per platform
✅ All tests passing
📌 Commands Summary
# Run migration
psql -U postgres -d storygenius -f migrations/week23_video_formats.sql

# Run tests
pytest tests/ -v

# Start backend
uvicorn app.main:app --reload

# Test endpoint
curl -X POST http://localhost:8000/api/v1/video/generate \
  -H "Content-Type: application/json" \
  -d '{"story_id": "xxx", "target_platforms": ["youtube_shorts", "instagram_ree