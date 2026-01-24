"""
Trend Injection Engine
Enables riding trends without becoming a trend slave.
"""
import json
from datetime import datetime, timedelta
from dataclasses import dataclass, field
from typing import List, Dict, Optional

from app.core.logging import get_logger

logger = get_logger(__name__)


@dataclass
class Trend:
    """A trend definition for content injection."""
    id: str
    name: str
    keywords: List[str]
    tone: str  # curious, funny, serious, shocking
    expiry_date: datetime
    priority: int = 1  # 1-5, higher = more important
    
    # Injection guidance
    hook_modifier: str = ""      # How to modify hooks
    visual_elements: List[str] = field(default_factory=list)
    title_keywords: List[str] = field(default_factory=list)
    
    @property
    def is_active(self) -> bool:
        return datetime.utcnow() < self.expiry_date
    
    @property
    def days_remaining(self) -> int:
        delta = self.expiry_date - datetime.utcnow()
        return max(0, delta.days)


class TrendEngine:
    """
    Manages active trends and injects them into content.
    """
    
    def __init__(self):
        self._active_trends: Dict[str, Trend] = {}
    
    def add_trend(
        self,
        name: str,
        keywords: List[str],
        tone: str = "curious",
        expiry_days: int = 3,
        hook_modifier: str = "",
        visual_elements: List[str] = None,
        title_keywords: List[str] = None,
        priority: int = 1
    ) -> Trend:
        """
        Add a new active trend.
        
        Args:
            name: Trend name/topic
            keywords: Related keywords
            tone: Content tone (curious, funny, serious, shocking)
            expiry_days: Days until trend expires
            hook_modifier: How to modify hooks for this trend
            visual_elements: Visual elements to include
            title_keywords: Keywords for titles
            priority: 1-5 importance level
            
        Returns:
            Created Trend object
        """
        trend_id = name.lower().replace(" ", "_")
        
        trend = Trend(
            id=trend_id,
            name=name,
            keywords=keywords,
            tone=tone,
            expiry_date=datetime.utcnow() + timedelta(days=expiry_days),
            priority=priority,
            hook_modifier=hook_modifier or f"Reference {name} trend",
            visual_elements=visual_elements or [],
            title_keywords=title_keywords or keywords[:3]
        )
        
        self._active_trends[trend_id] = trend
        logger.info(f"Added trend: {name} (expires in {expiry_days} days)")
        
        return trend
    
    def add_trend_from_json(self, trend_json: dict) -> Trend:
        """Add trend from JSON format."""
        return self.add_trend(
            name=trend_json.get("trend", trend_json.get("name", "Unknown")),
            keywords=trend_json.get("keywords", [trend_json.get("trend", "")]),
            tone=trend_json.get("tone", "curious"),
            expiry_days=trend_json.get("expiry_days", 3),
            hook_modifier=trend_json.get("hook_modifier", ""),
            visual_elements=trend_json.get("visual_elements", []),
            title_keywords=trend_json.get("title_keywords", []),
            priority=trend_json.get("priority", 1)
        )
    
    def get_active_trends(self) -> List[Trend]:
        """Get all active (non-expired) trends."""
        active = [t for t in self._active_trends.values() if t.is_active]
        # Sort by priority (highest first)
        return sorted(active, key=lambda t: t.priority, reverse=True)
    
    def get_top_trend(self) -> Optional[Trend]:
        """Get highest priority active trend."""
        active = self.get_active_trends()
        return active[0] if active else None
    
    def remove_trend(self, trend_id: str) -> bool:
        """Remove a trend by ID."""
        if trend_id in self._active_trends:
            del self._active_trends[trend_id]
            logger.info(f"Removed trend: {trend_id}")
            return True
        return False
    
    def clear_expired(self):
        """Remove all expired trends."""
        expired = [tid for tid, t in self._active_trends.items() if not t.is_active]
        for tid in expired:
            del self._active_trends[tid]
        if expired:
            logger.info(f"Cleared {len(expired)} expired trends")
    
    def inject_into_hook(self, hook_text: str, trend: Trend = None) -> str:
        """
        Inject trend reference into hook text.
        
        Args:
            hook_text: Original hook
            trend: Trend to inject (or use top trend)
            
        Returns:
            Modified hook text
        """
        trend = trend or self.get_top_trend()
        if not trend:
            return hook_text
        
        # Simple injection - prepend trend reference
        # In production, use LLM for natural integration
        if any(kw.lower() in hook_text.lower() for kw in trend.keywords):
            return hook_text  # Already contains trend reference
        
        # Add trend keyword naturally
        keyword = trend.keywords[0] if trend.keywords else trend.name
        injected = f"{hook_text.rstrip('?!.')} — {keyword}!"
        
        logger.debug(f"Injected trend '{trend.name}' into hook")
        return injected
    
    def inject_into_visual(self, visual_prompt: str, trend: Trend = None) -> str:
        """
        Inject trend visual elements into prompt.
        
        Args:
            visual_prompt: Original visual prompt
            trend: Trend to use
            
        Returns:
            Enhanced visual prompt
        """
        trend = trend or self.get_top_trend()
        if not trend or not trend.visual_elements:
            return visual_prompt
        
        elements = ", ".join(trend.visual_elements[:2])
        return f"{visual_prompt}, featuring {elements}"
    
    def get_title_boost(self, trend: Trend = None) -> List[str]:
        """Get keywords to potentially add to titles."""
        trend = trend or self.get_top_trend()
        if not trend:
            return []
        return trend.title_keywords
    
    def has_active_trends(self) -> bool:
        """Check if any trends are active."""
        return len(self.get_active_trends()) > 0
    
    def get_trend_report(self) -> Dict:
        """Get summary of trend status."""
        active = self.get_active_trends()
        return {
            "active_count": len(active),
            "trends": [
                {
                    "name": t.name,
                    "days_remaining": t.days_remaining,
                    "priority": t.priority
                }
                for t in active
            ]
        }


# Singleton instance for global trend management
_trend_engine = None

def get_trend_engine() -> TrendEngine:
    """Get global trend engine instance."""
    global _trend_engine
    if _trend_engine is None:
        _trend_engine = TrendEngine()
    return _trend_engine
