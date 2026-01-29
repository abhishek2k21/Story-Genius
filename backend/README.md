# Story-Genius Backend v2.0

Refactored backend with clean architecture, async database, and Celery task queue.

## Architecture Overview

```
backend/src/
├── core/               # Settings, logging, exceptions
│   ├── settings.py     # Pydantic settings from env vars
│   ├── logging.py      # Structured logging
│   └── exceptions.py   # Custom exception hierarchy
├── database/           # Async SQLAlchemy
│   └── session.py      # Async session factory
├── clients/            # External API wrappers (TODO)
│   ├── vertex_client.py
│   ├── elevenlabs_client.py
│   └── storage_client.py
├── domains/            # Domain-driven modules (TODO)
│   ├── projects/
│   ├── stories/
│   └── video_generation/
├── tasks/              # Celery tasks
│   ├── celery_app.py
│   └── test_task.py
└── main.py             # FastAPI application
```

## Quick Start

### Local Development (without Docker)

```bash
cd backend
poetry install
poetry run uvicorn src.main:app --reload
```

### Docker Development

```bash
# From project root
docker-compose -f docker-compose.dev.yml up
```

### Health Check

```bash
curl http://localhost:8000/health
curl http://localhost:8000/api/v1/health
```

## Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `DATABASE_URL` | `postgresql+asyncpg://...` | Async Postgres URL |
| `REDIS_URL` | `redis://localhost:6379/0` | Redis connection |
| `CELERY_BROKER_URL` | `redis://localhost:6379/1` | Celery broker |
| `GOOGLE_CLOUD_PROJECT` | `winged-precept-458206-j1` | GCP project |
| `DEBUG` | `false` | Enable debug mode |

## Phase 1 Status

- [x] Core skeleton (settings, logging, exceptions)
- [x] Async database session
- [x] Celery configuration
- [x] Health endpoints
- [ ] Clients (Vertex, ElevenLabs)
- [ ] Domains (projects, stories, video_generation)
