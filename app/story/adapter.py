"""
Enhanced Story Adapter (Week 2)
Integrates Hook Engine, Persona System, and Emotion Curves.
"""
import uuid
import json
import sys
from pathlib import Path
from typing import List, Optional, Tuple

# Add StoryGenius to path
STORYGENIUS_PATH = Path(__file__).parent.parent.parent / "StoryGenius"
sys.path.insert(0, str(STORYGENIUS_PATH))

from app.core.models import Story, Scene, ScenePurpose, Job
from app.core.logging import JobLogger, get_logger
from app.core.config import settings
from app.strategy.hook_engine import HookEngine, HookResult
from app.intelligence.personas import PersonaService, Persona
from app.intelligence.emotion_curves import EmotionCurveService, EmotionCurve, Emotion

logger = get_logger(__name__)


class StoryAdapter:
    """
    Week 2 Story Adapter with intelligent content generation.
    Integrates Hook Engine, Personas, and Emotion Curves.
    """
    
    def __init__(self, job: Job):
        self.job = job
        self.job_logger = JobLogger(job.id)
        self._llm = None
        
        # Week 2 components
        self.hook_engine = HookEngine()
        self.persona = PersonaService.select_persona(job.audience, job.genre)
        self.emotion_curve = EmotionCurveService.select_curve(job.genre, job.audience)
        
        self.job_logger.info(f"Using persona: {self.persona.name}")
        self.job_logger.info(f"Using curve: {self.emotion_curve.name}")
        
    def _get_llm(self):
        """Lazy load Vertex LLM."""
        if self._llm is None:
            try:
                from story_genius.llm.vertex_wrapper import VertexLLM
                self._llm = VertexLLM()
            except Exception as e:
                logger.error(f"Failed to initialize LLM: {e}")
                raise
        return self._llm
    
    def _determine_scene_purpose(self, index: int, total: int) -> ScenePurpose:
        """Determine scene purpose based on position."""
        if index == 0:
            return ScenePurpose.HOOK
        elif index == total - 1:
            return ScenePurpose.LOOP
        elif index < total * 0.4:
            return ScenePurpose.ESCALATE
        elif index < total * 0.7:
            return ScenePurpose.TENSION
        else:
            return ScenePurpose.TWIST
    
    def _calculate_scene_timing(self, index: int, total: int, duration: int) -> Tuple[int, int]:
        """Calculate start and end seconds for a scene."""
        if index == 0:
            return (0, min(2, duration // total))
        
        scene_duration = duration // total
        start_sec = 2 + (index - 1) * scene_duration if index > 0 else 0
        end_sec = start_sec + scene_duration
        
        if index == total - 1:
            end_sec = duration
            
        return (start_sec, end_sec)
    
    def generate_hook(self) -> HookResult:
        """Generate and select the best hook using Hook Engine."""
        self.job_logger.info("Generating hook variants...")
        
        return self.hook_engine.generate_and_select(
            topic=f"{self.job.genre} content for {self.job.audience}",
            audience=self.job.audience,
            platform=self.job.platform if isinstance(self.job.platform, str) else self.job.platform.value,
            count=5
        )
    
    def generate_story(self, use_hook_engine: bool = True) -> Story:
        """
        Generate a story with Week 2 intelligence.
        
        Args:
            use_hook_engine: Whether to use Hook Engine for Scene 1
            
        Returns:
            Story object with scenes
        """
        self.job_logger.info("Generating intelligent story...")
        
        llm = self._get_llm()
        num_scenes = max(3, self.job.duration // 5)
        
        # Get hook using Hook Engine
        hook_result = None
        if use_hook_engine:
            hook_result = self.generate_hook()
        
        # Get emotion assignments for scenes
        emotions = EmotionCurveService.get_scene_emotions(
            self.emotion_curve, num_scenes, self.job.duration
        )
        
        # Build prompt with persona and emotion guidance
        persona_modifier = self.persona.get_prompt_modifier()
        emotion_guidance = "\n".join([
            f"Scene {i+1}: Target emotion = {emotions[i].value}"
            for i in range(num_scenes)
        ])
        
        # If we have a hook, generate remaining scenes
        scenes_to_generate = num_scenes - 1 if hook_result else num_scenes
        
        prompt = f"""
        Create a {self.job.duration}-second short-form video script for {self.job.platform}.
        
        Target Audience: {self.job.audience}
        Genre: {self.job.genre}
        Language: {self.job.language}
        
        PERSONA STYLE: {self.persona.name}
        {persona_modifier}
        
        EMOTION CURVE: {self.emotion_curve.name}
        {emotion_guidance}
        
        {"IMPORTANT: Scene 1 hook is already provided. Generate ONLY scenes 2-" + str(num_scenes) + "." if hook_result else ""}
        
        RULES:
        1. Each scene narration MAX 10 words
        2. Match the target emotion for each scene
        3. Visual prompts must be detailed for AI generation
        4. Last scene must create loop desire
        
        Output valid JSON array with {scenes_to_generate} scenes:
        [
            {{"narration": "...", "visual": "...", "emotion": "..."}}
        ]
        """
        
        try:
            response = llm.generate_content(prompt)
            response = response.replace("```json", "").replace("```", "").strip()
            scene_data = json.loads(response)
            
            scenes = []
            
            # Add hook as Scene 1 if using Hook Engine
            if hook_result:
                hook = hook_result.selected_hook
                scenes.append(Scene(
                    id=1,
                    start_sec=0,
                    end_sec=2,
                    purpose=ScenePurpose.HOOK,
                    narration_text=hook.text,
                    visual_prompt=f"{self.persona.visual_style_prefix}, {hook.visual_prompt}"
                ))
            
            # Add remaining scenes
            start_index = 1 if hook_result else 0
            for i, item in enumerate(scene_data):
                scene_num = i + start_index + 1
                if scene_num > num_scenes:
                    break
                    
                start_sec, end_sec = self._calculate_scene_timing(
                    scene_num - 1, num_scenes, self.job.duration
                )
                purpose = self._determine_scene_purpose(scene_num - 1, num_scenes)
                
                # Add persona visual style
                visual = f"{self.persona.visual_style_prefix}, {item.get('visual', '')}"
                
                scene = Scene(
                    id=scene_num,
                    start_sec=start_sec,
                    end_sec=end_sec,
                    purpose=purpose,
                    narration_text=item.get("narration", item.get("script", "")),
                    visual_prompt=visual
                )
                scenes.append(scene)
            
            story = Story(
                id=str(uuid.uuid4()),
                job_id=self.job.id,
                total_duration=self.job.duration,
                scenes=scenes
            )
            
            self.job_logger.info(f"Generated story with {len(scenes)} scenes using {self.persona.name} persona")
            return story
            
        except json.JSONDecodeError as e:
            self.job_logger.error(f"Failed to parse LLM response: {e}")
            raise
        except Exception as e:
            self.job_logger.error(f"Story generation failed: {e}")
            raise
    
    def regenerate_hook_only(self, story: Story) -> Story:
        """Regenerate only the hook scene (targeted retry)."""
        self.job_logger.info("Regenerating hook only...")
        
        hook_result = self.generate_hook()
        hook = hook_result.selected_hook
        
        # Replace Scene 1
        if story.scenes:
            story.scenes[0] = Scene(
                id=1,
                start_sec=0,
                end_sec=2,
                purpose=ScenePurpose.HOOK,
                narration_text=hook.text,
                visual_prompt=f"{self.persona.visual_style_prefix}, {hook.visual_prompt}"
            )
        
        return story
    
    def regenerate_ending_only(self, story: Story) -> Story:
        """Regenerate only the ending scene (targeted retry)."""
        self.job_logger.info("Regenerating ending only...")
        
        llm = self._get_llm()
        
        prompt = f"""
        Create a LOOP ending for a {self.job.duration}-second {self.job.genre} video.
        
        The ending must:
        1. Create replay desire (question, cliffhanger, or callback)
        2. MAX 10 words
        3. Match {self.persona.name} style
        
        Output ONLY JSON:
        {{"narration": "...", "visual": "..."}}
        """
        
        try:
            response = llm.generate_content(prompt)
            response = response.replace("```json", "").replace("```", "").strip()
            data = json.loads(response)
            
            if story.scenes:
                last_scene = story.scenes[-1]
                story.scenes[-1] = Scene(
                    id=last_scene.id,
                    start_sec=last_scene.start_sec,
                    end_sec=last_scene.end_sec,
                    purpose=ScenePurpose.LOOP,
                    narration_text=data.get("narration", ""),
                    visual_prompt=f"{self.persona.visual_style_prefix}, {data.get('visual', '')}"
                )
            
            return story
            
        except Exception as e:
            self.job_logger.error(f"Ending regeneration failed: {e}")
            return story
    
    def story_to_dict(self, story: Story) -> dict:
        """Convert story to dictionary format."""
        return {
            "id": story.id,
            "job_id": story.job_id,
            "total_duration": story.total_duration,
            "persona": self.persona.id,
            "emotion_curve": self.emotion_curve.id,
            "scenes": [
                {
                    "id": scene.id,
                    "start_sec": scene.start_sec,
                    "end_sec": scene.end_sec,
                    "purpose": scene.purpose.value,
                    "narration_text": scene.narration_text,
                    "visual_prompt": scene.visual_prompt
                }
                for scene in story.scenes
            ]
        }
