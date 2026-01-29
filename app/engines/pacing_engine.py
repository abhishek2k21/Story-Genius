"""
Pacing Analysis Engine
Analyzes script pacing and compares to genre benchmarks.
"""
from dataclasses import dataclass
from typing import List, Dict, Any, Optional
from datetime import datetime
import re

from app.core.logging import get_logger

logger = get_logger(__name__)


@dataclass
class StoryBeat:
    """Represents a story beat"""
    timestamp: float  # seconds
    content: str
    type: str  # setup, conflict, climax, resolution
    intensity: float  # 0-1


@dataclass
class PacingScore:
    """Pacing analysis result"""
    total_score: float  # 0-100
    beat_density: float  # beats per minute
    rhythm_consistency: float  # 0-1
    genre_match: float  # 0-1
    beats: List[StoryBeat]
    grade: str
    suggestions: List[str]
    timestamp: datetime = None
    
    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = datetime.utcnow()
    
    def to_dict(self) -> dict:
        return {
            "total_score": round(self.total_score, 2),
            "beat_density": round(self.beat_density, 2),
            "rhythm_consistency": round(self.rhythm_consistency, 2),
            "genre_match": round(self.genre_match, 2),
            "beat_count": len(self.beats),
            "grade": self.grade,
            "suggestions": self.suggestions,
            "beats": [
                {
                    "timestamp": b.timestamp,
                    "type": b.type,
                    "intensity": b.intensity
                } for b in self.beats
            ]
        }


class PacingEngine:
    """
    Analyzes script pacing and compares to genre benchmarks.
    """
    
    # Genre pacing benchmarks (beats per minute)
    GENRE_BENCHMARKS = {
        "action": {"min": 5, "max": 7, "optimal": 6},
        "adventure": {"min": 4, "max": 6, "optimal": 5},
        "comedy": {"min": 4, "max": 8, "optimal": 6},
        "drama": {"min": 3, "max": 5, "optimal": 4},
        "horror": {"min": 2, "max": 4, "optimal": 3},
        "thriller": {"min": 3, "max": 5, "optimal": 4},
        "romance": {"min": 2, "max": 4, "optimal": 3},
        "scifi": {"min": 3, "max": 5, "optimal": 4},
        "fantasy": {"min": 3, "max": 5, "optimal": 4},
        "mystery": {"min": 3, "max": 5, "optimal": 4},
        "documentary": {"min": 2, "max": 4, "optimal": 3},
        "educational": {"min": 2, "max": 3, "optimal": 2.5}
    }
    
    def __init__(self):
        logger.info("PacingEngine initialized")
    
    def analyze_pacing(
        self,
        script: str,
        genre: str = "general",
        duration: int = 60
    ) -> PacingScore:
        """
        Analyze script pacing.
        
        Args:
            script: Full script text
            genre: Content genre
            duration: Expected duration in seconds
        
        Returns:
            PacingScore with detailed analysis
        """
        logger.info(f"Analyzing pacing for {genre} genre ({duration}s)")
        
        # Extract story beats
        beats = self._extract_beats(script, duration)
        
        # Calculate beat density (beats per minute)
        beat_density = len(beats) / (duration / 60)
        
        # Calculate rhythm consistency
        rhythm = self._calculate_rhythm_consistency(beats)
        
        # Compare to genre benchmark
        genre_match = self._compare_to_benchmark(beat_density, genre)
        
        # Calculate total score
        total_score = self._calculate_total_score(beat_density, rhythm, genre_match, genre)
        
        # Determine grade
        if total_score >= 90:
            grade = "Excellent"
        elif total_score >= 70:
            grade = "Good"
        elif total_score >= 50:
            grade = "Fair"
        else:
            grade = "Poor"
        
        # Generate suggestions
        suggestions = self._generate_suggestions(beat_density, rhythm, genre_match, genre)
        
        score = PacingScore(
            total_score=total_score,
            beat_density=beat_density,
            rhythm_consistency=rhythm,
            genre_match=genre_match,
            beats=beats,
            grade=grade,
            suggestions=suggestions
        )
        
        logger.info(f"Pacing score: {total_score}/100 ({grade}), {beat_density:.1f} beats/min")
        return score
    
    def _extract_beats(self, script: str, duration: int) -> List[StoryBeat]:
        """Extract story beats from script"""
        # Split script into sentences
        sentences = re.split(r'[.!?]+', script)
        sentences = [s.strip() for s in sentences if s.strip()]
        
        if not sentences:
            return []
        
        beats = []
        time_per_sentence = duration / len(sentences)
        
        for i, sentence in enumerate(sentences):
            timestamp = i * time_per_sentence
            
            # Classify beat type
            beat_type = self._classify_beat(sentence, i, len(sentences))
            
            # Calculate intensity (simple heuristic based on punctuation and caps)
            intensity = min(1.0, (sentence.count('!') * 0.3 + 
                                  sentence.count('?') * 0.2 + 
                                  sum(1 for c in sentence if c.isupper()) * 0.01))
            
            beats.append(StoryBeat(
                timestamp=timestamp,
                content=sentence[:50],  # First 50 chars
                type=beat_type,
                intensity=intensity
            ))
        
        return beats
    
    def _classify_beat(self, sentence: str, index: int, total: int) -> str:
        """Classify beat type based on position and content"""
        position = index / total
        
        if position < 0.25:
            return "setup"
        elif position < 0.75:
            # Check for conflict markers
            conflict_words = ['but', 'however', 'problem', 'challenge', 'issue']
            if any(word in sentence.lower() for word in conflict_words):
                return "conflict"
            return "development"
        elif position < 0.9:
            return "climax"
        else:
            return "resolution"
    
    def _calculate_rhythm_consistency(self, beats: List[StoryBeat]) -> float:
        """Calculate rhythm consistency (0-1)"""
        if len(beats) < 2:
            return 1.0
        
        # Calculate time intervals between beats
        intervals = [beats[i+1].timestamp - beats[i].timestamp 
                     for i in range(len(beats)-1)]
        
        if not intervals:
            return 1.0
        
        # Calculate standard deviation of intervals
        mean_interval = sum(intervals) / len(intervals)
        variance = sum((x - mean_interval) ** 2 for x in intervals) / len(intervals)
        std_dev = variance ** 0.5
        
        # Normalize (lower std_dev = higher consistency)
        consistency = max(0, 1 - (std_dev / mean_interval))
        
        return consistency
    
    def _compare_to_benchmark(self, beat_density: float, genre: str) -> float:
        """Compare beat density to genre benchmark (0-1)"""
        benchmark = self.GENRE_BENCHMARKS.get(genre.lower(), 
                                               {"min": 2, "max": 6, "optimal": 4})
        
        optimal = benchmark["optimal"]
        min_val = benchmark["min"]
        max_val = benchmark["max"]
        
        # Calculate how close to optimal
        if beat_density == optimal:
            return 1.0
        elif min_val <= beat_density <= max_val:
            # Within acceptable range
            distance = abs(beat_density - optimal)
            max_distance = max(optimal - min_val, max_val - optimal)
            return 1 - (distance / max_distance) * 0.3  # 70-100% match
        else:
            # Outside acceptable range
            if beat_density < min_val:
                return max(0, 1 - (min_val - beat_density) / min_val)
            else:
                return max(0, 1 - (beat_density - max_val) / max_val)
    
    def _calculate_total_score(
        self, 
        beat_density: float, 
        rhythm: float, 
        genre_match: float, 
        genre: str
    ) -> float:
        """Calculate total pacing score (0-100)"""
        # Weighted scoring
        genre_weight = 0.4
        rhythm_weight = 0.3
        density_weight = 0.3
        
        # Density score (based on reasonable range 2-8 beats/min)
        density_score = min(1.0, beat_density / 6) if beat_density <= 6 else max(0, 1 - (beat_density - 6) / 4)
        
        total = (genre_match * genre_weight * 100 + 
                 rhythm * rhythm_weight * 100 + 
                 density_score * density_weight * 100)
        
        return min(100, total)
    
    def _generate_suggestions(
        self, 
        beat_density: float, 
        rhythm: float, 
        genre_match: float, 
        genre: str
    ) -> List[str]:
        """Generate pacing suggestions"""
        suggestions = []
        
        benchmark = self.GENRE_BENCHMARKS.get(genre.lower(), 
                                               {"min": 2, "max": 6, "optimal": 4})
        
        if beat_density < benchmark["min"]:
            suggestions.append(f"Pacing is too slow for {genre}. Add more story beats.")
        elif beat_density > benchmark["max"]:
            suggestions.append(f"Pacing is too fast for {genre}. Reduce beat density.")
        
        if rhythm < 0.7:
            suggestions.append("Rhythm is inconsistent. Distribute story beats more evenly.")
        
        if genre_match < 0.7:
            suggestions.append(f"Pacing doesn't match {genre} genre expectations. "
                              f"Target {benchmark['optimal']} beats/minute.")
        
        return suggestions


# Global instance
pacing_engine = PacingEngine()
