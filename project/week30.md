# Week 29 Sign-Off

**Status:** ✅ Approved and Complete

Pacing engine is well-implemented. Five presets, seven bump types, quality scoring, and visual instruction generation all properly structured. Retention optimization is now systematic rather than accidental.

---

# Week 30 Plan: Thumbnail Engine and Click-Through Optimization

## Objective
Build thumbnail engine that extracts high-engagement frames from generated videos, applies optimized text overlays, generates platform-specific sizes, and scores thumbnails for predicted click-through rate. After this week, every video has algorithmically optimized thumbnails ready for upload.

## Why This Week
Hook determines if viewers stay. Thumbnail determines if viewers click. A video with perfect content and poor thumbnail gets zero views. Thumbnail is the first impression and the only thing viewers see before deciding to watch. This is not optional polish. This is the entry gate to all views.

---

## Day-by-Day Breakdown

---

### Monday: Frame Analysis Foundation

**Focus:** Build frame extraction and analysis system to identify high-engagement frame candidates.

**What to build:**

**Frame extraction parameters:**

| Parameter | Value | Reasoning |
|-----------|-------|-----------|
| Extraction interval | Every 0.5 seconds | Balance coverage and performance |
| Frame format | PNG | Lossless for analysis |
| Resolution | Full source resolution | Quality preservation |
| Color space | RGB | Standard analysis format |

**Frame quality metrics:**

| Metric | Measurement | Weight |
|--------|-------------|--------|
| Sharpness | Edge detection score | 20% |
| Brightness | Luminance distribution | 15% |
| Contrast | Dynamic range | 15% |
| Color vibrancy | Saturation levels | 15% |
| Face presence | Face detection | 20% |
| Motion blur | Blur detection | 15% |

**Face detection importance:**
- Thumbnails with faces get 38% higher CTR
- Eye contact with camera scores highest
- Emotional expressions score higher than neutral
- Multiple faces can work for specific content

**Frame scoring algorithm:**

1. Extract frame at interval
2. Calculate sharpness score
3. Calculate brightness score
4. Calculate contrast score
5. Calculate color vibrancy score
6. Run face detection
7. Calculate motion blur penalty
8. Compute weighted total score
9. Rank all frames by score
10. Return top N candidates

**Frame candidate output:**

| Field | Type | Purpose |
|-------|------|---------|
| frame_id | string | Unique identifier |
| timestamp | float | Position in video |
| file_path | string | Extracted frame location |
| quality_score | float | Overall quality 0-100 |
| sharpness | float | Sharpness component |
| brightness | float | Brightness component |
| contrast | float | Contrast component |
| vibrancy | float | Color vibrancy component |
| faces_detected | integer | Number of faces |
| face_positions | list | Bounding boxes for faces |
| blur_score | float | Motion blur level |

**Deliverables for Monday:**
- Frame extraction utility
- Quality metric calculators
- Face detection integration
- Frame scoring algorithm
- Candidate ranking system

---

### Tuesday: Thumbnail Text Overlay System

**Focus:** Build text overlay system specifically optimized for thumbnail readability and click appeal.

**What to build:**

**Thumbnail text requirements:**

| Requirement | Reasoning |
|-------------|-----------|
| Maximum 5-7 words | Must read in under 1 second |
| Large font size | Visible at small sizes |
| High contrast | Readable on any background |
| Clear hierarchy | One main message |
| Emotional trigger | Compel click action |

**Text position options for thumbnails:**

| Position | Use Case | Avoid When |
|----------|----------|------------|
| Top center | Strong visual below | Face at top |
| Bottom center | Strong visual above | Platform UI overlap |
| Left third | Face on right | Left-facing subject |
| Right third | Face on left | Right-facing subject |
| Center overlay | Text-focused thumbnail | Detailed visual |

**Text style presets for thumbnails:**

| Preset | Font | Background | Border | Use Case |
|--------|------|------------|--------|----------|
| bold_shadow | Heavy bold | None | Drop shadow | Most content |
| boxed | Bold | Solid color | None | Busy backgrounds |
| outlined | Bold | None | Thick stroke | High contrast needs |
| gradient_box | Bold | Gradient | None | Modern aesthetic |
| minimal | Medium | Semi-transparent | None | Clean look |

**Text generation from content:**

Input sources for thumbnail text:
- Hook from script
- Key phrase from content
- Manually provided text
- Generated curiosity text

**Text optimization rules:**
- Remove filler words
- Capitalize key words
- Add emotional punctuation
- Keep under word limit
- Verify readability at small size

**Text overlay output:**

| Field | Type | Purpose |
|-------|------|---------|
| text | string | Display text |
| position | string | Placement option |
| style_preset | string | Visual style |
| font_size | integer | Calculated size |
| font_color | string | Text color |
| background_color | string | Background if applicable |
| stroke_color | string | Outline color |
| stroke_width | integer | Outline thickness |
| shadow_offset | tuple | Shadow position |
| shadow_color | string | Shadow color |

**Deliverables for Tuesday:**
- Thumbnail text position calculator
- Text style presets
- Text optimization algorithm
- Text from content extractor
- Overlay parameter generator

---

### Wednesday: Thumbnail Composition Engine

**Focus:** Build composition system that combines frame and text into final thumbnail.

**What to build:**

**Composition process:**

1. Load frame candidate
2. Analyze frame for text placement
3. Select optimal text position
4. Calculate text area dimensions
5. Apply text style preset
6. Render text onto frame
7. Apply final adjustments
8. Export thumbnail

**Intelligent text placement:**

Avoid placing text over:
- Detected faces
- High detail areas
- Critical visual elements
- Platform UI zones

Prefer placing text on:
- Low detail areas
- Solid color regions
- Sky or background areas
- Intentional negative space

**Text area analysis:**

For each potential position:
- Calculate average complexity in region
- Check for face overlap
- Measure contrast with planned text color
- Score position suitability

**Composition adjustments:**

| Adjustment | Purpose | When Applied |
|------------|---------|--------------|
| Brightness boost | Make thumbnail pop | Always subtle |
| Saturation boost | Increase vibrancy | If vibrancy low |
| Contrast enhancement | Improve definition | If contrast low |
| Vignette | Focus attention | Optional style |
| Color grading | Mood enhancement | Template-based |

**Composition output:**

| Field | Type | Purpose |
|-------|------|---------|
| thumbnail_id | string | Unique identifier |
| source_frame_id | string | Frame used |
| text_applied | string | Text on thumbnail |
| text_position | string | Where text placed |
| style_preset | string | Style used |
| adjustments_applied | list | Post-processing done |
| output_path | string | Final file location |

**Deliverables for Wednesday:**
- Frame analysis for text placement
- Position scoring algorithm
- Text rendering system
- Image adjustment utilities
- Composition pipeline

---

### Thursday: Multi-Format Export and Platform Optimization

**Focus:** Build export system for platform-specific thumbnail sizes and requirements.

**What to build:**

**Platform thumbnail specifications:**

| Platform | Aspect Ratio | Resolution | Max File Size |
|----------|--------------|------------|---------------|
| YouTube | 16:9 | 1280x720 | 2MB |
| YouTube Shorts | 9:16 | 1080x1920 | 2MB |
| Instagram Reels | 9:16 | 1080x1920 | - |
| Instagram Feed | 1:1 | 1080x1080 | - |
| TikTok | 9:16 | 1080x1920 | - |

**Aspect ratio handling:**

When source frame ratio differs from target:
- Crop to target ratio with smart centering
- Avoid cropping faces
- Preserve text area
- Maintain visual balance

**Smart cropping algorithm:**

1. Identify key elements in frame
2. Calculate optimal crop region
3. Verify faces remain in frame
4. Verify text area remains in frame
5. Apply crop
6. Scale to target resolution

**File optimization:**

| Format | Quality | Use Case |
|--------|---------|----------|
| JPEG | 85-95% | Standard export |
| PNG | Lossless | When transparency needed |
| WebP | 85% | Web optimization |

**File size management:**
- Start at high quality
- Reduce if over platform limit
- Maintain minimum quality threshold
- Report if cannot meet size limit

**Export batch output:**

| Field | Type | Purpose |
|-------|------|---------|
| export_id | string | Batch identifier |
| thumbnail_id | string | Source thumbnail |
| exports | list | All format exports |
| platform | string | Target platform |
| resolution | string | Export resolution |
| file_path | string | Output location |
| file_size | integer | Size in bytes |
| format | string | File format |

**Deliverables for Thursday:**
- Platform specification definitions
- Smart cropping algorithm
- Multi-resolution export
- File size optimization
- Batch export capability

---

### Friday: Click-Through Scoring and Thumbnail Engine Integration

**Focus:** Build CTR prediction scoring and integrate all components into unified engine.

**What to build:**

**CTR prediction factors:**

| Factor | Weight | Measurement |
|--------|--------|-------------|
| Face presence | 25% | Detected faces with emotion |
| Text clarity | 20% | Readability at small size |
| Color contrast | 15% | Visual pop |
| Curiosity element | 15% | Text creates question |
| Emotional trigger | 15% | Expression or text emotion |
| Visual quality | 10% | Sharpness and clarity |

**Face emotion scoring:**

| Emotion | CTR Multiplier |
|---------|----------------|
| Surprise | 1.3x |
| Excitement | 1.25x |
| Curiosity | 1.2x |
| Happiness | 1.15x |
| Neutral | 1.0x |
| Negative emotions | 0.9x |

**Text curiosity scoring:**

| Element | Score Boost |
|---------|-------------|
| Question implied | +15 |
| Number present | +10 |
| Power word present | +10 |
| Controversy implied | +10 |
| Secret implied | +10 |

**Power words for thumbnails:**
- Secret, Hidden, Truth, Revealed
- Shocking, Insane, Unbelievable
- Easy, Simple, Quick, Fast
- Free, New, Proven, Best

**Thumbnail engine interface:**

**Inputs:**

| Input | Required | Description |
|-------|----------|-------------|
| video_artifact_id | Yes | Source video reference |
| script_artifact_id | No | Script for text extraction |
| text_override | No | Custom thumbnail text |
| style_preset | No | Visual style preference |
| platforms | No | Target platforms for export |
| candidate_count | No | How many options to generate |

**Outputs:**

| Output | Description |
|--------|-------------|
| thumbnail_id | Generated thumbnail identifier |
| candidates | All thumbnail options with scores |
| recommended | Highest scoring option |
| exports | Platform-specific files |
| ctr_scores | Predicted CTR for each candidate |

**Engine execution flow:**

1. Validate inputs
2. Extract frames from video
3. Score all frames
4. Select top N candidates
5. Generate text from script or use override
6. For each candidate frame:
   - Analyze for text placement
   - Compose with text overlay
   - Apply adjustments
   - Calculate CTR score
7. Rank by CTR score
8. Export recommended for all platforms
9. Return all candidates with scores

**Deliverables for Friday:**
- CTR scoring algorithm
- Emotion detection integration
- Text curiosity scoring
- Complete thumbnail engine
- Engine registration

---

### Saturday: API Endpoints and Testing

**Focus:** Expose thumbnail capabilities via API and comprehensive testing.

**What to build:**

**API endpoints:**

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/v1/thumbnails/generate` | POST | Generate thumbnails for video |
| `/v1/thumbnails/candidates` | POST | Get frame candidates only |
| `/v1/thumbnails/{id}` | GET | Get thumbnail details |
| `/v1/thumbnails/{id}/exports` | GET | Get all exports |
| `/v1/thumbnails/{id}/export/{platform}` | GET | Get specific platform export |
| `/v1/thumbnails/styles` | GET | List style presets |
| `/v1/thumbnails/platforms` | GET | List platform specifications |
| `/v1/thumbnails/score` | POST | Score existing thumbnail |
| `/v1/thumbnails/{id}/regenerate` | POST | Regenerate with new options |
| `/v1/thumbnails/text/optimize` | POST | Optimize text for thumbnail |

**Request structure for generation:**

| Field | Required | Description |
|-------|----------|-------------|
| video_artifact_id | Yes | Source video reference |
| script_artifact_id | No | Script for text extraction |
| text | No | Custom thumbnail text |
| style_preset | No | Visual style |
| platforms | No | Target platforms |
| candidate_count | No | Number of options |
| auto_select | No | Auto-export best option |

**Response structure:**

| Field | Description |
|-------|-------------|
| thumbnail_id | Generated identifier |
| candidate_count | Number of options created |
| recommended_index | Best option index |
| candidates | All options with details |
| exports | Platform exports if auto_select |
| processing_time | Generation duration |

**Testing requirements:**

| Test Category | Coverage |
|---------------|----------|
| Frame extraction | Various video lengths and formats |
| Quality scoring | Metric accuracy validation |
| Face detection | Various face counts and positions |
| Text placement | All position options |
| Style presets | Each preset rendering |
| Platform exports | All platform specifications |
| CTR scoring | Score consistency and accuracy |
| Edge cases | No faces, solid frames, very short videos |
| Integration | Full pipeline with real videos |
| Performance | Processing time benchmarks |

**Validation tests:**
- Frames extract at correct intervals
- Quality scores are consistent
- Text remains readable at small sizes
- Exports meet platform specifications
- File sizes are within limits
- CTR scores are reasonable

**Deliverables for Saturday:**
- All API endpoints implemented
- Request and response validation
- Comprehensive test suite
- Style preset configuration
- Platform specification files
- Documentation and examples

---

## Database Concepts Needed

**Thumbnail artifact table:**
- Thumbnail identifier
- Video artifact reference
- Script artifact reference
- Text used
- Style preset
- Created timestamp
- Recommended candidate index

**Thumbnail candidate table:**
- Candidate identifier
- Thumbnail artifact reference
- Frame timestamp
- Frame file path
- Quality score
- Quality score breakdown
- Face count
- Face positions
- CTR score
- CTR score breakdown
- Composed file path

**Thumbnail export table:**
- Export identifier
- Candidate reference
- Platform
- Resolution
- Aspect ratio
- File format
- File path
- File size
- Created timestamp

**Thumbnail style preset table:**
- Preset identifier
- Preset name
- Style configuration
- Is system preset
- Usage count

---

## Files To Create

| File | Purpose |
|------|---------|
| `app/engines/thumbnail/engine.py` | Main thumbnail engine |
| `app/engines/thumbnail/extraction.py` | Frame extraction |
| `app/engines/thumbnail/analysis.py` | Frame quality analysis |
| `app/engines/thumbnail/face_detection.py` | Face detection wrapper |
| `app/engines/thumbnail/text_overlay.py` | Thumbnail text system |
| `app/engines/thumbnail/composition.py` | Frame and text composition |
| `app/engines/thumbnail/export.py` | Multi-platform export |
| `app/engines/thumbnail/scoring.py` | CTR prediction scoring |
| `app/engines/thumbnail/presets.py` | Style preset definitions |
| `app/api/thumbnail_routes.py` | API endpoints |
| `tests/test_thumbnail.py` | Comprehensive tests |

---

## Success Criteria for Week 30

Frame extraction produces quality candidates at regular intervals. Quality scoring accurately identifies visually appealing frames. Face detection correctly identifies and locates faces.

Text overlay system produces readable text at thumbnail sizes. Smart positioning avoids faces and busy areas. Style presets produce consistent visual results.

Multi-platform export meets all specification requirements. Smart cropping preserves important elements. File size optimization stays within limits.

CTR scoring produces meaningful predictions. Higher-scored thumbnails are visually more compelling. Scoring is consistent across similar content.

API endpoints expose all thumbnail capabilities. Tests cover all components and edge cases.

Every generated video has optimized thumbnails ready for all target platforms.

---

## Integration Points

**With Video Engine:**
Thumbnail engine receives completed video for frame extraction.

**With Script Engine (Week 27):**
Hook text can be used for thumbnail text generation.

**With Template System (Week 25):**
Templates can specify thumbnail style preferences.

**With Batch System (Week 24):**
Batch items can share thumbnail style for series consistency.

**With Format System (Week 20):**
Platform specifications inform export requirements.

---

## What This Enables

After Week 30, Story-Genius produces complete content packages. Video plus optimized thumbnail for every platform. Creators upload and post immediately without additional thumbnail creation work.

CTR scoring helps creators understand which visual approaches work. Over time, thumbnail preferences can be learned from performance data.

The system now handles the complete content creation pipeline from script to upload-ready assets.

