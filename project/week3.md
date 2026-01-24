🗓️ WEEK 3 EXECUTION PLAN
Theme: Growth, Visual Identity & Platform Readiness
🎯 Week 3 North Star

By end of Week 3:

The system produces Shorts that are visually recognizable, metadata-optimized, platform-aware, and ready to win distribution.

Week 3 is not about better stories
It’s about getting more reach per story.

WEEK 3 PILLARS
Pillar	Why it matters
Visual Style Engine	Brand recognition
Metadata Intelligence	Click + discoverability
Platform Profiles	Algorithm alignment
Trend Injection	Relevance & velocity
Metrics Readiness	Feedback loop setup
🟢 DAY 15 — Visual Style Engine (Brand Identity)
🎯 Objective

Make outputs instantly recognizable, not generic AI visuals.

What to Build
1️⃣ Visual Style Presets

Create:

app/intelligence/visual_styles.py


Examples:

bright_kids_cartoon

cinematic_dark

minimal_facts

mythological_epic

Each style defines:

color palette

lighting

camera distance

composition rules

2️⃣ Persona → Visual Style Binding

Example:

Curious Kid → bright_kids_cartoon
Storyteller → cinematic_dark

3️⃣ Enforce style in image prompts

Every scene prompt must include:

style

color

framing

✅ Success Criteria

✔ Thumbnails feel consistent
✔ Visuals feel “channel-like”
✔ You can identify persona just by visuals

🟢 DAY 16 — Metadata Optimization Engine
🎯 Objective

Increase clicks and discoverability, not just watch time.

What to Build
1️⃣ Title Generator

Generate 5 title variants:

curiosity-driven

question-based

shock-based

emoji-light

emoji-heavy

2️⃣ Description Generator

Include:

hook restated

keyword-rich sentence

CTA (watch till end / follow)

3️⃣ Tag Generator

Platform-aware keywords

Persona-aware tone

Create:

app/strategy/metadata_engine.py

✅ Success Criteria

✔ Titles feel YouTube-native
✔ Descriptions aren’t generic
✔ Metadata varies per persona

🟢 DAY 17 — Platform Profiles (YouTube Shorts First)
🎯 Objective

Stop treating all platforms the same.

What to Build
1️⃣ Platform Profile Definitions

Create:

app/strategy/platform_profiles.py


For YouTube Shorts:

Ideal length: 27–33s

Hook window: 1.5–2s

Loop importance: HIGH

Title importance: MEDIUM

2️⃣ Platform-aware decisions

Affect:

duration trimming

hook aggressiveness

ending style

title tone

✅ Success Criteria

✔ Shorts feel YouTube-optimized
✔ Less wasted frames
✔ Better endings

🟢 DAY 18 — Trend Injection System (Lightweight)
🎯 Objective

Ride trends without becoming a trend slave.

What to Build
1️⃣ Trend Input Interface

Manual for now:

{
  "trend": "Talking toys",
  "tone": "curious",
  "expiry_days": 3
}

2️⃣ Trend-aware Hook Mutation

Inject trend into:

hook wording

visual reference

title

✅ Success Criteria

✔ Same engine adapts to trends
✔ No hard-coding
✔ Trend logic is optional

🟢 DAY 19 — Retention Curve Approximation
🎯 Objective

Approximate how the algorithm will judge the video.

What to Build
1️⃣ Retention Estimator (LLM-based)

Estimate:

drop at 2s

mid-video sag

loop replay likelihood

2️⃣ Add score to Critic

New metric:

"estimated_retention": 0.78

✅ Success Criteria

✔ Scores correlate with intuition
✔ Bad pacing flagged early

🟢 DAY 20 — Batch Scale + Cost Discipline
🎯 Objective

Prove this can scale economically.

What to Do

Run batch of 20 Shorts

Track:

avg generation time

cost per short

retries per batch

Enforce Limits

Max retries = 2

Max duration = 35s

Lower preview resolution

✅ Success Criteria

✔ Batch stable
✔ Costs predictable
✔ No runaway retries

🟢 DAY 21 — Freeze + Week 3 Report
🎯 Objective

Stabilize and document.

Tasks

Lock Week-3 features

Clean up interfaces

Prepare demo batch

Write Week-3 report

📄 WEEK 3 FINAL REPORT (EXPECTED FORMAT)

You should end Week 3 with something like this 👇

Week 3 Progress Report
Status: ✅ WEEK 3 COMPLETE
Major Upgrades

Visual Style Engine with 4 brand-level styles

Metadata Optimization (titles, descriptions, tags)

YouTube Shorts platform profile

Trend injection (optional, safe)

Retention estimation scoring

Measurable Impact
Metric	Week 2	Week 3
Visual Consistency	Medium	High
Metadata Quality	Basic	Optimized
Platform Readiness	Partial	Strong
Estimated Retention	~0.82	0.88+
Key Insight

“The system now optimizes not just what we create, but how it travels through the algorithm.”

🚀 End of Week 3 State (Very Important)

By end of Week 3, you will have:

✅ Brand-level visuals
✅ Click-optimized metadata
✅ Platform-aware logic
✅ Trend adaptability
✅ Scale-ready batches

At this point, you are ready for:

real channel launches

agency pilots

monetization

investor demos