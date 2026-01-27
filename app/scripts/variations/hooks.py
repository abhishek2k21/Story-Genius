"""
Hook Testing
A/B hook testing system.
"""
from typing import Dict, List, Optional
from datetime import datetime
import uuid
import random
import threading

from app.scripts.variations.models import HookTest
from app.scripts.variations.generator import HOOK_TEMPLATES
from app.scripts.variations.scoring import variation_scorer


class HookTestService:
    """Hook A/B testing service"""
    
    _instance = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._tests: Dict[str, HookTest] = {}
            cls._instance._lock = threading.Lock()
        return cls._instance
    
    def create_test(
        self,
        user_id: str,
        base_script_id: str,
        body: str,
        cta: str,
        topic: str,
        hook_count: int = 5,
        hook_styles: List[str] = None
    ) -> HookTest:
        """Create hook A/B test"""
        
        # Ensure diverse styles
        if not hook_styles:
            hook_styles = list(HOOK_TEMPLATES.keys())
        
        # Generate hooks
        hooks = []
        used_styles = []
        
        for i in range(hook_count):
            style = hook_styles[i % len(hook_styles)]
            templates = HOOK_TEMPLATES.get(style, HOOK_TEMPLATES["curiosity"])
            
            # Avoid duplicate templates
            template = random.choice(templates)
            hook_text = template.format(topic=topic)
            
            # Score the hook
            hook_score = variation_scorer._score_hook(hook_text)
            
            hooks.append({
                "index": i + 1,
                "text": hook_text,
                "style": style,
                "score": round(hook_score, 1),
                "word_count": len(hook_text.split())
            })
            used_styles.append(style)
        
        # Sort by score
        hooks.sort(key=lambda h: h["score"], reverse=True)
        
        test = HookTest(
            test_id=str(uuid.uuid4()),
            user_id=user_id,
            base_script_id=base_script_id,
            body=body,
            cta=cta,
            hook_count=hook_count,
            hooks=hooks
        )
        
        with self._lock:
            self._tests[test.test_id] = test
        
        return test
    
    def get_test(self, test_id: str, user_id: str) -> Optional[HookTest]:
        """Get hook test by ID"""
        test = self._tests.get(test_id)
        if test and test.user_id == user_id:
            return test
        return None
    
    def list_tests(self, user_id: str) -> List[HookTest]:
        """List user's hook tests"""
        return [t for t in self._tests.values() if t.user_id == user_id]
    
    def select_hook(
        self,
        test_id: str,
        user_id: str,
        hook_index: int,
        reason: str = ""
    ) -> tuple:
        """Select hook for test"""
        test = self.get_test(test_id, user_id)
        if not test:
            return None, "Test not found"
        
        if hook_index < 1 or hook_index > len(test.hooks):
            return None, "Invalid hook index"
        
        test.selected_hook_index = hook_index
        test.selection_reason = reason
        test.completed_at = datetime.utcnow()
        
        # Build final script
        selected_hook = test.hooks[hook_index - 1]["text"]
        final_script = f"{selected_hook}\n\n{test.body}\n\n{test.cta}"
        
        return final_script, "Hook selected"
    
    def get_comparison(self, test_id: str, user_id: str) -> Optional[Dict]:
        """Get hook comparison view"""
        test = self.get_test(test_id, user_id)
        if not test:
            return None
        
        return {
            "test_id": test.test_id,
            "hook_count": test.hook_count,
            "hooks": test.hooks,
            "recommended_index": test.hooks[0]["index"] if test.hooks else None,
            "status": "completed" if test.completed_at else "pending"
        }


hook_test_service = HookTestService()
