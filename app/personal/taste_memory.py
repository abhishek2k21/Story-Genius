"""
Taste Memory
Teaches the system your preferences - what you like, what you hate.
"""
import json
from datetime import datetime
from pathlib import Path
from dataclasses import dataclass, asdict
from typing import Dict, List, Optional

from app.core.logging import get_logger

logger = get_logger(__name__)


@dataclass
class TasteSignal:
    """A single taste signal (like/dislike)."""
    job_id: str
    signal: str  # "like", "dislike", "love", "hate"
    category: str  # "hook", "pacing", "style", "overall"
    details: str
    timestamp: datetime


class TasteMemory:
    """
    Your taste memory - the system learns what you want.
    """
    
    def __init__(self):
        self._signals: List[TasteSignal] = []
        self._path = Path("config/taste_memory.json")
        self._load()
        
        # Aggregated preferences
        self.liked_hooks: List[str] = []
        self.disliked_hooks: List[str] = []
        self.liked_styles: List[str] = []
        self.disliked_styles: List[str] = []
        self.never_again: List[str] = []  # Hard rejections
    
    def _load(self):
        """Load taste memory from file."""
        if self._path.exists():
            with open(self._path, "r") as f:
                data = json.load(f)
                self._signals = [
                    TasteSignal(**{**s, "timestamp": datetime.fromisoformat(s["timestamp"])})
                    for s in data.get("signals", [])
                ]
                self.liked_hooks = data.get("liked_hooks", [])
                self.disliked_hooks = data.get("disliked_hooks", [])
                self.liked_styles = data.get("liked_styles", [])
                self.disliked_styles = data.get("disliked_styles", [])
                self.never_again = data.get("never_again", [])
    
    def _save(self):
        """Save taste memory to file."""
        self._path.parent.mkdir(parents=True, exist_ok=True)
        data = {
            "signals": [
                {**asdict(s), "timestamp": s.timestamp.isoformat()}
                for s in self._signals[-100:]  # Keep last 100
            ],
            "liked_hooks": self.liked_hooks[-20:],
            "disliked_hooks": self.disliked_hooks[-20:],
            "liked_styles": self.liked_styles[-10:],
            "disliked_styles": self.disliked_styles[-10:],
            "never_again": self.never_again
        }
        with open(self._path, "w") as f:
            json.dump(data, f, indent=2)
    
    def like(self, job_id: str, category: str, details: str = ""):
        """Record a like signal."""
        signal = TasteSignal(
            job_id=job_id,
            signal="like",
            category=category,
            details=details,
            timestamp=datetime.utcnow()
        )
        self._signals.append(signal)
        
        if category == "hook" and details:
            self.liked_hooks.append(details)
        elif category == "style" and details:
            self.liked_styles.append(details)
        
        self._save()
        logger.info(f"👍 Liked {category}: {details[:30]}")
    
    def dislike(self, job_id: str, category: str, details: str = ""):
        """Record a dislike signal."""
        signal = TasteSignal(
            job_id=job_id,
            signal="dislike",
            category=category,
            details=details,
            timestamp=datetime.utcnow()
        )
        self._signals.append(signal)
        
        if category == "hook" and details:
            self.disliked_hooks.append(details)
        elif category == "style" and details:
            self.disliked_styles.append(details)
        
        self._save()
        logger.info(f"👎 Disliked {category}: {details[:30]}")
    
    def never_use(self, pattern: str):
        """Mark something to never use again."""
        self.never_again.append(pattern)
        self._save()
        logger.warning(f"❌ Never again: {pattern}")
    
    def rate(self, job_id: str, rating: int, feedback: str = ""):
        """Rate output 1-5."""
        signal = "like" if rating >= 4 else "dislike" if rating <= 2 else "neutral"
        
        taste_signal = TasteSignal(
            job_id=job_id,
            signal=signal,
            category="overall",
            details=f"Rating: {rating}/5. {feedback}",
            timestamp=datetime.utcnow()
        )
        self._signals.append(taste_signal)
        self._save()
        
        logger.info(f"Rated {job_id[:8]}: {rating}/5")
    
    def should_avoid(self, content: str) -> bool:
        """Check if content matches disliked patterns."""
        content_lower = content.lower()
        
        for pattern in self.never_again:
            if pattern.lower() in content_lower:
                return True
        
        for hook in self.disliked_hooks[-10:]:
            if hook.lower() in content_lower:
                return True
        
        return False
    
    def get_preferences(self) -> Dict:
        """Get current preference summary."""
        return {
            "total_signals": len(self._signals),
            "liked_hooks_count": len(self.liked_hooks),
            "disliked_hooks_count": len(self.disliked_hooks),
            "never_again": self.never_again,
            "recent_likes": [s.details[:30] for s in self._signals[-5:] if s.signal == "like"]
        }
    
    def display(self):
        """Display taste memory summary."""
        print("\n" + "=" * 50)
        print("  YOUR TASTE MEMORY")
        print("=" * 50)
        print(f"  Total signals: {len(self._signals)}")
        print(f"  Liked hooks: {len(self.liked_hooks)}")
        print(f"  Disliked hooks: {len(self.disliked_hooks)}")
        print(f"  Never again: {len(self.never_again)}")
        if self.never_again:
            print(f"  ❌ Blocked: {', '.join(self.never_again[:5])}")
