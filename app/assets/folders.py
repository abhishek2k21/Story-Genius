"""
Folder Operations
Hierarchical folder organization for assets.
"""
from typing import Dict, List, Optional
from datetime import datetime
import threading

from app.assets.models import Folder, create_folder_id


MAX_DEPTH = 5


class FolderService:
    """Folder management service"""
    
    _instance = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._folders: Dict[str, Folder] = {}
            cls._instance._lock = threading.Lock()
        return cls._instance
    
    def create_folder(
        self,
        user_id: str,
        name: str,
        parent_folder_id: str = None,
        description: str = "",
        color: str = "#6366f1"
    ) -> tuple:
        """Create new folder"""
        # Check depth limit
        if parent_folder_id:
            depth = self._get_folder_depth(parent_folder_id)
            if depth >= MAX_DEPTH:
                return None, f"Maximum folder depth ({MAX_DEPTH}) exceeded"
            
            parent = self._folders.get(parent_folder_id)
            if not parent or parent.user_id != user_id:
                return None, "Parent folder not found"
        
        # Check unique name in parent
        for f in self._folders.values():
            if f.user_id == user_id and f.parent_folder_id == parent_folder_id:
                if f.name.lower() == name.lower():
                    return None, "Folder name already exists"
        
        with self._lock:
            folder = Folder(
                folder_id=create_folder_id(),
                user_id=user_id,
                name=name,
                parent_folder_id=parent_folder_id,
                description=description,
                color=color
            )
            self._folders[folder.folder_id] = folder
        
        return folder, "Folder created"
    
    def get_folder(self, folder_id: str, user_id: str) -> Optional[Folder]:
        """Get folder by ID"""
        folder = self._folders.get(folder_id)
        if folder and folder.user_id == user_id:
            return folder
        return None
    
    def list_folders(self, user_id: str, parent_id: str = None) -> List[Folder]:
        """List folders for user"""
        return [
            f for f in self._folders.values()
            if f.user_id == user_id and f.parent_folder_id == parent_id
        ]
    
    def update_folder(
        self,
        folder_id: str,
        user_id: str,
        name: str = None,
        description: str = None,
        color: str = None
    ) -> tuple:
        """Update folder"""
        folder = self._folders.get(folder_id)
        if not folder or folder.user_id != user_id:
            return None, "Folder not found"
        
        if name:
            folder.name = name
        if description is not None:
            folder.description = description
        if color:
            folder.color = color
        
        folder.updated_at = datetime.utcnow()
        return folder, "Folder updated"
    
    def delete_folder(self, folder_id: str, user_id: str, force: bool = False) -> tuple:
        """Delete folder"""
        folder = self._folders.get(folder_id)
        if not folder or folder.user_id != user_id:
            return False, "Folder not found"
        
        if folder.asset_count > 0 and not force:
            return False, f"Folder contains {folder.asset_count} assets. Use force=true to delete."
        
        # Delete subfolders
        subfolders = [f for f in self._folders.values() if f.parent_folder_id == folder_id]
        for sf in subfolders:
            self.delete_folder(sf.folder_id, user_id, force)
        
        with self._lock:
            del self._folders[folder_id]
        
        return True, "Folder deleted"
    
    def _get_folder_depth(self, folder_id: str) -> int:
        """Get depth of folder in hierarchy"""
        depth = 0
        current = self._folders.get(folder_id)
        
        while current and current.parent_folder_id:
            depth += 1
            current = self._folders.get(current.parent_folder_id)
            if depth > MAX_DEPTH:
                break
        
        return depth
    
    def increment_asset_count(self, folder_id: str) -> None:
        """Increment folder asset count"""
        folder = self._folders.get(folder_id)
        if folder:
            folder.asset_count += 1
    
    def decrement_asset_count(self, folder_id: str) -> None:
        """Decrement folder asset count"""
        folder = self._folders.get(folder_id)
        if folder and folder.asset_count > 0:
            folder.asset_count -= 1


folder_service = FolderService()
