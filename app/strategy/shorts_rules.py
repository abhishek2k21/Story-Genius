"""
Shorts Validation Rules
Enforces platform-specific rules for short-form video optimization.
"""
from typing import List, Tuple
from app.core.models import Scene, ScenePurpose
from app.core.config import settings
from app.core.logging import get_logger

logger = get_logger(__name__)


class ShortsValidator:
    """
    Validates content against shorts platform requirements.
    """
    
    def __init__(self, platform: str = "youtube_shorts"):
        self.platform = platform
        self.hook_window = settings.HOOK_WINDOW_SECONDS
        self.min_duration = settings.MIN_DURATION
        self.max_duration = settings.MAX_DURATION
    
    def validate_hook(self, scene: Scene) -> Tuple[bool, str]:
        """
        Validate hook scene (Scene 1 must be ≤ 2 seconds).
        
        Args:
            scene: The first scene to validate
            
        Returns:
            Tuple of (is_valid, message)
        """
        if scene.purpose != ScenePurpose.HOOK:
            return False, "First scene must have purpose 'hook'"
        
        duration = scene.end_sec - scene.start_sec
        
        if duration > self.hook_window:
            return False, f"Hook too long: {duration}s (max {self.hook_window}s)"
        
        # Check for attention-grabbing elements
        hook_words = ["what", "why", "how", "imagine", "watch", "look", "wait", "?", "!"]
        text_lower = scene.narration_text.lower()
        has_hook_element = any(word in text_lower for word in hook_words)
        
        if not has_hook_element:
            logger.warning(f"Hook lacks attention-grabbing elements: {scene.narration_text[:50]}")
        
        return True, "Hook valid"
    
    def validate_loop(self, scene: Scene) -> Tuple[bool, str]:
        """
        Validate loop ending (must end with question or mid-action cut).
        
        Args:
            scene: The last scene to validate
            
        Returns:
            Tuple of (is_valid, message)
        """
        if scene.purpose != ScenePurpose.LOOP:
            return False, "Last scene must have purpose 'loop'"
        
        text = scene.narration_text
        
        # Check for question ending
        has_question = "?" in text or any(
            text.lower().startswith(q) for q in ["what", "why", "how", "who", "will", "can"]
        )
        
        # Check for mid-action indicators
        mid_action_words = ["but", "suddenly", "until", "when", "before", "..."]
        has_mid_action = any(word in text.lower() for word in mid_action_words)
        
        if not has_question and not has_mid_action:
            return False, "Loop ending lacks question or mid-action cut"
        
        return True, "Loop ending valid"
    
    def validate_duration(self, scenes: List[Scene]) -> Tuple[bool, str]:
        """
        Validate total duration is within bounds (25-35 seconds).
        
        Args:
            scenes: All scenes to validate
            
        Returns:
            Tuple of (is_valid, message)
        """
        if not scenes:
            return False, "No scenes provided"
        
        total_duration = scenes[-1].end_sec
        
        if total_duration < self.min_duration:
            return False, f"Too short: {total_duration}s (min {self.min_duration}s)"
        
        if total_duration > self.max_duration:
            return False, f"Too long: {total_duration}s (max {self.max_duration}s)"
        
        return True, f"Duration valid: {total_duration}s"
    
    def validate_all(self, scenes: List[Scene]) -> Tuple[bool, List[str]]:
        """
        Run all validations on scenes.
        
        Args:
            scenes: All scenes to validate
            
        Returns:
            Tuple of (all_valid, list of messages)
        """
        messages = []
        all_valid = True
        
        if not scenes:
            return False, ["No scenes to validate"]
        
        # Validate hook (first scene)
        hook_valid, hook_msg = self.validate_hook(scenes[0])
        messages.append(f"Hook: {hook_msg}")
        if not hook_valid:
            all_valid = False
        
        # Validate loop (last scene)
        loop_valid, loop_msg = self.validate_loop(scenes[-1])
        messages.append(f"Loop: {loop_msg}")
        if not loop_valid:
            all_valid = False
        
        # Validate duration
        dur_valid, dur_msg = self.validate_duration(scenes)
        messages.append(f"Duration: {dur_msg}")
        if not dur_valid:
            all_valid = False
        
        return all_valid, messages
    
    def fix_hook(self, scene: Scene) -> Scene:
        """
        Attempt to fix hook scene if too long.
        
        Args:
            scene: Hook scene to fix
            
        Returns:
            Fixed scene
        """
        duration = scene.end_sec - scene.start_sec
        
        if duration > self.hook_window:
            scene.end_sec = scene.start_sec + int(self.hook_window)
            logger.info(f"Fixed hook duration: {duration}s → {self.hook_window}s")
        
        return scene
    
    def fix_duration(self, scenes: List[Scene], target: int = 30) -> List[Scene]:
        """
        Adjust scene durations to hit target total.
        
        Args:
            scenes: Scenes to adjust
            target: Target total duration in seconds
            
        Returns:
            Adjusted scenes
        """
        if not scenes:
            return scenes
        
        current_total = scenes[-1].end_sec
        
        if current_total == target:
            return scenes
        
        # Scale all scenes proportionally (except hook)
        scale = target / current_total
        
        current_time = scenes[0].end_sec  # Keep hook as-is
        
        for i, scene in enumerate(scenes[1:], 1):
            original_duration = scene.end_sec - scene.start_sec
            new_duration = max(2, int(original_duration * scale))
            
            scene.start_sec = current_time
            scene.end_sec = current_time + new_duration
            current_time = scene.end_sec
        
        # Ensure last scene ends at target
        scenes[-1].end_sec = target
        
        logger.info(f"Adjusted duration: {current_total}s → {scenes[-1].end_sec}s")
        
        return scenes
