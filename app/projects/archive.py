"""
Project Archive and Favorites
Archive workflow and favorites management.
"""
from typing import Dict, List, Set
from datetime import datetime
import threading


class ProjectArchiveService:
    """Archive and favorites management"""
    
    _instance = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._archived: Set[str] = set()
            cls._instance._favorites: Set[str] = set()
            cls._instance._recent: Dict[str, List[tuple]] = {}  # user_id -> [(project_id, timestamp)]
            cls._instance._lock = threading.Lock()
        return cls._instance
    
    # Archive operations
    def archive_project(self, project_id: str) -> bool:
        """Archive a project"""
        with self._lock:
            self._archived.add(project_id)
        return True
    
    def unarchive_project(self, project_id: str) -> bool:
        """Unarchive a project"""
        with self._lock:
            self._archived.discard(project_id)
        return True
    
    def is_archived(self, project_id: str) -> bool:
        """Check if project is archived"""
        return project_id in self._archived
    
    def bulk_archive(self, project_ids: List[str]) -> int:
        """Archive multiple projects"""
        with self._lock:
            for pid in project_ids:
                self._archived.add(pid)
        return len(project_ids)
    
    def bulk_unarchive(self, project_ids: List[str]) -> int:
        """Unarchive multiple projects"""
        with self._lock:
            for pid in project_ids:
                self._archived.discard(pid)
        return len(project_ids)
    
    # Favorites operations
    def add_favorite(self, project_id: str) -> bool:
        """Mark project as favorite"""
        with self._lock:
            self._favorites.add(project_id)
        return True
    
    def remove_favorite(self, project_id: str) -> bool:
        """Remove project from favorites"""
        with self._lock:
            self._favorites.discard(project_id)
        return True
    
    def is_favorite(self, project_id: str) -> bool:
        """Check if project is favorite"""
        return project_id in self._favorites
    
    def get_favorites(self) -> Set[str]:
        """Get all favorite project IDs"""
        return self._favorites.copy()
    
    # Recent projects
    def record_access(self, user_id: str, project_id: str) -> None:
        """Record project access"""
        if user_id not in self._recent:
            self._recent[user_id] = []
        
        # Remove existing entry for this project
        self._recent[user_id] = [(pid, ts) for pid, ts in self._recent[user_id] if pid != project_id]
        
        # Add new entry
        self._recent[user_id].insert(0, (project_id, datetime.utcnow()))
        
        # Keep only last 50
        self._recent[user_id] = self._recent[user_id][:50]
    
    def get_recent(self, user_id: str, limit: int = 10) -> List[str]:
        """Get recent project IDs"""
        if user_id not in self._recent:
            return []
        return [pid for pid, _ in self._recent[user_id][:limit]]


project_archive_service = ProjectArchiveService()
