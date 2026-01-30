# Story-Genius: AI Video Generation Platform

> **Complete End-to-End Documentation**
> Version 2.0 | 110+ Files | Production-Ready

---

## 🎯 Overview

Story-Genius is an AI-powered video generation platform that transforms text prompts into complete narrated videos. Built with FastAPI, Celery, and modern Python async patterns.

### Key Features
- **AI Script Generation** - Gemini creates structured story scripts
- **Video Generation** - Google Veo generates video clips per scene
- **Voice Narration** - ElevenLabs TTS with natural voices
- **Auto Stitching** - MoviePy combines clips into final video
- **15+ Style Presets** - Pixar, anime, cinematic, and more
- **Batch Processing** - Generate multiple videos in parallel
- **Sound Effects** - Freesound API integration

---

## 🏗️ Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                         Frontend (Next.js)                       │
└─────────────────────────┬───────────────────────────────────────┘
                          │ REST API + WebSocket
┌─────────────────────────▼───────────────────────────────────────┐
│                      FastAPI Backend                             │
│  ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────┐            │
│  │ Projects │ │ Stories  │ │  Video   │ │ Content  │            │
│  │  Domain  │ │  Domain  │ │  Domain  │ │  Domain  │            │
│  └────┬─────┘ └────┬─────┘ └────┬─────┘ └────┬─────┘            │
│       └────────────┴────────────┴────────────┘                   │
│                          │                                       │
│  ┌──────────────────────▼────────────────────────────────────┐  │
│  │                    Celery Task Queue                       │  │
│  └──────────────────────┬────────────────────────────────────┘  │
└─────────────────────────┼───────────────────────────────────────┘
                          │
┌─────────────────────────▼───────────────────────────────────────┐
│                     External Services                            │
│  ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────┐            │
│  │  Gemini  │ │   Veo    │ │ElevenLabs│ │Freesound │            │
│  │  (Text)  │ │ (Video)  │ │  (TTS)   │ │  (SFX)   │            │
│  └──────────┘ └──────────┘ └──────────┘ └──────────┘            │
└─────────────────────────────────────────────────────────────────┘
```

---

## 📁 Project Structure

```
yt-video-creator/
├── backend/
│   ├── src/
│   │   ├── api/v1/
│   │   │   ├── endpoints/
│   │   │   │   ├── health.py          # Health checks
│   │   │   │   ├── projects.py        # Project CRUD + video gen
│   │   │   │   ├── styles.py          # Style presets API
│   │   │   │   ├── monitoring.py      # Usage & costs
│   │   │   │   └── websocket.py       # Real-time progress
│   │   │   └── router.py              # API router
│   │   │
│   │   ├── core/
│   │   │   ├── settings.py            # Configuration
│   │   │   ├── logging.py             # Structured logging
│   │   │   ├── exceptions.py          # Custom exceptions
│   │   │   ├── middleware.py          # Request logging
│   │   │   ├── rate_limit.py          # Token bucket throttling
│   │   │   ├── auth.py                # JWT + API keys
│   │   │   ├── safety.py              # Prompt safety filters
│   │   │   ├── validation.py          # Input sanitization
│   │   │   ├── observability.py       # Metrics & tracing
│   │   │   ├── retry.py               # Exponential backoff
│   │   │   ├── usage_logging.py       # Cost tracking
│   │   │   └── websocket.py           # WS connection manager
│   │   │
│   │   ├── clients/
│   │   │   ├── vertex_client.py       # Gemini + Veo + Imagen
│   │   │   ├── elevenlabs_client.py   # Text-to-speech
│   │   │   ├── storage_client.py      # GCS file storage
│   │   │   └── freesound_client.py    # Sound effects API
│   │   │
│   │   ├── database/
│   │   │   ├── models.py              # SQLAlchemy models
│   │   │   └── session.py             # Async session factory
│   │   │
│   │   ├── domains/
│   │   │   ├── projects/
│   │   │   │   ├── entities.py        # Pydantic schemas
│   │   │   │   ├── repositories.py    # DB operations
│   │   │   │   ├── services.py        # Business logic
│   │   │   │   └── routers.py         # REST endpoints
│   │   │   │
│   │   │   ├── stories/
│   │   │   │   ├── entities.py        # Story, Scene schemas
│   │   │   │   ├── repositories.py    # Story/Scene DB ops
│   │   │   │   ├── services.py        # Gemini script generation
│   │   │   │   └── routers.py         # /stories endpoints
│   │   │   │
│   │   │   ├── video_generation/
│   │   │   │   ├── entities.py        # VideoJob schemas
│   │   │   │   ├── services.py        # Veo + stitch logic
│   │   │   │   ├── enhanced_service.py # Imagen refs + fallbacks
│   │   │   │   ├── tasks.py           # Celery tasks
│   │   │   │   ├── enhanced_tasks.py  # Full pipeline task
│   │   │   │   ├── styles.py          # 15+ style presets
│   │   │   │   ├── batch.py           # Batch generation
│   │   │   │   └── routers.py         # /video endpoints
│   │   │   │
│   │   │   ├── analytics/
│   │   │   │   ├── entities.py        # Usage schemas
│   │   │   │   ├── services.py        # Stats aggregation
│   │   │   │   └── routers.py         # /analytics endpoints
│   │   │   │
│   │   │   └── content/
│   │   │       ├── entities.py        # Caption, Export schemas
│   │   │       ├── services.py        # Caption gen, exports
│   │   │       └── routers.py         # /content endpoints
│   │   │
│   │   ├── tasks/
│   │   │   ├── celery_app.py          # Celery configuration
│   │   │   └── test_task.py           # Test tasks
│   │   │
│   │   ├── utils/
│   │   │   └── video/
│   │   │       ├── pacing.py          # Scene timing
│   │   │       ├── text_overlay.py    # Caption compositing
│   │   │       ├── effects.py         # Zoom, pan, Ken Burns
│   │   │       ├── thumbnail.py       # Frame extraction
│   │   │       └── thumbnails_ab.py   # A/B variants
│   │   │
│   │   └── main.py                    # FastAPI app
│   │
│   ├── tests/
│   │   ├── conftest.py                # Pytest fixtures
│   │   ├── test_projects.py           # Project tests
│   │   ├── test_stories.py            # Story tests
│   │   ├── test_video.py              # Video tests
│   │   └── test_smoke.py              # E2E smoke tests
│   │
│   ├── requirements.txt
│   ├── Dockerfile.prod
│   ├── pytest.ini
│   └── .env.example
│
├── docker-compose.dev.yml             # Development stack
├── docker-compose.prod.yml            # Production stack
└── README.md
```

---

## 🔌 API Endpoints

### Core Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/health` | GET | Basic health check |
| `/api/v1/health` | GET | Detailed status with DB/Redis |

### Projects

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/v1/projects` | GET | List projects |
| `/api/v1/projects` | POST | Create project |
| `/api/v1/projects/{id}` | GET | Get project |
| `/api/v1/projects/{id}` | PATCH | Update project |
| `/api/v1/projects/{id}` | DELETE | Delete project |
| `/api/v1/projects/{id}/generate-video` | POST | **Full pipeline** |

### Stories

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/v1/stories` | GET/POST | List/Create stories |
| `/api/v1/stories/generate` | POST | AI script generation |
| `/api/v1/stories/{id}` | GET/DELETE | Get/Delete story |
| `/api/v1/stories/{id}/scenes` | GET | List scenes |

### Video Generation

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/v1/video/jobs` | POST | Start video job |
| `/api/v1/video/jobs/{id}` | GET | Job status |
| `/api/v1/video/styles` | GET | List style presets |
| `/api/v1/video/batch` | POST | Batch generation |

### Content

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/v1/content/captions` | POST | Generate captions |
| `/api/v1/content/exports` | POST | Export video |
| `/api/v1/content/preview/{id}` | GET | Preview status |

### Monitoring

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/v1/monitoring/usage` | GET | API usage stats |
| `/api/v1/monitoring/costs` | GET | Cost breakdown |
| `/api/v1/analytics/stats` | GET | Generation stats |

### WebSocket

| Endpoint | Description |
|----------|-------------|
| `WS /api/v1/ws/jobs/{id}` | Real-time job progress |
| `WS /api/v1/ws/user/{id}` | User notifications |

---

## 🚀 Video Generation Pipeline

```
┌─────────────────────────────────────────────────────────────────┐
│                    POST /projects/{id}/generate-video            │
│                    { "prompt": "...", "style_id": "pixar" }      │
└─────────────────────────┬───────────────────────────────────────┘
                          │
                          ▼
┌─────────────────────────────────────────────────────────────────┐
│ 1. SCRIPT GENERATION (Gemini)                                    │
│    • Parse prompt with style prefix                              │
│    • Generate structured story with scenes                       │
│    • Each scene: narration + visual_prompt + duration            │
└─────────────────────────┬───────────────────────────────────────┘
                          │
                          ▼
┌─────────────────────────────────────────────────────────────────┐
│ 2. PARALLEL SCENE PROCESSING                                     │
│    ┌──────────────┐ ┌──────────────┐ ┌──────────────┐           │
│    │  Scene 1     │ │  Scene 2     │ │  Scene 3     │           │
│    │  • Imagen    │ │  • Imagen    │ │  • Imagen    │           │
│    │  • TTS       │ │  • TTS       │ │  • TTS       │           │
│    │  • Veo       │ │  • Veo       │ │  • Veo       │           │
│    └──────────────┘ └──────────────┘ └──────────────┘           │
└─────────────────────────┬───────────────────────────────────────┘
                          │
                          ▼
┌─────────────────────────────────────────────────────────────────┐
│ 3. STITCHING (MoviePy)                                           │
│    • Combine video clips with transitions                        │
│    • Sync audio narration                                        │
│    • Add text overlays                                           │
│    • Generate thumbnails                                         │
└─────────────────────────┬───────────────────────────────────────┘
                          │
                          ▼
┌─────────────────────────────────────────────────────────────────┐
│ 4. EXPORT                                                        │
│    • Final MP4 (1080p)                                           │
│    • Thumbnail variants                                          │
│    • Optional captions (SRT)                                     │
└─────────────────────────────────────────────────────────────────┘
```

---

## 🎨 Style Presets

| ID | Name | Category | Description |
|----|------|----------|-------------|
| `pixar` | Pixar 3D | Animation | Vibrant, expressive, smooth 3D |
| `anime` | Japanese Anime | Animation | Detailed line art, dynamic |
| `disney` | Disney Classic | Animation | Magical, enchanting |
| `cartoon` | Classic Cartoon | Animation | Bold outlines, playful |
| `cinematic` | Cinematic | Cinematic | Hollywood film quality |
| `documentary` | Documentary | Cinematic | Natural, authentic |
| `noir` | Film Noir | Cinematic | High contrast B&W |
| `scifi` | Sci-Fi Epic | Cinematic | Futuristic, epic |
| `watercolor` | Watercolor | Artistic | Soft, flowing |
| `oilpainting` | Oil Painting | Artistic | Rich textures |
| `minimalist` | Minimalist | Artistic | Clean, elegant |
| `photorealistic` | Photorealistic | Realistic | Hyperrealistic |
| `nature` | Nature Doc | Realistic | BBC Earth quality |
| `retro80s` | 80s Retro | Vintage | Neon, synthwave |
| `vintage` | Vintage Film | Vintage | Sepia, nostalgic |

---

## 🔧 Quick Start

### Prerequisites
- Python 3.11+
- Docker & Docker Compose
- Google Cloud account (for Vertex AI)
- Optional: ElevenLabs API key

### 1. Clone & Setup

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

```bash
cp .env.example .env
# Edit .env with your API keys
```

Required variables:
```env
DATABASE_URL=postgresql+asyncpg://postgres:postgres@localhost:5432/story_genius
REDIS_URL=redis://localhost:6379/0
CELERY_BROKER_URL=redis://localhost:6379/1
GOOGLE_CLOUD_PROJECT=your-project-id
```

### 3. Start Services

```bash
# Development
docker-compose -f docker-compose.dev.yml up -d

# Start API
cd backend
uvicorn src.main:app --reload --port 8000

# Start Celery worker (separate terminal)
celery -A src.tasks.celery_app worker --loglevel=info
```

### 4. Generate Your First Video

```bash
# Create project
curl -X POST http://localhost:8000/api/v1/projects \
  -H "Content-Type: application/json" \
  -d '{"name": "My First Video"}'

# Generate video
curl -X POST http://localhost:8000/api/v1/projects/{project_id}/generate-video \
  -H "Content-Type: application/json" \
  -d '{
    "prompt": "A magical journey through an enchanted forest",
    "style_id": "pixar",
    "target_duration": 30
  }'
```

---

## 🧪 Testing

```bash
cd backend

# Run all tests
pytest tests/ -v

# Run specific test file
pytest tests/test_smoke.py -v

# Run with coverage
pytest tests/ --cov=src --cov-report=html
```

---

## 🚢 Production Deployment

### Docker Production

```bash
# Build and deploy
docker-compose -f docker-compose.prod.yml up -d

# View logs
docker-compose -f docker-compose.prod.yml logs -f api
```

### Environment Variables (Production)

```env
DEBUG=false
POSTGRES_PASSWORD=secure-password
SECRET_KEY=your-secret-key
CORS_ORIGINS=["https://yourdomain.com"]
```

### Services in Production Stack
- **PostgreSQL** - Primary database
- **Redis** - Celery broker + cache
- **API** - FastAPI with 4 workers
- **Celery** - 2 concurrent workers
- **Celery Beat** - Scheduled tasks

---

## 📊 Monitoring

### Usage Stats
```bash
curl http://localhost:8000/api/v1/monitoring/usage?hours=24
```

### Cost Breakdown
```bash
curl http://localhost:8000/api/v1/monitoring/costs?days=7
```

### WebSocket Progress
```javascript
const ws = new WebSocket('ws://localhost:8000/api/v1/ws/jobs/job-123');
ws.onmessage = (e) => {
  const data = JSON.parse(e.data);
  console.log(`Progress: ${data.progress * 100}% - ${data.step}`);
};
```

---

## 🔒 Security Features

| Feature | Description |
|---------|-------------|
| Rate Limiting | Token bucket per endpoint (10-60/min) |
| JWT Auth | Bearer token authentication |
| API Keys | X-API-Key header support |
| Input Validation | XSS prevention, size limits |
| Prompt Safety | Pattern detection, safe alternatives |
| CORS | Configurable allowed origins |

---

## 📈 Performance

| Metric | Target |
|--------|--------|
| API Response | < 200ms |
| Script Generation | 3-5s |
| Scene Video (5s) | 30-60s |
| Full 60s Video | 5-10 min |
| Batch (10 videos) | ~30 min |

---

## 🛠️ Development Timeline

| Phase | Days | Status |
|-------|------|--------|
| Core Infrastructure | 1-28 | ✅ |
| API + Domains | 29-56 | ✅ |
| Analytics + Content | 57-70 | ✅ |
| Video Utils | 71-84 | ✅ |
| Tests + Deploy | 85-91 | ✅ |
| Hardening | 92-100 | ✅ |
| Features | 101-110 | ✅ |

**Total: 110+ files, production-ready**

---

## 📝 License

MIT License - See LICENSE file

---

## 🤝 Contributing

1. Fork the repository
2. Create feature branch (`git checkout -b feature/amazing`)
3. Commit changes (`git commit -m 'Add amazing feature'`)
4. Push to branch (`git push origin feature/amazing`)
5. Open Pull Request

---

*Built with ❤️ using FastAPI, Celery, and Google Vertex AI*
