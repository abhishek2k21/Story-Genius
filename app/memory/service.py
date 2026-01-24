"""
Memory Service (v1)
Stores and retrieves high-performing content patterns for reuse and learning.
"""
import uuid
from datetime import datetime
from typing import List, Optional, Dict
from dataclasses import dataclass, asdict

from app.core.database import get_db_session, Base
from app.core.logging import get_logger
from app.core.config import settings
from sqlalchemy import Column, String, Float, DateTime, Text, Integer

logger = get_logger(__name__)


@dataclass
class MemoryEntry:
    """A stored pattern in creative memory."""
    id: str
    memory_type: str  # hook, persona, emotion_curve
    reference_id: str  # original hook text or ID
    platform: str
    score: float
    metadata: Dict
    reuse_count: int = 0
    created_at: datetime = None


class MemoryService:
    """
    Creative Memory System (v1).
    Stores winning patterns and enables intelligent reuse.
    """
    
    SCORE_THRESHOLD = 0.85  # Store patterns scoring above this
    
    def __init__(self):
        self.db = get_db_session()
        self._memory_cache: List[MemoryEntry] = []
    
    def store_winning_hook(
        self,
        hook_text: str,
        hook_type: str,
        score: float,
        platform: str,
        visual_prompt: str = ""
    ) -> Optional[MemoryEntry]:
        """
        Store a high-scoring hook in memory.
        
        Args:
            hook_text: The hook text
            hook_type: Type of hook
            score: Hook's total score
            platform: Target platform
            visual_prompt: Associated visual
            
        Returns:
            MemoryEntry if stored, None if score too low
        """
        if score < self.SCORE_THRESHOLD:
            logger.debug(f"Hook score {score} below threshold {self.SCORE_THRESHOLD}, not storing")
            return None
        
        entry = MemoryEntry(
            id=str(uuid.uuid4()),
            memory_type="hook",
            reference_id=hook_text[:100],  # Truncate for ID
            platform=platform,
            score=score,
            metadata={
                "hook_text": hook_text,
                "hook_type": hook_type,
                "visual_prompt": visual_prompt
            },
            reuse_count=0,
            created_at=datetime.utcnow()
        )
        
        self._memory_cache.append(entry)
        logger.info(f"Stored winning hook (score={score:.2f}): {hook_text[:40]}...")
        
        # TODO: Persist to database in future version
        return entry
    
    def get_top_hooks(
        self,
        platform: str = None,
        limit: int = 5
    ) -> List[MemoryEntry]:
        """
        Get top-scoring hooks from memory.
        
        Args:
            platform: Filter by platform (optional)
            limit: Max results
            
        Returns:
            List of MemoryEntry for hooks
        """
        hooks = [e for e in self._memory_cache if e.memory_type == "hook"]
        
        if platform:
            hooks = [h for h in hooks if h.platform == platform]
        
        # Sort by score
        hooks.sort(key=lambda h: h.score, reverse=True)
        
        return hooks[:limit]
    
    def mutate_hook(self, hook_text: str, mutation_type: str = "rephrase") -> str:
        """
        Create a variation of an existing hook for reuse.
        
        Args:
            hook_text: Original hook
            mutation_type: Type of mutation (rephrase, intensify, simplify)
            
        Returns:
            Mutated hook text
        """
        # In v1, we use simple text transformations
        # In future, use LLM for smarter mutations
        
        mutations = {
            "intensify": lambda t: t.replace(".", "!").upper() if not t.endswith("?") else t,
            "simplify": lambda t: t.split(",")[0] if "," in t else t,
            "question": lambda t: t.rstrip(".!") + "?" if not t.endswith("?") else t
        }
        
        mutator = mutations.get(mutation_type, lambda t: t)
        mutated = mutator(hook_text)
        
        logger.debug(f"Mutated hook: '{hook_text}' → '{mutated}'")
        return mutated
    
    def store_pattern(
        self,
        pattern_type: str,
        pattern_id: str,
        score: float,
        platform: str,
        metadata: Dict = None
    ) -> Optional[MemoryEntry]:
        """
        Generic pattern storage (persona, curve, etc.).
        """
        if score < self.SCORE_THRESHOLD:
            return None
        
        entry = MemoryEntry(
            id=str(uuid.uuid4()),
            memory_type=pattern_type,
            reference_id=pattern_id,
            platform=platform,
            score=score,
            metadata=metadata or {},
            created_at=datetime.utcnow()
        )
        
        self._memory_cache.append(entry)
        logger.info(f"Stored {pattern_type} pattern: {pattern_id} (score={score:.2f})")
        return entry
    
    def get_reusable_hook(self, platform: str = None) -> Optional[Dict]:
        """
        Get a hook suitable for reuse (with mutation).
        
        Returns:
            Hook metadata dict or None
        """
        top_hooks = self.get_top_hooks(platform, limit=3)
        
        if not top_hooks:
            return None
        
        # Pick best hook and mutate it
        best = top_hooks[0]
        best.reuse_count += 1
        
        original_text = best.metadata.get("hook_text", "")
        mutated_text = self.mutate_hook(original_text, "intensify")
        
        return {
            "text": mutated_text,
            "original_text": original_text,
            "hook_type": best.metadata.get("hook_type"),
            "visual_prompt": best.metadata.get("visual_prompt"),
            "original_score": best.score,
            "is_reused": True
        }
    
    def get_memory_stats(self) -> Dict:
        """Get statistics about stored memories."""
        hooks = [e for e in self._memory_cache if e.memory_type == "hook"]
        
        return {
            "total_entries": len(self._memory_cache),
            "hooks": len(hooks),
            "avg_hook_score": sum(h.score for h in hooks) / len(hooks) if hooks else 0,
            "total_reuses": sum(e.reuse_count for e in self._memory_cache)
        }
    
    def clear_memory(self):
        """Clear all memory (for testing)."""
        self._memory_cache.clear()
        logger.info("Memory cleared")
