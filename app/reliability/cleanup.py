"""
Artifact Cleanup Routines
Manages cleanup of temporary files, failed job artifacts, and orphaned data.
"""
from typing import Dict, List, Optional
from dataclasses import dataclass
from datetime import datetime, timedelta
from enum import Enum
import os
import shutil
import json

from app.core.logging import get_logger

logger = get_logger(__name__)


class ArtifactType(str, Enum):
    """Types of artifacts that can be cleaned"""
    TEMP_FILES = "temp_files"
    FAILED_JOB = "failed_job"
    DEAD_LETTER = "dead_letter"
    PREVIEW = "preview"
    COMPLETED = "completed"
    ORPHANED = "orphaned"


# Retention policies (in hours)
RETENTION_POLICIES = {
    ArtifactType.TEMP_FILES: 1,
    ArtifactType.FAILED_JOB: 168,  # 7 days
    ArtifactType.DEAD_LETTER: 720,  # 30 days
    ArtifactType.PREVIEW: 24,
    ArtifactType.COMPLETED: 720,  # 30 days (configurable by user)
    ArtifactType.ORPHANED: 0  # Immediate
}


@dataclass
class CleanupTarget:
    """A file or directory targeted for cleanup"""
    path: str
    artifact_type: ArtifactType
    size_bytes: int
    age_hours: float
    
    def to_dict(self):
        return {
            "path": self.path,
            "type": self.artifact_type.value,
            "size_mb": round(self.size_bytes / (1024 * 1024), 2),
            "age_hours": round(self.age_hours, 1)
        }


@dataclass
class CleanupResult:
    """Result of a cleanup operation"""
    timestamp: datetime
    artifact_type: ArtifactType
    items_scanned: int
    items_deleted: int
    bytes_reclaimed: int
    errors: List[str]
    
    def to_dict(self):
        return {
            "timestamp": self.timestamp.isoformat(),
            "type": self.artifact_type.value,
            "scanned": self.items_scanned,
            "deleted": self.items_deleted,
            "bytes_reclaimed": self.bytes_reclaimed,
            "mb_reclaimed": round(self.bytes_reclaimed / (1024 * 1024), 2),
            "errors": self.errors
        }


class CleanupService:
    """Service for cleaning up artifacts"""
    
    def __init__(self):
        self.base_path = ".story_assets"
        self.paths = {
            ArtifactType.TEMP_FILES: os.path.join(self.base_path, "temp"),
            ArtifactType.FAILED_JOB: os.path.join(self.base_path, "failed"),
            ArtifactType.PREVIEW: os.path.join(self.base_path, "previews"),
            ArtifactType.COMPLETED: os.path.join(self.base_path, "videos"),
            ArtifactType.DEAD_LETTER: os.path.join(self.base_path, "dead_letters")
        }
    
    def preview_cleanup(
        self,
        artifact_type: Optional[ArtifactType] = None
    ) -> Dict:
        """Preview what would be cleaned up without deleting"""
        targets = self._find_cleanup_targets(artifact_type)
        
        total_size = sum(t.size_bytes for t in targets)
        
        return {
            "timestamp": datetime.now().isoformat(),
            "dry_run": True,
            "targets_count": len(targets),
            "total_size_mb": round(total_size / (1024 * 1024), 2),
            "targets": [t.to_dict() for t in targets[:50]],  # Limit to 50 for preview
            "by_type": self._group_by_type(targets)
        }
    
    def run_cleanup(
        self,
        artifact_type: Optional[ArtifactType] = None,
        dry_run: bool = False
    ) -> List[CleanupResult]:
        """Run cleanup for specified type or all types"""
        if artifact_type:
            types_to_clean = [artifact_type]
        else:
            types_to_clean = list(ArtifactType)
        
        results = []
        for atype in types_to_clean:
            result = self._cleanup_type(atype, dry_run)
            results.append(result)
        
        return results
    
    def _cleanup_type(
        self,
        artifact_type: ArtifactType,
        dry_run: bool
    ) -> CleanupResult:
        """Clean up artifacts of a specific type"""
        targets = self._find_cleanup_targets(artifact_type)
        targets = [t for t in targets if t.artifact_type == artifact_type]
        
        deleted = 0
        bytes_reclaimed = 0
        errors = []
        
        for target in targets:
            if dry_run:
                deleted += 1
                bytes_reclaimed += target.size_bytes
            else:
                try:
                    if os.path.isfile(target.path):
                        os.remove(target.path)
                    elif os.path.isdir(target.path):
                        shutil.rmtree(target.path)
                    
                    deleted += 1
                    bytes_reclaimed += target.size_bytes
                    logger.debug(f"Deleted: {target.path}")
                    
                except Exception as e:
                    errors.append(f"{target.path}: {str(e)}")
                    logger.error(f"Error deleting {target.path}: {e}")
        
        result = CleanupResult(
            timestamp=datetime.now(),
            artifact_type=artifact_type,
            items_scanned=len(targets),
            items_deleted=deleted,
            bytes_reclaimed=bytes_reclaimed,
            errors=errors
        )
        
        if not dry_run:
            logger.info(
                f"Cleanup {artifact_type.value}: {deleted} items, "
                f"{bytes_reclaimed / (1024*1024):.1f}MB reclaimed"
            )
        
        return result
    
    def _find_cleanup_targets(
        self,
        artifact_type: Optional[ArtifactType] = None
    ) -> List[CleanupTarget]:
        """Find all files eligible for cleanup"""
        targets = []
        
        types_to_scan = [artifact_type] if artifact_type else list(ArtifactType)
        
        for atype in types_to_scan:
            path = self.paths.get(atype)
            if not path or not os.path.exists(path):
                continue
            
            retention_hours = RETENTION_POLICIES.get(atype, 24)
            cutoff = datetime.now() - timedelta(hours=retention_hours)
            
            for root, dirs, files in os.walk(path):
                for filename in files:
                    filepath = os.path.join(root, filename)
                    try:
                        stat = os.stat(filepath)
                        mtime = datetime.fromtimestamp(stat.st_mtime)
                        
                        if mtime < cutoff:
                            age_hours = (datetime.now() - mtime).total_seconds() / 3600
                            targets.append(CleanupTarget(
                                path=filepath,
                                artifact_type=atype,
                                size_bytes=stat.st_size,
                                age_hours=age_hours
                            ))
                    except Exception as e:
                        logger.error(f"Error scanning {filepath}: {e}")
        
        return targets
    
    def _group_by_type(self, targets: List[CleanupTarget]) -> Dict:
        """Group targets by artifact type"""
        grouped = {}
        for target in targets:
            key = target.artifact_type.value
            if key not in grouped:
                grouped[key] = {"count": 0, "size_mb": 0}
            grouped[key]["count"] += 1
            grouped[key]["size_mb"] += target.size_bytes / (1024 * 1024)
        
        # Round sizes
        for key in grouped:
            grouped[key]["size_mb"] = round(grouped[key]["size_mb"], 2)
        
        return grouped
    
    def get_storage_stats(self) -> Dict:
        """Get storage usage statistics"""
        stats = {}
        total_size = 0
        
        for atype, path in self.paths.items():
            if os.path.exists(path):
                size = self._get_dir_size(path)
                stats[atype.value] = {
                    "path": path,
                    "size_mb": round(size / (1024 * 1024), 2),
                    "file_count": self._count_files(path)
                }
                total_size += size
            else:
                stats[atype.value] = {
                    "path": path,
                    "size_mb": 0,
                    "file_count": 0
                }
        
        stats["total"] = {
            "size_mb": round(total_size / (1024 * 1024), 2)
        }
        
        return stats
    
    def _get_dir_size(self, path: str) -> int:
        """Get total size of directory"""
        total = 0
        for root, dirs, files in os.walk(path):
            for f in files:
                try:
                    total += os.path.getsize(os.path.join(root, f))
                except:
                    pass
        return total
    
    def _count_files(self, path: str) -> int:
        """Count files in directory"""
        count = 0
        for root, dirs, files in os.walk(path):
            count += len(files)
        return count
