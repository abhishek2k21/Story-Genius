"""
Batch Generation Models
Defines batch containers, items, and lifecycle states for series production.
"""
from enum import Enum
from typing import List, Dict, Optional, Any
from dataclasses import dataclass, field
from datetime import datetime
import uuid


class BatchStatus(str, Enum):
    """Batch lifecycle states"""
    DRAFT = "draft"  # Items can be added/removed
    LOCKED = "locked"  # Config frozen, ready to process
    PROCESSING = "processing"  # Jobs executing
    PARTIAL = "partial"  # Some complete, some pending
    COMPLETE = "complete"  # All jobs finished successfully
    FAILED = "failed"  # One or more jobs failed permanently
    CANCELLED = "cancelled"  # User cancelled


class BatchItemStatus(str, Enum):
    """Individual item states within batch"""
    PENDING = "pending"  # Not started
    QUEUED = "queued"  # In processing queue
    PROCESSING = "processing"  # Currently generating
    COMPLETE = "complete"  # Successfully finished
    FAILED = "failed"  # Generation failed
    SKIPPED = "skipped"  # Skipped due to batch cancellation


@dataclass
class BatchItem:
    """Single item within a batch"""
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    order: int = 0  # Position in batch
    content: str = ""  # Topic/script/prompt for this item
    status: BatchItemStatus = BatchItemStatus.PENDING
    job_id: Optional[str] = None  # Reference to generated job
    output_path: Optional[str] = None  # Path to output video
    error_message: Optional[str] = None
    retry_count: int = 0
    created_at: datetime = field(default_factory=datetime.now)
    completed_at: Optional[datetime] = None
    
    def to_dict(self) -> Dict:
        return {
            "id": self.id,
            "order": self.order,
            "content": self.content,
            "status": self.status.value,
            "job_id": self.job_id,
            "output_path": self.output_path,
            "error_message": self.error_message,
            "retry_count": self.retry_count,
            "created_at": self.created_at.isoformat(),
            "completed_at": self.completed_at.isoformat() if self.completed_at else None
        }


@dataclass
class BatchConfig:
    """Locked configuration for batch generation"""
    platform: str = "youtube_shorts"
    duration: int = 30
    voice: str = "en-US-GuyNeural"
    style_profile: Optional[str] = None  # Reference to saved style
    genre: str = "educational"
    language: str = "en"
    audience: str = "general"
    
    def to_dict(self) -> Dict:
        return {
            "platform": self.platform,
            "duration": self.duration,
            "voice": self.voice,
            "style_profile": self.style_profile,
            "genre": self.genre,
            "language": self.language,
            "audience": self.audience
        }
    
    @classmethod
    def from_dict(cls, data: Dict) -> "BatchConfig":
        return cls(
            platform=data.get("platform", "youtube_shorts"),
            duration=data.get("duration", 30),
            voice=data.get("voice", "en-US-GuyNeural"),
            style_profile=data.get("style_profile"),
            genre=data.get("genre", "educational"),
            language=data.get("language", "en"),
            audience=data.get("audience", "general")
        )


@dataclass
class Batch:
    """Batch container for series production"""
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    name: str = ""
    description: Optional[str] = None
    status: BatchStatus = BatchStatus.DRAFT
    config: BatchConfig = field(default_factory=BatchConfig)
    items: List[BatchItem] = field(default_factory=list)
    max_parallel: int = 3  # Max concurrent processing
    
    # Progress tracking
    total_items: int = 0
    completed_items: int = 0
    failed_items: int = 0
    
    # Timestamps
    created_at: datetime = field(default_factory=datetime.now)
    locked_at: Optional[datetime] = None
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    
    # Metadata
    user_id: Optional[str] = None
    tags: List[str] = field(default_factory=list)
    
    def add_item(self, content: str) -> BatchItem:
        """Add item to draft batch"""
        if self.status != BatchStatus.DRAFT:
            raise ValueError("Cannot add items to non-draft batch")
        
        item = BatchItem(
            order=len(self.items),
            content=content
        )
        self.items.append(item)
        self.total_items = len(self.items)
        return item
    
    def remove_item(self, item_id: str) -> bool:
        """Remove item from draft batch"""
        if self.status != BatchStatus.DRAFT:
            raise ValueError("Cannot remove items from non-draft batch")
        
        for i, item in enumerate(self.items):
            if item.id == item_id:
                self.items.pop(i)
                # Reorder remaining items
                for j, remaining in enumerate(self.items):
                    remaining.order = j
                self.total_items = len(self.items)
                return True
        return False
    
    def get_item(self, item_id: str) -> Optional[BatchItem]:
        """Get item by ID"""
        for item in self.items:
            if item.id == item_id:
                return item
        return None
    
    def get_pending_items(self) -> List[BatchItem]:
        """Get items ready to process"""
        return [i for i in self.items if i.status == BatchItemStatus.PENDING]
    
    def get_failed_items(self) -> List[BatchItem]:
        """Get failed items for retry"""
        return [i for i in self.items if i.status == BatchItemStatus.FAILED]
    
    def get_complete_items(self) -> List[BatchItem]:
        """Get successfully completed items"""
        return [i for i in self.items if i.status == BatchItemStatus.COMPLETE]
    
    def update_progress(self):
        """Recalculate progress counters"""
        self.completed_items = len(self.get_complete_items())
        self.failed_items = len(self.get_failed_items())
        
        # Update batch status based on item states
        if all(i.status == BatchItemStatus.COMPLETE for i in self.items):
            self.status = BatchStatus.COMPLETE
            self.completed_at = datetime.now()
        elif all(i.status in [BatchItemStatus.COMPLETE, BatchItemStatus.FAILED] for i in self.items):
            if self.failed_items > 0:
                self.status = BatchStatus.PARTIAL
            else:
                self.status = BatchStatus.COMPLETE
                self.completed_at = datetime.now()
    
    def to_dict(self) -> Dict:
        return {
            "id": self.id,
            "name": self.name,
            "description": self.description,
            "status": self.status.value,
            "config": self.config.to_dict(),
            "items": [i.to_dict() for i in self.items],
            "max_parallel": self.max_parallel,
            "progress": {
                "total": self.total_items,
                "completed": self.completed_items,
                "failed": self.failed_items,
                "pending": self.total_items - self.completed_items - self.failed_items
            },
            "created_at": self.created_at.isoformat(),
            "locked_at": self.locked_at.isoformat() if self.locked_at else None,
            "started_at": self.started_at.isoformat() if self.started_at else None,
            "completed_at": self.completed_at.isoformat() if self.completed_at else None,
            "user_id": self.user_id,
            "tags": self.tags
        }
    
    @classmethod
    def from_dict(cls, data: Dict) -> "Batch":
        batch = cls(
            id=data.get("id", str(uuid.uuid4())),
            name=data.get("name", ""),
            description=data.get("description"),
            status=BatchStatus(data.get("status", "draft")),
            config=BatchConfig.from_dict(data.get("config", {})),
            max_parallel=data.get("max_parallel", 3),
            user_id=data.get("user_id"),
            tags=data.get("tags", [])
        )
        
        # Reconstruct items
        for item_data in data.get("items", []):
            item = BatchItem(
                id=item_data.get("id", str(uuid.uuid4())),
                order=item_data.get("order", 0),
                content=item_data.get("content", ""),
                status=BatchItemStatus(item_data.get("status", "pending")),
                job_id=item_data.get("job_id"),
                output_path=item_data.get("output_path"),
                error_message=item_data.get("error_message"),
                retry_count=item_data.get("retry_count", 0)
            )
            batch.items.append(item)
        
        batch.total_items = len(batch.items)
        return batch
