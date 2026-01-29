# Story-Genius Backend v2.0

Refactored backend with clean architecture, async database, and Celery task queue.

## Architecture

```
backend/src/
├── core/           # Settings, logging, exceptions, middleware
├── database/       # Async SQLAlchemy, models
├── clients/        # Vertex AI, ElevenLabs, Storage
├── domains/        # Business logic (projects, stories, etc.)
│   └── projects/   # First domain migrated
├── tasks/          # Celery async tasks
├── api/v1/         # REST API endpoints
└── main.py         # FastAPI app
```

## Quick Start

```bash
# Docker (recommended)
docker-compose -f docker-compose.dev.yml up

# Or manual
cd backend && pip install -r requirements.txt
uvicorn src.main:app --reload
```

## API Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/health` | GET | Basic health check |
| `/api/v1/health` | GET | Detailed health with DB/Redis |
| `/api/v1/status` | GET | Status with Celery workers |
| `/api/v1/projects` | GET | List projects |
| `/api/v1/projects` | POST | Create project |
| `/api/v1/projects/{id}` | GET | Get project |
| `/api/v1/projects/{id}` | PATCH | Update project |
| `/api/v1/projects/{id}` | DELETE | Delete project |

## Phase Status

- [x] Phase 1: Core skeleton (Days 1-14)
- [x] Phase 2: Core utilities, DB models, clients (Days 15-28)
- [x] Phase 3 (partial): API base, projects domain (Days 29-42)
- [ ] Phase 3 (remaining): stories, video_generation domains
