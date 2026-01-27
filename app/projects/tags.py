"""
Project Tagging System
Tag-based categorization for projects.
"""
from typing import Dict, List, Optional, Set
from dataclasses import dataclass, field
from datetime import datetime
import uuid
import threading


MAX_TAGS_PER_USER = 200
MAX_TAGS_PER_PROJECT = 20


@dataclass
class ProjectTag:
    """Project tag model"""
    tag_id: str
    user_id: str
    name: str
    color: str = "#6366f1"
    description: str = ""
    usage_count: int = 0
    created_at: datetime = field(default_factory=datetime.utcnow)
    
    def to_dict(self) -> Dict:
        return {
            "tag_id": self.tag_id,
            "name": self.name,
            "color": self.color,
            "description": self.description,
            "usage_count": self.usage_count
        }


class ProjectTagService:
    """Project tag management"""
    
    _instance = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._tags: Dict[str, ProjectTag] = {}
            cls._instance._project_tags: Dict[str, Set[str]] = {}  # project_id -> tag_ids
            cls._instance._lock = threading.Lock()
        return cls._instance
    
    def create_tag(
        self,
        user_id: str,
        name: str,
        color: str = "#6366f1",
        description: str = ""
    ) -> tuple:
        """Create new tag"""
        # Check limit
        user_tags = [t for t in self._tags.values() if t.user_id == user_id]
        if len(user_tags) >= MAX_TAGS_PER_USER:
            return None, f"Maximum {MAX_TAGS_PER_USER} tags reached"
        
        # Check unique name
        for t in self._tags.values():
            if t.user_id == user_id and t.name.lower() == name.lower():
                return None, "Tag already exists"
        
        with self._lock:
            tag = ProjectTag(
                tag_id=str(uuid.uuid4()),
                user_id=user_id,
                name=name,
                color=color,
                description=description
            )
            self._tags[tag.tag_id] = tag
        
        return tag, "Tag created"
    
    def get_tag(self, tag_id: str, user_id: str) -> Optional[ProjectTag]:
        """Get tag by ID"""
        tag = self._tags.get(tag_id)
        if tag and tag.user_id == user_id:
            return tag
        return None
    
    def list_tags(self, user_id: str) -> List[ProjectTag]:
        """List tags for user"""
        return sorted(
            [t for t in self._tags.values() if t.user_id == user_id],
            key=lambda t: t.name.lower()
        )
    
    def update_tag(
        self,
        tag_id: str,
        user_id: str,
        name: str = None,
        color: str = None,
        description: str = None
    ) -> tuple:
        """Update tag"""
        tag = self.get_tag(tag_id, user_id)
        if not tag:
            return None, "Tag not found"
        
        if name:
            tag.name = name
        if color:
            tag.color = color
        if description is not None:
            tag.description = description
        
        return tag, "Tag updated"
    
    def delete_tag(self, tag_id: str, user_id: str) -> tuple:
        """Delete tag"""
        tag = self.get_tag(tag_id, user_id)
        if not tag:
            return False, "Tag not found"
        
        # Remove from all projects
        for project_id in list(self._project_tags.keys()):
            self._project_tags[project_id].discard(tag_id)
        
        with self._lock:
            del self._tags[tag_id]
        
        return True, "Tag deleted"
    
    def merge_tags(self, source_id: str, target_id: str, user_id: str) -> tuple:
        """Merge source tag into target tag"""
        source = self.get_tag(source_id, user_id)
        target = self.get_tag(target_id, user_id)
        
        if not source or not target:
            return False, "Tag not found"
        
        # Move all projects from source to target
        for project_id, tags in self._project_tags.items():
            if source_id in tags:
                tags.discard(source_id)
                tags.add(target_id)
                target.usage_count += 1
        
        # Delete source
        self.delete_tag(source_id, user_id)
        
        return True, f"Merged into {target.name}"
    
    def add_tags_to_project(self, project_id: str, tag_ids: List[str]) -> tuple:
        """Add tags to project"""
        if project_id not in self._project_tags:
            self._project_tags[project_id] = set()
        
        current = self._project_tags[project_id]
        
        if len(current) + len(tag_ids) > MAX_TAGS_PER_PROJECT:
            return False, f"Maximum {MAX_TAGS_PER_PROJECT} tags per project"
        
        for tag_id in tag_ids:
            if tag_id in self._tags:
                current.add(tag_id)
                self._tags[tag_id].usage_count += 1
        
        return True, "Tags added"
    
    def remove_tags_from_project(self, project_id: str, tag_ids: List[str]) -> None:
        """Remove tags from project"""
        if project_id in self._project_tags:
            for tag_id in tag_ids:
                if tag_id in self._project_tags[project_id]:
                    self._project_tags[project_id].discard(tag_id)
                    if tag_id in self._tags:
                        self._tags[tag_id].usage_count = max(0, self._tags[tag_id].usage_count - 1)
    
    def get_project_tags(self, project_id: str) -> List[ProjectTag]:
        """Get tags for project"""
        tag_ids = self._project_tags.get(project_id, set())
        return [self._tags[tid] for tid in tag_ids if tid in self._tags]
    
    def get_projects_by_tag(self, tag_id: str) -> List[str]:
        """Get project IDs with tag"""
        return [pid for pid, tags in self._project_tags.items() if tag_id in tags]
    
    def get_projects_by_tags(self, tag_ids: List[str], match_all: bool = False) -> List[str]:
        """Get projects matching tags"""
        if not tag_ids:
            return []
        
        tag_set = set(tag_ids)
        results = []
        
        for project_id, tags in self._project_tags.items():
            if match_all:
                if tag_set.issubset(tags):
                    results.append(project_id)
            else:
                if tags.intersection(tag_set):
                    results.append(project_id)
        
        return results


project_tag_service = ProjectTagService()
