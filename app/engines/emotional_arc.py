"""
Emotional Arc Tracking
Tracks emotional trajectory through a script for visualization and analysis.
"""
from dataclasses import dataclass
from typing import List, Dict, Optional
from datetime import datetime
import re

from app.core.logging import get_logger

logger = get_logger(__name__)


@dataclass
class EmotionPoint:
    """Single point on the emotional arc"""
    timestamp: float  # seconds
    emotion: str  # primary emotion
    intensity: float  # 0-1
    secondary_emotions: List[str]
    text_snippet: str


@dataclass
class EmotionalArc:
    """Complete emotional arc analysis"""
    arc: List[EmotionPoint]
    peaks: List[EmotionPoint]
    valleys: List[EmotionPoint]
    dominant_emotion: str
    emotion_variety: int
    arc_shape: str  # ascending, descending, u-shape, inverted-u, rollercoaster
    timestamp: datetime = None
    
    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = datetime.utcnow()
    
    def to_dict(self) -> dict:
        return {
            "arc": [
                {
                    "timestamp": p.timestamp,
                    "emotion": p.emotion,
                    "intensity": round(p.intensity, 2),
                    "secondary_emotions": p.secondary_emotions
                } for p in self.arc
            ],
            "peaks": [
                {
                    "timestamp": p.timestamp,
                    "emotion": p.emotion,
                    "intensity": round(p.intensity, 2)
                } for p in self.peaks
            ],
            "valleys": [
                {
                    "timestamp": p.timestamp,
                    "emotion": p.emotion,
                    "intensity": round(p.intensity, 2)
                } for p in self.valleys
            ],
            "dominant_emotion": self.dominant_emotion,
            "emotion_variety": self.emotion_variety,
            "arc_shape": self.arc_shape
        }


class EmotionalArcTracker:
    """
    Tracks emotional arc through content.
    Uses keyword-based emotion detection.
    """
    
    # Emotion keyword mappings
    EMOTION_KEYWORDS = {
        "joy": ["happy", "joy", "excited", "delighted", "cheerful", "glad", 
                "pleased", "wonderful", "amazing", "fantastic", "love"],
        "sadness": ["sad", "unhappy", "depressed", "miserable", "sorrowful", 
                    "gloomy", "melancholy", "crying", "tears", "heartbroken"],
        "anger": ["angry", "mad", "furious", "rage", "annoyed", "irritated", 
                  "frustrated", "outraged", "hostile", "bitter"],
        "fear": ["scared", "afraid", "terrified", "frightened", "anxious", 
                 "worried", "nervous", "panicked", "alarmed", "dread"],
        "surprise": ["surprised", "shocked", "astonished", "amazed", "stunned", 
                     "startled", "unexpected", "wow", "unbelievable"],
        "anticipation": ["excited", "eager", "hopeful", "expecting", "anticipate", 
                         "looking forward", "can't wait", "upcoming"],
        "trust": ["trust", "confident", "secure", "safe", "reliable", 
                  "believe", "faith", "certain"],
        "disgust": ["disgusted", "revolted", "sickened", "repulsed", 
                    "appalled", "nauseated", "gross", "yuck"]
    }
    
    # Emotion intensity modifiers
    INTENSITY_MODIFIERS = {
        "very": 1.3,
        "extremely": 1.5,
        "incredibly": 1.5,
        "absolutely": 1.4,
        "totally": 1.3,
        "completely": 1.4,
        "really": 1.2,
        "quite": 1.1,
        "somewhat": 0.8,
        "slightly": 0.6,
        "barely": 0.4
    }
    
    def __init__(self):
        logger.info("EmotionalArcTracker initialized")
    
    def track_emotions(
        self, 
        script: str, 
        duration: int = 60
    ) -> EmotionalArc:
        """
        Track emotional arc through script.
        
        Args:
            script: Full script text
            duration: Duration in seconds
        
        Returns:
            EmotionalArc with complete analysis
        """
        logger.info(f"Tracking emotional arc ({duration}s)")
        
        # Split script into segments
        segments = self._segment_script(script)
        
        # Extract emotions at each segment
        arc_points = []
        time_per_segment = duration / len(segments) if segments else duration
        
        for i, segment in enumerate(segments):
            timestamp = i * time_per_segment
            
            emotions = self._detect_emotions(segment)
            if emotions:
                primary = emotions[0]
                secondary = emotions[1:3] if len(emotions) > 1 else []
                intensity = self._calculate_intensity(segment, primary["emotion"])
                
                arc_points.append(EmotionPoint(
                    timestamp=timestamp,
                    emotion=primary["emotion"],
                    intensity=intensity,
                    secondary_emotions=[e["emotion"] for e in secondary],
                    text_snippet=segment[:50]
                ))
        
        # Identify peaks and valleys
        peaks = self._identify_peaks(arc_points)
        valleys = self._identify_valleys(arc_points)
        
        # Determine dominant emotion
        dominant = self._find_dominant_emotion(arc_points)
        
        # Count emotion variety
        unique_emotions = len(set(p.emotion for p in arc_points))
        
        # Determine arc shape
        arc_shape = self._determine_arc_shape(arc_points)
        
        arc = EmotionalArc(
            arc=arc_points,
            peaks=peaks,
            valleys=valleys,
            dominant_emotion=dominant,
            emotion_variety=unique_emotions,
            arc_shape=arc_shape
        )
        
        logger.info(f"Emotional arc tracked: {len(arc_points)} points, "
                   f"dominant={dominant}, shape={arc_shape}")
        return arc
    
    def _segment_script(self, script: str) -> List[str]:
        """Segment script into analysis chunks"""
        # Split by sentences
        sentences = re.split(r'[.!?]+', script)
        sentences = [s.strip() for s in sentences if s.strip()]
        
        # Group into segments (3-5 sentences each)
        segments = []
        segment_size = 3
        
        for i in range(0, len(sentences), segment_size):
            segment = ' '.join(sentences[i:i+segment_size])
            segments.append(segment)
        
        return segments
    
    def _detect_emotions(self, text: str) -> List[Dict[str, any]]:
        """Detect all emotions in text segment"""
        text_lower = text.lower()
        detected_emotions = []
        
        for emotion, keywords in self.EMOTION_KEYWORDS.items():
            score = sum(1 for keyword in keywords if keyword in text_lower)
            if score > 0:
                detected_emotions.append({
                    "emotion": emotion,
                    "score": score
                })
        
        # Sort by score (highest first)
        detected_emotions.sort(key=lambda x: x["score"], reverse=True)
        
        return detected_emotions if detected_emotions else [{"emotion": "neutral", "score": 0}]
    
    def _calculate_intensity(self, text: str, emotion: str) -> float:
        """Calculate emotion intensity (0-1)"""
        # Base intensity from punctuation
        intensity = 0.5
        
        # Exclamation marks increase intensity
        intensity += min(0.3, text.count('!') * 0.1)
        
        # Question marks add slight intensity
        intensity += min(0.1, text.count('?') * 0.05)
        
        # Caps words increase intensity
        caps_words = sum(1 for word in text.split() if word.isupper() and len(word) > 2)
        intensity += min(0.2, caps_words * 0.05)
        
        # Check for intensity modifiers
        text_lower = text.lower()
        for modifier, multiplier in self.INTENSITY_MODIFIERS.items():
            if modifier in text_lower:
                intensity *= multiplier
                break
        
        return min(1.0, intensity)
    
    def _identify_peaks(self, arc_points: List[EmotionPoint]) -> List[EmotionPoint]:
        """Identify emotional peaks (local maxima)"""
        if len(arc_points) < 3:
            return []
        
        peaks = []
        
        for i in range(1, len(arc_points) - 1):
            prev_intensity = arc_points[i-1].intensity
            curr_intensity = arc_points[i].intensity
            next_intensity = arc_points[i+1].intensity
            
            # Local maximum
            if curr_intensity > prev_intensity and curr_intensity > next_intensity:
                if curr_intensity > 0.6:  # Only significant peaks
                    peaks.append(arc_points[i])
        
        return peaks
    
    def _identify_valleys(self, arc_points: List[EmotionPoint]) -> List[EmotionPoint]:
        """Identify emotional valleys (local minima)"""
        if len(arc_points) < 3:
            return []
        
        valleys = []
        
        for i in range(1, len(arc_points) - 1):
            prev_intensity = arc_points[i-1].intensity
            curr_intensity = arc_points[i].intensity
            next_intensity = arc_points[i+1].intensity
            
            # Local minimum
            if curr_intensity < prev_intensity and curr_intensity < next_intensity:
                if curr_intensity < 0.4:  # Only significant valleys
                    valleys.append(arc_points[i])
        
        return valleys
    
    def _find_dominant_emotion(self, arc_points: List[EmotionPoint]) -> str:
        """Find most prevalent emotion"""
        if not arc_points:
            return "neutral"
        
        emotion_counts = {}
        for point in arc_points:
            emotion_counts[point.emotion] = emotion_counts.get(point.emotion, 0) + 1
        
        dominant = max(emotion_counts.items(), key=lambda x: x[1])[0]
        return dominant
    
    def _determine_arc_shape(self, arc_points: List[EmotionPoint]) -> str:
        """Determine overall arc shape"""
        if len(arc_points) < 3:
            return "flat"
        
        # Compare start, middle, end intensities
        start_avg = sum(p.intensity for p in arc_points[:len(arc_points)//3]) / (len(arc_points)//3)
        middle_avg = sum(p.intensity for p in arc_points[len(arc_points)//3:2*len(arc_points)//3]) / max(1, len(arc_points)//3)
        end_avg = sum(p.intensity for p in arc_points[2*len(arc_points)//3:]) / max(1, len(arc_points)//3)
        
        # Determine shape
        if end_avg > start_avg + 0.2:
            return "ascending"  # Builds up
        elif end_avg < start_avg - 0.2:
            return "descending"  # Winds down
        elif middle_avg < start_avg - 0.2 and middle_avg < end_avg - 0.2:
            return "u-shape"  # Valley in middle
        elif middle_avg > start_avg + 0.2 and middle_avg > end_avg + 0.2:
            return "inverted-u"  # Peak in middle
        else:
            # Check variance for rollercoaster
            intensities = [p.intensity for p in arc_points]
            variance = sum((x - sum(intensities)/len(intensities))**2 for x in intensities) / len(intensities)
            
            if variance > 0.1:
                return "rollercoaster"
            else:
                return "steady"


# Global instance
emotional_arc_tracker = EmotionalArcTracker()
