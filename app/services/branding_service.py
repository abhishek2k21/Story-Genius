"""
Custom Branding Service.
Add watermarks and custom logos to videos.
"""
import subprocess
import os
from typing import Optional, Tuple
from enum import Enum
import logging
from PIL import Image
import uuid

logger = logging.getLogger(__name__)


class BrandingPosition(str, Enum):
    """Watermark position options."""
    TOP_LEFT = "top_left"
    TOP_RIGHT = "top_right"
    BOTTOM_LEFT = "bottom_left"
    BOTTOM_RIGHT = "bottom_right"
    CENTER = "center"


class CustomBranding:
    """Custom branding configuration model."""
    
    def __init__(
        self,
        user_id: str,
        logo_url: str,
        position: BrandingPosition = BrandingPosition.BOTTOM_RIGHT,
        opacity: int = 80,  # 0-100
        scale: float = 0.1,  # 0.05-0.3 (relative to video width)
        margin: int = 20  # pixels from edge
    ):
        self.user_id = user_id
        self.logo_url = logo_url
        self.position = position
        self.opacity = opacity
        self.scale = scale
        self.margin = margin
        
        # Validate
        if not 0 <= opacity <= 100:
            raise ValueError("Opacity must be between 0 and 100")
        if not 0.05 <= scale <= 0.3:
            raise ValueError("Scale must be between 0.05 and 0.3")
    
    def to_dict(self):
        """Convert to dictionary."""
        return {
            "logo_url": self.logo_url,
            "position": self.position.value,
            "opacity": self.opacity,
            "scale": self.scale,
            "margin": self.margin
        }


class BrandingService:
    """Apply custom branding to videos."""
    
    def __init__(self, s3_client):
        self.s3_client = s3_client
    
    async def apply_branding(
        self,
        video_path: str,
        output_path: str,
        branding: CustomBranding
    ) -> str:
        """
        Apply branding watermark to video.
        
        Args:
            video_path: Input video path
            output_path: Output video path
            branding: Branding configuration
            
        Returns:
            Output video path
        """
        logger.info(f"Applying branding to video: {video_path}")
        
        # Download logo
        logo_path = await self._download_logo(branding.logo_url)
        
        # Prepare logo (resize, add transparency)
        prepared_logo_path = self._prepare_logo(
            logo_path,
            video_path,
            branding.scale,
            branding.opacity
        )
        
        # Get position filter
        position_filter = self._get_position_filter(
            branding.position,
            branding.margin
        )
        
        # Apply watermark with ffmpeg
        await self._apply_watermark(
            video_path,
            prepared_logo_path,
            output_path,
            position_filter
        )
        
        # Cleanup temporary files
        os.remove(logo_path)
        os.remove(prepared_logo_path)
        
        logger.info(f"Branding applied successfully: {output_path}")
        
        return output_path
    
    async def _download_logo(self, logo_url: str) -> str:
        """Download logo from S3 or URL."""
        # Download logo
        temp_path = f"/tmp/logo_{uuid.uuid4()}.png"
        
        # If S3 URL, download from S3
        # If HTTP URL, download via requests
        # Placeholder implementation
        
        return temp_path
    
    def _prepare_logo(
        self,
        logo_path: str,
        video_path: str,
        scale: float,
        opacity: int
    ) -> str:
        """Prepare logo (resize and set opacity)."""
        # Get video dimensions
        video_width, video_height = self._get_video_dimensions(video_path)
        
        # Calculate logo size
        logo_width = int(video_width * scale)
        
        # Open and resize logo
        logo = Image.open(logo_path)
        
        # Convert to RGBA
        if logo.mode != "RGBA":
            logo = logo.convert("RGBA")
        
        # Resize maintaining aspect ratio
        aspect_ratio = logo.height / logo.width
        logo_height = int(logo_width * aspect_ratio)
        logo = logo.resize((logo_width, logo_height), Image.Resampling.LANCZOS)
        
        # Apply opacity
        alpha = logo.split()[3]
        alpha = alpha.point(lambda p: int(p * (opacity / 100)))
        logo.putalpha(alpha)
        
        # Save prepared logo
        prepared_path = f"/tmp/prepared_logo_{uuid.uuid4()}.png"
        logo.save(prepared_path, "PNG")
        
        return prepared_path
    
    def _get_video_dimensions(self, video_path: str) -> Tuple[int, int]:
        """Get video dimensions using ffprobe."""
        cmd = [
            "ffprobe",
            "-v", "error",
            "-select_streams", "v:0",
            "-show_entries", "stream=width,height",
            "-of", "csv=s=x:p=0",
            video_path
        ]
        
        result = subprocess.run(cmd, capture_output=True, text=True)
        width, height = map(int, result.stdout.strip().split('x'))
        
        return width, height
    
    def _get_position_filter(
        self,
        position: BrandingPosition,
        margin: int
    ) -> str:
        """
        Get FFmpeg overlay position filter.
        
        Args:
            position: Watermark position
            margin: Margin from edge in pixels
            
        Returns:
            FFmpeg position filter string
        """
        positions = {
            BrandingPosition.TOP_LEFT: f"{margin}:{margin}",
            BrandingPosition.TOP_RIGHT: f"(main_w-overlay_w-{margin}):{margin}",
            BrandingPosition.BOTTOM_LEFT: f"{margin}:(main_h-overlay_h-{margin})",
            BrandingPosition.BOTTOM_RIGHT: f"(main_w-overlay_w-{margin}):(main_h-overlay_h-{margin})",
            BrandingPosition.CENTER: "(main_w-overlay_w)/2:(main_h-overlay_h)/2"
        }
        
        return positions[position]
    
    async def _apply_watermark(
        self,
        video_path: str,
        logo_path: str,
        output_path: str,
        position_filter: str
    ):
        """Apply watermark using FFmpeg."""
        cmd = [
            "ffmpeg",
            "-i", video_path,
            "-i", logo_path,
            "-filter_complex",
            f"[1:v]format=rgba[logo];[0:v][logo]overlay={position_filter}",
            "-codec:a", "copy",
            "-y",  # Overwrite output
            output_path
        ]
        
        logger.info(f"Running FFmpeg: {' '.join(cmd)}")
        
        process = await asyncio.create_subprocess_exec(
            *cmd,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE
        )
        
        stdout, stderr = await process.communicate()
        
        if process.returncode != 0:
            error_msg = stderr.decode()
            logger.error(f"FFmpeg error: {error_msg}")
            raise RuntimeError(f"Failed to apply watermark: {error_msg}")
    
    async def save_user_branding(
        self,
        user_id: str,
        branding: CustomBranding
    ):
        """Save user's branding configuration."""
        # Save to database
        # Placeholder
        logger.info(f"Saved branding config for user {user_id}")
    
    async def get_user_branding(self, user_id: str) -> Optional[CustomBranding]:
        """Get user's saved branding configuration."""
        # Query from database
        # Placeholder
        return None


# FastAPI endpoints
"""
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File
from pydantic import BaseModel
from app.services.branding_service import BrandingService, CustomBranding, BrandingPosition

router = APIRouter(prefix="/branding", tags=["branding"])

class BrandingConfig(BaseModel):
    logo_url: str
    position: str = "bottom_right"
    opacity: int = 80
    scale: float = 0.1
    margin: int = 20

@router.post("/upload-logo")
async def upload_logo(
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_user)
):
    '''Upload custom logo.'''
    # Validate file type
    if not file.content_type.startswith("image/"):
        raise HTTPException(status_code=400, detail="File must be an image")
    
    # Upload to S3
    # s3_url = await upload_to_s3(file, current_user.id)
    s3_url = f"https://s3.amazonaws.com/logos/{current_user.id}/{file.filename}"
    
    return {"logo_url": s3_url}

@router.post("/config")
async def save_branding_config(
    config: BrandingConfig,
    current_user: User = Depends(get_current_user)
):
    '''Save branding configuration.'''
    branding = CustomBranding(
        user_id=current_user.id,
        logo_url=config.logo_url,
        position=BrandingPosition(config.position),
        opacity=config.opacity,
        scale=config.scale,
        margin=config.margin
    )
    
    service = BrandingService(s3_client)
    await service.save_user_branding(current_user.id, branding)
    
    return {"success": True, "config": branding.to_dict()}

@router.get("/config")
async def get_branding_config(current_user: User = Depends(get_current_user)):
    '''Get saved branding configuration.'''
    service = BrandingService(s3_client)
    branding = await service.get_user_branding(current_user.id)
    
    if not branding:
        return {"has_branding": False}
    
    return {"has_branding": True, "config": branding.to_dict()}

@router.post("/apply/{video_id}")
async def apply_branding_to_video(
    video_id: str,
    current_user: User = Depends(get_current_user)
):
    '''Apply branding to a specific video.'''
    # Get user's branding config
    service = BrandingService(s3_client)
    branding = await service.get_user_branding(current_user.id)
    
    if not branding:
        raise HTTPException(status_code=400, detail="No branding configured")
    
    # Create job to apply branding
    job_id = create_branding_job(video_id, current_user.id, branding)
    
    return {
        "job_id": job_id,
        "status": "processing",
        "message": "Applying branding to video"
    }
"""
