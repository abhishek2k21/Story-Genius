# Story-Genius Backend v2.0

AI-powered video generation platform with clean architecture.

## Quick Start

```bash
# Docker (recommended)
docker-compose -f docker-compose.dev.yml up -d
cd backend && uvicorn src.main:app --reload

# Celery worker (separate terminal)
celery -A src.tasks.celery_app worker --loglevel=info
```

## API Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/health` | GET | Basic health |
| `/api/v1/health` | GET | Full status |
| `/api/v1/projects` | CRUD | Project management |
| `/api/v1/projects/{id}/generate-video` | POST | **Full pipeline** |
| `/api/v1/stories` | CRUD | Story management |
| `/api/v1/stories/generate` | POST | AI script generation |
| `/api/v1/video/jobs` | POST/GET | Video job management |
| `/api/v1/content/captions` | POST | Caption generation |
| `/api/v1/content/exports` | POST | Video exports |
| `/api/v1/analytics/stats` | GET | Usage statistics |

## Architecture

```
src/
├── api/v1/         # REST endpoints
├── core/           # Settings, logging, observability
├── database/       # Async SQLAlchemy models
├── clients/        # Vertex AI, ElevenLabs, Storage
├── domains/        # Business logic (5 domains)
├── tasks/          # Celery async tasks
└── utils/video/    # MoviePy utilities
```

## Video Pipeline

```
Prompt → Gemini Script → [Imagen Ref + ElevenLabs TTS + Veo Video] → MoviePy Stitch → Export
```

## Phase Status
- [x] Phase 1: Core infrastructure (Days 1-84)
- [ ] Phase 2: Frontend integration
- [ ] Phase 3: Deployment
