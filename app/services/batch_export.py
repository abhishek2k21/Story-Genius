"""
Batch Video Export Service.
Export multiple videos as a single ZIP download.
"""
import os
import zipfile
import shutil
import asyncio
from typing import List, Dict, Optional
from datetime import datetime
import logging
import uuid

logger = logging.getLogger(__name__)


class BatchExportService:
    """Handle batch video exports."""
    
    def __init__(self, s3_client, video_service):
        self.s3_client = s3_client
        self.video_service = video_service
        self.jobs: Dict[str, Dict] = {}
    
    async def create_batch_export(
        self,
        user_id: str,
        video_ids: List[str],
        format: str = "mp4"
    ) -> Dict:
        """
        Create batch export job.
        
        Args:
            user_id: User ID
            video_ids: List of video IDs to export
            format: Export format (default: mp4)
            
        Returns:
            Export job details
        """
        # Validate
        if not video_ids:
            raise ValueError("No videos specified")
        
        if len(video_ids) > 50:
            raise ValueError("Maximum 50 videos per batch export")
        
        # Validate access to all videos
        for video_id in video_ids:
            if not await self._user_owns_video(user_id, video_id):
                raise PermissionError(f"No access to video {video_id}")
        
        # Create export job
        job_id = str(uuid.uuid4())
        
        self.jobs[job_id] = {
            "job_id": job_id,
            "user_id": user_id,
            "video_ids": video_ids,
            "status": "queued",
            "progress": 0,
            "total_videos": len(video_ids),
            "created_at": datetime.now().isoformat(),
            "download_url": None,
            "error": None
        }
        
        # Start async export
        asyncio.create_task(
            self._process_batch_export(job_id, user_id, video_ids, format)
        )
        
        logger.info(f"Created batch export job {job_id} for user {user_id}")
        
        return {
            "job_id": job_id,
            "status": "queued",
            "total_videos": len(video_ids),
            "estimated_time_minutes": len(video_ids) * 2
        }
    
    async def _process_batch_export(
        self,
        job_id: str,
        user_id: str,
        video_ids: List[str],
        format: str
    ):
        """Process batch export asynchronously."""
        try:
            # Update status
            self.jobs[job_id]["status"] = "processing"
            
            # Create temporary directory
            temp_dir = f"/tmp/batch_export_{job_id}"
            os.makedirs(temp_dir, exist_ok=True)
            
            # Download all videos
            for i, video_id in enumerate(video_ids):
                logger.info(f"Processing video {i+1}/{len(video_ids)}: {video_id}")
                
                # Get video metadata
                video = await self.video_service.get_video(video_id)
                
                # Sanitize filename
                safe_title = self._sanitize_filename(video['title'])
                video_path = f"{temp_dir}/{safe_title}.{format}"
                
                # Download from S3
                await self._download_video(video['s3_url'], video_path)
                
                # Update progress
                progress = int((i + 1) / len(video_ids) * 100)
                self.jobs[job_id]["progress"] = progress
                
                logger.info(f"Progress: {progress}%")
            
            # Create ZIP file
            zip_filename = f"videos_export_{datetime.now().strftime('%Y%m%d_%H%M%S')}.zip"
            zip_path = f"/tmp/{job_id}.zip"
            
            logger.info(f"Creating ZIP archive: {zip_filename}")
            self._create_zip(temp_dir, zip_path)
            
            # Upload to S3
            download_url = await self._upload_to_s3(
                zip_path,
                user_id,
                zip_filename
            )
            
            # Mark job complete
            self.jobs[job_id]["status"] = "completed"
            self.jobs[job_id]["download_url"] = download_url
            self.jobs[job_id]["completed_at"] = datetime.now().isoformat()
            
            logger.info(f"Batch export {job_id} completed successfully")
            
            # Send email notification
            await self._send_notification(user_id, job_id, download_url)
            
            # Cleanup
            os.remove(zip_path)
            shutil.rmtree(temp_dir)
            
        except Exception as e:
            logger.error(f"Batch export {job_id} failed: {str(e)}")
            
            self.jobs[job_id]["status"] = "failed"
            self.jobs[job_id]["error"] = str(e)
    
    def _create_zip(self, source_dir: str, output_path: str):
        """Create ZIP archive."""
        with zipfile.ZipFile(output_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
            for root, dirs, files in os.walk(source_dir):
                for file in files:
                    file_path = os.path.join(root, file)
                    arcname = os.path.relpath(file_path, source_dir)
                    zipf.write(file_path, arcname)
        
        logger.info(f"Created ZIP: {output_path}")
    
    def _sanitize_filename(self, filename: str) -> str:
        """Sanitize filename for safe storage."""
        # Remove/replace unsafe characters
        safe_chars = "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789-_ "
        sanitized = "".join(c if c in safe_chars else "_" for c in filename)
        
        # Limit length
        return sanitized[:100]
    
    async def _user_owns_video(self, user_id: str, video_id: str) -> bool:
        """Check if user owns video."""
        # Query database
        # Placeholder
        return True
    
    async def _download_video(self, url: str, dest_path: str):
        """Download video from S3."""
        # Download using S3 client
        # Placeholder
        pass
    
    async def _upload_to_s3(
        self,
        file_path: str,
        user_id: str,
        filename: str
    ) -> str:
        """Upload ZIP to S3 and return download URL."""
        # Upload to S3
        s3_key = f"exports/{user_id}/{filename}"
        
        # Generate presigned URL (valid for 7 days)
        download_url = f"https://s3.amazonaws.com/bucket/{s3_key}?presigned=..."
        
        return download_url
    
    async def _send_notification(
        self,
        user_id: str,
        job_id: str,
        download_url: str
    ):
        """Send email notification about completed export."""
        # Send email
        logger.info(f"Sending notification to user {user_id} for job {job_id}")
        # Email service would be called here
        pass
    
    async def get_job_status(self, job_id: str) -> Dict:
        """
        Get export job status.
        
        Args:
            job_id: Job ID
            
        Returns:
            Job status details
        """
        job = self.jobs.get(job_id)
        
        if not job:
            raise ValueError("Job not found")
        
        return {
            "job_id": job["job_id"],
            "status": job["status"],
            "progress": job["progress"],
            "total_videos": job["total_videos"],
            "download_url": job.get("download_url"),
            "error": job.get("error"),
            "created_at": job["created_at"]
        }
    
    async def cancel_job(self, job_id: str, user_id: str):
        """Cancel an export job."""
        job = self.jobs.get(job_id)
        
        if not job:
            raise ValueError("Job not found")
        
        if job["user_id"] != user_id:
            raise PermissionError("Not authorized")
        
        if job["status"] in ["completed", "failed"]:
            raise ValueError("Cannot cancel completed or failed job")
        
        job["status"] = "cancelled"
        logger.info(f"Job {job_id} cancelled by user {user_id}")


# FastAPI endpoints
"""
from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from pydantic import BaseModel
from app.services.batch_export import BatchExportService

router = APIRouter(prefix="/export", tags=["export"])

class BatchExportRequest(BaseModel):
    video_ids: List[str]
    format: str = "mp4"

@router.post("/batch")
async def create_batch_export(
    data: BatchExportRequest,
    current_user: User = Depends(get_current_user)
):
    '''Create batch export job.'''
    service = BatchExportService(s3_client, video_service)
    
    try:
        return await service.create_batch_export(
            user_id=current_user.id,
            video_ids=data.video_ids,
            format=data.format
        )
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.get("/batch/{job_id}")
async def get_export_status(
    job_id: str,
    current_user: User = Depends(get_current_user)
):
    '''Get export job status.'''
    service = BatchExportService(s3_client, video_service)
    
    try:
        return await service.get_job_status(job_id)
    except Exception as e:
        raise HTTPException(status_code=404, detail=str(e))

@router.delete("/batch/{job_id}")
async def cancel_export(
    job_id: str,
    current_user: User = Depends(get_current_user)
):
    '''Cancel export job.'''
    service = BatchExportService(s3_client, video_service)
    
    try:
        await service.cancel_job(job_id, current_user.id)
        return {"success": True}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))
"""
