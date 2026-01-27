"""
Asset Service
Main asset management operations.
"""
from typing import Dict, List, Optional, Tuple
from datetime import datetime
import threading

from app.assets.models import (
    Asset, AssetType, AssetStatus, AssetReference,
    create_asset_id, get_asset_type_from_extension, validate_asset_type
)
from app.assets.storage import (
    get_storage_path, save_file, delete_file, calculate_checksum_from_bytes
)
from app.assets.folders import folder_service
from app.assets.tags import tag_service
from app.assets.versions import version_service


class AssetService:
    """Central asset management service"""
    
    _instance = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._assets: Dict[str, Asset] = {}
            cls._instance._references: Dict[str, List[AssetReference]] = {}
            cls._instance._lock = threading.Lock()
        return cls._instance
    
    def upload_asset(
        self,
        user_id: str,
        filename: str,
        data: bytes,
        name: str = None,
        description: str = "",
        folder_id: str = None,
        tags: List[str] = None
    ) -> Tuple[Optional[Asset], str]:
        """Upload new asset"""
        # Extract extension and determine type
        ext = filename.rsplit('.', 1)[-1].lower() if '.' in filename else ""
        asset_type = get_asset_type_from_extension(ext)
        
        if not asset_type:
            return None, f"Unsupported file type: {ext}"
        
        # Validate
        valid, msg = validate_asset_type(asset_type, ext, len(data))
        if not valid:
            return None, msg
        
        # Check for duplicates
        checksum = calculate_checksum_from_bytes(data)
        existing = self._find_by_checksum(user_id, checksum)
        if existing:
            return existing, f"Duplicate detected. Existing asset: {existing.name}"
        
        # Generate storage path
        asset_id = create_asset_id()
        storage_path = get_storage_path(user_id, asset_type.value, asset_id, ext)
        
        # Save file
        file_size = save_file(data, storage_path)
        
        # Create asset record
        asset = Asset(
            asset_id=asset_id,
            user_id=user_id,
            name=name or filename,
            asset_type=asset_type,
            mime_type=self._get_mime_type(ext),
            file_extension=ext,
            file_size=file_size,
            storage_path=storage_path,
            original_filename=filename,
            checksum=checksum,
            description=description,
            folder_id=folder_id,
            status=AssetStatus.READY
        )
        
        with self._lock:
            self._assets[asset_id] = asset
        
        # Update folder count
        if folder_id:
            folder_service.increment_asset_count(folder_id)
        
        # Add tags
        if tags:
            tag_service.add_tags_to_asset(asset_id, tags)
        
        # Create initial version
        version_service.create_version(
            asset_id=asset_id,
            user_id=user_id,
            storage_path=storage_path,
            file_size=file_size,
            checksum=checksum,
            extension=ext,
            change_description="Initial upload"
        )
        
        return asset, "Asset uploaded successfully"
    
    def get_asset(self, asset_id: str, user_id: str) -> Optional[Asset]:
        """Get asset by ID"""
        asset = self._assets.get(asset_id)
        if asset and asset.user_id == user_id and asset.status != AssetStatus.DELETED:
            return asset
        return None
    
    def list_assets(
        self,
        user_id: str,
        asset_type: str = None,
        folder_id: str = None,
        status: str = None
    ) -> List[Asset]:
        """List assets with filters"""
        assets = [
            a for a in self._assets.values()
            if a.user_id == user_id and a.status != AssetStatus.DELETED
        ]
        
        if asset_type:
            assets = [a for a in assets if a.asset_type.value == asset_type]
        
        if folder_id:
            assets = [a for a in assets if a.folder_id == folder_id]
        
        if status:
            assets = [a for a in assets if a.status.value == status]
        
        return sorted(assets, key=lambda a: a.created_at, reverse=True)
    
    def update_asset(
        self,
        asset_id: str,
        user_id: str,
        name: str = None,
        description: str = None,
        folder_id: str = None
    ) -> Tuple[Optional[Asset], str]:
        """Update asset metadata"""
        asset = self.get_asset(asset_id, user_id)
        if not asset:
            return None, "Asset not found"
        
        old_folder = asset.folder_id
        
        if name:
            asset.name = name
        if description is not None:
            asset.description = description
        if folder_id is not None:
            asset.folder_id = folder_id
            
            # Update folder counts
            if old_folder:
                folder_service.decrement_asset_count(old_folder)
            if folder_id:
                folder_service.increment_asset_count(folder_id)
        
        asset.updated_at = datetime.utcnow()
        return asset, "Asset updated"
    
    def delete_asset(self, asset_id: str, user_id: str, force: bool = False) -> Tuple[bool, str]:
        """Delete asset"""
        asset = self.get_asset(asset_id, user_id)
        if not asset:
            return False, "Asset not found"
        
        # Check references
        refs = self._references.get(asset_id, [])
        if refs and not force:
            return False, f"Asset is used in {len(refs)} resources. Use force=true to delete."
        
        # Soft delete
        asset.status = AssetStatus.DELETED
        asset.updated_at = datetime.utcnow()
        
        # Update folder count
        if asset.folder_id:
            folder_service.decrement_asset_count(asset.folder_id)
        
        return True, "Asset deleted"
    
    def search_assets(
        self,
        user_id: str,
        query: str = None,
        asset_type: str = None,
        tags: List[str] = None,
        folder_id: str = None
    ) -> List[Asset]:
        """Search assets"""
        assets = self.list_assets(user_id, asset_type, folder_id)
        
        if query:
            query_lower = query.lower()
            assets = [a for a in assets if query_lower in a.name.lower()]
        
        if tags:
            tag_assets = set()
            for tag_id in tags:
                tag_assets.update(tag_service.get_assets_by_tag(tag_id))
            assets = [a for a in assets if a.asset_id in tag_assets]
        
        return assets
    
    def add_reference(
        self,
        asset_id: str,
        resource_type: str,
        resource_id: str,
        usage_type: str
    ) -> None:
        """Track asset usage"""
        if asset_id not in self._references:
            self._references[asset_id] = []
        
        ref = AssetReference(
            reference_id=create_asset_id(),
            asset_id=asset_id,
            resource_type=resource_type,
            resource_id=resource_id,
            usage_type=usage_type
        )
        self._references[asset_id].append(ref)
    
    def get_references(self, asset_id: str) -> List[AssetReference]:
        """Get asset references"""
        return self._references.get(asset_id, [])
    
    def get_stats(self, user_id: str) -> Dict:
        """Get asset statistics for user"""
        assets = [a for a in self._assets.values() if a.user_id == user_id and a.status != AssetStatus.DELETED]
        
        by_type = {}
        total_size = 0
        for a in assets:
            by_type[a.asset_type.value] = by_type.get(a.asset_type.value, 0) + 1
            total_size += a.file_size
        
        return {
            "total_assets": len(assets),
            "by_type": by_type,
            "total_size_bytes": total_size,
            "total_size_mb": round(total_size / (1024 * 1024), 2)
        }
    
    def _find_by_checksum(self, user_id: str, checksum: str) -> Optional[Asset]:
        """Find existing asset by checksum"""
        for a in self._assets.values():
            if a.user_id == user_id and a.checksum == checksum and a.status != AssetStatus.DELETED:
                return a
        return None
    
    def _get_mime_type(self, ext: str) -> str:
        """Get MIME type from extension"""
        mime_map = {
            "jpg": "image/jpeg", "jpeg": "image/jpeg", "png": "image/png",
            "webp": "image/webp", "gif": "image/gif", "svg": "image/svg+xml",
            "mp3": "audio/mpeg", "wav": "audio/wav", "m4a": "audio/x-m4a",
            "mp4": "video/mp4", "mov": "video/quicktime", "webm": "video/webm",
            "ttf": "font/ttf", "otf": "font/otf", "woff": "font/woff"
        }
        return mime_map.get(ext.lower(), "application/octet-stream")


asset_service = AssetService()
