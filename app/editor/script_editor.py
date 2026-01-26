"""
Week 18 Day 2 - Script Editor Service
Allows manual edits to generated script before media generation.
Creators want control over the AI output.
"""
from typing import Dict, List, Optional
from dataclasses import dataclass
from datetime import datetime
import uuid

from app.preview.models import Preview, ScenePreview, PreviewStatus
from app.core.logging import get_logger

logger = get_logger(__name__)


@dataclass
class EditOperation:
    """Record of an edit operation."""
    op_type: str  # "update_text", "swap", "regenerate", "split", "merge"
    scene_id: int
    old_value: Optional[str] = None
    new_value: Optional[str] = None
    timestamp: datetime = datetime.now()


class ScriptEditor:
    """
    Service for editing generated scripts.
    Tracks changes and ensures consistency (e.g. re-estimating duration).
    """
    
    def __init__(self):
        # In a real app, this would connect to DB/Redis
        # For now, we simulate persistence
        self._previews: Dict[str, Preview] = {}
        logger.info("ScriptEditor service initialized")
        
    def save_preview(self, preview: Preview):
        """Save preview state (simulate DB save)."""
        self._previews[preview.id] = preview
        
    def get_preview(self, preview_id: str) -> Optional[Preview]:
        """Get preview by ID."""
        return self._previews.get(preview_id)
        
    def update_scene_text(self, preview_id: str, scene_idx: int, new_text: str) -> Preview:
        """
        Update the narration text of a specific scene.
        Recalculates estimated duration.
        """
        preview = self.get_preview(preview_id)
        if not preview:
            raise ValueError(f"Preview {preview_id} not found")
            
        if scene_idx < 0 or scene_idx >= len(preview.scenes):
            raise ValueError(f"Invalid scene index {scene_idx}")
            
        scene = preview.scenes[scene_idx]
        
        # Track original if first edit
        if not scene.edited:
            scene.original_script = scene.script
            scene.edited = True
            
        # Update text
        scene.script = new_text
        
        # Estimate new duration (rough rule: ~2.5 words per second)
        word_count = len(new_text.split())
        scene.estimated_duration = max(3.0, word_count / 2.5)
        
        preview.status = PreviewStatus.EDITING
        preview.update_estimates()
        
        logger.info(f"Updated scene {scene_idx} in preview {preview_id}: {scene.estimated_duration:.1f}s")
        self.save_preview(preview)
        
        return preview

    def update_visual_description(self, preview_id: str, scene_idx: int, new_visual: str) -> Preview:
        """Update the visual description prompt for a scene."""
        preview = self.get_preview(preview_id)
        if not preview:
            raise ValueError(f"Preview {preview_id} not found")
            
        if scene_idx < 0 or scene_idx >= len(preview.scenes):
            raise ValueError(f"Invalid scene index {scene_idx}")
            
        scene = preview.scenes[scene_idx]
        scene.visual_description = new_visual
        scene.edited = True
        
        preview.status = PreviewStatus.EDITING
        self.save_preview(preview)
        return preview

    def swap_scenes(self, preview_id: str, idx_a: int, idx_b: int) -> Preview:
        """Reorder content by swapping two scenes."""
        preview = self.get_preview(preview_id)
        if not preview:
            raise ValueError(f"Preview {preview_id} not found")
            
        scenes = preview.scenes
        if not (0 <= idx_a < len(scenes)) or not (0 <= idx_b < len(scenes)):
            raise ValueError("Invalid scene indices")
            
        # Swap
        scenes[idx_a], scenes[idx_b] = scenes[idx_b], scenes[idx_a]
        
        # Renumber IDs to maintain 1..N order logic if needed, 
        # but usually we keep object IDs stable. 
        # Let's just swap positions in the list.
        
        preview.status = PreviewStatus.EDITING
        self.save_preview(preview)
        return preview
    
    def delete_scene(self, preview_id: str, scene_idx: int) -> Preview:
        """Remove a scene from the script."""
        preview = self.get_preview(preview_id)
        if not preview:
            raise ValueError(f"Preview {preview_id} not found")
        
        if 0 <= scene_idx < len(preview.scenes):
            preview.scenes.pop(scene_idx)
            preview.status = PreviewStatus.EDITING
            preview.update_estimates()
            self.save_preview(preview)
            
        return preview


# Singleton
_editor = None

def get_script_editor() -> ScriptEditor:
    global _editor
    if _editor is None:
        _editor = ScriptEditor()
    return _editor
