"""
Script Engine
Generates segmented scripts with separate hook, body, and CTA sections.
"""
from typing import Dict, List, Optional
from dataclasses import dataclass, field
from enum import Enum

from app.engines.base import BaseEngine, EngineInput, EngineOutput, EngineStatus, EngineDefinition
from app.engines.registry import EngineRegistry
from app.engines.hook_engine import hook_engine, HookStyle
from app.core.logging import get_logger

logger = get_logger(__name__)


class ContentCategory(str, Enum):
    FACT = "fact"
    STORY = "story"
    TUTORIAL = "tutorial"
    MOTIVATION = "motivation"
    ENTERTAINMENT = "entertainment"


class StructureTemplate(str, Enum):
    HOOK_BODY_CTA = "hook_body_cta"  # Standard structure
    HOOK_PROBLEM_SOLUTION = "hook_problem_solution"
    HOOK_LIST = "hook_list"  # Hook + numbered list
    HOOK_STORY_LESSON = "hook_story_lesson"


@dataclass
class ScriptSegment:
    """A single segment of the script"""
    segment_type: str  # "hook", "body", "cta", "problem", "solution", etc.
    text: str
    target_duration: float  # seconds
    order: int
    
    def to_dict(self) -> Dict:
        return {
            "type": self.segment_type,
            "text": self.text,
            "target_duration": self.target_duration,
            "order": self.order,
            "word_count": len(self.text.split())
        }


@dataclass
class SegmentedScript:
    """Complete script with segments"""
    segments: List[ScriptSegment] = field(default_factory=list)
    total_duration: float = 0
    word_count: int = 0
    
    @property
    def hook(self) -> Optional[ScriptSegment]:
        for s in self.segments:
            if s.segment_type == "hook":
                return s
        return None
    
    @property
    def body(self) -> List[ScriptSegment]:
        return [s for s in self.segments if s.segment_type == "body"]
    
    @property
    def cta(self) -> Optional[ScriptSegment]:
        for s in self.segments:
            if s.segment_type == "cta":
                return s
        return None
    
    @property
    def full_text(self) -> str:
        return " ".join(s.text for s in sorted(self.segments, key=lambda x: x.order))
    
    def to_dict(self) -> Dict:
        return {
            "segments": [s.to_dict() for s in self.segments],
            "full_text": self.full_text,
            "total_duration": self.total_duration,
            "word_count": self.word_count,
            "segment_count": len(self.segments)
        }


# Words per second for duration estimation
WORDS_PER_SECOND = 2.5


class ScriptEngine(BaseEngine):
    """Engine for generating segmented video scripts"""
    
    def __init__(self):
        super().__init__(
            engine_id="script_engine_v1",
            engine_type="script",
            version="1.0.0"
        )
    
    def validate_input(self, input_data: EngineInput) -> Dict:
        errors = []
        params = input_data.parameters
        
        if not params.get("topic"):
            errors.append("Missing required parameter: topic")
        
        duration = params.get("target_duration", 30)
        if duration < 5 or duration > 180:
            errors.append("target_duration must be 5-180 seconds")
        
        return {"valid": len(errors) == 0, "errors": errors}
    
    async def execute(self, input_data: EngineInput) -> EngineOutput:
        """Generate segmented script"""
        self.status = EngineStatus.RUNNING
        
        params = input_data.parameters
        topic = params.get("topic", "")
        category = ContentCategory(params.get("category", "fact"))
        structure = StructureTemplate(params.get("structure", "hook_body_cta"))
        target_duration = params.get("target_duration", 30)
        hook_style = HookStyle(params.get("hook_style", "curiosity"))
        
        # Generate script
        script = await self._generate_script(
            topic, category, structure, target_duration, hook_style
        )
        
        self.status = EngineStatus.COMPLETED
        
        return EngineOutput(
            job_id=input_data.job_id,
            engine_id=self.engine_id,
            status=EngineStatus.COMPLETED,
            primary_artifact=script.full_text,
            metadata={
                "script": script.to_dict(),
                "topic": topic,
                "category": category.value,
                "structure": structure.value
            },
            quality_scores={
                "duration_accuracy": self._score_duration(script, target_duration),
                "structure_score": 0.9
            }
        )
    
    def validate_output(self, output: EngineOutput) -> Dict:
        errors = []
        if not output.primary_artifact:
            errors.append("No script generated")
        return {"valid": len(errors) == 0, "errors": errors}
    
    async def _generate_script(
        self,
        topic: str,
        category: ContentCategory,
        structure: StructureTemplate,
        target_duration: float,
        hook_style: HookStyle
    ) -> SegmentedScript:
        """Generate a complete segmented script"""
        segments = []
        
        # Allocate time to segments
        hook_duration = 3  # 2-3 seconds for hook
        cta_duration = 4  # 3-5 seconds for CTA
        body_duration = target_duration - hook_duration - cta_duration
        
        # Generate hook
        hook_input = EngineInput(
            job_id="internal",
            engine_id="hook_engine_v1",
            parameters={"topic": topic, "style": hook_style.value, "count": 1}
        )
        hook_output = await hook_engine.execute(hook_input)
        hook_text = hook_output.primary_artifact or f"Here's something amazing about {topic}"
        
        segments.append(ScriptSegment(
            segment_type="hook",
            text=hook_text,
            target_duration=hook_duration,
            order=0
        ))
        
        # Generate body based on structure
        body_segments = self._generate_body(topic, category, structure, body_duration)
        for i, seg in enumerate(body_segments):
            seg.order = i + 1
            segments.append(seg)
        
        # Generate CTA
        cta_text = self._generate_cta(topic, category)
        segments.append(ScriptSegment(
            segment_type="cta",
            text=cta_text,
            target_duration=cta_duration,
            order=len(segments)
        ))
        
        script = SegmentedScript(segments=segments)
        script.word_count = len(script.full_text.split())
        script.total_duration = script.word_count / WORDS_PER_SECOND
        
        return script
    
    def _generate_body(
        self,
        topic: str,
        category: ContentCategory,
        structure: StructureTemplate,
        duration: float
    ) -> List[ScriptSegment]:
        """Generate body segments based on structure"""
        target_words = int(duration * WORDS_PER_SECOND)
        
        if structure == StructureTemplate.HOOK_BODY_CTA:
            return [ScriptSegment(
                segment_type="body",
                text=self._generate_body_text(topic, category, target_words),
                target_duration=duration,
                order=0
            )]
        
        elif structure == StructureTemplate.HOOK_PROBLEM_SOLUTION:
            half_words = target_words // 2
            return [
                ScriptSegment(
                    segment_type="problem",
                    text=f"The problem is that most people don't understand {topic}. They struggle with getting results because they've been given the wrong information.",
                    target_duration=duration / 2,
                    order=0
                ),
                ScriptSegment(
                    segment_type="solution",
                    text=f"The solution is simple. Once you understand how {topic} really works, everything changes. Here's what you need to do.",
                    target_duration=duration / 2,
                    order=1
                )
            ]
        
        elif structure == StructureTemplate.HOOK_LIST:
            point_duration = duration / 3
            return [
                ScriptSegment(
                    segment_type="body",
                    text=f"First, understand the basics of {topic}.",
                    target_duration=point_duration,
                    order=0
                ),
                ScriptSegment(
                    segment_type="body",
                    text=f"Second, apply what you've learned consistently.",
                    target_duration=point_duration,
                    order=1
                ),
                ScriptSegment(
                    segment_type="body",
                    text=f"Third, track your progress and adjust.",
                    target_duration=point_duration,
                    order=2
                )
            ]
        
        return [ScriptSegment(
            segment_type="body",
            text=self._generate_body_text(topic, category, target_words),
            target_duration=duration,
            order=0
        )]
    
    def _generate_body_text(self, topic: str, category: ContentCategory, target_words: int) -> str:
        """Generate body content based on category"""
        templates = {
            ContentCategory.FACT: f"Scientists discovered that {topic} works in ways we never expected. Research shows that understanding this can change how you think about everything. The evidence is clear and the implications are massive.",
            ContentCategory.STORY: f"This story about {topic} will blow your mind. It started with a simple observation but led to an incredible discovery. What happened next changed everything we thought we knew.",
            ContentCategory.TUTORIAL: f"Here's exactly how to master {topic}. Start by understanding the fundamentals. Then practice consistently. The key is to focus on one thing at a time until you get it right.",
            ContentCategory.MOTIVATION: f"Most people give up on {topic} too early. They don't realize that success is closer than they think. The difference between those who succeed and those who fail is persistence.",
            ContentCategory.ENTERTAINMENT: f"What you're about to learn about {topic} is absolutely wild. Most people have no idea this exists. Get ready to have your mind blown."
        }
        return templates.get(category, templates[ContentCategory.FACT])
    
    def _generate_cta(self, topic: str, category: ContentCategory) -> str:
        """Generate call to action"""
        ctas = [
            "Follow for more content like this.",
            "Like and share if you learned something new.",
            "Save this for later and follow for more.",
            "Comment below what you think."
        ]
        return ctas[hash(topic) % len(ctas)]
    
    def _score_duration(self, script: SegmentedScript, target: float) -> float:
        """Score how close we got to target duration"""
        diff = abs(script.total_duration - target)
        if diff <= 2:
            return 1.0
        elif diff <= 5:
            return 0.8
        elif diff <= 10:
            return 0.6
        return 0.4


# Create and register engine
script_engine = ScriptEngine()
EngineRegistry.register(
    script_engine,
    EngineDefinition(
        engine_id="script_engine_v1",
        engine_type="script",
        version="1.0.0",
        capabilities=["segmented_generation", "structure_templates", "duration_targeting"],
        required_inputs=["topic"],
        optional_inputs=["category", "structure", "target_duration", "hook_style"],
        output_types=["segmented_script", "full_text"]
    )
)
