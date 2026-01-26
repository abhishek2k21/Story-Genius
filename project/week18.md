# CTO Analysis & Week 18 Plan

## Current State Assessment

**What You Have Built (Weeks 1-17):**
- ✅ Solid content generation pipeline (story → media → video)
- ✅ Intelligence layer (Path 1 thinking, personas, emotion curves)
- ✅ Agency workflow (multi-client, reporting, billing)
- ✅ Adult-first contract system with tone/language control

**What's Missing for Real Creators:**
- ❌ **No visual preview** - creators can't see before generating
- ❌ **No editing** - can't tweak script/visuals after generation
- ❌ **No brand consistency** - each video feels different
- ❌ **No content calendar** - batch planning is manual
- ❌ **No performance tracking** - can't see what works
- ❌ **Frontend UI** - everything is API/scripts

---

## Week 18 Plan: Creator Reality Bridge

**Theme:** Bridge the gap between "generates videos" and "creators actually use this"

### Day 1 (Monday) - Video Preview System
**What:** Generate lightweight preview before full render
**Why:** Creators need to see script + storyboard before committing $0.01 and 20 seconds

**Implementation:**
```python
# app/preview/service.py
class PreviewService:
    def generate_preview(self, config: Contract) -> Preview:
        """
        Returns:
        - Script text (3-5 scenes)
        - Scene descriptions (no actual images)
        - Estimated duration
        - Estimated cost
        - Hook score prediction
        """
        # Use Path 1 to score idea FIRST
        # If score < 70%, warn user
        # Generate script using contract
        # Return preview (no media generation yet)
```

**Files to create:**
- `app/preview/service.py`
- `app/preview/models.py` (Preview, ScenePreview)
- `app/tests/test_preview.py`

**Test:** Same idea → 3 different configs → get 3 different previews in <5 seconds

---

### Day 2 (Tuesday) - Script Editor
**What:** Allow manual edits to generated script before media generation
**Why:** No creator trusts 100% AI output - they want control

**Implementation:**
```python
# app/editor/script_editor.py
class ScriptEditor:
    def edit_scene(self, job_id: str, scene_idx: int, new_text: str):
        """Update scene narration, re-validate duration"""
        
    def swap_scenes(self, job_id: str, scene_a: int, scene_b: int):
        """Reorder scenes"""
        
    def regenerate_scene(self, job_id: str, scene_idx: int, prompt: str):
        """Regenerate just one scene with custom prompt"""
```

**Database changes:**
```sql
ALTER TABLE story_scenes ADD COLUMN edited_by_user BOOLEAN DEFAULT FALSE;
ALTER TABLE story_scenes ADD COLUMN original_narration TEXT;
ALTER TABLE story_scenes ADD COLUMN edit_timestamp TIMESTAMP;
```

**Files:**
- `app/editor/script_editor.py`
- `migrations/007_add_edit_tracking.sql`
- `app/tests/test_editor.py`

---

### Day 3 (Wednesday) - Brand Kit System
**What:** Save creator's visual style, voice, intro/outro templates
**Why:** Every creator wants their videos to look/sound consistent

**Implementation:**
```python
# app/brand/brand_kit.py
@dataclass
class BrandKit:
    user_id: str
    visual_style: str  # "neon_genz", "minimal_facts"
    voice_preference: str  # "en-IN-NeerjaNeural"
    color_palette: List[str]  # ["#FF6B6B", "#4ECDC4"]
    intro_template: Optional[str]  # "Hey everyone, it's [CHANNEL]"
    outro_template: Optional[str]  # "Drop a like if you learned something!"
    logo_url: Optional[str]
    background_music: Optional[str]

class BrandKitService:
    def create_kit(self, user_id: str, preferences: dict) -> BrandKit
    def apply_to_job(self, job_id: str, brand_kit_id: str)
    def list_kits(self, user_id: str) -> List[BrandKit]
```

**Database:**
```sql
CREATE TABLE brand_kits (
    id UUID PRIMARY KEY,
    user_id UUID REFERENCES users(id),
    name VARCHAR(100),
    visual_style VARCHAR(50),
    voice_preference VARCHAR(50),
    color_palette JSONB,
    intro_template TEXT,
    outro_template TEXT,
    logo_url TEXT,
    created_at TIMESTAMP DEFAULT NOW()
);
```

**Files:**
- `app/brand/brand_kit.py`
- `app/brand/service.py`
- `migrations/008_create_brand_kits.sql`

---

### Day 4 (Thursday) - Content Calendar
**What:** Plan 7-30 days of content in advance
**Why:** Creators think in batches, not single videos

**Implementation:**
```python
# app/calendar/service.py
class ContentCalendar:
    def create_plan(
        self,
        user_id: str,
        start_date: date,
        end_date: date,
        frequency: int,  # videos per week
        themes: List[str]  # ["space facts", "history mysteries"]
    ) -> CalendarPlan
    
    def schedule_generation(
        self,
        plan_id: str,
        auto_publish: bool = False
    )
```

**Database:**
```sql
CREATE TABLE content_calendar (
    id UUID PRIMARY KEY,
    user_id UUID,
    plan_name VARCHAR(100),
    start_date DATE,
    end_date DATE,
    frequency INT,
    themes JSONB,
    status VARCHAR(20)  -- draft/scheduled/active
);

CREATE TABLE calendar_slots (
    id UUID PRIMARY KEY,
    calendar_id UUID REFERENCES content_calendar(id),
    slot_date DATE,
    slot_time TIME,
    theme VARCHAR(100),
    job_id UUID,  -- NULL until generated
    status VARCHAR(20)  -- pending/generated/published
);
```

**Files:**
- `app/calendar/service.py`
- `app/calendar/models.py`
- `migrations/009_create_calendar.sql`

---

### Day 5 (Friday) - Performance Dashboard
**What:** Show which videos performed best and why
**Why:** Creators optimize based on data, not guesses

**Implementation:**
```python
# app/analytics/performance.py
class PerformanceAnalytics:
    def get_top_performers(
        self,
        user_id: str,
        metric: str = "views",  # views/retention/engagement
        limit: int = 10
    ) -> List[VideoPerformance]
    
    def get_insights(self, user_id: str) -> dict:
        """
        Returns:
        - Best performing hook types
        - Best performing visual styles
        - Best performing durations
        - Best performing topics
        """
```

**Database:**
```sql
CREATE TABLE video_performance (
    id UUID PRIMARY KEY,
    job_id UUID REFERENCES jobs(id),
    platform VARCHAR(20),
    views INT DEFAULT 0,
    watch_time_seconds INT DEFAULT 0,
    avg_retention_percent FLOAT,
    likes INT DEFAULT 0,
    comments INT DEFAULT 0,
    shares INT DEFAULT 0,
    updated_at TIMESTAMP DEFAULT NOW()
);
```

**Files:**
- `app/analytics/performance.py`
- `migrations/010_create_performance.sql`

---

### Day 6 (Saturday) - API Documentation
**What:** Clean REST API docs with examples
**Why:** Developers/agencies need clear integration paths

**Implementation:**
```python
# Update app/api/main.py with OpenAPI metadata
app = FastAPI(
    title="Story Genius API",
    description="AI-powered shorts & reels generator",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# Add response models to all endpoints
@app.post("/v1/preview", response_model=PreviewResponse)
@app.post("/v1/generate", response_model=GenerationResponse)
@app.get("/v1/jobs/{job_id}", response_model=JobStatus)
```

**Create:**
- `docs/api_guide.md` - Quick start guide
- `docs/examples/` - Code examples in Python/JS/curl
- Postman collection export

---

### Day 7 (Sunday) - Week 18 Integration Test
**What:** End-to-end test of all new features
**Why:** Verify everything works together

**Test Flow:**
```python
# app/tests/test_week18_integration.py
def test_creator_workflow():
    # 1. Create brand kit
    brand = create_brand_kit(user_id, {...})
    
    # 2. Generate preview
    preview = generate_preview(idea, brand_kit_id=brand.id)
    assert preview.estimated_cost < 0.02
    
    # 3. Edit script
    edit_scene(preview.job_id, scene_idx=1, new_text="Better hook")
    
    # 4. Generate full video
    video = generate_video(preview.job_id)
    assert video.status == "completed"
    
    # 5. Create content calendar
    calendar = create_calendar(
        user_id=user_id,
        start_date=today,
        end_date=today + 7days,
        frequency=2,
        brand_kit_id=brand.id
    )
    assert len(calendar.slots) == 2
```

---

## Success Metrics for Week 18

| Metric | Target |
|--------|--------|
| Preview generation | <5 seconds |
| Script edits don't break video | 100% |
| Brand kit applied consistently | Visual diff test passes |
| Calendar creates correct slots | Math checks out |
| Performance data ingests | No errors |
| API docs complete | All endpoints documented |

---

## Files Summary

**New Files (7 days):**
- `app/preview/service.py`, `models.py`
- `app/editor/script_editor.py`
- `app/brand/brand_kit.py`, `service.py`
- `app/calendar/service.py`, `models.py`
- `app/analytics/performance.py`
- `migrations/007-010_*.sql` (4 migrations)
- `app/tests/test_week18_integration.py`
- `docs/api_guide.md`

**Database Tables Added:**
- `brand_kits`
- `content_calendar`
- `calendar_slots`
- `video_performance`

---

## Why This Week Matters

**Before Week 18:** You have a content generator
**After Week 18:** You have a **creator tool**

The difference:
- Creators can **preview** before spending money
- Creators can **edit** AI output (trust++)
- Creators can **stay consistent** (brand kits)
- Creators can **plan ahead** (calendar)
- Creators can **learn** what works (analytics)

---

## Next Steps After Week 18

Once you complete this week, you'll be ready for:
- **Week 19-20:** Simple web UI (React dashboard)
- **Week 21-22:** Upload your own voice/logo
- **Week 23-24:** Auto-publish to YouTube/TikTok
- **Week 25-30:** Monetization + referrals

But **Week 18 is the bridge** from "works" to "usable".

---

**Start Day 1 Monday. Ship Day 7 Sunday. No exceptions.**