"""
Video Versioning System.
Track video history and enable version restoration.
"""
from typing import List, Dict, Optional
from datetime import datetime
import uuid
import logging

logger = logging.getLogger(__name__)


class VideoVersion:
    """Video version model."""
    
    def __init__(
        self,
        id: str,
        video_id: str,
        version_number: int,
        s3_url: str,
        created_by: str,
        change_description: Optional[str] = None
    ):
        self.id = id
        self.video_id = video_id
        self.version_number = version_number
        self.s3_url = s3_url
        self.created_by = created_by
        self.change_description = change_description or "Updated video"
        self.created_at = datetime.utcnow()
        self.file_size = 0  # bytes
        self.duration_seconds = 0
        self.thumbnail_url: Optional[str] = None
    
    def to_dict(self) -> Dict:
        """Convert to dictionary."""
        return {
            "version_id": self.id,
            "version_number": self.version_number,
            "s3_url": self.s3_url,
            "created_by": self.created_by,
            "change_description": self.change_description,
            "created_at": self.created_at.isoformat(),
            "file_size_mb": round(self.file_size / 1024 / 1024, 2),
            "duration_seconds": self.duration_seconds,
            "thumbnail_url": self.thumbnail_url
        }


class VideoVersioningService:
    """Manage video versions."""
    
    def __init__(self, s3_client, video_service):
        self.s3 = s3_client
        self.video_service = video_service
        self.versions: Dict[str, List[VideoVersion]] = {}
    
    def create_version(
        self,
        video_id: str,
        user_id: str,
        video_file_path: str,
        change_description: str = "Updated video"
    ) -> Dict:
        """
        Create new video version.
        
        When user edits a video, save previous version as history.
        
        Args:
            video_id: Video ID
            user_id: User making change
            video_file_path: Path to new video file
            change_description: What changed
            
        Returns:
            Version details
        """
        # Get current version number
        current_versions = self.versions.get(video_id, [])
        new_version_number = len(current_versions) + 1
        
        # Get file metadata
        file_size = self._get_file_size(video_file_path)
        duration = self._get_video_duration(video_file_path)
        
        # Upload to S3 with version
        s3_url = self._upload_version(
            video_id,
            new_version_number,
            video_file_path
        )
        
        # Generate thumbnail
        thumbnail_url = self._generate_thumbnail(video_file_path, video_id, new_version_number)
        
        # Create version record
        version_id = str(uuid.uuid4())
        
        version = VideoVersion(
            id=version_id,
            video_id=video_id,
            version_number=new_version_number,
            s3_url=s3_url,
            created_by=user_id,
            change_description=change_description
        )
        
        version.file_size = file_size
        version.duration_seconds = duration
        version.thumbnail_url = thumbnail_url
        
        # Save version
        if video_id not in self.versions:
            self.versions[video_id] = []
        
        self.versions[video_id].append(version)
        self._save_version(version)
        
        logger.info(f"Created version {new_version_number} for video {video_id}")
        
        return version.to_dict()
    
    def get_version_history(
        self,
        video_id: str,
        limit: Optional[int] = None
    ) -> List[Dict]:
        """
        Get all versions for a video.
        
        Args:
            video_id: Video ID
            limit: Optional limit on number of versions
            
        Returns:
            List of versions (newest first)
        """
        versions = self.versions.get(video_id, [])
        
        # Sort by version number (newest first)
        versions.sort(key=lambda x: x.version_number, reverse=True)
        
        if limit:
            versions = versions[:limit]
        
        return [v.to_dict() for v in versions]
    
    def get_version(
        self,
        video_id: str,
        version_number: int
    ) -> Optional[Dict]:
        """Get specific version."""
        versions = self.versions.get(video_id, [])
        
        for v in versions:
            if v.version_number == version_number:
                return v.to_dict()
        
        return None
    
    def restore_version(
        self,
        video_id: str,
        version_number: int,
        user_id: str
    ) -> Dict:
        """
        Restore video to previous version.
        
        Creates a new version from the restored content.
        
        Args:
            video_id: Video ID
            version_number: Version to restore
            user_id: User performing restore
            
        Returns:
            New version details
        """
        # Get version to restore
        versions = self.versions.get(video_id, [])
        version_to_restore = None
        
        for v in versions:
            if v.version_number == version_number:
                version_to_restore = v
                break
        
        if not version_to_restore:
            raise ValueError(f"Version {version_number} not found for video {video_id}")
        
        # Download version from S3
        temp_file = self._download_from_s3(version_to_restore.s3_url)
        
        # Create new version from restored
        new_version = self.create_version(
            video_id=video_id,
            user_id=user_id,
            video_file_path=temp_file,
            change_description=f"Restored from version {version_number}"
        )
        
        logger.info(f"Restored video {video_id} to version {version_number}")
        
        return new_version
    
    def compare_versions(
        self,
        video_id: str,
        version_a: int,
        version_b: int
    ) -> Dict:
        """
        Compare two versions.
        
        Args:
            video_id: Video ID
            version_a: First version number
            version_b: Second version number
            
        Returns:
            Comparison details
        """
        versions = self.versions.get(video_id, [])
        
        v_a = next((v for v in versions if v.version_number == version_a), None)
        v_b = next((v for v in versions if v.version_number == version_b), None)
        
        if not v_a or not v_b:
            raise ValueError("One or both versions not found")
        
        # Calculate differences
        size_diff_mb = (v_b.file_size - v_a.file_size) / 1024 / 1024
        duration_diff = v_b.duration_seconds - v_a.duration_seconds
        time_between_hours = (v_b.created_at - v_a.created_at).total_seconds() / 3600
        
        return {
            "video_id": video_id,
            "version_a": {
                "number": version_a,
                "size_mb": round(v_a.file_size / 1024 / 1024, 2),
                "duration_sec": v_a.duration_seconds,
                "created_at": v_a.created_at.isoformat(),
                "created_by": v_a.created_by
            },
            "version_b": {
                "number": version_b,
                "size_mb": round(v_b.file_size / 1024 / 1024, 2),
                "duration_sec": v_b.duration_seconds,
                "created_at": v_b.created_at.isoformat(),
                "created_by": v_b.created_by
            },
            "differences": {
                "size_difference_mb": round(size_diff_mb, 2),
                "duration_difference_sec": round(duration_diff, 1),
                "hours_between": round(time_between_hours, 1)
            }
        }
    
    def delete_old_versions(
        self,
        video_id: str,
        keep_latest_n: int = 5
    ) -> int:
        """
        Delete old versions to save storage.
        
        Keeps the N most recent versions.
        
        Args:
            video_id: Video ID
            keep_latest_n: Number of recent versions to keep
            
        Returns:
            Number of versions deleted
        """
        versions = self.versions.get(video_id, [])
        
        if len(versions) <= keep_latest_n:
            return 0
        
        # Sort by version number
        versions.sort(key=lambda x: x.version_number, reverse=True)
        
        # Keep latest N, delete rest
        versions_to_delete = versions[keep_latest_n:]
        
        deleted_count = 0
        for version in versions_to_delete:
            # Delete from S3
            self._delete_from_s3(version.s3_url)
            
            # Remove from list
            self.versions[video_id].remove(version)
            
            deleted_count += 1
        
        logger.info(f"Deleted {deleted_count} old versions for video {video_id}")
        
        return deleted_count
    
    # Helper methods
    
    def _upload_version(
        self,
        video_id: str,
        version_number: int,
        file_path: str
    ) -> str:
        """Upload version to S3."""
        s3_key = f"videos/{video_id}/versions/v{version_number}.mp4"
        
        # Upload to S3
        # self.s3.upload_file(file_path, bucket, s3_key)
        
        return f"https://s3.amazonaws.com/bucket/{s3_key}"
    
    def _generate_thumbnail(
        self,
        video_path: str,
        video_id: str,
        version_number: int
    ) -> str:
        """Generate thumbnail for version."""
        # Use FFmpeg to extract frame
        thumbnail_key = f"videos/{video_id}/versions/v{version_number}_thumb.jpg"
        
        return f"https://s3.amazonaws.com/bucket/{thumbnail_key}"
    
    def _get_file_size(self, file_path: str) -> int:
        """Get file size in bytes."""
        import os
        return os.path.getsize(file_path)
    
    def _get_video_duration(self, file_path: str) -> int:
        """Get video duration in seconds."""
        # Use FFprobe or moviepy
        return 60  # Placeholder
    
    def _download_from_s3(self, s3_url: str) -> str:
        """Download file from S3."""
        # Download and return temp file path
        return "/tmp/restored_video.mp4"
    
    def _delete_from_s3(self, s3_url: str):
        """Delete file from S3."""
        pass
    
    def _save_version(self, version: VideoVersion):
        """Save version to database."""
        pass


# FastAPI endpoints
"""
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File
from app.services.video_versioning import VideoVersioningService

router = APIRouter(prefix="/videos/{video_id}/versions", tags=["versions"])

@router.post("/")
async def create_version(
    video_id: str,
    file: UploadFile = File(...),
    change_description: str = "Updated video",
    current_user: User = Depends(get_current_user)
):
    '''Create new video version.'''
    # Save uploaded file
    file_path = await save_upload(file)
    
    service = VideoVersioningService(s3_client, video_service)
    
    return service.create_version(
        video_id=video_id,
        user_id=current_user.id,
        video_file_path=file_path,
        change_description=change_description
    )

@router.get("/")
async def get_version_history(
    video_id: str,
    limit: Optional[int] = None,
    current_user: User = Depends(get_current_user)
):
    '''Get version history for video.'''
    service = VideoVersioningService(s3_client, video_service)
    return service.get_version_history(video_id, limit)

@router.post("/{version_number}/restore")
async def restore_version(
    video_id: str,
    version_number: int,
    current_user: User = Depends(get_current_user)
):
    '''Restore video to previous version.'''
    service = VideoVersioningService(s3_client, video_service)
    
    return service.restore_version(
        video_id=video_id,
        version_number=version_number,
        user_id=current_user.id
    )

@router.get("/compare/{version_a}/{version_b}")
async def compare_versions(
    video_id: str,
    version_a: int,
    version_b: int
):
    '''Compare two versions.'''
    service = VideoVersioningService(s3_client, video_service)
    return service.compare_versions(video_id, version_a, version_b)
"""
