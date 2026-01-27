"""
Project Folder System
Hierarchical folder organization for projects.
"""
from typing import Dict, List, Optional
from dataclasses import dataclass, field
from datetime import datetime
import uuid
import threading


MAX_DEPTH = 4
MAX_FOLDERS = 100


@dataclass
class ProjectFolder:
    """Project folder model"""
    folder_id: str
    user_id: str
    name: str
    parent_folder_id: Optional[str] = None
    description: str = ""
    color: str = "#6366f1"
    icon: str = "folder"
    project_count: int = 0
    is_default: bool = False
    sort_order: int = 0
    created_at: datetime = field(default_factory=datetime.utcnow)
    updated_at: datetime = field(default_factory=datetime.utcnow)
    
    def to_dict(self) -> Dict:
        return {
            "folder_id": self.folder_id,
            "name": self.name,
            "parent_folder_id": self.parent_folder_id,
            "description": self.description,
            "color": self.color,
            "icon": self.icon,
            "project_count": self.project_count,
            "is_default": self.is_default,
            "sort_order": self.sort_order,
            "created_at": self.created_at.isoformat()
        }


# Default folders for new users
DEFAULT_FOLDERS = [
    {"name": "Drafts", "color": "#f59e0b", "icon": "edit", "is_default": True},
    {"name": "Published", "color": "#10b981", "icon": "check"},
    {"name": "Archive", "color": "#6b7280", "icon": "archive"}
]


class ProjectFolderService:
    """Project folder management"""
    
    _instance = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._folders: Dict[str, ProjectFolder] = {}
            cls._instance._lock = threading.Lock()
        return cls._instance
    
    def init_user_folders(self, user_id: str) -> List[ProjectFolder]:
        """Create default folders for new user"""
        created = []
        for folder_def in DEFAULT_FOLDERS:
            folder, _ = self.create_folder(
                user_id=user_id,
                name=folder_def["name"],
                color=folder_def.get("color", "#6366f1"),
                icon=folder_def.get("icon", "folder"),
                is_default=folder_def.get("is_default", False)
            )
            if folder:
                created.append(folder)
        return created
    
    def create_folder(
        self,
        user_id: str,
        name: str,
        parent_folder_id: str = None,
        description: str = "",
        color: str = "#6366f1",
        icon: str = "folder",
        is_default: bool = False
    ) -> tuple:
        """Create new project folder"""
        # Check folder limit
        user_folders = [f for f in self._folders.values() if f.user_id == user_id]
        if len(user_folders) >= MAX_FOLDERS:
            return None, f"Maximum {MAX_FOLDERS} folders reached"
        
        # Check depth
        if parent_folder_id:
            depth = self._get_depth(parent_folder_id)
            if depth >= MAX_DEPTH:
                return None, f"Maximum depth ({MAX_DEPTH}) exceeded"
            
            parent = self._folders.get(parent_folder_id)
            if not parent or parent.user_id != user_id:
                return None, "Parent folder not found"
        
        # Check unique name in parent
        for f in self._folders.values():
            if f.user_id == user_id and f.parent_folder_id == parent_folder_id:
                if f.name.lower() == name.lower():
                    return None, "Folder name already exists"
        
        with self._lock:
            folder = ProjectFolder(
                folder_id=str(uuid.uuid4()),
                user_id=user_id,
                name=name,
                parent_folder_id=parent_folder_id,
                description=description,
                color=color,
                icon=icon,
                is_default=is_default,
                sort_order=len(user_folders)
            )
            self._folders[folder.folder_id] = folder
            
            # If default, unset other defaults
            if is_default:
                for f in self._folders.values():
                    if f.user_id == user_id and f.folder_id != folder.folder_id:
                        f.is_default = False
        
        return folder, "Folder created"
    
    def get_folder(self, folder_id: str, user_id: str) -> Optional[ProjectFolder]:
        """Get folder by ID"""
        folder = self._folders.get(folder_id)
        if folder and folder.user_id == user_id:
            return folder
        return None
    
    def list_folders(self, user_id: str, parent_id: str = None) -> List[ProjectFolder]:
        """List folders for user"""
        folders = [
            f for f in self._folders.values()
            if f.user_id == user_id and f.parent_folder_id == parent_id
        ]
        return sorted(folders, key=lambda f: f.sort_order)
    
    def get_all_folders(self, user_id: str) -> List[ProjectFolder]:
        """Get all folders for user"""
        return [f for f in self._folders.values() if f.user_id == user_id]
    
    def update_folder(
        self,
        folder_id: str,
        user_id: str,
        name: str = None,
        description: str = None,
        color: str = None,
        icon: str = None
    ) -> tuple:
        """Update folder"""
        folder = self.get_folder(folder_id, user_id)
        if not folder:
            return None, "Folder not found"
        
        if name:
            folder.name = name
        if description is not None:
            folder.description = description
        if color:
            folder.color = color
        if icon:
            folder.icon = icon
        
        folder.updated_at = datetime.utcnow()
        return folder, "Folder updated"
    
    def delete_folder(self, folder_id: str, user_id: str, force: bool = False) -> tuple:
        """Delete folder"""
        folder = self.get_folder(folder_id, user_id)
        if not folder:
            return False, "Folder not found"
        
        if folder.project_count > 0 and not force:
            return False, f"Folder has {folder.project_count} projects. Use force=true."
        
        # Delete subfolders
        subfolders = [f for f in self._folders.values() if f.parent_folder_id == folder_id]
        for sf in subfolders:
            self.delete_folder(sf.folder_id, user_id, force)
        
        with self._lock:
            del self._folders[folder_id]
        
        return True, "Folder deleted"
    
    def get_default_folder(self, user_id: str) -> Optional[ProjectFolder]:
        """Get default folder for user"""
        for f in self._folders.values():
            if f.user_id == user_id and f.is_default:
                return f
        return None
    
    def increment_count(self, folder_id: str) -> None:
        """Increment project count"""
        folder = self._folders.get(folder_id)
        if folder:
            folder.project_count += 1
    
    def decrement_count(self, folder_id: str) -> None:
        """Decrement project count"""
        folder = self._folders.get(folder_id)
        if folder and folder.project_count > 0:
            folder.project_count -= 1
    
    def _get_depth(self, folder_id: str) -> int:
        """Get folder depth"""
        depth = 0
        current = self._folders.get(folder_id)
        while current and current.parent_folder_id:
            depth += 1
            current = self._folders.get(current.parent_folder_id)
            if depth > MAX_DEPTH:
                break
        return depth


project_folder_service = ProjectFolderService()
