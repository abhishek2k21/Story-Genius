"""
Variation Generator
Multi-variation script generation with different strategies.
"""
from typing import Dict, List
import random

from app.scripts.variations.models import (
    VariationRequest, ScriptVariation, VariationStrategy,
    create_variation_id
)


# Hook templates by style
HOOK_TEMPLATES = {
    "curiosity": [
        "What if I told you {topic} isn't what you think?",
        "Here's something about {topic} nobody talks about...",
        "The secret of {topic} that changed everything for me",
        "Why does everyone get {topic} wrong?"
    ],
    "fear": [
        "Stop doing {topic} like this - it's ruining your results",
        "The {topic} mistake that costs you everything",
        "If you're ignoring {topic}, you're already falling behind",
        "Warning: This {topic} error will hurt you"
    ],
    "promise": [
        "How to master {topic} in just 5 minutes",
        "The {topic} strategy that actually works",
        "Transform your {topic} with this simple trick",
        "Finally: A {topic} approach that delivers"
    ],
    "question": [
        "Have you ever wondered about {topic}?",
        "Why do some people succeed at {topic} while others fail?",
        "What's the real secret behind {topic}?",
        "Can {topic} really change your life?"
    ],
    "story": [
        "I failed at {topic} for years until I discovered this",
        "My {topic} journey started with a disaster",
        "When I first tried {topic}, everything went wrong",
        "The moment {topic} clicked for me"
    ]
}

TONES = ["educational", "entertaining", "inspirational", "practical"]
STRUCTURES = ["list", "narrative", "problem_solution", "question_answer"]


class VariationGenerator:
    """Generate multiple script variations"""
    
    def generate_variations(
        self,
        request: VariationRequest
    ) -> List[ScriptVariation]:
        """Generate variations based on strategy"""
        strategy = request.variation_strategy
        
        if strategy == VariationStrategy.HOOK_FOCUSED:
            return self._generate_hook_focused(request)
        elif strategy == VariationStrategy.TONE_VARIED:
            return self._generate_tone_varied(request)
        elif strategy == VariationStrategy.STRUCTURE_VARIED:
            return self._generate_structure_varied(request)
        elif strategy == VariationStrategy.ANGLE_VARIED:
            return self._generate_angle_varied(request)
        elif strategy == VariationStrategy.LENGTH_VARIED:
            return self._generate_length_varied(request)
        else:  # MIXED
            return self._generate_mixed(request)
    
    def _generate_hook_focused(self, request: VariationRequest) -> List[ScriptVariation]:
        """Same body, different hooks"""
        body = self._generate_body(request, "educational", "narrative")
        cta = self._generate_cta(request)
        
        styles = list(HOOK_TEMPLATES.keys())
        random.shuffle(styles)
        
        variations = []
        for i in range(request.variation_count):
            style = styles[i % len(styles)]
            hook = self._generate_hook(request.topic, style)
            
            variations.append(ScriptVariation(
                variation_id=create_variation_id(),
                request_id=request.request_id,
                variation_index=i + 1,
                hook=hook,
                body=body,
                cta=cta
            ))
        
        return variations
    
    def _generate_tone_varied(self, request: VariationRequest) -> List[ScriptVariation]:
        """Same topic, different tones"""
        variations = []
        
        for i in range(request.variation_count):
            tone = TONES[i % len(TONES)]
            hook = self._generate_hook(request.topic, "curiosity")
            body = self._generate_body(request, tone, "narrative")
            cta = self._generate_cta(request)
            
            variations.append(ScriptVariation(
                variation_id=create_variation_id(),
                request_id=request.request_id,
                variation_index=i + 1,
                hook=hook,
                body=body,
                cta=cta
            ))
        
        return variations
    
    def _generate_structure_varied(self, request: VariationRequest) -> List[ScriptVariation]:
        """Different content structures"""
        variations = []
        
        for i in range(request.variation_count):
            structure = STRUCTURES[i % len(STRUCTURES)]
            hook = self._generate_hook(request.topic, "promise")
            body = self._generate_body(request, "educational", structure)
            cta = self._generate_cta(request)
            
            variations.append(ScriptVariation(
                variation_id=create_variation_id(),
                request_id=request.request_id,
                variation_index=i + 1,
                hook=hook,
                body=body,
                cta=cta
            ))
        
        return variations
    
    def _generate_angle_varied(self, request: VariationRequest) -> List[ScriptVariation]:
        """Different perspectives"""
        angles = ["beginner", "advanced", "skeptic", "enthusiast", "practical"]
        variations = []
        
        for i in range(request.variation_count):
            angle = angles[i % len(angles)]
            style = list(HOOK_TEMPLATES.keys())[i % 5]
            
            hook = self._generate_hook(request.topic, style)
            body = self._generate_body(request, "educational", "narrative", angle)
            cta = self._generate_cta(request)
            
            variations.append(ScriptVariation(
                variation_id=create_variation_id(),
                request_id=request.request_id,
                variation_index=i + 1,
                hook=hook,
                body=body,
                cta=cta
            ))
        
        return variations
    
    def _generate_length_varied(self, request: VariationRequest) -> List[ScriptVariation]:
        """Different depths/lengths"""
        length_mods = [0.8, 1.0, 1.2]  # short, standard, long
        variations = []
        
        for i in range(request.variation_count):
            mod = length_mods[i % len(length_mods)]
            hook = self._generate_hook(request.topic, "curiosity")
            body = self._generate_body(request, "educational", "narrative", length_mod=mod)
            cta = self._generate_cta(request)
            
            variations.append(ScriptVariation(
                variation_id=create_variation_id(),
                request_id=request.request_id,
                variation_index=i + 1,
                hook=hook,
                body=body,
                cta=cta
            ))
        
        return variations
    
    def _generate_mixed(self, request: VariationRequest) -> List[ScriptVariation]:
        """Maximum diversity"""
        variations = []
        styles = list(HOOK_TEMPLATES.keys())
        
        for i in range(request.variation_count):
            style = styles[i % len(styles)]
            tone = TONES[i % len(TONES)]
            structure = STRUCTURES[i % len(STRUCTURES)]
            
            hook = self._generate_hook(request.topic, style)
            body = self._generate_body(request, tone, structure)
            cta = self._generate_cta(request)
            
            variations.append(ScriptVariation(
                variation_id=create_variation_id(),
                request_id=request.request_id,
                variation_index=i + 1,
                hook=hook,
                body=body,
                cta=cta
            ))
        
        return variations
    
    def _generate_hook(self, topic: str, style: str) -> str:
        """Generate hook with specific style"""
        templates = HOOK_TEMPLATES.get(style, HOOK_TEMPLATES["curiosity"])
        template = random.choice(templates)
        return template.format(topic=topic)
    
    def _generate_body(
        self,
        request: VariationRequest,
        tone: str,
        structure: str,
        angle: str = "general",
        length_mod: float = 1.0
    ) -> str:
        """Generate body content"""
        base_sentences = int(6 * length_mod)
        topic = request.topic
        
        if structure == "list":
            body = f"Here are the key points about {topic}:\n\n"
            for i in range(base_sentences):
                body += f"{i+1}. Important insight about {topic} from {angle} perspective.\n"
        elif structure == "problem_solution":
            body = f"The problem with {topic} is often overlooked.\n\n"
            body += f"Many people struggle because they don't understand {topic}.\n\n"
            body += f"The solution is simpler than you think.\n\n"
            body += f"By applying these principles to {topic}, you'll see results."
        elif structure == "question_answer":
            body = f"Why does {topic} matter? Let me explain.\n\n"
            body += f"What's the best approach? Here's what works.\n\n"
            body += f"How do you get started? Follow these steps."
        else:  # narrative
            body = f"Let me tell you about {topic}.\n\n"
            body += f"This {tone} perspective will change how you think.\n\n"
            for i in range(base_sentences - 2):
                body += f"Here's another key insight about {topic}. "
        
        return body.strip()
    
    def _generate_cta(self, request: VariationRequest) -> str:
        """Generate call to action"""
        ctas = [
            "Like and subscribe for more content like this!",
            "Drop a comment below with your thoughts!",
            "Share this with someone who needs to hear it!",
            "Follow for the next part of this series!",
            "Save this for later - you'll need it!"
        ]
        return random.choice(ctas)


variation_generator = VariationGenerator()
