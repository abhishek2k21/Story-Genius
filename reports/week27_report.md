# Week 27 Report: Engine Refactoring and Hook System

**Status:** ✅ Complete
**Focus:** Standardized engines, viral hook generation, segmented scripts

## Summary
Refactored to standardized engine interfaces, built hook generation with 10 viral templates, and created segmented script engine with hook/body/CTA separation.

## Key Features

### Standard Engine Interface
- `EngineInput` / `EngineOutput` structures
- `BaseEngine` abstract class with lifecycle methods
- `EngineRegistry` for discovery and metrics

### Hook Templates (10 Viral Patterns)
| Template | Style | Example |
|----------|-------|---------|
| Curiosity Gap | curiosity | "Nobody knows why {topic} happens" |
| Contrarian Claim | contrarian | "Everything you believe about {topic} is wrong" |
| Fear Trigger | fear | "Stop doing this with {topic} immediately" |
| Secret Promise | secret | "What experts won't tell you about {topic}" |
| Hidden Truth | secret | "They don't want you to know this about {topic}" |

### Hook Scoring (5 Criteria)
| Criterion | Weight |
|-----------|--------|
| Curiosity | 30% |
| Relevance | 25% |
| Emotion | 20% |
| Clarity | 15% |
| Brevity | 10% |

### Segmented Script Engine
- Hook (2-3s) → Body → CTA (4s)
- 4 structure templates
- 5 content categories
- Duration targeting

## API Endpoints (14 new)
| Endpoint | Method | Description |
|----------|--------|-------------|
| `/v1/engines` | GET | List engines |
| `/v1/engines/{id}` | GET | Engine details |
| `/v1/hooks/generate` | POST | Generate hooks |
| `/v1/hooks/templates` | GET | List templates |
| `/v1/hooks/score` | POST | Score a hook |
| `/v1/hooks/styles` | GET | List styles |
| `/v1/scripts/generate` | POST | Generate script |
| `/v1/scripts/structures` | GET | List structures |

## Files Created
| File | Lines | Purpose |
|------|-------|---------|
| `app/engines/base.py` | ~140 | Engine interface |
| `app/engines/registry.py` | ~120 | Discovery & metrics |
| `app/engines/hook_templates.py` | ~130 | Viral patterns |
| `app/engines/hook_engine.py` | ~200 | Hook generation |
| `app/engines/script_engine.py` | ~280 | Segmented scripts |
| `app/api/engine_routes.py` | ~180 | API endpoints |

## Example Usage
```bash
# Generate hooks
curl -X POST http://localhost:8000/v1/hooks/generate \
  -H "Content-Type: application/json" \
  -d '{"topic": "sleep", "style": "curiosity"}'

# Generate script
curl -X POST http://localhost:8000/v1/scripts/generate \
  -d '{"topic": "productivity", "target_duration": 30}'
```
