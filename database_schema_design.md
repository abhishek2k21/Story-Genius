🗄️ Database Schema per Service
Creative AI Shorts / Reels Platform
0️⃣ Global Principles (important)

Each service owns its schema

No cross-service joins

Share only via IDs + APIs

Store decisions, not raw prompts

Media blobs stay in object storage (S3/GCS), DB stores metadata only

1️⃣ API Gateway Service (Minimal)
Purpose

Tracking jobs + requests.

jobs
jobs (
  id UUID PRIMARY KEY,
  status VARCHAR(20),           -- queued, running, completed, failed
  request_payload JSONB,
  created_at TIMESTAMP,
  updated_at TIMESTAMP
)


👉 This is your global job tracker.

2️⃣ Strategy Service (Platform Intelligence)
Purpose

Store platform rules & experiments.

platform_profiles
platform_profiles (
  id UUID PRIMARY KEY,
  platform VARCHAR(30),         -- youtube_shorts, instagram_reels
  ideal_length INT,
  hook_window_seconds FLOAT,
  loop_weight FLOAT,
  priority_metrics JSONB,
  created_at TIMESTAMP
)


Example:

["completion", "replays"]

strategy_runs
strategy_runs (
  id UUID PRIMARY KEY,
  job_id UUID,
  platform VARCHAR(30),
  strategy_output JSONB,
  created_at TIMESTAMP
)


Stores decisions, not logic.

3️⃣ Orchestrator Service (Brain State)
Purpose

Track execution plans & retries.

execution_plans
execution_plans (
  id UUID PRIMARY KEY,
  job_id UUID,
  persona_id VARCHAR(50),
  emotion_curve_id UUID,
  hook_type VARCHAR(50),
  retry_limit INT,
  current_retry INT DEFAULT 0,
  status VARCHAR(20),          -- active, retrying, completed
  created_at TIMESTAMP
)

orchestrator_events
orchestrator_events (
  id UUID PRIMARY KEY,
  job_id UUID,
  event_type VARCHAR(50),      -- retry_triggered, accepted
  metadata JSONB,
  created_at TIMESTAMP
)


This is gold for debugging.

4️⃣ Audience Intelligence Service
Purpose

Normalize audience assumptions.

audience_profiles
audience_profiles (
  id UUID PRIMARY KEY,
  audience_key VARCHAR(50),    -- kids_india, genz_us
  attention_span FLOAT,
  language_mix JSONB,
  visual_energy VARCHAR(20),
  emotion_bias JSONB,
  created_at TIMESTAMP
)


Example:

["fun", "surprise"]

5️⃣ Emotion Service
Purpose

Store reusable emotion curves.

emotion_curves
emotion_curves (
  id UUID PRIMARY KEY,
  name VARCHAR(50),
  timeline JSONB,              -- array of {sec, emotion}
  platform VARCHAR(30),
  created_at TIMESTAMP
)

emotion_curve_runs
emotion_curve_runs (
  id UUID PRIMARY KEY,
  job_id UUID,
  emotion_curve_id UUID,
  created_at TIMESTAMP
)

6️⃣ Persona Service (Brand Consistency)
Purpose

Define and evolve personas.

personas
personas (
  id VARCHAR(50) PRIMARY KEY,
  name VARCHAR(50),
  sentence_length VARCHAR(20),
  energy_level VARCHAR(20),
  vocabulary_level VARCHAR(20),
  voice_profile JSONB,
  created_at TIMESTAMP
)

persona_usage
persona_usage (
  id UUID PRIMARY KEY,
  persona_id VARCHAR(50),
  job_id UUID,
  created_at TIMESTAMP
)


Used later for performance tracking.

7️⃣ Story Service (Micro-Scene Engine)
Purpose

Store structured stories (not text blobs).

stories
stories (
  id UUID PRIMARY KEY,
  job_id UUID,
  total_duration INT,
  created_at TIMESTAMP
)

story_scenes
story_scenes (
  id UUID PRIMARY KEY,
  story_id UUID,
  start_sec INT,
  end_sec INT,
  purpose VARCHAR(30),        -- hook, escalate, twist, loop
  narration_text TEXT,
  visual_prompt TEXT
)


This is one of the most important tables.

8️⃣ Media Generation Services
A️⃣ Script Service
scripts
scripts (
  id UUID PRIMARY KEY,
  story_id UUID,
  full_script TEXT,
  language VARCHAR(10),
  created_at TIMESTAMP
)

B️⃣ Image Service
images
images (
  id UUID PRIMARY KEY,
  scene_id UUID,
  storage_url TEXT,
  style VARCHAR(50),
  created_at TIMESTAMP
)

C️⃣ Video Service
videos
videos (
  id UUID PRIMARY KEY,
  job_id UUID,
  storage_url TEXT,
  duration INT,
  resolution VARCHAR(20),
  created_at TIMESTAMP
)

D️⃣ Audio Service
audio_tracks
audio_tracks (
  id UUID PRIMARY KEY,
  script_id UUID,
  storage_url TEXT,
  voice_id VARCHAR(50),
  created_at TIMESTAMP
)

9️⃣ Critic Service (Performance Intelligence)
Purpose

Score what matters.

critic_scores
critic_scores (
  id UUID PRIMARY KEY,
  job_id UUID,
  platform VARCHAR(30),
  total_score FLOAT,
  hook_score FLOAT,
  pacing_score FLOAT,
  loop_score FLOAT,
  verdict VARCHAR(20),        -- accept, retry
  created_at TIMESTAMP
)

critic_feedback
critic_feedback (
  id UUID PRIMARY KEY,
  critic_score_id UUID,
  feedback JSONB,
  created_at TIMESTAMP
)

🔟 Memory Service (Your Moat)
Purpose

Store winning patterns.

creative_memory
creative_memory (
  id UUID PRIMARY KEY,
  type VARCHAR(30),           -- hook, persona, emotion_curve
  reference_id VARCHAR(100),
  platform VARCHAR(30),
  score FLOAT,
  metadata JSONB,
  reuse_count INT DEFAULT 0,
  created_at TIMESTAMP
)

memory_usage
memory_usage (
  id UUID PRIMARY KEY,
  memory_id UUID,
  job_id UUID,
  used_at TIMESTAMP
)


This enables:

reinforcement

compounding advantage

style dominance

🔁 How This Evolves Over Time
Phase 1 (MVP)

Single DB

Logical service separation

Minimal indexes

Phase 2 (Scale)

Split DBs per service

Add read replicas

Add analytics warehouse

🔑 Final CTO Insight

This schema:

avoids prompt leakage

supports experimentation

enables learning loops

keeps infra sane

scales from 1 channel → 1,000 channels

You’re now designing a real creative platform, not a hack