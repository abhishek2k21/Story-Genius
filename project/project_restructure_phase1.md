Here is the complete Phases 1–4 plan (Days 1–84) for rebuilding your Story-Genius structure, with the focus you requested: no heavy emphasis on auth for now. I've adjusted the plan to deprioritize auth migration entirely in Phase 3 (treat it as a low-priority or future item; keep your existing auth flow working via the old code until later). Instead, prioritize the core business domains (projects, stories, video generation, etc.) and the new video feature that fixes your "rubbish" animation issues.
The overall goal remains: refactor to a clean, modular monolith with layered architecture (domain → application → infrastructure → presentation), Celery for async AI tasks, and deep integration for Veo 3 + ElevenLabs + assembly.
Key Reminders (unchanged from before)

New structure: backend/src/ with core/, database/, domains/, api/, clients/, tasks/.
Use Poetry, Docker, PostgreSQL + Redis, Vertex AI SDK, ElevenLabs SDK, MoviePy + FFmpeg.
All external AI calls go through clients/ wrappers.
Async orchestration via Celery tasks (critical for Veo polling/assembly).

Phase 1: Planning & Setup (Days 1–14, Weeks 1–2)
Goal: Get a fresh, runnable skeleton without touching old code yet.

Days 1–3: Full audit.
Clone repo, run current app locally.
Map high-level flows: e.g., how a prompt → script → video happens today (grep for Vertex/ElevenLabs calls, orchestrator usage).
List all domains/folders to migrate (projects, stories, video_generation, scheduling, captions, editor, exports, preview, billing, analytics, etc.). Group similar ones (e.g., combine pacing/text_overlay/thumbnail into video_generation/utils).
Document pain points: tight coupling, sync AI calls blocking, no error handling for Veo fails.

Days 4–7: Design & diagram.
Draw architecture diagrams (use Excalidraw/Miro): layers (entities → services → repos → clients), how video gen flow works (prompt → LLM → Veo task → assembly → store).
Define domain boundaries: e.g., projects/ owns project CRUD + file storage; stories/ owns script gen + templates; video_generation/ owns Veo/ElevenLabs orchestration + MoviePy utils.
Decide on minimal migration path: keep old app/ alive in parallel during refactor (use feature flags or separate routes).

Days 8–10: Setup new branch & tooling.
Create branch refactor-core-2026.
Init Poetry: poetry new backend, add core deps (fastapi[all], sqlalchemy[asyncio], alembic, celery[redis], google-cloud-aiplatform, elevenlabs, moviepy, ffmpeg-python, pytest-asyncio, ruff).
Create docker-compose.yml: services for postgres, redis, backend (mount src/), pgadmin optional.
Add .pre-commit-config.yaml with Ruff.

Days 11–14: Build skeleton.
Create backend/src/core/ (settings.py with env vars, logging, exceptions).
database/ (async engine, session maker, Base model).
main.py: minimal FastAPI app with /health endpoint.
Run docker-compose up → API responds. Alembic init.
Commit README.md with "Architecture Overview" section + folder tree.
Milestone: Clean app runs in Docker, no old code yet.


Phase 2: Core & Infrastructure (Days 15–35, Weeks 3–5)
Goal: Build the foundation all domains will use.

Days 15–18: Core utilities.
Implement core/dependencies.py (get_db, get_settings for DI).
Add security basics (if needed later: JWT, but skip full auth flow).
Global exception handlers, request logging.

Days 19–23: Database & migrations.
Migrate key models to database/models/ (Project, StoryTemplate, etc.; use your existing schemas).
Run Alembic migrations for dev DB.
Add async session usage examples.

Days 24–28: External clients.
clients/vertex_client.py: auth, Imagen 3 (ref images), Veo 3 (image-to-video, prompt-to-video, polling status).
clients/elevenlabs_client.py: text-to-speech, voice selection.
clients/storage_client.py (optional: local/S3 for media/files).
Test clients with dummy calls (use Vertex dev quotas).

Days 29–35: Celery + API base.
Setup Celery: tasks/celery_app.py, Redis broker.
Sample task: tasks/test_task.py (ping Redis).
api/v1/: base router, dependencies.
Add /api/v1/health + /api/v1/status (Celery + DB check).
Milestone: Celery task runs async, clients make real calls (e.g., generate tiny Imagen image), API skeleton ready.


Phase 3: Migrate Key Domains (Days 36–70, Weeks 6–10)
Goal: Move essential business logic to new structure. Skip auth completely (keep old auth working; add note to migrate later).

Days 36–42: projects/ domain (highest priority).
domains/projects/entities.py (Pydantic models).
domains/projects/application/services.py (ProjectService: CRUD).
domains/projects/infrastructure/repositories.py (SQLAlchemy repo).
domains/projects/presentation/routers.py (include in api/v1).
Migrate project creation/listing/storage flows.
Test: create project via new API.

Days 43–49: stories/ domain.
Entities: Story, Scene, Template.
Services: StoryService (Gemini prompt → script breakdown → scene list).
Repos: DB ops.
Router: endpoints for generate-story, get-scenes.
Integrate VertexClient for Gemini calls (structured output for scenes).

Days 50–56: scheduling/ + calendar/ + automation/.
Group into domains/scheduling/.
Services for queueing jobs (e.g., schedule video gen).
Repos for calendar events.
Celery tasks for timed runs.

Days 57–63: analytics/ + observability/ + reliability/.
domains/analytics/: log usage, track generations.
Observability: OpenTelemetry or simple logging to file/DB.
Reliability: retry logic in clients (e.g., Veo polling).

Days 64–70: captions/ + editor/ + exports/ + preview/.
Merge into domains/content/ or keep separate if large.
Services for caption generation, editor state, export MP4.
Preview: endpoints to stream partial video or status.
Milestone: Core flows work end-to-end via new APIs (create project → generate story script → export placeholder). Old folders still there but bypassed for new routes.


Phase 4: Video Generation Feature + Remaining Domains (Days 71–84, Weeks 11–12)
Goal: Implement the faceless.so-style video builder that fixes your animation issues.

Days 71–75: video_generation/ domain setup.
Entities: VideoJob, SceneClip.
Services: VideoGenerationService (orchestrates: LLM → prompts → ref images → Veo → assembly).
Utils (move from old engines/): pacing, text_overlay, thumbnail (MoviePy functions).

Days 76–80: Core video flow.
Celery task: tasks/video_gen_task(project_id, prompt):
Call StoryService for scenes.
Generate ref images (Imagen 3).
Per-scene: Veo call (5–10 sec clips, detailed prompts + ref image).
Safety fallback: if fail → cartoon style or Ken Burns on image.
Assembly: MoviePy stitch + ElevenLabs audio sync + overlays/transitions.

Router: POST /v1/projects/{id}/generate-video (queues task, returns job_id).

Days 81–84: Polish & remaining.
Add polling endpoint for job status/result.
Integrate thumbnail gen.
Migrate any leftovers (brand, personal, experiments → group into misc/ or video-related).
Clean up: remove redundant old code (or comment out).
Milestone: Test full flow: input prompt → safe, coherent 20-sec video (no rubbish via short clips + refs). Preview works.


Next Steps After Phase 4

Proceed to Phase 5 (Days 85–91: tests, frontend updates, deploy) once Phase 4 is solid.
Daily: 3–4 hrs coding + tests, commit often.
Track progress in a Notion/Google Sheet (domain | status | blockers).
If Veo costs spike, add mock mode in clients/.

This gets you to a refactored, video-focused core by day 84, without auth distractions. If you hit blockers (e.g., specific domain coupling), share details for tweaks. Start Phase 1 today!3.9s