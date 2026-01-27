"""
Frame Analysis
Quality scoring and face detection for thumbnail candidates.
"""
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass
import math


@dataclass
class FaceDetection:
    """Detected face in frame"""
    x: int
    y: int
    width: int
    height: int
    confidence: float = 0.9
    
    def to_dict(self) -> Dict:
        return {
            "position": {"x": self.x, "y": self.y},
            "size": {"w": self.width, "h": self.height},
            "confidence": round(self.confidence, 2)
        }


@dataclass
class FrameAnalysis:
    """Complete frame quality analysis"""
    frame_id: str
    quality_score: float  # 0-100
    sharpness: float
    brightness: float
    contrast: float
    vibrancy: float
    blur_score: float
    faces_detected: int
    face_positions: List[FaceDetection]
    
    def to_dict(self) -> Dict:
        return {
            "frame_id": self.frame_id,
            "quality_score": round(self.quality_score, 2),
            "metrics": {
                "sharpness": round(self.sharpness, 2),
                "brightness": round(self.brightness, 2),
                "contrast": round(self.contrast, 2),
                "vibrancy": round(self.vibrancy, 2),
                "blur": round(self.blur_score, 2)
            },
            "faces": {
                "count": self.faces_detected,
                "positions": [f.to_dict() for f in self.face_positions]
            }
        }


# Metric weights for quality scoring
QUALITY_WEIGHTS = {
    "sharpness": 0.20,
    "brightness": 0.15,
    "contrast": 0.15,
    "vibrancy": 0.15,
    "face_presence": 0.20,
    "blur_penalty": 0.15
}


def analyze_frame(frame_path: str, frame_id: str) -> FrameAnalysis:
    """Analyze frame for thumbnail quality"""
    try:
        from PIL import Image
        import numpy as np
        
        img = Image.open(frame_path).convert('RGB')
        pixels = np.array(img)
        
        # Calculate metrics
        sharpness = _calculate_sharpness(pixels)
        brightness = _calculate_brightness(pixels)
        contrast = _calculate_contrast(pixels)
        vibrancy = _calculate_vibrancy(pixels)
        blur_score = _calculate_blur(pixels)
        
        # Detect faces (simplified - in production use face_recognition library)
        faces = _detect_faces_simple(pixels)
        
        # Calculate overall quality score
        face_score = min(100, len(faces) * 50) if faces else 0
        
        quality_score = (
            sharpness * QUALITY_WEIGHTS["sharpness"] +
            brightness * QUALITY_WEIGHTS["brightness"] +
            contrast * QUALITY_WEIGHTS["contrast"] +
            vibrancy * QUALITY_WEIGHTS["vibrancy"] +
            face_score * QUALITY_WEIGHTS["face_presence"] +
            (100 - blur_score) * QUALITY_WEIGHTS["blur_penalty"]
        )
        
        return FrameAnalysis(
            frame_id=frame_id,
            quality_score=quality_score,
            sharpness=sharpness,
            brightness=brightness,
            contrast=contrast,
            vibrancy=vibrancy,
            blur_score=blur_score,
            faces_detected=len(faces),
            face_positions=faces
        )
        
    except ImportError:
        # Return mock analysis without PIL
        return _mock_analysis(frame_id)


def _calculate_sharpness(pixels) -> float:
    """Calculate sharpness using Laplacian variance"""
    try:
        import numpy as np
        gray = np.mean(pixels, axis=2)
        
        # Laplacian kernel approximation
        lap = np.abs(np.diff(np.diff(gray, axis=0), axis=0)) + \
              np.abs(np.diff(np.diff(gray, axis=1), axis=1))
        
        variance = np.var(lap)
        # Normalize to 0-100
        return min(100, variance / 10)
    except:
        return 70


def _calculate_brightness(pixels) -> float:
    """Calculate average brightness"""
    try:
        import numpy as np
        luminance = np.mean(pixels)
        # Optimal brightness around 127
        brightness_score = 100 - abs(127 - luminance) * 0.7
        return max(0, min(100, brightness_score))
    except:
        return 60


def _calculate_contrast(pixels) -> float:
    """Calculate contrast (dynamic range)"""
    try:
        import numpy as np
        std = np.std(pixels)
        # Normalize to 0-100
        return min(100, std * 1.5)
    except:
        return 65


def _calculate_vibrancy(pixels) -> float:
    """Calculate color saturation/vibrancy"""
    try:
        import numpy as np
        # Convert to HSV-like saturation
        r, g, b = pixels[:,:,0], pixels[:,:,1], pixels[:,:,2]
        max_c = np.maximum(np.maximum(r, g), b)
        min_c = np.minimum(np.minimum(r, g), b)
        diff = max_c - min_c
        
        # Avoid division by zero
        saturation = np.where(max_c > 0, diff / (max_c + 1), 0)
        avg_saturation = np.mean(saturation)
        
        return min(100, avg_saturation * 200)
    except:
        return 55


def _calculate_blur(pixels) -> float:
    """Calculate motion blur level (lower is better)"""
    try:
        import numpy as np
        gray = np.mean(pixels, axis=2)
        
        # Simple edge detection
        edges_h = np.abs(np.diff(gray, axis=1))
        edges_v = np.abs(np.diff(gray, axis=0))
        
        edge_strength = np.mean(edges_h) + np.mean(edges_v)
        # Lower blur = higher edge strength
        blur = max(0, 100 - edge_strength * 2)
        return blur
    except:
        return 20


def _detect_faces_simple(pixels) -> List[FaceDetection]:
    """Simple face detection placeholder"""
    # In production, use face_recognition or OpenCV cascade
    # For now, return empty or mock based on image characteristics
    try:
        import numpy as np
        # Check for skin-tone colors as proxy for face presence
        r, g, b = pixels[:,:,0], pixels[:,:,1], pixels[:,:,2]
        
        # Skin tone detection (simplified)
        skin_mask = (r > 95) & (g > 40) & (b > 20) & \
                   (r > g) & (r > b) & \
                   (np.abs(r.astype(int) - g.astype(int)) > 15)
        
        skin_ratio = np.sum(skin_mask) / skin_mask.size
        
        if skin_ratio > 0.05:
            # Likely has a face, return mock position
            h, w = pixels.shape[:2]
            return [FaceDetection(
                x=w // 3,
                y=h // 4,
                width=w // 3,
                height=h // 2,
                confidence=0.7
            )]
    except:
        pass
    
    return []


def _mock_analysis(frame_id: str) -> FrameAnalysis:
    """Generate mock analysis for testing"""
    return FrameAnalysis(
        frame_id=frame_id,
        quality_score=72.5,
        sharpness=75,
        brightness=68,
        contrast=70,
        vibrancy=65,
        blur_score=15,
        faces_detected=0,
        face_positions=[]
    )


def rank_frames(analyses: List[FrameAnalysis], top_n: int = 5) -> List[FrameAnalysis]:
    """Rank frames by quality score and return top N"""
    sorted_analyses = sorted(analyses, key=lambda a: a.quality_score, reverse=True)
    return sorted_analyses[:top_n]
