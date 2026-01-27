"""
Tag Operations
Tag-based categorization for assets.
"""
from typing import Dict, List, Optional, Set
from datetime import datetime
import threading

from app.assets.models import Tag, create_tag_id


class TagService:
    """Tag management service"""
    
    _instance = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._tags: Dict[str, Tag] = {}
            cls._instance._asset_tags: Dict[str, Set[str]] = {}  # asset_id -> tag_ids
            cls._instance._lock = threading.Lock()
        return cls._instance
    
    def create_tag(
        self,
        user_id: str,
        name: str,
        color: str = "#6366f1"
    ) -> tuple:
        """Create new tag"""
        # Check unique name for user
        for t in self._tags.values():
            if t.user_id == user_id and t.name.lower() == name.lower():
                return None, "Tag already exists"
        
        with self._lock:
            tag = Tag(
                tag_id=create_tag_id(),
                user_id=user_id,
                name=name,
                color=color
            )
            self._tags[tag.tag_id] = tag
        
        return tag, "Tag created"
    
    def get_tag(self, tag_id: str, user_id: str) -> Optional[Tag]:
        """Get tag by ID"""
        tag = self._tags.get(tag_id)
        if tag and tag.user_id == user_id:
            return tag
        return None
    
    def list_tags(self, user_id: str) -> List[Tag]:
        """List tags for user"""
        return [t for t in self._tags.values() if t.user_id == user_id]
    
    def update_tag(
        self,
        tag_id: str,
        user_id: str,
        name: str = None,
        color: str = None
    ) -> tuple:
        """Update tag"""
        tag = self._tags.get(tag_id)
        if not tag or tag.user_id != user_id:
            return None, "Tag not found"
        
        if name:
            tag.name = name
        if color:
            tag.color = color
        
        return tag, "Tag updated"
    
    def delete_tag(self, tag_id: str, user_id: str) -> tuple:
        """Delete tag"""
        tag = self._tags.get(tag_id)
        if not tag or tag.user_id != user_id:
            return False, "Tag not found"
        
        # Remove from all assets
        for asset_id, tags in self._asset_tags.items():
            tags.discard(tag_id)
        
        with self._lock:
            del self._tags[tag_id]
        
        return True, "Tag deleted"
    
    def add_tags_to_asset(self, asset_id: str, tag_ids: List[str]) -> None:
        """Add tags to asset"""
        if asset_id not in self._asset_tags:
            self._asset_tags[asset_id] = set()
        
        for tag_id in tag_ids:
            if tag_id in self._tags:
                self._asset_tags[asset_id].add(tag_id)
                self._tags[tag_id].usage_count += 1
    
    def remove_tags_from_asset(self, asset_id: str, tag_ids: List[str]) -> None:
        """Remove tags from asset"""
        if asset_id in self._asset_tags:
            for tag_id in tag_ids:
                if tag_id in self._asset_tags[asset_id]:
                    self._asset_tags[asset_id].discard(tag_id)
                    if tag_id in self._tags:
                        self._tags[tag_id].usage_count = max(0, self._tags[tag_id].usage_count - 1)
    
    def get_asset_tags(self, asset_id: str) -> List[Tag]:
        """Get tags for asset"""
        tag_ids = self._asset_tags.get(asset_id, set())
        return [self._tags[tid] for tid in tag_ids if tid in self._tags]
    
    def get_assets_by_tag(self, tag_id: str) -> List[str]:
        """Get asset IDs with tag"""
        return [
            asset_id for asset_id, tags in self._asset_tags.items()
            if tag_id in tags
        ]


tag_service = TagService()
