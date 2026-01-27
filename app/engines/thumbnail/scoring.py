"""
CTR Scoring
Predict click-through rate for thumbnails.
"""
from typing import Dict, List
from dataclasses import dataclass

from app.engines.thumbnail.analysis import FrameAnalysis
from app.engines.thumbnail.presets import POWER_WORDS


@dataclass
class CTRScore:
    """Click-through rate prediction score"""
    total_score: float  # 0-100
    face_score: float
    text_score: float
    contrast_score: float
    curiosity_score: float
    emotion_score: float
    quality_score: float
    
    def to_dict(self) -> Dict:
        return {
            "total": round(self.total_score, 2),
            "breakdown": {
                "face_presence": round(self.face_score, 2),
                "text_clarity": round(self.text_score, 2),
                "color_contrast": round(self.contrast_score, 2),
                "curiosity_element": round(self.curiosity_score, 2),
                "emotional_trigger": round(self.emotion_score, 2),
                "visual_quality": round(self.quality_score, 2)
            }
        }


# CTR scoring weights
CTR_WEIGHTS = {
    "face_presence": 0.25,
    "text_clarity": 0.20,
    "color_contrast": 0.15,
    "curiosity_element": 0.15,
    "emotional_trigger": 0.15,
    "visual_quality": 0.10
}


def calculate_ctr_score(
    analysis: FrameAnalysis,
    text: str,
    style_contrast: float = 80
) -> CTRScore:
    """Calculate predicted CTR score for thumbnail"""
    
    # Face presence (25%)
    face_score = _score_face_presence(analysis)
    
    # Text clarity (20%)
    text_score = _score_text_clarity(text, style_contrast)
    
    # Color contrast (15%)
    contrast_score = analysis.contrast
    
    # Curiosity element (15%)
    curiosity_score = _score_curiosity(text)
    
    # Emotional trigger (15%)
    emotion_score = _score_emotion(text, analysis)
    
    # Visual quality (10%)
    quality_score = analysis.quality_score
    
    # Calculate weighted total
    total = (
        face_score * CTR_WEIGHTS["face_presence"] +
        text_score * CTR_WEIGHTS["text_clarity"] +
        contrast_score * CTR_WEIGHTS["color_contrast"] +
        curiosity_score * CTR_WEIGHTS["curiosity_element"] +
        emotion_score * CTR_WEIGHTS["emotional_trigger"] +
        quality_score * CTR_WEIGHTS["visual_quality"]
    )
    
    return CTRScore(
        total_score=total,
        face_score=face_score,
        text_score=text_score,
        contrast_score=contrast_score,
        curiosity_score=curiosity_score,
        emotion_score=emotion_score,
        quality_score=quality_score
    )


def _score_face_presence(analysis: FrameAnalysis) -> float:
    """Score based on face detection"""
    if analysis.faces_detected == 0:
        return 30  # No face penalty
    elif analysis.faces_detected == 1:
        return 100  # Optimal
    elif analysis.faces_detected == 2:
        return 85  # Good
    else:
        return 70  # Multiple faces can work


def _score_text_clarity(text: str, contrast: float) -> float:
    """Score text readability"""
    words = text.split()
    word_count = len(words)
    
    # Optimal 3-5 words
    if 3 <= word_count <= 5:
        length_score = 100
    elif word_count <= 7:
        length_score = 85
    elif word_count <= 2:
        length_score = 70
    else:
        length_score = 60
    
    # Factor in contrast
    return (length_score * 0.6) + (contrast * 0.4)


def _score_curiosity(text: str) -> float:
    """Score curiosity-inducing elements"""
    score = 50  # Base score
    text_upper = text.upper()
    
    # Question marks
    if "?" in text:
        score += 15
    
    # Numbers
    if any(c.isdigit() for c in text):
        score += 10
    
    # Power words
    power_word_count = sum(1 for word in POWER_WORDS if word in text_upper)
    score += min(25, power_word_count * 10)
    
    # Ellipsis or incomplete
    if "..." in text or text.endswith("?"):
        score += 5
    
    return min(100, score)


def _score_emotion(text: str, analysis: FrameAnalysis) -> float:
    """Score emotional impact"""
    score = 50
    
    # Emotional punctuation
    if "!" in text:
        score += 15
    if text.isupper():
        score += 10
    
    # Face with expression would boost this
    # (In production, use emotion detection on faces)
    if analysis.faces_detected > 0:
        score += 20
    
    # Emotional words
    emotional_words = ["amazing", "shocking", "insane", "incredible", "unbelievable", "secret"]
    text_lower = text.lower()
    for word in emotional_words:
        if word in text_lower:
            score += 10
            break
    
    return min(100, score)


def rank_by_ctr(
    thumbnails: List[Dict],
    analyses: List[FrameAnalysis],
    text: str
) -> List[Dict]:
    """Rank thumbnails by CTR score"""
    scored = []
    
    for i, (thumb, analysis) in enumerate(zip(thumbnails, analyses)):
        score = calculate_ctr_score(analysis, text)
        scored.append({
            "thumbnail": thumb,
            "analysis": analysis.to_dict(),
            "ctr_score": score.to_dict(),
            "rank": 0
        })
    
    # Sort by total score
    scored.sort(key=lambda x: x["ctr_score"]["total"], reverse=True)
    
    # Assign ranks
    for i, item in enumerate(scored):
        item["rank"] = i + 1
    
    return scored
