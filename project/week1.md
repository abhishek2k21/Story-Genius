Perfect — since you’ve **already shared the project and codebase earlier**, I’ll design **Week 1 tasks as a CTO execution plan that builds *on top of what you already have***, not a greenfield fantasy.

This is **hands-on, repo-level, day-by-day**.
If you follow this, by end of Week 1 you’ll feel: *“yes, this is becoming a real product.”*

---

# 🗓️ WEEK 1 EXECUTION PLAN

## Goal: Convert existing project → Shorts-ready production foundation

### 🎯 Week 1 North Star

By end of Week 1:

> **One API call → one automated Shorts job → stored media artifacts → trackable job state**

No UI. No perfection. Just **real execution**.

---

## DAY 1 — Repo Cleanup + Architectural Alignment

### Objective

Turn your existing project into a **modular monolith** aligned with the new HLD.

### Tasks

#### 1️⃣ Create clear top-level structure

Refactor (don’t rewrite) into something like:

```
/app
  /api              # FastAPI routes
  /orchestrator     # job control logic
  /strategy         # shorts logic (stub)
  /intelligence     # audience/emotion/persona
  /story            # your existing StoryGenius
  /media            # image/video/audio adapters
  /critic           # stub for now
  /memory           # stub for now
  /core             # config, logging, db
```

👉 Your **existing engines and adapters go into `/story` and `/media`**.

Do NOT touch generation logic yet.

---

#### 2️⃣ Introduce `Job` as a first-class concept

Add a simple job model (even if DB comes Day 2).

```python
Job:
  id
  status (queued, running, done, failed)
  created_at
```

Everything must reference `job_id`.

---

#### 3️⃣ Freeze feature creep

Make a rule:

> ❌ No new creative features this week
> ✅ Only plumbing, contracts, execution

---

### ✅ Day 1 success check

* Repo feels clean
* You know *where* each responsibility lives
* No broken imports

---

## DAY 2 — FastAPI Gateway + Job Lifecycle

### Objective

Expose **one real API** and manage job state.

---

### Tasks

#### 1️⃣ Add FastAPI entrypoint

If not already present:

```python
POST /v1/shorts/generate
```

Payload (keep minimal):

```json
{
  "platform": "youtube_shorts",
  "audience": "kids_india",
  "duration": 30
}
```

Response:

```json
{
  "job_id": "...",
  "status": "queued"
}
```

---

#### 2️⃣ Setup PostgreSQL (local)

* Cloud SQL later
* Local Postgres now

Create `jobs` table.

---

#### 3️⃣ Persist job lifecycle

Update status transitions:

```
queued → running → completed / failed
```

No async yet — sync is OK for now.

---

### ✅ Day 2 success check

* You can hit the API
* Job is created in DB
* Status updates correctly

---

## DAY 3 — Wire Existing StoryGenius into Orchestrator

### Objective

Make **your existing story engine run through the orchestrator**.

---

### Tasks

#### 1️⃣ Create Orchestrator service

Minimal logic:

```text
start_job(job_id)
  → call StoryGenius
  → save story output
```

---

#### 2️⃣ Adapt StoryGenius input/output

Do NOT rewrite logic.

Just wrap output as:

```json
{
  "scenes": [
    {
      "start_sec": 0,
      "end_sec": 2,
      "purpose": "hook",
      "text": "...",
      "visual_prompt": "..."
    }
  ]
}
```

If current output is different → adapt, don’t fight it.

---

#### 3️⃣ Store story in DB

Create:

* `stories`
* `story_scenes`

---

### ✅ Day 3 success check

* One API call → story scenes stored
* Scenes are time-bounded
* You can print the timeline and it makes sense

---

## DAY 4 — Media Generation (Reuse What You Have)

### Objective

Generate **real media files**, even if ugly.

---

### Tasks

#### 1️⃣ Plug existing image + audio logic

Reuse:

* your image generation
* your TTS pipeline

Store outputs in **GCS or local FS**.

---

#### 2️⃣ Simple video stitching

Use FFmpeg:

* images as slides
* audio overlay
* 9:16 canvas

NO animations yet.

---

#### 3️⃣ Store media metadata

Create:

* `images`
* `audio_tracks`
* `videos`

---

### ✅ Day 4 success check

* You can play the generated video
* It’s vertical
* Audio is synced
* Stored via job_id

---

## DAY 5 — Shorts-Specific Rules (Light Touch)

### Objective

Make it **feel like a Short**, not a generic video.

---

### Tasks

#### 1️⃣ Enforce hook rule

* Scene 1 must be ≤ 2 sec
* If not → trim or regenerate

---

#### 2️⃣ Enforce loop ending

* Last scene must:

  * ask a question OR
  * cut mid-action

Hard-code this for now.

---

#### 3️⃣ Duration enforcement

Total duration = 25–35 sec.

Trim or pad.

---

### ✅ Day 5 success check

* Video starts fast
* Ends abruptly (loopable)
* No long silences

---

## DAY 6 — Basic Critic (Very Simple)

### Objective

Introduce **quality gate**, even if naive.

---

### Tasks

#### 1️⃣ LLM-based critic (simple prompt)

Score:

* hook clarity (0–1)
* pacing (0–1)
* loop effectiveness (0–1)

---

#### 2️⃣ Retry once

If total < 0.6:

* regenerate story only
* reuse same job

---

### ✅ Day 6 success check

* Some jobs retry
* You see score differences
* System feels “alive”

---

## DAY 7 — Hardening + Demo

### Objective

Stabilize and **prove end-to-end**.

---

### Tasks

#### 1️⃣ Error handling

* Catch failures
* Mark job failed
* Log cleanly

---

#### 2️⃣ Batch test

Trigger:

* 5 jobs
* same audience
* different hooks

---

#### 3️⃣ Save 3 best outputs

These are your **demo assets**.

---

### ✅ Day 7 success check

* No crashes
* Multiple jobs complete
* You can confidently show results

---

# 📌 End of Week 1 Reality Check

You now have:

✅ A real backend
✅ Job-based orchestration
✅ Reused your existing code
✅ Shorts-native structure
✅ Foundation for scaling

You are **ahead of most founders at this stage**.

---

## What Week 2 unlocks (preview)

Week 2 = **Hook Engine + Personas + Emotion Curves**
This is where quality jumps.

If you want, next I can:

* create **Week 2 task plan**
* refactor your StoryGenius into **micro-scenes**
* review your repo structure *line-by-line*
* help you cut **unnecessary code**

Just say the next move.
