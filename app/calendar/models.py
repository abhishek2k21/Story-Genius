"""
Week 18 Day 4 - Content Calendar Models
Plan content in advance.
"""
from dataclasses import dataclass, field
from typing import List, Optional, Dict
from datetime import date, time, datetime
from enum import Enum
import uuid


class PlanStatus(str, Enum):
    DRAFT = "draft"
    SCHEDULED = "scheduled"
    ACTIVE = "active"
    ARCHIVED = "archived"


class SlotStatus(str, Enum):
    PENDING = "pending"   # Empty slot
    PLANNED = "planned"   # Topic assigned
    GENERATED = "generated" # Video generated
    PUBLISHED = "published" # Uploaded to YT


@dataclass
class CalendarSlot:
    """A single slot in the content calendar."""
    date: date
    time: time
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    
    # Content
    theme: str = "General"  # e.g. "Motivation Monday"
    topic: Optional[str] = None
    
    # Linkage
    job_id: Optional[str] = None
    preview_id: Optional[str] = None
    
    status: SlotStatus = SlotStatus.PENDING
    
    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "date": self.date.isoformat(),
            "time": self.time.strftime("%H:%M"),
            "theme": self.theme,
            "topic": self.topic,
            "job_id": self.job_id,
            "status": self.status.value
        }


@dataclass
class CalendarPlan:
    """A weekly or monthly content plan."""
    user_id: str
    name: str
    start_date: date
    end_date: date
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    
    frequency_per_week: int = 3
    themes: List[str] = field(default_factory=list)
    slots: List[CalendarSlot] = field(default_factory=list)
    
    status: PlanStatus = PlanStatus.DRAFT
    brand_kit_id: Optional[str] = None
    
    created_at: datetime = field(default_factory=datetime.now)
    
    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "user_id": self.user_id,
            "name": self.name,
            "start_date": self.start_date.isoformat(),
            "end_date": self.end_date.isoformat(),
            "frequency": self.frequency_per_week,
            "themes": self.themes,
            "status": self.status.value,
            "slots": [s.to_dict() for s in self.slots]
        }
