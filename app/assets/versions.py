"""
Asset Versioning
Version history and rollback for assets.
"""
from typing import Dict, List, Optional
from datetime import datetime
import threading
import uuid

from app.assets.models import AssetVersion
from app.assets.storage import get_version_path, copy_file, delete_file


MAX_VERSIONS = 10


class VersionService:
    """Asset version management"""
    
    _instance = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._versions: Dict[str, List[AssetVersion]] = {}  # asset_id -> versions
            cls._instance._lock = threading.Lock()
        return cls._instance
    
    def create_version(
        self,
        asset_id: str,
        user_id: str,
        storage_path: str,
        file_size: int,
        checksum: str,
        extension: str,
        change_description: str = "",
        metadata: Dict = None
    ) -> AssetVersion:
        """Create new version of asset"""
        if asset_id not in self._versions:
            self._versions[asset_id] = []
        
        versions = self._versions[asset_id]
        version_number = len(versions) + 1
        
        # Copy file to version storage
        version_path = get_version_path(user_id, asset_id, version_number, extension)
        copy_file(storage_path, version_path)
        
        version = AssetVersion(
            version_id=str(uuid.uuid4()),
            asset_id=asset_id,
            version_number=version_number,
            storage_path=version_path,
            file_size=file_size,
            checksum=checksum,
            change_description=change_description,
            metadata=metadata or {},
            created_by=user_id
        )
        
        with self._lock:
            self._versions[asset_id].append(version)
            
            # Prune old versions if over limit
            self._prune_versions(asset_id)
        
        return version
    
    def get_versions(self, asset_id: str) -> List[AssetVersion]:
        """Get all versions for asset"""
        return self._versions.get(asset_id, [])
    
    def get_version(self, asset_id: str, version_number: int) -> Optional[AssetVersion]:
        """Get specific version"""
        versions = self._versions.get(asset_id, [])
        for v in versions:
            if v.version_number == version_number:
                return v
        return None
    
    def get_latest_version(self, asset_id: str) -> Optional[AssetVersion]:
        """Get most recent version"""
        versions = self._versions.get(asset_id, [])
        if versions:
            return versions[-1]
        return None
    
    def rollback_to_version(
        self,
        asset_id: str,
        version_number: int
    ) -> Optional[AssetVersion]:
        """Rollback asset to specific version"""
        version = self.get_version(asset_id, version_number)
        if not version:
            return None
        
        # Return version info for caller to update asset
        return version
    
    def delete_version(self, asset_id: str, version_number: int) -> bool:
        """Delete specific version"""
        versions = self._versions.get(asset_id, [])
        
        for i, v in enumerate(versions):
            if v.version_number == version_number:
                # Don't delete if it's the only version
                if len(versions) <= 1:
                    return False
                
                # Delete file
                delete_file(v.storage_path)
                
                with self._lock:
                    versions.pop(i)
                
                return True
        
        return False
    
    def _prune_versions(self, asset_id: str) -> None:
        """Remove old versions if over limit"""
        versions = self._versions.get(asset_id, [])
        
        while len(versions) > MAX_VERSIONS:
            # Remove oldest (keep current)
            oldest = versions[0]
            delete_file(oldest.storage_path)
            versions.pop(0)
    
    def get_version_count(self, asset_id: str) -> int:
        """Get number of versions"""
        return len(self._versions.get(asset_id, []))


version_service = VersionService()
