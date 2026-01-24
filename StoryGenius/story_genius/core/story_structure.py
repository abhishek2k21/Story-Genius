import json
from dataclasses import dataclass, field
from typing import Optional, List

@dataclass
class SceneNode:
    id: int
    script: str
    visual_description: str
    duration: int = 8 # Default for Veo
    prev: Optional['SceneNode'] = None
    next: Optional['SceneNode'] = None
    
    # Artifacts
    audio_path: str = ""
    video_path: str = ""

class StoryBoard:
    def __init__(self):
        self.head: Optional[SceneNode] = None
        self.tail: Optional[SceneNode] = None
        self.scenes: List[SceneNode] = []

    def add_scene(self, script, visual_description):
        new_scene = SceneNode(
            id=len(self.scenes) + 1,
            script=script,
            visual_description=visual_description
        )
        
        if not self.head:
            self.head = new_scene
            self.tail = new_scene
        else:
            new_scene.prev = self.tail
            self.tail.next = new_scene
            self.tail = new_scene
            
        self.scenes.append(new_scene)
        return new_scene

    def to_list(self):
        return self.scenes
