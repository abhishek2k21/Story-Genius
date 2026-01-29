# Story-Genius Backend - Development Guide

## Prerequisites

- Python 3.11+
- Docker & Docker Compose
- Redis (for Celery)
- PostgreSQL

## Quick Start

### 1. Clone and Setup

```bash
cd yt-video-creator/backend

# Create virtual environment
python -m venv .venv
.venv\Scripts\activate  # Windows
# source .venv/bin/activate  # Linux/Mac

# Install dependencies
pip install -r requirements.txt
```

### 2. Environment Variables

Create `.env` in `backend/`:

```env
# Database
DATABASE_URL=postgresql+asyncpg://postgres:postgres@localhost:5432/story_genius

# Redis
REDIS_URL=redis://localhost:6379/0
CELERY_BROKER_URL=redis://localhost:6379/1
CELERY_RESULT_BACKEND=redis://localhost:6379/1

# Google Cloud
GOOGLE_CLOUD_PROJECT=your-project-id
GCP_LOCATION=us-central1

# ElevenLabs (optional)
ELEVENLABS_API_KEY=your-key

# Debug
DEBUG=true
```

### 3. Start Services (Docker)

```bash
# From project root
docker-compose -f docker-compose.dev.yml up -d

# Check services
docker ps
```

### 4. Run API Server

```bash
cd backend
uvicorn src.main:app --reload --port 8000
```

### 5. Run Celery Worker (separate terminal)

```bash
cd backend
celery -A src.tasks.celery_app worker --loglevel=info
```

## API Endpoints

### Health
```bash
curl http://localhost:8000/health
curl http://localhost:8000/api/v1/health
```

### Projects
```bash
# Create project
curl -X POST http://localhost:8000/api/v1/projects \
  -H "Content-Type: application/json" \
  -d '{"name": "My Video", "description": "Test project"}'

# Generate video from prompt
curl -X POST http://localhost:8000/api/v1/projects/{id}/generate-video \
  -H "Content-Type: application/json" \
  -d '{"prompt": "Create a video about space exploration", "target_duration": 60}'
```

### Stories
```bash
# Generate story with AI
curl -X POST http://localhost:8000/api/v1/stories/generate \
  -H "Content-Type: application/json" \
  -d '{"project_id": "uuid", "prompt": "Space exploration story", "num_scenes": 5}'
```

### Video Jobs
```bash
# Start video generation
curl -X POST http://localhost:8000/api/v1/video/jobs \
  -H "Content-Type: application/json" \
  -d '{"story_id": "uuid"}'

# Check job status
curl http://localhost:8000/api/v1/video/jobs/{job_id}
```

## Testing

```bash
# Run tests (when available)
pytest tests/ -v

# Test API manually
curl http://localhost:8000/api/docs  # Swagger UI
```

## Architecture

```
src/
├── api/v1/          # REST endpoints
├── core/            # Settings, logging, middleware
├── database/        # Models, session
├── clients/         # External APIs (Vertex, ElevenLabs)
├── domains/         # Business logic
│   ├── projects/    # Project CRUD
│   ├── stories/     # Gemini story generation
│   ├── video_generation/  # Veo + MoviePy
│   ├── analytics/   # Usage tracking
│   └── content/     # Captions, exports
├── tasks/           # Celery async tasks
└── utils/           # Video utilities
```

## Video Pipeline

1. **Prompt** → Gemini generates script with scenes
2. **Scenes** → Parallel generation:
   - Imagen: Reference images
   - ElevenLabs: Audio narration
   - Veo: Video clips (with Ken Burns fallback)
3. **Stitch** → MoviePy combines clips + audio
4. **Export** → Final MP4 with captions
