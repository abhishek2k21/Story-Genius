Week 21 Plan: AI Power & Accuracy (Intelligence Upgrade)
Theme: Make the AI smarter, faster, and more reliable - not just shinier UI

Strategic Shift
Week 18-20 Focus: Creator tools (preview, editing, calendar, frontend)
Week 21 Focus: AI Core Quality - the engine that powers everything
Philosophy:

"A beautiful dashboard showing mediocre videos is still mediocre.
Exceptional AI in a simple interface wins."


Current AI Weaknesses (Based on Weeks 1-17)
ProblemImpactPriorityHook generation feels genericLow retention🔴 CRITICALVisual prompts don't match narrationViewer confusion🔴 CRITICALVoice timing often off-syncUnprofessional🟡 HIGHScene transitions feel abruptPoor flow🟡 HIGHEmotion curve isn't respectedFlat pacing🟠 MEDIUMTrending topic integration weakMisses viral potential🟠 MEDIUM

Week 21: AI Intelligence Upgrade
Day 1 (Monday) - Hook Intelligence v2
Problem: Hooks feel templated ("Did you know...?", "You won't believe...")
Solution: Train on real high-performing hooks
Implementation:
python# app/intelligence/hook_analyzer.py
class HookAnalyzer:
    """Learns from real viral hooks"""
    
    def analyze_viral_hooks(self, platform: str) -> HookPatterns:
        """
        Scrapes/uses dataset of viral shorts hooks
        Returns patterns like:
        - Question complexity (simple vs layered)
        - Emotional trigger (curiosity, shock, fear, joy)
        - Word choice (active verbs, specificity)
        - Length (3-7 words vs 8-12 words)
        """
        pass
    
    def score_hook_originality(self, hook: str) -> float:
        """
        Checks if hook is too similar to:
        - Our previous hooks (avoid repetition)
        - Common templates (avoid generic)
        Returns 0-1 score
        """
        pass
    
    def generate_hook_variants(
        self, 
        topic: str, 
        avoid_patterns: List[str]
    ) -> List[Hook]:
        """
        Generates 10 hooks, ranks by:
        - Originality score
        - Predicted retention (first 2 seconds)
        - Emotion intensity
        Returns top 3
        """
        pass
Database:
sqlCREATE TABLE viral_hooks (
    id UUID PRIMARY KEY,
    hook_text TEXT,
    platform VARCHAR(20),
    views INT,
    retention_2s FLOAT,
    emotional_trigger VARCHAR(50),
    scraped_at TIMESTAMP DEFAULT NOW()
);

CREATE TABLE generated_hooks (
    id UUID PRIMARY KEY,
    job_id UUID REFERENCES jobs(id),
    hook_text TEXT,
    originality_score FLOAT,
    predicted_retention FLOAT,
    selected BOOLEAN DEFAULT FALSE,
    actual_retention FLOAT  -- filled later from analytics
);
Test:
python# Generate hooks for "Why the moon has phases"
hooks = HookAnalyzer().generate_hook_variants(
    topic="moon phases",
    avoid_patterns=["did you know", "you won't believe"]
)

# Should get creative variants like:
# - "The moon is lying to you"
# - "Ancient humans got this wrong for 10,000 years"
# - "NASA's secret about the moon"
Files:

app/intelligence/hook_analyzer.py
app/intelligence/viral_patterns.py (pattern database)
migrations/011_create_viral_hooks.sql
app/tests/test_hook_intelligence.py


Day 2 (Tuesday) - Visual-Narration Coherence
Problem: Imagen generates visuals that don't match what's being said
Solution: Scene-level vision-language alignment
Implementation:
python# app/media/visual_coherence.py
class VisualCoherenceEngine:
    """Ensures visuals match narration precisely"""
    
    def extract_visual_entities(self, narration: str) -> List[Entity]:
        """
        Uses NER (Named Entity Recognition) to extract:
        - Objects (coffee cup, mountain, phone)
        - Actions (running, exploding, glowing)
        - Settings (forest, office, space)
        - Emotions (happy child, angry crowd)
        """
        # Use spacy or Gemini for entity extraction
        pass
    
    def build_coherent_prompt(
        self,
        narration: str,
        visual_style: str,
        scene_emotion: str
    ) -> str:
        """
        Generates Imagen prompt that MUST include:
        1. All mentioned entities from narration
        2. Correct spatial relationships
        3. Emotional tone matching
        
        Example:
        Narration: "The coffee triggered his energy"
        Prompt: "A man's face lighting up with energy as he drinks 
                 steaming coffee, warm morning light, energetic expression,
                 cinematic style"
        """
        entities = self.extract_visual_entities(narration)
        
        # Build structured prompt
        return f"""
        Main subject: {entities.subject}
        Action: {entities.action}
        Objects: {', '.join(entities.objects)}
        Setting: {entities.setting}
        Emotion: {scene_emotion}
        Style: {visual_style}
        Lighting: {self._infer_lighting(scene_emotion)}
        """
    
    def verify_coherence(self, image_url: str, narration: str) -> float:
        """
        Uses Gemini Vision to check if generated image
        actually contains entities mentioned in narration
        Returns coherence score 0-1
        """
        # Use gemini-pro-vision to analyze image
        pass
```

**Process Flow:**
```
Narration → Entity Extraction → Structured Prompt → Image Generation 
                                                      ↓
                                            Coherence Verification
                                                      ↓
                                            If score < 0.7: Regenerate
Test:
pythonnarration = "Einstein writing equations on a chalkboard"
prompt = engine.build_coherent_prompt(narration, "cinematic", "focused")

# Should include: Einstein, chalkboard, equations, writing action
assert "Einstein" in prompt
assert "chalkboard" in prompt
assert "equations" in prompt

# Generate image and verify
image = generate_image(prompt)
coherence = engine.verify_coherence(image, narration)
assert coherence > 0.7
Files:

app/media/visual_coherence.py
app/media/entity_extractor.py
app/tests/test_visual_coherence.py


Day 3 (Wednesday) - Voice Timing Precision
Problem: Voice narration doesn't sync with scene changes
Solution: Phoneme-level timing analysis
Implementation:
python# app/media/voice_timing.py
class VoiceTimingEngine:
    """Ensures perfect voice-to-scene sync"""
    
    def analyze_voice_duration(self, text: str, voice: str) -> float:
        """
        Predicts exact duration BEFORE generating audio
        Uses character count + speech rate model
        """
        # EdgeTTS has predictable speeds per voice
        char_count = len(text)
        words = len(text.split())
        
        # Voice-specific rates (words per minute)
        speech_rates = {
            "en-US-GuyNeural": 160,  # moderate
            "en-IN-NeerjaNeural": 150,  # slightly slower
            "hi-IN-MadhurNeural": 140   # conversational
        }
        
        wpm = speech_rates.get(voice, 150)
        predicted_duration = (words / wpm) * 60
        
        return predicted_duration
    
    def adjust_scene_duration(
        self,
        scenes: List[Scene],
        voice: str
    ) -> List[Scene]:
        """
        Adjusts scene durations to match actual voice length
        Ensures no abrupt cuts mid-sentence
        """
        for scene in scenes:
            predicted = self.analyze_voice_duration(scene.narration, voice)
            
            # Add 0.3s buffer for natural pauses
            scene.duration = predicted + 0.3
            
            # Ensure hook (Scene 1) stays under 2 seconds
            if scene.index == 0 and scene.duration > 2.0:
                scene.narration = self.compress_text(scene.narration, 2.0)
                scene.duration = 2.0
        
        return scenes
    
    def compress_text(self, text: str, max_duration: float) -> str:
        """Uses LLM to shorten text while keeping meaning"""
        # Use Gemini Flash to compress
        pass
    
    def generate_with_markers(self, text: str, voice: str) -> Audio:
        """
        Generates audio with SSML markers for scene transitions
        
        <break time="500ms"/> between scenes for smooth transition
        """
        ssml = f"""
        <speak>
            <voice name="{voice}">
                {text}
                <break time="500ms"/>
            </voice>
        </speak>
        """
        return self.tts_service.generate(ssml)
Database:
sqlALTER TABLE story_scenes ADD COLUMN predicted_duration FLOAT;
ALTER TABLE story_scenes ADD COLUMN actual_duration FLOAT;
ALTER TABLE story_scenes ADD COLUMN timing_accuracy FLOAT;
Test:
python# Test prediction accuracy
text = "This is a test narration for timing accuracy."
predicted = engine.analyze_voice_duration(text, "en-US-GuyNeural")

# Generate actual audio
audio = generate_audio(text, "en-US-GuyNeural")
actual = get_audio_duration(audio)

# Accuracy should be >95%
accuracy = abs(predicted - actual) / actual
assert accuracy < 0.05
Files:

app/media/voice_timing.py
app/tests/test_voice_timing.py


Day 4 (Thursday) - Scene Transition Intelligence
Problem: Scenes feel choppy, no visual flow
Solution: Smart transition selection based on content
Implementation:
python# app/media/transitions.py
class TransitionEngine:
    """Selects appropriate transitions based on scene relationship"""
    
    TRANSITIONS = {
        "cut": {"duration": 0, "use_case": "same location, time jump"},
        "fade": {"duration": 0.5, "use_case": "time passage, mood shift"},
        "dissolve": {"duration": 0.3, "use_case": "related concepts"},
        "slide": {"duration": 0.4, "use_case": "spatial movement"},
        "zoom": {"duration": 0.3, "use_case": "focus shift"}
    }
    
    def select_transition(
        self,
        scene_a: Scene,
        scene_b: Scene
    ) -> Transition:
        """
        Analyzes semantic relationship between scenes
        Returns appropriate transition
        """
        # Extract semantic similarity
        similarity = self.semantic_similarity(
            scene_a.narration,
            scene_b.narration
        )
        
        # Check for time indicators
        has_time_jump = self.detect_time_jump(scene_a, scene_b)
        
        # Check for location change
        location_change = self.detect_location_change(scene_a, scene_b)
        
        # Decision logic
        if has_time_jump:
            return "fade"
        elif location_change:
            return "slide"
        elif similarity > 0.7:
            return "dissolve"
        else:
            return "cut"
    
    def semantic_similarity(self, text_a: str, text_b: str) -> float:
        """Uses sentence embeddings to measure similarity"""
        # Use sentence-transformers or Gemini embeddings
        pass
    
    def detect_time_jump(self, scene_a: Scene, scene_b: Scene) -> bool:
        """Detects temporal phrases like 'later', 'meanwhile', 'then'"""
        time_indicators = ["later", "meanwhile", "next", "then", "after"]
        return any(word in scene_b.narration.lower() for word in time_indicators)
Video Composition Update:
python# app/media/video_service.py (enhanced)
def stitch_scenes(self, scenes: List[Scene]) -> VideoFile:
    """Enhanced stitching with smart transitions"""
    clips = []
    
    for i, scene in enumerate(scenes):
        clip = VideoFileClip(scene.video_path)
        
        # Add transition if not last scene
        if i < len(scenes) - 1:
            transition = TransitionEngine().select_transition(
                scene,
                scenes[i + 1]
            )
            clip = self.apply_transition(clip, transition)
        
        clips.append(clip)
    
    final = concatenate_videoclips(clips, method="compose")
    return final
Files:

app/media/transitions.py
app/tests/test_transitions.py


Day 5 (Friday) - Emotion Curve Enforcement
Problem: Emotion curves defined but not enforced in generation
Solution: Scene-level emotion validation
Implementation:
python# app/intelligence/emotion_enforcer.py
class EmotionEnforcer:
    """Validates that generated scenes match emotion curve"""
    
    def validate_scene_emotion(
        self,
        scene: Scene,
        expected_emotion: str,
        expected_intensity: float
    ) -> EmotionScore:
        """
        Analyzes scene narration for emotional content
        Returns score 0-1 and detected emotion
        """
        # Use Gemini to analyze emotional content
        prompt = f"""
        Analyze this text for emotion:
        "{scene.narration}"
        
        Expected emotion: {expected_emotion}
        Expected intensity: {expected_intensity}/10
        
        Return JSON:
        {{
            "detected_emotion": "curiosity|tension|wonder|joy|fear",
            "intensity": 0-10,
            "matches_expectation": true/false,
            "suggestion": "how to adjust if not matching"
        }}
        """
        
        result = self.llm.generate(prompt)
        return EmotionScore(**result)
    
    def enforce_curve(
        self,
        scenes: List[Scene],
        curve: EmotionCurve
    ) -> List[Scene]:
        """
        Validates each scene against emotion curve
        Regenerates scenes that don't match
        """
        for i, scene in enumerate(scenes):
            expected = curve.get_emotion_at_index(i)
            
            score = self.validate_scene_emotion(
                scene,
                expected.emotion,
                expected.intensity
            )
            
            if not score.matches_expectation:
                # Regenerate with explicit emotion instruction
                scene.narration = self.regenerate_with_emotion(
                    scene.narration,
                    expected.emotion,
                    expected.intensity,
                    suggestion=score.suggestion
                )
        
        return scenes
Integration:
python# Update app/orchestrator/service.py
def generate_story(self, job: Job) -> Story:
    # Existing story generation...
    
    # NEW: Enforce emotion curve
    if job.config.emotion_curve:
        scenes = EmotionEnforcer().enforce_curve(
            story.scenes,
            job.config.emotion_curve
        )
        story.scenes = scenes
    
    return story
Files:

app/intelligence/emotion_enforcer.py
app/tests/test_emotion_enforcement.py


Day 6 (Saturday) - Trending Topic Injection v2
Problem: Trend integration feels forced
Solution: Natural trend weaving
Implementation:
python# app/intelligence/trend_weaver.py
class TrendWeaver:
    """Naturally integrates trending topics into content"""
    
    def fetch_current_trends(self, platform: str, region: str) -> List[Trend]:
        """
        Fetches trending topics from:
        - Google Trends API
        - YouTube trending (via scraping)
        - Twitter trending (if available)
        """
        pass
    
    def find_relevant_trends(
        self,
        topic: str,
        trends: List[Trend]
    ) -> List[Trend]:
        """
        Finds trends semantically related to video topic
        
        Example:
        Topic: "History of coffee"
        Relevant trends: "#morningroutine", "coffee recipes trending"
        Irrelevant trends: "football scores"
        """
        # Use embeddings to find semantic matches
        pass
    
    def weave_trend(
        self,
        narration: str,
        trend: Trend,
        position: str = "hook"  # or "mid" or "end"
    ) -> str:
        """
        Naturally integrates trend into narration
        
        BEFORE: "Coffee has an interesting history"
        AFTER: "While everyone's posting their #morningroutine, 
                let me show you coffee's wild history"
        """
        prompt = f"""
        Original text: "{narration}"
        Trending topic: "{trend.name}"
        Position: {position}
        
        Rewrite to naturally include the trend WITHOUT:
        - Feeling forced
        - Losing original message
        - Being too promotional
        
        Keep it conversational.
        """
        
        return self.llm.generate(prompt)
    
    def should_use_trend(self, topic: str, trend: Trend) -> bool:
        """
        Determines if trend actually fits
        Returns False if trend would feel forced
        """
        # Check semantic alignment
        # Check if trend is rising (not declining)
        # Check if trend matches audience
        pass
Usage:
python# In story generation
trends = TrendWeaver().fetch_current_trends("youtube_shorts", "IN")
relevant = TrendWeaver().find_relevant_trends(job.topic, trends)

if relevant and TrendWeaver().should_use_trend(job.topic, relevant[0]):
    # Weave into hook
    hook.narration = TrendWeaver().weave_trend(
        hook.narration,
        relevant[0],
        position="hook"
    )
Files:

app/intelligence/trend_weaver.py
app/tests/test_trend_weaving.py


Day 7 (Sunday) - AI Quality Dashboard + Week 21 Integration Test
Goal: Measure and verify all AI improvements
Implementation:
python# app/analytics/ai_quality.py
class AIQualityDashboard:
    """Tracks AI performance metrics over time"""
    
    def get_quality_metrics(self, date_range: tuple) -> QualityReport:
        """
        Returns:
        - Hook originality trend (are we getting more creative?)
        - Visual coherence scores (improving?)
        - Voice timing accuracy (getting better?)
        - Transition smoothness ratings
        - Emotion curve adherence
        - Trend integration success rate
        """
        return QualityReport(
            hook_originality=self.avg_hook_originality(date_range),
            visual_coherence=self.avg_visual_coherence(date_range),
            voice_timing_accuracy=self.avg_timing_accuracy(date_range),
            transition_smoothness=self.avg_transition_score(date_range),
            emotion_adherence=self.avg_emotion_score(date_range),
            trend_success_rate=self.trend_success_rate(date_range)
        )
    
    def compare_before_after(self) -> Comparison:
        """
        Compares Week 20 vs Week 21 quality
        Shows improvement (or regression)
        """
        week20 = self.get_quality_metrics(("2026-01-13", "2026-01-19"))
        week21 = self.get_quality_metrics(("2026-01-20", "2026-01-26"))
        
        return Comparison(
            hook_improvement=week21.hook_originality - week20.hook_originality,
            coherence_improvement=week21.visual_coherence - week20.visual_coherence,
            # ... etc
        )
Integration Test:
python# app/tests/test_week21_ai_quality.py
def test_ai_improvements():
    """Test that all AI upgrades work together"""
    
    job = create_test_job(topic="Why stars twinkle")
    
    # 1. Generate with all new features
    result = orchestrator.generate_full_video(job)
    
    # 2. Verify hook intelligence
    hook = result.scenes[0]
    originality = HookAnalyzer().score_hook_originality(hook.narration)
    assert originality > 0.7, "Hook should be original"
    
    # 3. Verify visual coherence
    for scene in result.scenes:
        coherence = VisualCoherenceEngine().verify_coherence(
            scene.image_url,
            scene.narration
        )
        assert coherence > 0.7, f"Scene {scene.index} visual mismatch"
    
    # 4. Verify voice timing
    for scene in result.scenes:
        predicted = scene.predicted_duration
        actual = scene.actual_duration
        assert abs(predicted - actual) / actual < 0.05, "Timing off"
    
    # 5. Verify transitions
    assert result.metadata.transition_count > 0, "No transitions applied"
    
    # 6. Verify emotion curve
    if job.config.emotion_curve:
        for scene in result.scenes:
            assert scene.emotion_validated, "Emotion not enforced"
    
    # 7. Check overall quality improvement
    quality_score = result.critic_score.total_score
    assert quality_score > 0.80, "Quality should be >80% with upgrades"
Frontend Integration:
tsx// src/pages/AIQuality.tsx
export default function AIQuality() {
  const { data: metrics } = useQuery({
    queryKey: ['aiQuality'],
    queryFn: async () => {
      const response = await api.get('/v1/analytics/ai-quality')
      return response.data
    }
  })

  return (
    <div className="p-8">
      <h1 className="text-3xl font-bold mb-8">AI Quality Metrics</h1>
      
      {/* Before/After Comparison */}
      <Card className="p-6 mb-8">
        <h2 className="text-xl font-bold mb-4">Week 21 Improvements</h2>
        <div className="grid grid-cols-3 gap-4">
          <ImprovementCard 
            metric="Hook Originality"
            before={metrics?.week20.hook_originality}
            after={metrics?.week21.hook_originality}
          />
          <ImprovementCard 
            metric="Visual Coherence"
            before={metrics?.week20.visual_coherence}
            after={metrics?.week21.visual_coherence}
          />
          <ImprovementCard 
            metric="Voice Timing"
            before={metrics?.week20.voice_timing_accuracy}
            after={metrics?.week21.voice_timing_accuracy}
          />
        </div>
      </Card>
    </div>
  )
}
```

**Files:**
- `app/analytics/ai_quality.py`
- `app/tests/test_week21_ai_quality.py`
- `frontend/src/pages/AIQuality.tsx`

---

## Week 21 Deliverables

**New Files:**
```
app/
├── intelligence/
│   ├── hook_analyzer.py
│   ├── viral_patterns.py
│   ├── emotion_enforcer.py
│   └── trend_weaver.py
├── media/
│   ├── visual_coherence.py
│   ├── entity_extractor.py
│   ├── voice_timing.py
│   └── transitions.py
├── analytics/
│   └── ai_quality.py
├── tests/
│   ├── test_hook_intelligence.py
│   ├── test_visual_coherence.py
│   ├── test_voice_timing.py
│   ├── test_transitions.py
│   ├── test_emotion_enforcement.py
│   ├── test_trend_weaving.py
│   └── test_week21_ai_quality.py
migrations/
└── 011_create_viral_hooks.sql
frontend/src/pages/
└── AIQuality.tsx
Database Tables:

viral_hooks (for learning)
generated_hooks (for tracking)
Updated story_scenes (timing fields)


Success Metrics
MetricWeek 20 BaselineWeek 21 TargetMeasurementHook Originality~0.60>0.75Originality scoreVisual Coherence~0.65>0.80Entity match %Voice Timing~85%>95%Prediction accuracyTransition SmoothnessN/A>0.70User ratingEmotion Adherence~0.60>0.75Curve match %Overall Quality~0.75>0.85Critic score

Key Insight

"A creator will tolerate a clunky UI if the AI is brilliant.
They'll abandon a beautiful UI if the AI is mediocre."

Week 21 makes the AI worth using, regardless of interface polish.