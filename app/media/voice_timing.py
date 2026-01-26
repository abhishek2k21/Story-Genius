"""
Voice Timing Engine
Ensures perfect voice-to-scene synchronization with precise duration prediction.
"""
from typing import Dict, List, Optional
from dataclasses import dataclass
from app.core.logging import get_logger

logger = get_logger(__name__)


@dataclass
class TimingPrediction:
    """Predicted timing information for narration"""
    text: str
    predicted_duration: float  # seconds
    word_count: int
    character_count: int
    wpm: int  # words per minute


class VoiceTimingEngine:
    """Predicts and manages voice timing for perfect sync"""
    
    # Voice-specific speech rates (words per minute)
    SPEECH_RATES = {
        "en-US-GuyNeural": 160,
        "en-US-JennyNeural": 155,
        "en-US-AriaNeural": 158,
        "en-IN-NeerjaNeural": 150,
        "en-IN-PrabhatNeural": 145,
        "hi-IN-MadhurNeural": 140,
        "hi-IN-SwaraNeural": 142,
        "default": 150
    }
    
    # Pause durations for different punctuation (seconds)
    PAUSE_DURATIONS = {
        ".": 0.5,
        "!": 0.5,
        "?": 0.5,
        ",": 0.3,
        ";": 0.4,
        ":": 0.4,
        "scene_transition": 0.5  # Between scenes
    }
    
    def analyze_voice_duration(
        self,
        text: str,
        voice: str = "default",
        include_pauses: bool = True
    ) -> TimingPrediction:
        """
        Predict exact audio duration BEFORE generating
        
        Args:
            text: The narration text
            voice: Voice identifier (EdgeTTS voice name)
            include_pauses: Whether to account for punctuation pauses
        
        Returns:
            TimingPrediction with duration estimate
        """
        # Get speech rate for this voice
        wpm = self.SPEECH_RATES.get(voice, self.SPEECH_RATES["default"])
        
        # Count words and characters
        words = text.split()
        word_count = len(words)
        char_count = len(text)
        
        # Base duration from word count
        base_duration = (word_count / wpm) * 60
        
        # Add pause durations if requested
        pause_duration = 0
        if include_pauses:
            for punct, duration in self.PAUSE_DURATIONS.items():
                if punct != "scene_transition":
                    pause_duration += text.count(punct) * duration
        
        total_duration = base_duration + pause_duration
        
        prediction = TimingPrediction(
            text=text,
            predicted_duration=total_duration,
            word_count=word_count,
            character_count=char_count,
            wpm=wpm
        )
        
        logger.debug(
            f"Predicted {total_duration:.2f}s for {word_count} words "
            f"(base: {base_duration:.2f}s, pauses: {pause_duration:.2f}s)"
        )
        
        return prediction
    
    def adjust_scene_duration(
        self,
        scenes: List[Dict],
        voice: str = "default",
        max_hook_duration: float = 2.0
    ) -> List[Dict]:
        """
        Adjust scene durations to match predicted voice length
        
        Args:
            scenes: List of scene dictionaries with 'narration' field
            voice: Voice to use for prediction
            max_hook_duration: Maximum duration for hook (first scene)
        
        Returns:
            Scenes with updated 'duration' and 'predicted_duration' fields
        """
        adjusted_scenes = []
        
        for i, scene in enumerate(scenes):
            narration = scene.get("narration", "")
            
            # Predict duration
            prediction = self.analyze_voice_duration(narration, voice)
            
            # Add buffer for natural flow (0.3s)
            predicted = prediction.predicted_duration + 0.3
            
            # Special handling for hook (Scene 0)
            if i == 0 and predicted > max_hook_duration:
                logger.warning(
                    f"Hook too long ({predicted:.2f}s). "
                    f"Should compress to {max_hook_duration}s"
                )
                # Store original and target
                scene["predicted_duration"] = predicted
                scene["target_duration"] = max_hook_duration
                scene["needs_compression"] = True
                scene["duration"] = max_hook_duration
            else:
                scene["predicted_duration"] = predicted
                scene["duration"] = predicted
                scene["needs_compression"] = False
            
            adjusted_scenes.append(scene)
        
        logger.info(f"Adjusted durations for {len(scenes)} scenes")
        return adjusted_scenes
    
    def compress_text(
        self,
        text: str,
        target_duration: float,
        voice: str = "default",
        llm_service=None
    ) -> str:
        """
        Compress text to fit within target duration while keeping meaning
        
        Args:
            text: Original text
            target_duration: Target duration in seconds
            voice: Voice for duration calculation
            llm_service: LLM service for compression
        
        Returns:
            Compressed text that fits duration
        """
        current = self.analyze_voice_duration(text, voice)
        
        if current.predicted_duration <= target_duration:
            return text  # Already fits
        
        # Calculate target word count
        wpm = self.SPEECH_RATES.get(voice, self.SPEECH_RATES["default"])
        target_words = int((target_duration * wpm) / 60)
        
        logger.info(
            f"Compressing from {current.word_count} to ~{target_words} words "
            f"(target: {target_duration:.2f}s)"
        )
        
        # Use LLM to compress intelligently
        if llm_service is None:
            from app.llm.gemini_service import GeminiService
            llm_service = GeminiService()
        
        prompt = f"""
Compress this text to approximately {target_words} words while keeping the core message:

"{text}"

Requirements:
- Must be {target_words} words or fewer
- Keep the main point and key details
- Maintain natural flow
- Don't add new information

Return ONLY the compressed text.
"""
        
        try:
            compressed = llm_service.generate_text(prompt).strip()
            
            # Verify it fits
            verification = self.analyze_voice_duration(compressed, voice)
            if verification.predicted_duration <= target_duration:
                logger.info(f"Compression successful: {verification.predicted_duration:.2f}s")
                return compressed
            else:
                logger.warning(
                    f"Compression still too long: {verification.predicted_duration:.2f}s"
                )
                return compressed  # Return anyway, might need manual adjustment
                
        except Exception as e:
            logger.error(f"Compression failed: {e}")
            # Fallback: simple truncation
            words = text.split()[:target_words]
            return " ".join(words)
    
    def generate_with_markers(
        self,
        texts: List[str],
        voice: str = "default"
    ) -> str:
        """
        Generate SSML with scene transition markers
        
        Args:
            texts: List of narration texts (one per scene)
            voice: Voice name
        
        Returns:
            SSML string with pause markers between scenes
        """
        pause_duration = int(self.PAUSE_DURATIONS["scene_transition"] * 1000)  # ms
        
        ssml_parts = [f'<speak><voice name="{voice}">']
        
        for i, text in enumerate(texts):
            ssml_parts.append(text)
            
            # Add pause between scenes (except after last)
            if i < len(texts) - 1:
                ssml_parts.append(f'<break time="{pause_duration}ms"/>')
        
        ssml_parts.append('</voice></speak>')
        
        ssml = "\n".join(ssml_parts)
        logger.debug(f"Generated SSML for {len(texts)} scenes")
        
        return ssml
