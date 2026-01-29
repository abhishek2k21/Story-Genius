# 90-Day Enterprise Modernization Roadmap
## Creative AI Shorts & Reels Platform

**Start Date**: January 28, 2026  
**End Date**: April 28, 2026  
**Status**: Planning Phase

---

## Executive Summary

Transform the platform from a working prototype into a production-grade system. Focus on:
- **Stability**: Error handling, persistence, transactions
- **Scalability**: Async/distributed processing, caching
- **Quality**: Testing, monitoring, observability
- **Developer Experience**: API clients, documentation
- **User Experience**: Modern frontend, analytics, automation

---

## Phase 1: Weeks 1-4 — Foundation Hardening

### Week 1-2: Core Infrastructure Modernization

#### Task 1.1: Exception Hierarchy & Error Handling
- **Priority**: CRITICAL
- **Duration**: 3 days
- **Deliverables**:
  - [ ] Create `app/core/exceptions.py` with custom exceptions
    - VideoGenerationError, LLMError, AuthError, RateLimitError
    - ValidationError, DatabaseError, ExternalServiceError
  - [ ] Replace all generic `except Exception` with specific types
  - [ ] Add error context (error code, details, timestamp)
  - [ ] Implement error fingerprinting for deduplication
  - [ ] Create error tracking service integration
- **Files to Create/Modify**:
  - `app/core/exceptions.py` (new)
  - `app/core/error_tracking.py` (new)
  - `app/api/routes.py` (modify error handling)
  - `app/orchestrator/service.py` (modify error handling)
- **Tests**: Test each exception type with proper error codes
- **Success Criteria**: All exceptions caught are domain-specific, error tracking logs fingerprints

#### Task 1.2: Structured Logging with Context
- **Priority**: HIGH
- **Duration**: 2 days
- **Deliverables**:
  - [ ] Extend `app/core/logging.py` with context fields
    - Add contextvars for request_id, job_id, batch_id, user_id
    - Implement log context manager for request scope
  - [ ] Create structured log formatter (JSON output with metadata)
  - [ ] Add trace ID generation and propagation
  - [ ] Implement log level configuration per module
- **Files to Create/Modify**:
  - `app/core/logging.py` (extend)
  - `app/core/context.py` (new - contextvars)
- **Tests**: Verify context propagation across async calls
- **Success Criteria**: All logs include job_id, user_id, trace_id; JSON formatting works

#### Task 1.3: Database Infrastructure
- **Priority**: CRITICAL
- **Duration**: 4 days
- **Deliverables**:
  - [ ] Create Alembic migration runner
    - Initialize `alembic init migrations`
    - Create migration history tracking
  - [ ] Add SQL indexes on hot columns
    - user_id, batch_id, job_id, status, created_at
  - [ ] Create database transaction context manager
    - Implement `@transactional` decorator
    - Support nested transactions with savepoints
  - [ ] Add connection pool configuration for PostgreSQL
  - [ ] Create database health check endpoint
- **Files to Create/Modify**:
  - `migrations/env.py` (Alembic config)
  - `migrations/versions/` (index migration SQL)
  - `app/core/database.py` (extend with transactions, pooling)
  - `app/reliability/health_checks.py` (extend)
- **Tests**: Test transaction rollback, index effectiveness
- **Success Criteria**: Alembic migrations run, indexes present, transactions work

---

### Week 3: Service Layer Stability

#### Task 1.4: Distributed Locking for Schedulers
- **Priority**: HIGH
- **Duration**: 3 days
- **Deliverables**:
  - [ ] Move BatchSchedule from in-memory dict to database
    - Create BatchSchedule model with status, next_run_at
    - Implement persistence layer
  - [ ] Implement distributed lock using Redis/Celery
    - Create `LockManager` class
    - Use lock key: `batch_schedule:{batch_id}:lock`
    - Set TTL to prevent deadlocks
  - [ ] Add lock acquisition timeout with fallback
  - [ ] Create lock status monitoring endpoint
- **Files to Create/Modify**:
  - `app/scheduling/models.py` (extend with database fields)
  - `app/scheduling/lock_manager.py` (new)
  - `app/scheduling/service.py` (integrate locking)
  - `app/batch/service.py` (deduplication logic)
- **Tests**: Test concurrent scheduler invocations, lock timeout
- **Success Criteria**: No duplicate batch executions, locks timeout properly

#### Task 1.5: Service Health & Circuit Breakers
- **Priority**: HIGH
- **Duration**: 3 days
- **Deliverables**:
  - [ ] Implement circuit breaker pattern
    - Create `CircuitBreaker` class with states (closed, open, half-open)
    - Configure for Vertex AI, Veo, EdgeTTS services
  - [ ] Add health check for each service
    - Measure response time, error rate
    - Track failure counts for state transitions
  - [ ] Implement fallback models
    - If Gemini 2.0-flash fails, use Gemini 1.5-pro
    - If Veo unavailable, degrade gracefully
  - [ ] Create service health dashboard endpoint
- **Files to Create/Modify**:
  - `app/core/circuit_breaker.py` (new)
  - `app/engines/llm.py` (integrate circuit breaker)
  - `app/media/video_service.py` (integrate circuit breaker)
  - `app/reliability/health_checks.py` (extend)
- **Tests**: Test circuit breaker state transitions, fallback activation
- **Success Criteria**: Service failures handled gracefully, circuit breaker metrics available

#### Task 1.6: Auth Token Security
- **Priority**: CRITICAL
- **Duration**: 2 days
- **Deliverables**:
  - [ ] Remove hardcoded SECRET_KEY
    - Generate new SECRET_KEY from secrets manager
    - Implement automatic rotation (monthly)
  - [ ] Implement token refresh mechanism
    - Short-lived access tokens (15min)
    - Long-lived refresh tokens (7 days)
    - Refresh endpoint: `POST /v1/auth/refresh`
  - [ ] Add API key rotation
    - Create endpoint to generate new keys
    - Keep old keys valid for 30 days
  - [ ] Fix CORS configuration
    - Replace wildcard with specific origins
    - Add environment-based origin list
  - [ ] Create token revocation endpoint
- **Files to Create/Modify**:
  - `app/auth/models.py` (add refresh token model)
  - `app/auth/service.py` (implement token refresh, rotation)
  - `app/api/auth_routes.py` (add refresh, rotation endpoints)
  - `app/core/config.py` (remove hardcoded secrets)
- **Tests**: Test token refresh, API key rotation, CORS validation
- **Success Criteria**: No hardcoded secrets, token refresh works, CORS restricted

---

### Week 4: Batch Processing & API Foundation

#### Task 1.7: Standardized API Responses
- **Priority**: HIGH
- **Duration**: 2 days
- **Deliverables**:
  - [ ] Define error response schema
    - `{error: string, code: string, details: object, timestamp: string}`
  - [ ] Create `APIResponse[T]` wrapper for success responses
    - `{data: T, status: string, timestamp: string}`
  - [ ] Implement response interceptor in FastAPI
    - Auto-wrap all responses
  - [ ] Update OpenAPI documentation with schema
  - [ ] Create error code constants (e.g., LLM_TIMEOUT, VIDEO_GEN_FAILED)
- **Files to Create/Modify**:
  - `app/api/schemas.py` (APIResponse, ErrorResponse)
  - `app/api/middleware.py` (response interceptor)
  - `app/api/main.py` (register middleware)
- **Tests**: Test error response format, success response format
- **Success Criteria**: All API responses follow schema, OpenAPI docs updated

#### Task 1.8: Input Validation Layer
- **Priority**: MEDIUM
- **Duration**: 2 days
- **Deliverables**:
  - [ ] Create request validators for all endpoints
    - Content length validation
    - Audience compatibility checking
    - Platform constraint validation
  - [ ] Implement helpful error messages
    - "Script too long for TikTok, recommend 20-25s"
  - [ ] Create validation middleware
  - [ ] Add request sanitization (prevent prompt injection)
- **Files to Create/Modify**:
  - `app/api/validators.py` (new)
  - `app/api/middleware.py` (validation middleware)
- **Tests**: Test validation rules, error messages
- **Success Criteria**: Invalid inputs rejected with helpful messages

#### Task 1.9: Batch Processing Transactional Guarantees
- **Priority**: HIGH
- **Duration**: 3 days
- **Deliverables**:
  - [ ] Wrap batch operations in database transactions
    - Create batch record → Process items → Commit/Rollback
    - Use `@transactional` decorator
  - [ ] Implement batch result aggregation
    - Track success count, failure count, error breakdown
    - Store in BatchResult model
  - [ ] Add batch-level retries
    - Exponential backoff strategy
    - Max retry limit per batch
  - [ ] Create batch status tracking
    - draft → processing → completed → archived
- **Files to Create/Modify**:
  - `app/batch/models.py` (extend with result tracking)
  - `app/batch/service.py` (transaction wrapping, result aggregation)
  - `app/batch/retry_strategy.py` (new)
- **Tests**: Test transaction rollback, result aggregation, batch retries
- **Success Criteria**: Batch operations atomic, results tracked, retries work

---

## Phase 2: Weeks 5-8 — Quality & Observability

### Week 5-6: AI/ML Prompt Management & Evaluation

#### Task 2.1: Centralized Prompt System
- **Priority**: CRITICAL
- **Duration**: 4 days
- **Deliverables**:
  - [ ] Create `app/core/prompts/` folder structure
    - `base_prompts.py` - Hook, script, critic templates
    - `prompt_templates.py` - Jinja2-based templates with variables
    - `prompt_versioning.py` - Version tracking, A/B testing
    - `prompt_validation.py` - Length, variable validation
  - [ ] Migrate all scattered prompts
    - Extract from critic_service.py
    - Extract from contract_generator.py
    - Extract from intelligence modules
  - [ ] Implement prompt rendering with variables
    - `HookPrompt.render(audience=..., genre=...)`
  - [ ] Add prompt versioning
    - Track changes, dates, author
    - Support rollback to previous version
- **Files to Create/Modify**:
  - `app/core/prompts/base_prompts.py` (new)
  - `app/core/prompts/prompt_templates.py` (new)
  - `app/core/prompts/prompt_versioning.py` (new)
  - `app/core/prompts/prompt_validation.py` (new)
  - `app/engines/llm.py` (use centralized prompts)
  - `app/critic/service.py` (use centralized prompts)
- **Tests**: Test prompt rendering, versioning, validation
- **Success Criteria**: All LLM calls use centralized prompts, no scattered templates

#### Task 2.2: LLM Output Validation & Caching
- **Priority**: HIGH
- **Duration**: 3 days
- **Deliverables**:
  - [ ] Implement Pydantic validators for LLM responses
    - JSON parsing validation
    - Field presence/type validation
    - Length/format constraints
  - [ ] Add prompt caching
    - Use Vertex AI prompt caching (if available)
    - Fallback to Redis caching for repeated requests
  - [ ] Create LLMEvaluator
    - Score output quality before use
    - Reject malformed responses
  - [ ] Implement token usage tracking
    - Log tokens per request
    - Aggregate by model, endpoint
    - Create cost reporting
- **Files to Create/Modify**:
  - `app/engines/llm_validator.py` (new)
  - `app/engines/llm_cache.py` (new)
  - `app/engines/llm_evaluator.py` (new)
  - `app/engines/llm.py` (integrate validation, caching)
  - `app/analytics/token_tracker.py` (new)
- **Tests**: Test validators, cache hits/misses, token tracking
- **Success Criteria**: Invalid LLM outputs rejected, cache working, token usage tracked

#### Task 2.3: Intelligent Retry Strategy
- **Priority**: HIGH
- **Duration**: 2 days
- **Deliverables**:
  - [ ] Implement model fallback hierarchy
    - Primary: Gemini 2.0-flash
    - Fallback 1: Gemini 1.5-pro
    - Fallback 2: Gemini 1.5-flash
  - [ ] Add timeout enforcement
    - Max 30s per LLM call
    - Max 60s per Veo call
    - Timeout exceptions properly handled
  - [ ] Create failure metrics
    - Which prompts fail most often
    - Which models fail most often
    - Failure breakdown (timeout, error, malformed)
  - [ ] Implement adaptive timeout
    - Increase timeout for complex requests
- **Files to Create/Modify**:
  - `app/engines/llm.py` (extend with fallback, timeout)
  - `app/reliability/retry_strategy.py` (extend)
  - `app/observability/metrics.py` (failure tracking)
- **Tests**: Test model fallback, timeout enforcement, failure metrics
- **Success Criteria**: LLM failures handled gracefully, timeout working, metrics visible

---

### Week 7-8: Testing & Monitoring Infrastructure

#### Task 2.4: Test Framework Setup
- **Priority**: CRITICAL
- **Duration**: 4 days
- **Deliverables**:
  - [ ] Initialize pytest structure
    - `app/tests/conftest.py` - Fixtures
    - `app/tests/unit/` - Unit tests
    - `app/tests/integration/` - Integration tests
  - [ ] Create fixtures for mocking
    - Mock Vertex AI responses
    - Mock Veo responses
    - Mock database
  - [ ] Write unit tests for core modules
    - Config, models, exceptions
    - Validators, error handling
  - [ ] Write integration tests for services
    - Orchestrator job lifecycle
    - Batch processing
    - Critic scoring
  - [ ] Set up coverage reporting
    - Target 60%+ coverage
    - Create coverage report endpoint
  - [ ] Configure CI/CD
    - GitHub Actions: run tests on every commit
    - Fail if coverage < 60%
- **Files to Create/Modify**:
  - `app/tests/` folder structure (new)
  - `app/tests/conftest.py` (new)
  - `app/tests/unit/test_config.py` (new)
  - `app/tests/unit/test_models.py` (new)
  - `app/tests/integration/test_orchestrator.py` (new)
  - `app/tests/integration/test_batch.py` (new)
  - `.github/workflows/test.yml` (new)
  - `pytest.ini` (new)
  - `pyproject.toml` (add pytest config)
- **Tests**: Run test suite, check coverage
- **Success Criteria**: 60%+ test coverage, CI/CD running, all tests passing

#### Task 2.5: Monitoring & Alerting Infrastructure
- **Priority**: HIGH
- **Duration**: 3 days
- **Deliverables**:
  - [ ] Export metrics to Prometheus format
    - Create `/metrics` endpoint
    - Expose Counter, Gauge, Histogram metrics
  - [ ] Set up Prometheus server
    - Scrape metrics every 30 seconds
    - Configure retention (15 days)
  - [ ] Configure Grafana dashboards
    - Job success rate, latency (p50, p95, p99)
    - Error rate by type
    - Token usage and API costs
    - Batch processing throughput
  - [ ] Set up alerting rules
    - Alert if error rate > 5%
    - Alert if latency p99 > 30s
    - Alert if batch fails
  - [ ] Integrate with PagerDuty or Slack
- **Files to Create/Modify**:
  - `app/observability/prometheus_exporter.py` (new)
  - `app/api/metrics_routes.py` (new)
  - `docker-compose.yml` (add Prometheus, Grafana)
  - `grafana/dashboards/` (new - dashboard JSON)
  - `prometheus/alert.rules.yml` (new)
- **Tests**: Test metrics collection, Prometheus scrape
- **Success Criteria**: Prometheus metrics visible, Grafana dashboards working, alerts configured

#### Task 2.6: Structured Logging & Aggregation
- **Priority**: HIGH
- **Duration**: 2 days
- **Deliverables**:
  - [ ] Configure structured logging (JSON format)
    - Timestamp, level, logger, message, context fields
  - [ ] Set up log aggregation
    - Option A: ELK stack (Elasticsearch, Logstash, Kibana)
    - Option B: GCP Cloud Logging
    - Option C: CloudWatch (AWS)
  - [ ] Create log search UI
    - Filter by job_id, batch_id, error code
    - Time range selection
  - [ ] Configure log-based alerts
    - Alert on error spike
    - Alert on specific error codes
  - [ ] Implement trace ID propagation
    - Generate trace ID for each request
    - Include in all logs for that request
- **Files to Create/Modify**:
  - `app/core/logging.py` (JSON formatting)
  - `docker-compose.yml` (add ELK or Cloud Logging)
  - `app/observability/log_aggregation.py` (new - if self-hosted)
- **Tests**: Test log formatting, trace ID propagation
- **Success Criteria**: Logs in JSON format, searchable in aggregation tool, alerts working

---

## Phase 3: Weeks 9-12 — Content Engine & Services Enhancement

### Week 9: Content Engine Improvements

#### Task 3.1: Script-Hook Coherence
- **Priority**: MEDIUM
- **Duration**: 2 days
- **Deliverables**:
  - [ ] Create coherence validator
    - Check hook matches script tone (deadpan hook with funny script = bad)
    - Check hook setup matches script delivery
  - [ ] Implement reranking step
    - If coherence score < 0.7, regenerate hook only
    - Keep script, generate new hooks
  - [ ] Add confidence scores
    - Confidence that script will perform well
    - Confidence that hook-script pairing is coherent
  - [ ] Create A/B test for coherence impact
- **Files to Create/Modify**:
  - `app/intelligence/coherence_validator.py` (new)
  - `app/engines/hook_engine.py` (reranking)
  - `app/engines/script_engine.py` (confidence scoring)
- **Tests**: Test coherence scoring, reranking
- **Success Criteria**: Coherent hook-script pairs generated, reranking improves quality

#### Task 3.2: Pacing & Emotion Integration
- **Priority**: MEDIUM
- **Duration**: 2 days
- **Deliverables**:
  - [ ] Modify pacing engine to emotion-aware
    - Emotional peaks require shorter scenes
    - Emotional valleys can be longer
  - [ ] Implement visual overlap detection
    - Check if text overlay overlaps with video content
    - Shift overlay position if needed
  - [ ] Add local script editing capability
    - API endpoint: `PUT /v1/shorts/{id}/script`
    - Modify scene duration, content, tone
    - Re-validate and re-score
  - [ ] Create script preview (text only before video generation)
- **Files to Create/Modify**:
  - `app/engines/pacing.py` (emotion integration)
  - `app/media/text_overlay.py` (overlap detection)
  - `app/api/shorts_routes.py` (add script edit endpoint)
  - `app/orchestrator/service.py` (script validation on edit)
- **Tests**: Test pacing timing, overlay detection, script editing
- **Success Criteria**: Pacing adapts to emotion, overlays positioned correctly, script editing works

#### Task 3.3: Genre & Persona Expansion
- **Priority**: MEDIUM
- **Duration**: 2 days
- **Deliverables**:
  - [ ] Add 10+ new genres
    - productivity, gaming, fitness, education, lifestyle, wellness, tech, business, entertainment, social
  - [ ] Create genre-specific hooks
    - Hook templates tailored to each genre
    - Hook scoring weights adjusted per genre
  - [ ] Implement persona customization
    - Let creators define custom personas (name, traits, voice, style)
    - Save as profile for reuse
  - [ ] Create persona selector UI (frontend)
- **Files to Create/Modify**:
  - `app/core/genres.py` (extend with new genres)
  - `app/intelligence/personas.py` (custom persona support)
  - `app/api/persona_routes.py` (new - CRUD for personas)
- **Tests**: Test genre-specific hooks, custom personas
- **Success Criteria**: New genres available, persona customization working

---

### Week 10-11: Services Layer Refactoring

#### Task 3.4: Job Queue Modernization
- **Priority**: CRITICAL
- **Duration**: 4 days
- **Deliverables**:
  - [ ] Replace in-memory queue with Celery
    - Install Celery, Redis/RabbitMQ broker
    - Configure task serialization (JSON)
  - [ ] Implement distributed job queue
    - Video generation as Celery task
    - Batch processing as Celery task
    - Critic scoring as Celery task
  - [ ] Add job dependencies
    - Task A depends on Task B completion
    - Chain: script validation → video generation → thumbnail → export
  - [ ] Create job deduplication
    - Hash request payload
    - Return existing result if duplicate found
  - [ ] Implement dead letter queue
    - Jobs exceeding max retries go to DLQ
    - Separate DLQ monitoring and handling
  - [ ] Create job monitoring UI (backend)
- **Files to Create/Modify**:
  - `app/core/celery_app.py` (new)
  - `app/orchestrator/celery_tasks.py` (new)
  - `app/batch/celery_tasks.py` (new)
  - `app/orchestrator/job_deduplicator.py` (new)
  - `app/reliability/dead_letter_queue.py` (new)
  - `docker-compose.yml` (add Redis/RabbitMQ)
  - `app/api/job_queue_routes.py` (new - monitoring endpoints)
- **Tests**: Test Celery task execution, job dependencies, deduplication
- **Success Criteria**: Jobs processed via Celery, deduplication working, DLQ visible

#### Task 3.5: Advanced Batch Processing
- **Priority**: HIGH
- **Duration**: 3 days
- **Deliverables**:
  - [ ] Wrap batch operations in database transactions
    - All-or-nothing semantics
  - [ ] Implement batch result aggregation
    - Success count, failure breakdown
    - Error categorization (prompt error, API error, etc.)
  - [ ] Add batch-level retries
    - Exponential backoff
    - Jitter to avoid thundering herd
    - Max retry limit
  - [ ] Create batch progress tracking
    - Real-time progress: "3/10 videos generated"
    - ETA calculation
  - [ ] Implement batch cancellation
    - Mark as cancelled
    - Cancel in-flight jobs
  - [ ] Add batch cost tracking
    - Estimate cost before execution
    - Track actual cost after execution
- **Files to Create/Modify**:
  - `app/batch/models.py` (extend with progress, cost)
  - `app/batch/service.py` (transaction wrapping, progress)
  - `app/batch/result_aggregator.py` (new)
  - `app/batch/cost_estimator.py` (new - extend)
- **Tests**: Test transaction rollback, result aggregation, cost tracking
- **Success Criteria**: Batch operations atomic, progress tracked, costs estimated

#### Task 3.6: Media Services Robustness
- **Priority**: HIGH
- **Duration**: 2 days
- **Deliverables**:
  - [ ] Separate Veo failure types
    - Rate limit → backoff and retry
    - Timeout → fallback to slower method
    - API error → log and fail gracefully
    - Bad prompt → regenerate prompt and retry
  - [ ] Implement fallback video generation
    - If Veo unavailable, use simpler video generation (basic scene stitching)
    - Notify user of quality degradation
  - [ ] Optimize FFmpeg stitching
    - Parallel processing for multiple videos
    - Reuse cached transitions
  - [ ] Add video validation
    - Check output duration matches expected
    - Check frame rate, resolution match request
- **Files to Create/Modify**:
  - `app/media/video_service.py` (failure differentiation, fallback)
  - `app/media/ffmpeg_optimizer.py` (new)
  - `app/media/video_validator.py` (new)
- **Tests**: Test failure differentiation, fallback generation, video validation
- **Success Criteria**: Veo failures handled gracefully, fallback works, videos validated

---

### Week 12: API Contracts & Rate Limiting

#### Task 3.7: API Contract & Rate Limiting
- **Priority**: HIGH
- **Duration**: 3 days
- **Deliverables**:
  - [ ] Implement rate limiting
    - `@rate_limit(per_user=100/hour)` decorator
    - Per-endpoint configuration
    - Per-API-key configuration
  - [ ] Implement quota enforcement
    - Videos/month per tier (free, pro, enterprise)
    - API calls/month per tier
  - [ ] Create quota dashboard
    - Show current usage, remaining quota
    - Time to reset
  - [ ] Implement quota exceeded error
    - HTTP 429 status
    - Helpful message: "Quota exceeded. You have 5/100 videos this month."
  - [ ] Add quota alerts
    - Notify user when 80% of quota used
    - Notify when at limit
  - [ ] Create quota management endpoints
    - Check quota status
    - Request quota increase
- **Files to Create/Modify**:
  - `app/api/rate_limiter.py` (new)
  - `app/api/quota_manager.py` (new)
  - `app/api/middleware.py` (rate limiting middleware)
  - `app/api/quota_routes.py` (new)
  - `app/auth/models.py` (add quota fields)
- **Tests**: Test rate limiting, quota enforcement, quota alerts
- **Success Criteria**: Rate limiting enforced, quota tracking accurate, alerts sent

---

## Phase 4: Weeks 13-16 — Workflow Automation & Job Orchestration

### Week 13-14: Advanced Scheduling & Workflows

#### Task 4.1: Workflow Engine
- **Priority**: HIGH
- **Duration**: 3 days
- **Deliverables**:
  - [ ] Create workflow DAG system
    - Define workflows as DAGs (Directed Acyclic Graphs)
    - Support sequential and parallel tasks
  - [ ] Implement workflow examples
    - Generate Script → Approve → Generate Video → Export
    - Generate Script → Generate Video → Generate Thumbnail → Batch Export
  - [ ] Add workflow pause/resume/retry
    - Pause at specific step
    - Resume from paused step
    - Retry failed step with new parameters
  - [ ] Implement conditional logic
    - "If script score < 0.7, regenerate"
    - "If video duration > 35s, trim last scene"
  - [ ] Create workflow status tracking
    - Track each step completion
    - Show step duration, errors
- **Files to Create/Modify**:
  - `app/orchestrator/workflow.py` (new)
  - `app/orchestrator/workflow_executor.py` (new)
  - `app/orchestrator/workflow_validator.py` (new)
  - `app/api/workflow_routes.py` (new)
- **Tests**: Test workflow execution, conditional logic, pause/resume
- **Success Criteria**: Workflows execute correctly, conditionals work, status visible

#### Task 4.2: Schedule Persistence & UI
- **Priority**: MEDIUM
- **Duration**: 3 days
- **Deliverables**:
  - [ ] Migrate BatchSchedule to database
    - Add status, next_run_at, last_run_at fields
    - Implement change history (when was schedule modified)
  - [ ] Create scheduling API endpoints
    - GET /v1/schedules - list schedules
    - POST /v1/schedules - create schedule
    - PUT /v1/schedules/{id} - update
    - DELETE /v1/schedules/{id} - delete
    - POST /v1/schedules/{id}/test - dry run
  - [ ] Create frontend scheduling UI
    - Calendar view showing scheduled batches
    - Set frequency (daily, weekly, monthly, custom)
    - Set timezone
    - Test run before enabling
  - [ ] Add schedule notifications
    - Email when batch scheduled to run
    - Notification when batch completes
- **Files to Create/Modify**:
  - `app/scheduling/models.py` (database persistence)
  - `app/scheduling/service.py` (extend with database)
  - `app/api/schedule_routes.py` (extend with full CRUD)
  - `frontend/src/pages/Scheduling.tsx` (extend UI)
- **Tests**: Test schedule persistence, API endpoints, dry run
- **Success Criteria**: Schedules persistent, UI functional, dry run works

#### Task 4.3: Advanced Scheduling Features
- **Priority**: MEDIUM
- **Duration**: 2 days
- **Deliverables**:
  - [ ] Support cron expressions
    - Parse cron syntax (0 9 * * MON = Monday 9am)
    - Combine with timezone
  - [ ] Create schedule templates
    - "Weekly Monday/Wednesday"
    - "Monthly 1st and 15th"
    - "Daily at 9am"
    - Reuse for multiple batches
  - [ ] Implement schedule conflict detection
    - Don't start new batch if previous batch still running
    - Queue with max depth limit
  - [ ] Add schedule backtest
    - Show when schedule would have run in past
    - Verify cron expression correctness
- **Files to Create/Modify**:
  - `app/scheduling/cron_parser.py` (new)
  - `app/scheduling/schedule_templates.py` (new)
  - `app/scheduling/conflict_detector.py` (new)
  - `app/scheduling/backtest.py` (new)
- **Tests**: Test cron parsing, conflict detection, backtest
- **Success Criteria**: Cron expressions parsed, templates created, conflicts detected

---

### Week 15: Webhook & Event System

#### Task 4.4: Webhook System
- **Priority**: MEDIUM
- **Duration**: 2 days
- **Deliverables**:
  - [ ] Create webhook infrastructure
    - Webhook model: url, events, secret, active
    - Webhook delivery model: timestamp, status, retry_count, response
  - [ ] Implement event publishing
    - Job events: job_created, job_started, job_completed, job_failed
    - Batch events: batch_created, batch_started, batch_completed
    - Critic events: score_calculated
  - [ ] Add webhook retry logic
    - Exponential backoff (1s, 2s, 4s, 8s, 16s)
    - Max 5 retries
    - Dead letter tracking
  - [ ] Implement webhook signing
    - HMAC-SHA256 signature in header
    - Webhook receiver can verify signature
  - [ ] Create webhook management UI
    - Create webhook URL
    - Select events
    - View delivery history
    - Test webhook
- **Files to Create/Modify**:
  - `app/events/models.py` (new - Webhook, WebhookDelivery)
  - `app/events/publisher.py` (new)
  - `app/events/webhook_dispatcher.py` (new)
  - `app/api/webhook_routes.py` (new)
  - `frontend/src/pages/Webhooks.tsx` (new)
- **Tests**: Test event publishing, webhook delivery, retry logic
- **Success Criteria**: Webhooks delivered reliably, signing works, UI functional

#### Task 4.5: Background Task Management
- **Priority**: MEDIUM
- **Duration**: 2 days
- **Deliverables**:
  - [ ] Move long-running tasks to background
    - Video generation → Celery task
    - Thumbnail creation → Celery task
    - Batch processing → Celery task
  - [ ] Implement SLA enforcement
    - Video generation must complete within 5 minutes
    - Batch of 10 videos must complete within 30 minutes
    - If exceeded, timeout and mark as failed
  - [ ] Add progress tracking
    - "Video generation 60% complete"
    - Sent via WebSocket or polling endpoint
  - [ ] Create task monitoring UI
    - Show running tasks
    - Show completed tasks with duration
- **Files to Create/Modify**:
  - `app/orchestrator/celery_tasks.py` (extend with progress)
  - `app/api/task_routes.py` (new - progress endpoints)
  - `frontend/src/components/TaskProgress.tsx` (new)
- **Tests**: Test SLA enforcement, progress tracking
- **Success Criteria**: Long tasks run in background, SLA enforced, progress visible

---

### Week 16: Batch Optimization & Reporting

#### Task 4.6: Batch Cost Analysis
- **Priority**: MEDIUM
- **Duration**: 2 days
- **Deliverables**:
  - [ ] Track costs per batch
    - LLM token costs
    - Veo video generation costs
    - Storage costs
    - Total batch cost
  - [ ] Implement cost estimation
    - ML model to predict cost before execution
    - Accuracy tracking (predicted vs actual)
  - [ ] Create cost breakdown visualization
    - Pie chart: LLM (40%), Video (50%), Storage (10%)
    - Line chart: cost trend over time
  - [ ] Implement budget alerts
    - Notify if batch cost exceeds estimate by >10%
    - Warn if total account spend approaching limit
- **Files to Create/Modify**:
  - `app/billing/cost_tracker.py` (new)
  - `app/billing/cost_estimator.py` (extend)
  - `app/api/cost_routes.py` (new)
  - `frontend/src/pages/CostAnalysis.tsx` (new)
- **Tests**: Test cost tracking, estimation accuracy
- **Success Criteria**: Costs tracked accurately, estimates within 10%, alerts sent

#### Task 4.7: Automated Reporting
- **Priority**: MEDIUM
- **Duration**: 2 days
- **Deliverables**:
  - [ ] Generate weekly batch reports
    - Batch summary (videos generated, success rate)
    - Cost breakdown
    - Top performing videos
    - Trends (success rate improving/declining)
  - [ ] Email reports to users
    - Automated email scheduler
    - HTML formatted report
  - [ ] Create insights from reports
    - "Reels format has 20% higher success rate than Shorts"
    - "Script length 25s outperforms 30s"
  - [ ] Make reports accessible in UI
    - Show past reports
    - Download as PDF
- **Files to Create/Modify**:
  - `app/reporting/report_generator.py` (new)
  - `app/reporting/email_sender.py` (new)
  - `app/api/report_routes.py` (new)
  - `frontend/src/pages/Reports.tsx` (new)
- **Tests**: Test report generation, email sending
- **Success Criteria**: Reports generated, emailed, accessible in UI

---

## Phase 5: Weeks 17-20 — Quality & Content Optimization

### Week 17: Critic & Scoring Modernization

#### Task 5.1: ML-Based Scoring
- **Priority**: HIGH
- **Duration**: 3 days
- **Deliverables**:
  - [ ] Collect engagement data
    - Watch time, replays, shares, likes per generated video
    - Correlate with critic scores
  - [ ] Build correlation analysis
    - Which critic dimensions predict engagement
    - Adjust weights based on correlation (e.g., if hook score has 0.3 correlation with watch time, reduce weight)
  - [ ] Create scoring leaderboard
    - Top-performing hook patterns
    - Top-performing script structures
    - Top-performing genres
  - [ ] Implement score validation
    - Compare critic scores against actual performance
    - Flag if critic scores diverge from engagement
- **Files to Create/Modify**:
  - `app/intelligence/engagement_collector.py` (new)
  - `app/intelligence/correlation_analyzer.py` (new)
  - `app/intelligence/scoring_leaderboard.py` (new)
  - `app/critic/service.py` (adjust weights based on correlation)
- **Tests**: Test correlation analysis, leaderboard ranking
- **Success Criteria**: Correlations identified, weights adjusted, leaderboard functional

#### Task 5.2: Score Persistence & Versioning
- **Priority**: MEDIUM
- **Duration**: 2 days
- **Deliverables**:
  - [ ] Cache critic scores in database
    - Avoid re-evaluation of same script
    - Significant token savings
  - [ ] Implement score versioning
    - Track score history as prompt changes
    - Compare scores: "v1.0 avg=0.65 vs v1.1 avg=0.72"
  - [ ] Add score explainability
    - Show which dimensions drove score
    - Show what would improve score
- **Files to Create/Modify**:
  - `app/critic/models.py` (extend with versioning)
  - `app/critic/cache_manager.py` (new)
  - `app/critic/score_explainer.py` (new)
- **Tests**: Test score caching, versioning
- **Success Criteria**: Scores cached, versioning tracked, explanations generated

---

### Week 18: Content A/B Testing Framework

#### Task 5.3: Variation Generation
- **Priority**: MEDIUM
- **Duration**: 2 days
- **Deliverables**:
  - [ ] Expand variation generation strategies
    - hook_focused, tone_varied, structure_varied, angle_varied, length_varied, mixed
    - Add 4 more: pacing_varied, emotion_varied, visual_varied, niche_varied
  - [ ] Create 3-5 variation generation per request
    - API: `POST /v1/variations/generate` with variation_type
    - Return array of variations with scores
  - [ ] Implement variation comparison UI
    - Side-by-side hook/script comparison
    - Score breakdown per variation
  - [ ] Add one-click select
    - Select favorite variation
    - Proceed to video generation
- **Files to Create/Modify**:
  - `app/intelligence/variations.py` (extend strategies)
  - `app/api/variation_routes.py` (extend)
  - `frontend/src/pages/VariationComparison.tsx` (new)
- **Tests**: Test variation generation, comparison, selection
- **Success Criteria**: Variations generated, UI shows comparison, selection works

#### Task 5.4: Preference Learning
- **Priority**: MEDIUM
- **Duration**: 2 days
- **Deliverables**:
  - [ ] Track variation selection history
    - Which variations creators selected
    - Which led to better engagement
  - [ ] Build creator preference profiles
    - Prefers short/long scripts
    - Prefers certain tone (educational vs entertaining)
    - Prefers certain hook patterns
  - [ ] Auto-generate matching preferences
    - Use preference profile for future generations
    - Bias toward creator's preferred style
  - [ ] Create preference dashboard
    - Show inferred preferences
    - Let creators adjust preferences manually
- **Files to Create/Modify**:
  - `app/intelligence/preference_learner.py` (new)
  - `app/intelligence/creator_profile.py` (new)
  - `app/api/preference_routes.py` (new)
  - `frontend/src/pages/Preferences.tsx` (new)
- **Tests**: Test preference learning, auto-generation with preferences
- **Success Criteria**: Preferences learned, auto-generation uses preferences, dashboard functional

---

### Week 19: Validation & Error Recovery

#### Task 5.5: Pre-Generation Validation
- **Priority**: MEDIUM
- **Duration**: 2 days
- **Deliverables**:
  - [ ] Validate content constraints
    - Content length within bounds
    - Audience compatibility with platform
    - Platform feature availability (e.g., TikTok don't support 1:1)
  - [ ] Create validation error messages with suggestions
    - "Script too long for TikTok (currently 28s), recommend 20-25s"
    - "Audience 'Gen-Z Provocation' may face restrictions on Instagram, consider 'Gen-Z Engaging'"
  - [ ] Implement pre-flight checks
    - API quota available
    - Balance sufficient
  - [ ] Create dry-run endpoint
    - Run validation without generating video
    - Show recommendations
- **Files to Create/Modify**:
  - `app/api/validators.py` (extend)
  - `app/api/validation_routes.py` (new)
  - `app/orchestrator/service.py` (pre-flight checks)
- **Tests**: Test validation rules, suggestions
- **Success Criteria**: Validation blocks bad requests, suggestions helpful

#### Task 5.6: Failure Recovery UI
- **Priority**: MEDIUM
- **Duration**: 2 days
- **Deliverables**:
  - [ ] Show failed generation with reason
    - "Hook generation failed: LLM timeout after 30s"
    - "Video generation failed: Veo API rate limited, retry in 2 minutes"
  - [ ] Provide one-click retries
    - Retry specific step (regenerate hook, fix script, retry video)
    - Retry with different parameters
  - [ ] Add manual override
    - Creator can force-approve low-scoring content
    - Confirm override action
  - [ ] Track manual overrides
    - Log when creator overrides critic score
    - Analyze if overrides lead to good content
- **Files to Create/Modify**:
  - `app/api/recovery_routes.py` (new)
  - `frontend/src/components/FailureRecovery.tsx` (new)
  - `app/observability/override_tracker.py` (new)
- **Tests**: Test recovery UI, override tracking
- **Success Criteria**: Failed generations show reason, retries work, overrides tracked

---

### Week 20: Content Performance Insights

#### Task 5.7: Advanced Analytics
- **Priority**: MEDIUM
- **Duration**: 3 days
- **Deliverables**:
  - [ ] Create heatmap of hook patterns
    - Best-performing patterns by audience/genre
    - Visualization: audience x hook_pattern with performance metric
  - [ ] Show emotion curve effectiveness
    - Which curves lead to higher watch time
    - Optimize curve templates based on data
  - [ ] Visualize genre trends
    - Genre performance over time
    - Emerging trends, declining genres
  - [ ] Create content comparison
    - Side-by-side performance metrics
    - A/B test comparison
  - [ ] Implement recommendation engine
    - "Try curiosity_gap hook - works well with your audience"
    - "Reels format outperforms Shorts for travel content"
- **Files to Create/Modify**:
  - `app/analytics/pattern_analyzer.py` (new)
  - `app/analytics/trend_analyzer.py` (new)
  - `app/analytics/recommendation_engine.py` (new)
  - `frontend/src/pages/InsightsAnalytics.tsx` (new)
  - `frontend/src/pages/Recommendations.tsx` (new)
- **Tests**: Test analytics calculations, recommendation accuracy
- **Success Criteria**: Analytics visualized, trends identified, recommendations generated

---

## Phase 6: Weeks 21-24 — Frontend Modernization

### Week 21-22: API Client & Form Layer

#### Task 6.1: Type-Safe API Client
- **Priority**: HIGH
- **Duration**: 3 days
- **Deliverables**:
  - [ ] Create `app/api/schemas.py` with all request/response types
    - Autogenerate from OpenAPI schema
  - [ ] Create `frontend/src/lib/api-client.ts`
    - Typed endpoints with request/response types
    - Auto-generated from OpenAPI (use OpenAPI Generator)
  - [ ] Implement HTTP interceptors
    - Add authorization header to all requests
    - Add request ID header for tracing
    - Handle 401 (auto-refresh token), 429 (rate limit), 5xx (retry)
  - [ ] Implement error mapping
    - API error codes → user-friendly messages
  - [ ] Add request/response logging
    - Log all API calls to console (dev mode only)
- **Files to Create/Modify**:
  - `frontend/src/lib/api-client.ts` (new)
  - `frontend/src/lib/api-types.ts` (new - generated)
  - `frontend/src/lib/http-client.ts` (new - interceptors)
  - `frontend/src/lib/error-handler.ts` (new)
- **Tests**: Test API client, interceptors, error handling
- **Success Criteria**: API client generated, types correct, interceptors working

#### Task 6.2: Form Validation & State Management
- **Priority**: HIGH
- **Duration**: 2 days
- **Deliverables**:
  - [ ] Integrate React Hook Form + Zod
    - Typed form validation
    - Real-time validation feedback
  - [ ] Create reusable form components
    - TextInput, Select, DatePicker, Checkbox, FileUpload
    - Error display, loading states
  - [ ] Build form compositions
    - LoginForm, SignupForm, CreateBatchForm, ScheduleForm
  - [ ] Add inline validation errors
    - Show errors as user types
    - Clear errors when fixed
  - [ ] Implement form auto-save
    - Save form state to localStorage
    - Restore on page reload
- **Files to Create/Modify**:
  - `frontend/src/lib/form-schemas.ts` (new - Zod schemas)
  - `frontend/src/components/forms/FormInput.tsx` (new)
  - `frontend/src/components/forms/FormSelect.tsx` (new)
  - `frontend/src/components/forms/FormDatePicker.tsx` (new)
  - `frontend/src/pages/LoginNew.tsx` (refactor using forms)
  - `frontend/src/pages/SignupNew.tsx` (refactor using forms)
- **Tests**: Test form validation, submission, auto-save
- **Success Criteria**: Forms validated, errors clear, auto-save working

#### Task 6.3: Auth Flow Improvements
- **Priority**: MEDIUM
- **Duration**: 2 days
- **Deliverables**:
  - [ ] Add password reset via email
    - Request endpoint: `POST /v1/auth/password-reset`
    - Reset link with token sent via email
    - Reset form with new password
  - [ ] Implement OAuth (Google login optional)
    - Redirect to Google OAuth
    - Create user on first login
    - Link OAuth account to existing user
  - [ ] Add token refresh logic
    - Automatically refresh before token expiry
    - Transparent to user
  - [ ] Implement logout
    - Clear tokens, redirect to login
  - [ ] Add "Remember me" option
    - Store refresh token in localStorage (secure storage)
    - Auto-login if token valid
- **Files to Create/Modify**:
  - `frontend/src/lib/auth-context.ts` (extend)
  - `frontend/src/pages/PasswordReset.tsx` (new)
  - `frontend/src/pages/OAuth.tsx` (new)
  - `frontend/src/hooks/useAuthRefresh.ts` (new)
  - `app/api/auth_routes.py` (extend with password reset, OAuth)
- **Tests**: Test password reset, OAuth flow, token refresh
- **Success Criteria**: Password reset works, OAuth integrated, token refresh transparent

---

### Week 23: Component Library & Styling

#### Task 6.4: Complete Component Library
- **Priority**: HIGH
- **Duration**: 3 days
- **Deliverables**:
  - [ ] Build missing components
    - JobCard (show job status, progress, errors)
    - BatchCard (show batch summary, cost, success rate)
    - ScriptEditor (edit script with live preview)
    - ScriptViewer (read-only script display with timing)
    - HookSelector (preview 3-5 hooks, select best)
    - VideoPreview (stream generated videos inline)
    - ScheduleForm (create/edit schedules)
    - WebhookForm (create/manage webhooks)
  - [ ] Add pagination, filtering, sorting
    - List pages for jobs, batches, videos
    - Sort by date, status, score, cost
    - Filter by status, date range, genre
  - [ ] Implement infinite scroll
    - Load more content as user scrolls
  - [ ] Add skeleton loaders
    - Placeholder while data loading
- **Files to Create/Modify**:
  - `frontend/src/components/JobCard.tsx` (new)
  - `frontend/src/components/BatchCard.tsx` (new)
  - `frontend/src/components/ScriptEditor.tsx` (new)
  - `frontend/src/components/ScriptViewer.tsx` (new)
  - `frontend/src/components/HookSelector.tsx` (new)
  - `frontend/src/components/VideoPreview.tsx` (new)
  - `frontend/src/components/ScheduleForm.tsx` (new)
  - `frontend/src/components/WebhookForm.tsx` (new)
  - `frontend/src/components/Pagination.tsx` (new)
  - `frontend/src/hooks/usePagination.ts` (new)
  - `frontend/src/hooks/useFilters.ts` (new)
- **Tests**: Test component rendering, interactions
- **Success Criteria**: All components built, pagination works, infinite scroll working

#### Task 6.5: Advanced UI Features
- **Priority**: MEDIUM
- **Duration**: 2 days
- **Deliverables**:
  - [ ] Implement optimistic updates
    - Show content immediately on user action
    - Sync with server, handle conflicts
  - [ ] Add drag-and-drop
    - Reorder script scenes
    - Drag hooks to select
  - [ ] Implement live preview
    - Change script scene timing → preview updates
    - Change hook → preview hook effect
  - [ ] Add comparison view
    - Side-by-side script comparison
    - Diff highlighting
  - [ ] Create keyboard shortcuts
    - Cmd+S = Save
    - Cmd+Enter = Generate
    - Escape = Close modal
- **Files to Create/Modify**:
  - `frontend/src/hooks/useOptimisticUpdate.ts` (new)
  - `frontend/src/components/DragDropEditor.tsx` (new)
  - `frontend/src/components/ComparisonView.tsx` (new)
  - `frontend/src/hooks/useKeyboardShortcuts.ts` (new)
- **Tests**: Test optimistic updates, drag-drop, keyboard shortcuts
- **Success Criteria**: Optimistic updates work, drag-drop functional, shortcuts working

#### Task 6.6: Dark Mode & Responsive Design
- **Priority**: MEDIUM
- **Duration**: 2 days
- **Deliverables**:
  - [ ] Implement theme toggle
    - Light/dark mode toggle in header
    - Persist preference to localStorage
  - [ ] Update color scheme for dark mode
    - Use TailwindCSS dark mode classes
    - Test all components in dark mode
  - [ ] Add responsive design
    - Mobile breakpoints (sm, md, lg, xl)
    - Mobile-first design approach
    - Test on mobile/tablet viewports
  - [ ] Implement mobile navigation
    - Hamburger menu for mobile
    - Touch-friendly buttons
  - [ ] Add print styles
    - Print-friendly views for reports
- **Files to Create/Modify**:
  - `frontend/src/hooks/useTheme.ts` (new)
  - `frontend/src/components/ThemeToggle.tsx` (new)
  - `frontend/src/index.css` (dark mode styles)
  - `frontend/tailwind.config.js` (update color scheme)
  - All pages (add responsive classes)
- **Tests**: Test theme toggle, responsive layouts, mobile viewport
- **Success Criteria**: Dark mode works, responsive on mobile, colors correct

---

### Week 24: Analytics & Monitoring Dashboard

#### Task 6.7: Metrics Visualization
- **Priority**: MEDIUM
- **Duration**: 2 days
- **Deliverables**:
  - [ ] Create main metrics dashboard
    - Job success rate (line chart over time)
    - Average video quality score
    - Cost trends (line chart)
    - API token usage (bar chart)
  - [ ] Add metric filters
    - Date range picker
    - Platform filter (YouTube, Instagram, TikTok)
    - Genre filter
    - Status filter (completed, failed, pending)
  - [ ] Implement real-time metrics
    - WebSocket updates for live metrics
    - Or polling every 30 seconds
  - [ ] Add metric comparisons
    - Compare this month vs last month
    - Show trend (up/down)
  - [ ] Export metrics
    - Export as CSV, JSON, PDF
- **Files to Create/Modify**:
  - `frontend/src/pages/Dashboard.tsx` (extend)
  - `frontend/src/components/MetricsCard.tsx` (new)
  - `frontend/src/components/MetricsChart.tsx` (new)
  - `frontend/src/components/MetricsFilter.tsx` (new)
  - `frontend/src/hooks/useMetrics.ts` (new)
- **Tests**: Test metrics calculation, filtering, real-time updates
- **Success Criteria**: Metrics visualized, filters working, real-time updates visible

#### Task 6.8: Content Performance Dashboard
- **Priority**: MEDIUM
- **Duration**: 2 days
- **Deliverables**:
  - [ ] Create content performance page
    - List generated videos with thumbnails
    - Show performance metrics (views, watch time, engagement rate)
    - Sort by performance
  - [ ] Implement video playback
    - Play video inline
    - Show video metadata (hook, script, genre, audience)
  - [ ] Add comparison view
    - Select 2-3 videos to compare
    - Show performance side-by-side
    - Highlight differences (hook style, script length, genre)
  - [ ] Create recommendation engine UI
    - "Videos like this perform well..."
    - Show recommended content type
  - [ ] Implement engagement heatmap
    - Show when users drop off in videos
    - Scene-level performance
- **Files to Create/Modify**:
  - `frontend/src/pages/ContentPerformance.tsx` (new)
  - `frontend/src/components/VideoCard.tsx` (new)
  - `frontend/src/components/PerformanceComparison.tsx` (new)
  - `frontend/src/components/RecommendationCard.tsx` (new)
  - `frontend/src/hooks/usePerformanceMetrics.ts` (new)
- **Tests**: Test performance metrics, comparison, recommendations
- **Success Criteria**: Performance dashboard visible, comparisons work, recommendations shown

---

## Phase 7: Weeks 25-28 — Advanced Features & Integration

### Week 25: Creator Tools & Editing

#### Task 7.1: Script Editor UI
- **Priority**: MEDIUM
- **Duration**: 2 days
- **Deliverables**:
  - [ ] Build rich script editor
    - WYSIWYG editor mode (visual editing)
    - Markdown mode
    - Raw text mode
  - [ ] Add line-by-line timing adjustment
    - Click scene to adjust duration
    - Visual timeline shows duration
    - Drag to change timing
  - [ ] Implement hook selector
    - Preview 3-5 hooks side-by-side
    - One-click select favorite
    - Show hook score/confidence
  - [ ] Add script preview
    - Show how script will render as video
    - Scene breakdown with timing
  - [ ] Create undo/redo
    - Track edits, undo/redo history
- **Files to Create/Modify**:
  - `frontend/src/components/ScriptEditor.tsx` (extend)
  - `frontend/src/components/HookSelector.tsx` (extend)
  - `frontend/src/components/ScriptTimeline.tsx` (new)
  - `frontend/src/hooks/useScriptEdit.ts` (new)
  - `frontend/src/hooks/useUndoRedo.ts` (new)
- **Tests**: Test editor functionality, timing adjustment, hook selection
- **Success Criteria**: Editor functional, timing adjustable, hooks selectable

#### Task 7.2: Brand Kit Integration
- **Priority**: MEDIUM
- **Duration**: 2 days
- **Deliverables**:
  - [ ] Let creators upload brand kit
    - Logo image
    - Color palette (primary, secondary, accent)
    - Fonts (heading, body)
    - Brand guidelines (PDF)
  - [ ] Auto-apply brand kit to videos
    - Logo overlay on video
    - Color scheme for text overlays
    - Font matching
  - [ ] Implement brand kit versioning
    - Create versions of brand kit
    - Switch between versions for different campaigns
  - [ ] Create brand kit preview
    - Show how brand kit looks on video
    - Preview all colors, fonts
  - [ ] Add brand kit validation
    - Ensure colors meet accessibility standards
    - Check font legibility
- **Files to Create/Modify**:
  - `app/brand/models.py` (extend)
  - `app/brand/service.py` (auto-apply)
  - `frontend/src/pages/BrandKits.tsx` (extend)
  - `frontend/src/components/BrandKitUpload.tsx` (new)
  - `frontend/src/components/BrandKitPreview.tsx` (new)
- **Tests**: Test brand kit upload, application, versioning
- **Success Criteria**: Brand kits uploadable, auto-applied to videos, versions tracked

---

### Week 26: Multi-User & Collaboration

#### Task 7.3: Team Workspace
- **Priority**: MEDIUM
- **Duration**: 3 days
- **Deliverables**:
  - [ ] Allow agency to invite team members
    - Roles: Editor, Approver, Viewer, Admin
    - Permission matrix (who can do what)
  - [ ] Implement content approval workflow
    - Editor submits content
    - Approver reviews and approves/rejects
    - Approved content auto-published or queued
  - [ ] Add commenting system
    - Comment on scripts, videos
    - @mention team members
    - Reply to comments
  - [ ] Create activity feed
    - Show team activity (who edited what, when)
    - Notification on comments, approvals
  - [ ] Implement access control
    - Creator sees only own content by default
    - Admin sees all content
    - Shared projects visible to team
- **Files to Create/Modify**:
  - `app/auth/models.py` (extend with roles, permissions)
  - `app/auth/rbac.py` (new - role-based access control)
  - `app/collaboration/models.py` (new - workspace, roles)
  - `app/collaboration/service.py` (new)
  - `app/comments/models.py` (new)
  - `app/comments/service.py` (new)
  - `frontend/src/pages/Workspace.tsx` (new)
  - `frontend/src/components/TeamInvite.tsx` (new)
  - `frontend/src/components/ApprovalWorkflow.tsx` (new)
  - `frontend/src/components/CommentThread.tsx` (new)
- **Tests**: Test role assignment, permissions, approval workflow, comments
- **Success Criteria**: Team workspace functional, roles enforced, approval workflow working

#### Task 7.4: Bulk Operations
- **Priority**: MEDIUM
- **Duration**: 2 days
- **Deliverables**:
  - [ ] Bulk apply brand kit
    - Select multiple videos
    - Apply brand kit to all at once
    - Queue for processing
  - [ ] Bulk export to multiple platforms
    - Select videos and platforms
    - Export to YouTube, Instagram, TikTok simultaneously
  - [ ] Bulk reschedule batches
    - Select batches
    - Change schedule (date, time, recurrence)
  - [ ] Bulk delete/archive
    - Select content
    - Delete or archive
  - [ ] Create bulk operation progress
    - Show number of items processed
    - Time remaining estimate
- **Files to Create/Modify**:
  - `app/batch/bulk_operations.py` (new)
  - `app/api/bulk_routes.py` (new)
  - `frontend/src/hooks/useBulkSelect.ts` (new)
  - `frontend/src/components/BulkOperationPanel.tsx` (new)
- **Tests**: Test bulk operations, progress tracking
- **Success Criteria**: Bulk operations working, progress visible

---

### Week 27: Export & Integration

#### Task 7.5: Advanced Export
- **Priority**: MEDIUM
- **Duration**: 2 days
- **Deliverables**:
  - [ ] Add export templates
    - "YouTube Optimized" (longer videos, custom thumbnails)
    - "Reels Optimized" (square videos, captions)
    - "TikTok Optimized" (vertical, trending sounds)
  - [ ] Implement subtitle/caption generation
    - Auto-generate captions from script
    - Auto-translate to multiple languages
    - Burn captions into video or provide SRT file
  - [ ] Add watermark/branding options
    - Logo watermark position
    - Text watermark
    - Channel branding
  - [ ] Create export history
    - Show past exports, dates, destinations
    - Re-export to new platform
- **Files to Create/Modify**:
  - `app/exports/models.py` (extend)
  - `app/exports/templates.py` (new)
  - `app/media/caption_generator.py` (new)
  - `app/api/export_routes.py` (extend)
  - `frontend/src/components/ExportWizard.tsx` (new)
- **Tests**: Test export templates, caption generation, watermarking
- **Success Criteria**: Export templates working, captions generated, watermarks applied

#### Task 7.6: Platform Integration
- **Priority**: MEDIUM
- **Duration**: 3 days
- **Deliverables**:
  - [ ] YouTube integration
    - Auto-upload videos
    - Set title, description, tags, playlist
    - Enable monetization if applicable
    - Share to YouTube community
  - [ ] Instagram integration
    - Auto-post to Reels, Feed, Stories
    - Set captions, hashtags
    - Schedule posts
  - [ ] TikTok integration
    - Auto-post videos
    - Add hashtags, description
    - Schedule posting
  - [ ] Create integration settings UI
    - Authorize platforms (OAuth)
    - View connected accounts
    - Disconnect account
  - [ ] Implement posting queue
    - Queue videos for posting
    - Post at specified time
    - Retry on failure
- **Files to Create/Modify**:
  - `app/integrations/youtube_integration.py` (extend)
  - `app/integrations/instagram_integration.py` (extend)
  - `app/integrations/tiktok_integration.py` (extend)
  - `app/integrations/posting_queue.py` (new)
  - `app/api/integration_routes.py` (new)
  - `frontend/src/pages/Integrations.tsx` (new)
  - `frontend/src/components/PlatformAuthFlow.tsx` (new)
- **Tests**: Test platform integrations, posting queue
- **Success Criteria**: Platforms integrated, auto-posting working

---

### Week 28: Cost Optimization & Analytics

#### Task 7.7: Cost Prediction & Budgeting
- **Priority**: MEDIUM
- **Duration**: 2 days
- **Deliverables**:
  - [ ] Build ML cost prediction model
    - Features: video duration, platform, quality, audio language
    - Target: predicted cost
    - Training on historical data
  - [ ] Create budget limit feature
    - User sets monthly budget
    - Warn at 50%, 80%, 100%
    - Block new requests if over budget
  - [ ] Implement cost optimization tips
    - "Batch 3 similar videos to reuse prompts (save 10%)"
    - "Use mobile resolution for 30% cost savings"
  - [ ] Create billing alerts
    - Email alerts on budget milestones
    - Dashboard alert badge
  - [ ] Show cost per video breakdown
    - LLM cost, video generation cost, storage cost
- **Files to Create/Modify**:
  - `app/billing/cost_predictor.py` (new - ML model)
  - `app/billing/budget_manager.py` (new)
  - `app/api/budget_routes.py` (new)
  - `frontend/src/pages/Billing.tsx` (extend)
  - `frontend/src/components/BudgetAlert.tsx` (new)
- **Tests**: Test cost prediction accuracy, budget enforcement
- **Success Criteria**: Cost predictions within 10%, budget enforced, tips generated

#### Task 7.8: Performance Analytics
- **Priority**: MEDIUM
- **Duration**: 2 days
- **Deliverables**:
  - [ ] Track generation parameters impact
    - Which hook lengths perform best
    - Which script lengths perform best
    - Which tones perform best per audience
  - [ ] Auto-tune recommendations
    - "For travel content, 3-5s hooks perform best"
    - "Gen-Z audience prefers under 20s scripts"
  - [ ] Create A/B test results dashboard
    - Show active A/B tests
    - Results (winner, significance, p-value)
    - Auto-stop tests when significance reached
  - [ ] Implement winner selection
    - Auto-apply winner (best hook style) to future content
    - Option to manually select winner
  - [ ] Create parameter optimization report
    - Monthly trends in optimal parameters
    - Recommendations based on trends
- **Files to Create/Modify**:
  - `app/analytics/parameter_impact_analyzer.py` (new)
  - `app/analytics/ab_test_manager.py` (new)
  - `app/analytics/auto_tuning.py` (new)
  - `frontend/src/pages/Analytics.tsx` (extend)
  - `frontend/src/components/ABTestDashboard.tsx` (new)
- **Tests**: Test parameter impact analysis, A/B test winner detection
- **Success Criteria**: Parameter impacts identified, A/B tests working, tuning recommendations generated

---

## Phase 8: Weeks 29-32 — Infrastructure & DevOps

### Week 29: Containerization & Orchestration

#### Task 8.1: Docker Optimization
- **Priority**: MEDIUM
- **Duration**: 2 days
- **Deliverables**:
  - [ ] Create multi-stage Dockerfile
    - Stage 1: builder (compile, install dependencies)
    - Stage 2: runtime (minimal image with only runtime dependencies)
    - Final image size < 300MB
  - [ ] Add health checks
    - `/health` endpoint for container health
    - Startup probe (wait for app ready)
    - Liveness probe (restart if unhealthy)
    - Readiness probe (only send traffic if ready)
  - [ ] Create docker-compose for local dev
    - Backend service
    - PostgreSQL service
    - Redis service
    - Celery worker service
    - Prometheus service
  - [ ] Optimize for caching
    - Layer dependencies separately from code
    - Cache pip dependencies
  - [ ] Document Docker usage
    - How to build image
    - How to run container
    - How to run multi-container setup
- **Files to Create/Modify**:
  - `Dockerfile` (multi-stage, optimized)
  - `docker-compose.yml` (extend)
  - `.dockerignore` (new)
  - `README.md` (Docker setup instructions)
- **Tests**: Test Docker build, container startup, health checks
- **Success Criteria**: Docker image builds, container starts, health checks pass

#### Task 8.2: Kubernetes Setup (Optional, if needed for scale)
- **Priority**: MEDIUM
- **Duration**: 3 days
- **Deliverables**:
  - [ ] Create k8s manifests
    - Deployment (backend, celery-worker)
    - Service (expose backend, celery)
    - ConfigMap (environment variables)
    - Secret (API keys, database password)
    - PersistentVolumeClaim (database storage)
  - [ ] Implement Horizontal Pod Autoscaling
    - Scale based on CPU utilization (70%)
    - Min 2 replicas, max 10 replicas
  - [ ] Set up ingress
    - Route traffic to backend service
    - TLS termination
  - [ ] Create monitoring/logging setup
    - Prometheus for metrics
    - ELK/Loki for logs
  - [ ] Document k8s deployment
    - How to deploy to GKE/EKS/AKS
    - How to scale
- **Files to Create/Modify**:
  - `k8s/backend-deployment.yaml` (new)
  - `k8s/backend-service.yaml` (new)
  - `k8s/celery-deployment.yaml` (new)
  - `k8s/configmap.yaml` (new)
  - `k8s/secrets.yaml` (new)
  - `k8s/hpa.yaml` (new)
  - `k8s/ingress.yaml` (new)
  - `README-K8S.md` (new)
- **Tests**: Test k8s manifest syntax, deployment simulation
- **Success Criteria**: K8s manifests valid, deployment works, autoscaling configurable

---

### Week 30: Database Optimization

#### Task 8.3: PostgreSQL Migration
- **Priority**: HIGH
- **Duration**: 3 days
- **Deliverables**:
  - [ ] Migrate SQLite to PostgreSQL
    - Export SQLite data
    - Create PostgreSQL schema
    - Import data
    - Verify data integrity
  - [ ] Create/optimize indexes
    - Index on user_id, batch_id, job_id, status
    - Composite indexes on frequently joined columns
    - Analyze query plans
  - [ ] Implement connection pooling
    - PgBouncer (external) or SQLAlchemy pool (built-in)
    - Connection pool size: 10-20
    - Idle timeout: 5 minutes
  - [ ] Set up automatic backups
    - Daily backups to cloud storage (S3, GCS)
    - Point-in-time recovery capability
    - Backup retention: 30 days
  - [ ] Create migration guide
    - How to migrate from SQLite to PostgreSQL
    - Downtime windows
    - Rollback procedure
- **Files to Create/Modify**:
  - `app/core/database.py` (PostgreSQL config, pooling)
  - `migrations/versions/001_initial_postgresql_schema.sql` (new)
  - `scripts/migrate_sqlite_to_postgres.py` (new)
  - `docker-compose.yml` (add PostgreSQL service)
  - `README.md` (migration instructions)
- **Tests**: Test PostgreSQL setup, data integrity, backup/restore
- **Success Criteria**: PostgreSQL working, indexes optimized, backups automated

#### Task 8.4: Query Optimization
- **Priority**: MEDIUM
- **Duration**: 2 days
- **Deliverables**:
  - [ ] Profile slow queries
    - Use `pg_stat_statements` to find slow queries
    - Identify missing indexes
    - Identify N+1 queries
  - [ ] Optimize queries
    - Add indexes based on analysis
    - Rewrite inefficient queries
    - Add query result caching (Redis)
  - [ ] Implement query caching strategy
    - Cache frequently accessed data (user profiles, brand kits)
    - Cache invalidation on updates
    - TTL: 1 hour by default
  - [ ] Monitor query performance
    - Create dashboard showing query latency
    - Alert on slow queries (> 1 second)
- **Files to Create/Modify**:
  - `app/core/query_cache.py` (new)
  - `app/observability/query_monitor.py` (new)
  - `scripts/analyze_queries.py` (new)
- **Tests**: Test query optimization, cache effectiveness
- **Success Criteria**: Slow queries identified and optimized, caching working

---

### Week 31: Log Aggregation & Tracing

#### Task 8.5: Distributed Tracing
- **Priority**: MEDIUM
- **Duration**: 2 days
- **Deliverables**:
  - [ ] Implement OpenTelemetry
    - Instrument FastAPI endpoints
    - Instrument database calls
    - Instrument external API calls
  - [ ] Integrate Jaeger for visualization
    - Deploy Jaeger collector
    - Send traces from app
    - View traces in Jaeger UI
  - [ ] Track latency across services
    - Breakdown: LLM call (2s) → Veo call (8s) → FFmpeg (3s)
    - Identify bottlenecks
  - [ ] Add custom spans
    - Track major operations (batch processing, video generation)
    - Track errors and exceptions
  - [ ] Create performance dashboard
    - Show service dependency graph
    - Show latency percentiles (p50, p95, p99) per service
- **Files to Create/Modify**:
  - `app/observability/tracing.py` (new - OpenTelemetry setup)
  - `app/api/main.py` (instrument endpoints)
  - `docker-compose.yml` (add Jaeger service)
- **Tests**: Test trace collection, Jaeger visualization
- **Success Criteria**: Traces collected, Jaeger visualizing, bottlenecks identified

#### Task 8.6: Log Aggregation & Analysis
- **Priority**: MEDIUM
- **Duration**: 2 days
- **Deliverables**:
  - [ ] Set up ELK stack or cloud logging
    - Option A: Self-hosted ELK (Elasticsearch, Logstash, Kibana)
    - Option B: GCP Cloud Logging
    - Option C: Datadog
  - [ ] Create log parsing rules
    - Extract fields from log messages
    - Normalize timestamps
  - [ ] Build log dashboards
    - Error rate over time
    - Log volume by service
    - Top error types
  - [ ] Configure log-based alerts
    - Alert on error rate spike (> 5%)
    - Alert on specific error codes
    - Alert on missing expected logs
  - [ ] Implement log retention
    - Archive old logs after 90 days
    - Delete after 1 year
- **Files to Create/Modify**:
  - `app/observability/log_setup.py` (structured logging)
  - `elastic/logstash.conf` (new - if self-hosted)
  - `docker-compose.yml` (add ELK services if needed)
- **Tests**: Test log aggregation, dashboard queries
- **Success Criteria**: Logs aggregated, dashboards working, alerts firing

---

### Week 32: Load Testing & Performance Tuning

#### Task 8.7: Load Testing
- **Priority**: HIGH
- **Duration**: 2 days
- **Deliverables**:
  - [ ] Set up load testing tool
    - Locust (Python) or K6 (JavaScript)
  - [ ] Create load test scenarios
    - Scenario 1: 100 concurrent users, 5 requests/user
    - Scenario 2: 500 concurrent users, 10 requests/user
    - Scenario 3: Spike test (100 → 1000 users in 30 seconds)
  - [ ] Run load tests
    - Measure response times, error rates
    - Identify bottlenecks
  - [ ] Create load test report
    - Response time distribution (p50, p95, p99)
    - Error breakdown
    - Resource usage (CPU, memory, disk)
  - [ ] Document findings
    - Bottlenecks identified
    - Recommendations for optimization
- **Files to Create/Modify**:
  - `load_tests/locustfile.py` (new)
  - `load_tests/scenarios.py` (new)
  - `load_tests/report.md` (new - results)
- **Tests**: Run load tests, verify results
- **Success Criteria**: Load tests run successfully, bottlenecks identified, report generated

#### Task 8.8: Performance Optimization
- **Priority**: HIGH
- **Duration**: 3 days
- **Deliverables**:
  - [ ] Implement caching layer
    - Redis for session/data cache
    - Cache LLM outputs (prompt → response)
    - Cache critic scores
    - TTL: 1 hour default, configurable per cache key
  - [ ] Batch LLM requests
    - Group multiple short requests into single API call
    - Significant token savings
  - [ ] Optimize FFmpeg video stitching
    - Use hardware acceleration (GPU) if available
    - Parallel processing for multiple videos
    - Reduce codec conversion overhead
  - [ ] Implement lazy loading
    - Load batch items on demand (pagination)
    - Load video previews asynchronously
  - [ ] Add compression
    - Gzip responses
    - Compress video transcoding
  - [ ] Tune connection pools
    - Database: 20 connections
    - Redis: 10 connections
    - API client: 50 connections
- **Files to Create/Modify**:
  - `app/core/cache_manager.py` (new)
  - `app/media/ffmpeg_optimizer.py` (extend)
  - `app/engines/llm.py` (batching)
  - `app/core/database.py` (pool tuning)
- **Tests**: Benchmark before/after optimization
- **Success Criteria**: Response times reduced by 30%+, resource usage optimized

---

## Phase 9: Weeks 33-36 — Security & Compliance

### Week 33: Security Hardening

#### Task 9.1: Secrets Management
- **Priority**: CRITICAL
- **Duration**: 2 days
- **Deliverables**:
  - [ ] Migrate to secrets manager
    - Use GCP Secret Manager, AWS Secrets Manager, or HashiCorp Vault
    - Remove all hardcoded secrets
  - [ ] Implement automatic secret rotation
    - Monthly rotation schedule
    - Automatic key regeneration
    - Zero-downtime rotation (support both old and new)
  - [ ] Audit secrets usage
    - Log all secret access
    - Alert on unusual access patterns
  - [ ] Create secret management guide
    - How to add new secrets
    - How to rotate secrets
    - How to handle secret leaks
- **Files to Create/Modify**:
  - `app/core/secrets_manager.py` (new)
  - `app/core/config.py` (use secrets manager)
  - `scripts/rotate_secrets.py` (new)
  - `README-SECURITY.md` (secrets management guide)
- **Tests**: Test secret rotation, access logging
- **Success Criteria**: No hardcoded secrets, rotation working

#### Task 9.2: Input Validation & Sanitization
- **Priority**: HIGH
- **Duration**: 2 days
- **Deliverables**:
  - [ ] Validate all API inputs
    - Content length bounds
    - Allowed characters (prevent injection)
    - Type validation
  - [ ] Sanitize user content
    - Escape HTML
    - Remove script tags
    - Prevent SQL injection
    - Prevent prompt injection (for LLM calls)
  - [ ] Implement request size limits
    - Max request body: 10MB
    - Max batch size: 1000 items
  - [ ] Create input validation middleware
    - Apply to all endpoints
    - Clear error messages
- **Files to Create/Modify**:
  - `app/api/validators.py` (extend)
  - `app/api/sanitizers.py` (new)
  - `app/api/middleware.py` (validation middleware)
- **Tests**: Test validation, sanitization, injection prevention
- **Success Criteria**: Invalid inputs blocked, sanitization working

#### Task 9.3: CSRF & Security Headers
- **Priority**: MEDIUM
- **Duration**: 1 day
- **Deliverables**:
  - [ ] Add CSRF protection
    - Generate CSRF tokens
    - Validate on form submission
  - [ ] Add security headers
    - Content-Security-Policy
    - X-Frame-Options: DENY
    - X-Content-Type-Options: nosniff
    - Strict-Transport-Security
  - [ ] Implement SameSite cookies
    - Prevent cross-site request forgery
  - [ ] Add rate limiting per IP
    - Prevent brute force attacks
- **Files to Create/Modify**:
  - `app/api/middleware.py` (security headers, CSRF)
- **Tests**: Test CSRF protection, headers present
- **Success Criteria**: CSRF tokens working, security headers present

---

### Week 34: API Security & Authorization

#### Task 9.4: Fine-Grained Permissions
- **Priority**: HIGH
- **Duration**: 3 days
- **Deliverables**:
  - [ ] Implement role-based access control (RBAC)
    - Roles: ADMIN, MANAGER, EDITOR, VIEWER
    - Permissions per role (can_create_batch, can_approve, etc.)
  - [ ] Add resource-level permissions
    - Creator can only access own batches/videos
    - Team member can access shared batches
    - Admin can access all
  - [ ] Implement permission decorators
    - `@require_permission("can_create_batch")`
    - `@require_resource_permission("batch", "edit")`
  - [ ] Create audit logging
    - Log all permission checks
    - Log denied access attempts
  - [ ] Add delegation
    - Admin can delegate permissions to others
    - Audit trail for delegations
- **Files to Create/Modify**:
  - `app/auth/models.py` (extend with permissions)
  - `app/auth/rbac.py` (extend)
  - `app/auth/decorators.py` (new - permission decorators)
  - `app/observability/audit_log.py` (extend)
- **Tests**: Test permission enforcement, delegation
- **Success Criteria**: Permissions enforced, audit logs present

#### Task 9.5: API Security
- **Priority**: HIGH
- **Duration**: 2 days
- **Deliverables**:
  - [ ] Implement request signing
    - HMAC-SHA256 signature in header
    - Prevent API tampering
  - [ ] Add API key rotation
    - Generate new keys with old ones still valid
    - Grace period: 30 days
    - Revoke old keys after grace period
  - [ ] Implement API key restrictions
    - Restrict to specific IP addresses
    - Restrict to specific endpoints
  - [ ] Add CORS whitelist
    - Remove wildcard
    - Specific origin list from config
  - [ ] Implement webhook signing
    - Sign webhook payloads
    - Receiver can verify signature
- **Files to Create/Modify**:
  - `app/api/request_signing.py` (new)
  - `app/auth/service.py` (key rotation)
  - `app/events/webhook_dispatcher.py` (signing)
  - `app/core/config.py` (CORS origins)
- **Tests**: Test request signing, API key rotation, CORS validation
- **Success Criteria**: Signing working, key rotation functional, CORS restricted

---

### Week 35: Data Privacy & Compliance

#### Task 9.6: GDPR & Data Privacy
- **Priority**: MEDIUM
- **Duration**: 2 days
- **Deliverables**:
  - [ ] Implement data retention policies
    - Auto-delete logs after 90 days
    - Auto-delete old batches after 1 year
    - Configurable per data type
  - [ ] Add data export functionality
    - Creator can download all their data
    - Format: ZIP with JSON/CSV files
    - Includes: scripts, videos, logs, metrics
  - [ ] Implement right-to-be-forgotten
    - API: `DELETE /v1/user/data`
    - Deletes all creator data
    - Keeps minimal audit logs
  - [ ] Create privacy policy generator
    - Document data processing
    - Document third-party integrations
  - [ ] Add consent management
    - Track user consent for data processing
    - Allow opt-out of certain features
- **Files to Create/Modify**:
  - `app/privacy/data_retention.py` (new)
  - `app/privacy/data_export.py` (new)
  - `app/privacy/data_deletion.py` (new)
  - `app/api/privacy_routes.py` (new)
  - `scripts/data_retention_cleanup.py` (new)
- **Tests**: Test data export, deletion, retention cleanup
- **Success Criteria**: Data export working, deletion working, retention cleanup scheduled

#### Task 9.7: Compliance & Auditing
- **Priority**: MEDIUM
- **Duration**: 2 days
- **Deliverables**:
  - [ ] Create audit logs for sensitive operations
    - User creation, API key generation
    - Permission changes, data exports
    - Login, logout, access denials
  - [ ] Document data flow
    - Where data comes from
    - Where it goes
    - Who has access
    - How long it's retained
  - [ ] Create compliance checklist
    - GDPR, SOC2, HIPAA (if needed)
    - Self-assessment questions
    - Evidence collection
  - [ ] Set up compliance monitoring
    - Automated checks for policy violations
    - Alerts on non-compliance
  - [ ] Create incident response plan
    - Data breach procedure
    - Communication template
    - Recovery procedure
- **Files to Create/Modify**:
  - `app/observability/audit_log.py` (extend)
  - `docs/COMPLIANCE.md` (new)
  - `docs/DATA_FLOW.md` (new)
  - `docs/INCIDENT_RESPONSE.md` (new)
- **Tests**: Test audit logging, compliance checks
- **Success Criteria**: Audit logs complete, compliance checklist created

---

### Week 36: Penetration Testing & Hardening

#### Task 9.8: Security Testing
- **Priority**: MEDIUM
- **Duration**: 3 days
- **Deliverables**:
  - [ ] Conduct penetration testing
    - Use OWASP ZAP or Burp Suite
    - Test for SQL injection, XSS, CSRF
    - Test for authentication bypass
    - Test for authorization issues
  - [ ] Check SSL/TLS configuration
    - Use SSL Labs: get A+ grade
    - Check certificate validity
    - Check TLS version (1.2+)
  - [ ] Test rate limiting effectiveness
    - Verify brute force protection
    - Verify DDoS protection
  - [ ] Test API security
    - Test request signing
    - Test API key validation
  - [ ] Create penetration test report
    - Findings, severity, remediation
    - Pass/fail for each check
- **Files to Create/Modify**:
  - `docs/SECURITY_TESTING.md` (new - report)
  - `docs/REMEDIATION.md` (new - fix tracking)
- **Tests**: Run penetration tests, verify fixes
- **Success Criteria**: Penetration test passed, SSL grade A+, all findings remediated

#### Task 9.9: Security Documentation & Training
- **Priority**: MEDIUM
- **Duration**: 1 day
- **Deliverables**:
  - [ ] Create security documentation
    - Threat model (what we protect against)
    - Security best practices
    - Incident response procedure
    - Secret management guide
  - [ ] Implement developer security training
    - OWASP Top 10
    - Common vulnerabilities
    - Secure coding practices
  - [ ] Create security checklist
    - Before-deployment checklist
    - Code review security checklist
  - [ ] Set up security scanning
    - Auto-scan dependencies for vulnerabilities
    - Fail build if critical vulnerability found
- **Files to Create/Modify**:
  - `docs/SECURITY.md` (new)
  - `docs/THREAT_MODEL.md` (new)
  - `.github/workflows/security-scan.yml` (new)
  - `SECURITY_CHECKLIST.md` (new)
- **Tests**: Security scanning in CI/CD
- **Success Criteria**: Documentation complete, scanning automated

---

## Phase 10: Weeks 37-40 — Scalability & Production Readiness

### Week 37-38: Advanced Caching & CDN

#### Task 10.1: Multi-Level Caching
- **Priority**: MEDIUM
- **Duration**: 3 days
- **Deliverables**:
  - [ ] Implement Redis caching
    - Session caching
    - Data caching (user profiles, batch info)
    - LLM output caching (prompt → response)
    - Critic score caching
  - [ ] Add HTTP caching headers
    - Cache-Control headers for static content
    - ETag for change detection
    - Last-Modified for conditional requests
  - [ ] Implement query result caching
    - Cache frequent queries
    - Invalidate on data update
  - [ ] Create cache invalidation strategy
    - Time-based expiration (TTL)
    - Event-based invalidation
    - Manual invalidation endpoints
  - [ ] Monitor cache effectiveness
    - Cache hit rate, miss rate
    - Cache memory usage
    - Create cache metrics dashboard
- **Files to Create/Modify**:
  - `app/core/cache_manager.py` (extend)
  - `app/core/http_cache.py` (new)
  - `app/observability/cache_metrics.py` (new)
- **Tests**: Test cache hits/misses, invalidation
- **Success Criteria**: Cache hit rate > 80%, memory usage reasonable

#### Task 10.2: CDN Integration
- **Priority**: MEDIUM
- **Duration**: 2 days
- **Deliverables**:
  - [ ] Integrate CDN (CloudFront, Cloudflare, etc.)
    - Serve generated videos from CDN
    - Cache static assets (images, fonts)
    - Reduce load on origin server
  - [ ] Implement cache invalidation
    - Invalidate on video update
    - Batch invalidation for multiple files
  - [ ] Set up CDN authentication
    - Signed URLs for private videos
    - Prevent direct URL access
  - [ ] Monitor CDN performance
    - Cache hit rate, bandwidth saved
    - Origin bandwidth reduction
  - [ ] Configure origin failover
    - If primary origin down, use secondary
    - Health checks
- **Files to Create/Modify**:
  - `app/media/cdn_manager.py` (new)
  - `app/api/cdn_routes.py` (new)
  - `app/core/config.py` (CDN config)
- **Tests**: Test CDN integration, signed URLs
- **Success Criteria**: Videos served from CDN, cache working, bandwidth reduced

---

### Week 39: Cost Optimization & Billing

#### Task 10.3: Billing System
- **Priority**: MEDIUM
- **Duration**: 3 days
- **Deliverables**:
  - [ ] Implement metered billing
    - Charge per video generated
    - Charge per platform export
    - Charge per API call
    - Different rates per plan (free, pro, enterprise)
  - [ ] Create usage dashboard
    - Show costs by category (LLM, Veo, storage)
    - Show cumulative costs
    - Show projected bill
  - [ ] Implement prepaid credits system
    - User purchases credits upfront
    - Credits consumed on usage
    - Show credit balance
  - [ ] Create billing history
    - Show past invoices
    - Download invoice as PDF
  - [ ] Implement payment retry
    - Retry failed charges
    - Notification on failure
  - [ ] Add cost estimation
    - Estimate cost before generating batch
    - Show estimated cost to user
- **Files to Create/Modify**:
  - `app/billing/models.py` (extend with metering)
  - `app/billing/metering.py` (new - usage tracking)
  - `app/billing/invoice_generator.py` (new)
  - `app/api/billing_routes.py` (extend)
  - `frontend/src/pages/Billing.tsx` (extend)
- **Tests**: Test metering, invoice generation
- **Success Criteria**: Billing working, invoices generated, credits tracked

#### Task 10.4: Cost Reduction Strategies
- **Priority**: MEDIUM
- **Duration**: 2 days
- **Deliverables**:
  - [ ] Identify expensive operations
    - LLM calls cost breakdown
    - Veo video generation costs
    - Storage costs
  - [ ] Implement cost reduction
    - Prompt caching (reuse prompts)
    - Batch API requests
    - Use cheaper models when possible
    - Reuse generated assets (thumbnails, captions)
  - [ ] Implement auto-scaling
    - Run expensive jobs during off-peak hours
    - Lower pricing during off-peak
  - [ ] Create cost alerts
    - Notify if spending approaching budget
    - Notify on unusual spending pattern
  - [ ] Provide cost optimization tips
    - "Batching 5 videos saves 10% on LLM costs"
    - "Using lower resolution saves 20% on video costs"
- **Files to Create/Modify**:
  - `app/billing/cost_optimizer.py` (extend)
  - `app/billing/alert_manager.py` (new)
  - `app/api/cost_routes.py` (extend)
- **Tests**: Test cost optimization, alerts
- **Success Criteria**: Cost optimizations implemented, alerts sent

---

### Week 40: Production Launch & SLA

#### Task 10.5: Pre-Production Checklist
- **Priority**: CRITICAL
- **Duration**: 2 days
- **Deliverables**:
  - [ ] Database migration verification
    - Data integrity checks
    - Backup verification
    - Restore procedure tested
  - [ ] Load testing validation
    - 1K concurrent users passed
    - Latency acceptable (p99 < 10s)
    - Error rate < 1%
  - [ ] Security audit
    - Penetration test passed
    - Compliance checklist complete
    - No hardcoded secrets
  - [ ] Monitoring & alerting
    - All metrics collected
    - Dashboards created
    - Alerts configured
  - [ ] Documentation complete
    - API documentation
    - Deployment guide
    - Runbooks for common failures
  - [ ] Disaster recovery tested
    - Backup/restore procedure works
    - Can recover within RTO
  - [ ] Create go/no-go checklist
    - Sign-off from engineering, ops, product
- **Files to Create/Modify**:
  - `docs/PRODUCTION_CHECKLIST.md` (new)
  - `docs/DEPLOYMENT_GUIDE.md` (new)
  - `docs/RUNBOOKS.md` (new)
  - `docs/DISASTER_RECOVERY.md` (new)
- **Tests**: Run through checklist items
- **Success Criteria**: All checklist items passed, sign-offs obtained

#### Task 10.6: SLA & Monitoring
- **Priority**: MEDIUM
- **Duration**: 2 days
- **Deliverables**:
  - [ ] Define SLAs
    - Uptime: 99.9% (52 minutes/month downtime)
    - Video generation latency: < 5 minutes p99
    - API response time: < 2s p99
    - Error rate: < 0.5%
  - [ ] Create runbooks
    - Database connection pool exhausted
    - LLM API rate limit hit
    - Veo API unavailable
    - High error rate detected
  - [ ] Set up incident response process
    - Alerting → Page on-call engineer
    - Diagnosis → Mitigation → Post-mortem
    - Blameless post-mortems
  - [ ] Create incident severity levels
    - SEV1: Service down (> 30 min)
    - SEV2: Degraded service (> 5 min)
    - SEV3: Minor issue (< 5 min)
  - [ ] Set up on-call rotation
    - Weekly rotation
    - On-call engineer primary + secondary
  - [ ] Create communication plan
    - Status page for incidents
    - Email/Slack notifications
- **Files to Create/Modify**:
  - `docs/SLA.md` (new)
  - `docs/RUNBOOKS/` folder (new)
  - `docs/INCIDENT_RESPONSE.md` (new)
  - `docs/COMMUNICATION_PLAN.md` (new)
- **Tests**: Test incident response, communication
- **Success Criteria**: SLAs defined, runbooks created, incident process documented

---

## Summary & Timeline

| Phase | Weeks | Focus | Deliverables |
|-------|-------|-------|--------------|
| **1** | 1-4 | Foundation | Exception handling, persistence, database, auth security |
| **2** | 5-8 | Quality | Prompt management, testing, monitoring infrastructure |
| **3** | 9-12 | Content & Services | Script coherence, batch transactions, rate limiting |
| **4** | 13-16 | Automation | Workflows, scheduling, webhooks, cost tracking |
| **5** | 17-20 | Quality Content | ML scoring, A/B testing, performance insights |
| **6** | 21-24 | Frontend | API client, forms, components, analytics dashboard |
| **7** | 25-28 | Advanced Features | Script editor, team collaboration, platform integrations |
| **8** | 29-32 | Infrastructure | Docker, PostgreSQL, tracing, performance tuning |
| **9** | 33-36 | Security | Secrets, CSRF, RBAC, GDPR, penetration testing |
| **10** | 37-40 | Production | CDN, billing, SLA, launch preparation |

---

## Success Metrics

- **Code Quality**: 85%+ test coverage, 0 critical security issues
- **Performance**: p99 latency < 10s for batch creation, < 5s for API calls
- **Reliability**: 99.9% uptime, < 0.5% error rate
- **User Experience**: < 2s page load time, 0 accessibility violations
- **Cost Efficiency**: 30% reduction in API costs vs current baseline
- **Developer Experience**: Time-to-first-contribution < 2 hours

---
