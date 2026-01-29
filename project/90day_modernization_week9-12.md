# 90-Day Modernization Plan: Week 9-12
## Phase 3: Content Engine & Services Enhancement (Mar 25 - Apr 21, 2026)

---

## Week 9: Script-Hook Coherence & Pacing (Mar 25-31)

### 🎯 North Star
By end of Week 9:
> **Script-hook coherence score 90%+, pacing algorithms optimized, emotional arc tracking enabled**

---

### 📋 Day-by-Day Breakdown

#### **DAY 41 (Mon, Mar 24) — Coherence Framework Design**

**Morning (9am-12pm):**
- [ ] Design coherence system
  - [ ] Create `app/engines/coherence_engine.py`
  - [ ] Plan scoring mechanism (0-100 scale)
  - [ ] Design validation rules
  - [ ] Document coherence heuristics

**Afternoon (1pm-5pm):**
- [ ] Create coherence metrics
  - [ ] Hook-script semantic overlap (use embeddings)
  - [ ] Tone consistency (hook to script)
  - [ ] Narrative continuity (hook -> script progression)
  - [ ] Brand voice alignment

**Deliverables:**
- [ ] Coherence engine architecture
- [ ] Scoring mechanism design doc
- [ ] 5+ coherence rules defined

---

#### **DAY 42 (Tue, Mar 25) — Hook-Script Validation**

**Morning (9am-12pm):**
- [ ] Implement coherence checks
  - [ ] Hook emotion extraction (Vertex AI)
  - [ ] Script emotion extraction
  - [ ] Compare emotional trajectories
  - [ ] Flag mismatches

**Afternoon (1pm-5pm):**
- [ ] Create validation endpoint
  - [ ] POST `/api/validate/coherence`
  - [ ] Input: hook_id, script_id
  - [ ] Output: score, issues, suggestions
  - [ ] Add to API documentation

**Deliverables:**
- [ ] Coherence validation logic
- [ ] `/api/validate/coherence` endpoint
- [ ] Tests with 20+ test cases

---

#### **DAY 43 (Wed, Mar 26) — Pacing Analysis Engine**

**Morning (9am-12pm):**
- [ ] Design pacing system
  - [ ] Create `app/engines/pacing_engine.py`
  - [ ] Plan pacing metrics: beat timing, rhythm, cadence
  - [ ] Design optimal pacing ranges per genre
  - [ ] Plan user tension/excitement curve

**Afternoon (1pm-5pm):**
- [ ] Implement pacing analysis
  - [ ] Extract story beats from script
  - [ ] Calculate beat timing
  - [ ] Score pacing (0-100)
  - [ ] Compare to genre benchmarks

**Deliverables:**
- [ ] Pacing engine implementation
- [ ] Genre pacing benchmarks database
- [ ] Pacing score calculation

---

#### **DAY 44 (Thu, Mar 27) — Emotional Arc Tracking**

**Morning (9am-12pm):**
- [ ] Implement emotion tracking
  - [ ] Create `app/engines/emotional_arc.py`
  - [ ] Extract emotion at each story beat
  - [ ] Track emotion trajectory
  - [ ] Identify emotional peaks and valleys

**Afternoon (1pm-5pm):**
- [ ] Create arc visualization
  - [ ] Store arc data in database
  - [ ] Create JSON response with arc data
  - [ ] Add to dashboard (frontend)
  - [ ] Plot emotional curve

**Deliverables:**
- [ ] Emotional arc tracking system
- [ ] Arc visualization data API
- [ ] Dashboard showing emotional curves

---

#### **DAY 45 (Fri, Mar 28) — Genre & Persona Expansion**

**Morning (9am-12pm):**
- [ ] Expand genre database
  - [ ] Add 10+ new genres (comedy, thriller, drama, etc.)
  - [ ] Define genre characteristics
  - [ ] Define pacing ranges per genre
  - [ ] Define tone/emotion profiles

**Afternoon (1pm-5pm):**
- [ ] Expand persona system
  - [ ] Add 15+ new personas (influencer, educator, entertainer, etc.)
  - [ ] Define persona voice markers
  - [ ] Define persona tone ranges
  - [ ] Add to prompt system

**Deliverables:**
- [ ] Genre database expanded (20+ genres)
- [ ] Persona database expanded (20+ personas)
- [ ] Genre-persona matching rules

---

## Week 10: Job Queue Modernization (Apr 1-7)

### 🎯 North Star
By end of Week 10:
> **Celery-Redis queue operational, failed job retry strategy implemented, job visibility 100%**

---

### 📋 Day-by-Day Breakdown

#### **DAY 46 (Mon, Mar 31) — Celery Setup & Configuration**

**Morning (9am-12pm):**
- [ ] Initialize Celery
  - [ ] Create `app/queue/celery_app.py`
  - [ ] Configure Redis broker
  - [ ] Set up task base classes
  - [ ] Configure task routing

**Afternoon (1pm-5pm):**
- [ ] Configure task queue
  - [ ] Create separate queues: default, critical, batch
  - [ ] Set worker concurrency settings
  - [ ] Configure time limits (30m default)
  - [ ] Add to docker-compose

**Deliverables:**
- [ ] Celery configured
- [ ] Redis broker running
- [ ] Task routing configured

---

#### **DAY 47 (Tue, Apr 1) — Task Definition & Refactoring**

**Morning (9am-12pm):**
- [ ] Define async tasks
  - [ ] Create `app/queue/tasks/generation.py` (Vertex AI calls)
  - [ ] Create `app/queue/tasks/media.py` (Veo, TTS, Imagen)
  - [ ] Create `app/queue/tasks/processing.py` (batch, export)
  - [ ] Add task signatures and documentation

**Afternoon (1pm-5pm):**
- [ ] Refactor existing code
  - [ ] Replace blocking calls with Celery tasks
  - [ ] Update orchestrator to queue jobs
  - [ ] Update batch processor to use queue
  - [ ] Maintain backward compatibility

**Deliverables:**
- [ ] 15+ Celery tasks defined
- [ ] Orchestrator using Celery
- [ ] All existing features working via queue

---

#### **DAY 48 (Wed, Apr 2) — Retry Strategy & Error Handling**

**Morning (9am-12pm):**
- [ ] Implement retry logic
  - [ ] Create `app/queue/retry_strategy.py`
  - [ ] Exponential backoff: 60s, 5m, 30m, 2h
  - [ ] Max retries: 5
  - [ ] Circuit breaker pattern for repeated failures

**Afternoon (1pm-5pm):**
- [ ] Implement dead-letter queue
  - [ ] Tasks that fail after retries → DLQ
  - [ ] Manual review mechanism
  - [ ] Alerts on DLQ items
  - [ ] Admin UI for retry/discard

**Deliverables:**
- [ ] Retry strategy implemented
- [ ] Dead-letter queue functional
- [ ] DLQ monitoring alerts

---

#### **DAY 49 (Thu, Apr 3) — Job State Management & Tracking**

**Morning (9am-12pm):**
- [ ] Implement job state tracking
  - [ ] Create `app/queue/job_state.py`
  - [ ] States: pending, executing, completed, failed, retrying
  - [ ] Store state in database
  - [ ] Add state transition audit log

**Afternoon (1pm-5pm):**
- [ ] Create visibility endpoints
  - [ ] GET `/api/jobs/{job_id}/status`
  - [ ] GET `/api/jobs/{job_id}/history`
  - [ ] GET `/api/jobs?status=running&limit=100`
  - [ ] WebSocket for real-time updates (optional)

**Deliverables:**
- [ ] Job state tracking system
- [ ] Visibility APIs
- [ ] Real-time status updates

---

#### **DAY 50 (Fri, Apr 4) — Queue Monitoring & Dashboard**

**Morning (9am-12pm):**
- [ ] Create queue monitoring
  - [ ] Prometheus metrics for Celery
  - [ ] Track: task count, duration, failures
  - [ ] Queue depth monitoring

**Afternoon (1pm-5pm):**
- [ ] Create admin dashboard
  - [ ] View queue stats
  - [ ] View active tasks
  - [ ] View failed tasks
  - [ ] Trigger manual retries

**Deliverables:**
- [ ] Celery metrics exposed
- [ ] Admin dashboard (React)
- [ ] Manual retry UI

---

## Week 11: Batch Processing Modernization (Apr 8-14)

### 📋 Day-by-Day Breakdown

#### **DAY 51 (Mon, Apr 7) — Batch Transactional Guarantees**

**Morning (9am-12pm):**
- [ ] Design transaction wrapper
  - [ ] Create `app/batch/transaction_manager.py`
  - [ ] Plan: atomicity, consistency, isolation, durability
  - [ ] Design rollback mechanism
  - [ ] Plan savepoint strategy

**Afternoon (1pm-5pm):**
- [ ] Implement batch transactions
  - [ ] Wrap batch operations in DB transactions
  - [ ] Rollback on any failure
  - [ ] Store batch state after each step
  - [ ] Add transaction logging

**Deliverables:**
- [ ] Transaction manager implementation
- [ ] Batch operations transactional
- [ ] Rollback tests (15+ cases)

---

#### **DAY 52 (Tue, Apr 8) — Batch Checkpointing**

**Morning (9am-12pm):**
- [ ] Implement checkpointing
  - [ ] Create `app/batch/checkpoint.py`
  - [ ] Save state after each significant step
  - [ ] Allow resume from checkpoint
  - [ ] Support batch pause/resume

**Afternoon (1pm-5pm):**
- [ ] Implement resumable batches
  - [ ] Detect interrupted batches
  - [ ] Resume from last checkpoint
  - [ ] Skip already-processed items
  - [ ] Test with simulated failures

**Deliverables:**
- [ ] Checkpoint system implemented
- [ ] Resume from checkpoint working
- [ ] Skip-already-processed logic

---

#### **DAY 53 (Wed, Apr 9) — Idempotency Keys**

**Morning (9am-12pm):**
- [ ] Implement idempotency
  - [ ] Create `app/batch/idempotency.py`
  - [ ] Generate idempotency keys (UUIDs)
  - [ ] Store request-response pairs
  - [ ] Deduplicate requests

**Afternoon (1pm-5pm):**
- [ ] Apply idempotency
  - [ ] Wrap all batch operations
  - [ ] Ensure exactly-once processing
  - [ ] Return cached response if duplicate
  - [ ] Test with network failures

**Deliverables:**
- [ ] Idempotency key system
- [ ] Request deduplication working
- [ ] Cache cleanup mechanism

---

#### **DAY 54 (Thu, Apr 10) — Batch Progress & Reporting**

**Morning (9am-12pm):**
- [ ] Implement progress tracking
  - [ ] Create `app/batch/progress.py`
  - [ ] Track items completed, failed, remaining
  - [ ] Calculate ETA based on velocity
  - [ ] Store progress in database

**Afternoon (1pm-5pm):**
- [ ] Create progress APIs
  - [ ] GET `/api/batches/{batch_id}/progress`
  - [ ] Return: completion %, ETA, current item
  - [ ] WebSocket for real-time progress
  - [ ] Email notifications at milestones

**Deliverables:**
- [ ] Progress tracking system
- [ ] Progress API endpoints
- [ ] Real-time WebSocket updates
- [ ] Milestone notifications

---

#### **DAY 55 (Fri, Apr 11) — Batch Error Analysis**

**Morning (9am-12pm):**
- [ ] Create error analysis
  - [ ] Aggregate errors by type, code
  - [ ] Track error rates per item
  - [ ] Identify problematic patterns
  - [ ] Generate error report

**Afternoon (1pm-5pm):**
- [ ] Create recovery recommendations
  - [ ] Suggest manual fixes for common errors
  - [ ] Flag items for manual review
  - [ ] Create error triage dashboard
  - [ ] Document error codes

**Deliverables:**
- [ ] Error analysis system
- [ ] Error triage dashboard
- [ ] Recovery recommendations
- [ ] Error code documentation

---

## Week 12: Advanced Rate Limiting & Service Contracts (Apr 15-21)

### 📋 Day-by-Day Breakdown

#### **DAY 56 (Mon, Apr 14) — Sliding Window Rate Limiting**

**Morning (9am-12pm):**
- [ ] Design advanced rate limiting
  - [ ] Create `app/core/rate_limiting.py`
  - [ ] Implement sliding window algorithm
  - [ ] Support multiple rate windows (60s, 1h, 1d)
  - [ ] Per-user, per-API, per-IP buckets

**Afternoon (1pm-5pm):**
- [ ] Implement Redis-backed limiter
  - [ ] Store window state in Redis
  - [ ] Atomic window checks
  - [ ] Efficient cleanup of old windows
  - [ ] Support burst allowances

**Deliverables:**
- [ ] Rate limiter implementation
- [ ] Multiple window types
- [ ] Redis backend working

---

#### **DAY 57 (Tue, Apr 15) — Token Bucket Quota System**

**Morning (9am-12pm):**
- [ ] Implement token bucket algorithm
  - [ ] Create `app/core/quota_system.py`
  - [ ] Define quota pools: video_minutes, api_calls, storage_gb
  - [ ] Track consumption vs limits
  - [ ] Refill schedules

**Afternoon (1pm-5pm):**
- [ ] Implement quota enforcement
  - [ ] Check quota before operations
  - [ ] Deduct on operation completion
  - [ ] Handle quota exceeded scenarios
  - [ ] Plan upgrades/rollover

**Deliverables:**
- [ ] Quota system implementation
- [ ] Multiple quota types
- [ ] Quota enforcement in operations

---

#### **DAY 58 (Wed, Apr 16) — Service Contracts & SLAs**

**Morning (9am-12pm):**
- [ ] Define service contracts
  - [ ] Create `app/contracts/service_contracts.py`
  - [ ] Define: Vertex AI response time, Veo generation time
  - [ ] Define: database latency SLAs
  - [ ] Define: API availability targets

**Afternoon (1pm-5pm):**
- [ ] Implement SLA monitoring
  - [ ] Track metrics vs SLAs
  - [ ] Alert on SLA violations
  - [ ] Generate SLA reports
  - [ ] Document in API contracts

**Deliverables:**
- [ ] Service contracts defined
- [ ] SLA monitoring implemented
- [ ] Contract violations detected

---

#### **DAY 59 (Thu, Apr 17) — Graceful Degradation**

**Morning (9am-12pm):**
- [ ] Design degradation strategy
  - [ ] Create `app/core/graceful_degradation.py`
  - [ ] Define fallback modes per service
  - [ ] Plan reduced-feature operation
  - [ ] Support for maintenance windows

**Afternoon (1pm-5pm):**
- [ ] Implement fallbacks
  - [ ] Fallback: Veo unavailable → Imagen or cached video
  - [ ] Fallback: Vertex AI slow → Use simpler model
  - [ ] Fallback: Database slow → Use cached responses
  - [ ] Test each fallback scenario

**Deliverables:**
- [ ] Fallback mechanisms implemented
- [ ] Graceful degradation working
- [ ] Fallback tests (10+ scenarios)

---

#### **DAY 60 (Fri, Apr 18) — Phase 3 Validation & Integration**

**Morning (9am-12pm):**
- [ ] Run integration tests
  - [ ] All coherence tests passing
  - [ ] Queue operations working end-to-end
  - [ ] Batch processing transactional
  - [ ] Rate limiting enforced

**Afternoon (1pm-5pm):**
- [ ] Document and validate
  - [ ] Create integration testing guide
  - [ ] Validate SLA compliance
  - [ ] Document service contracts
  - [ ] Sign off Phase 3

**Deliverables:**
- [ ] All tests passing
- [ ] Integration documentation
- [ ] Phase 3 completion checklist

---

## Phase 3 Completion Checklist

**Content Engine:**
- [ ] Script-hook coherence scoring working
- [ ] Pacing analysis enabled
- [ ] Emotional arc tracking functional
- [ ] 20+ genres, 20+ personas supported

**Queue Modernization:**
- [ ] Celery-Redis queue operational
- [ ] 15+ async tasks defined
- [ ] Retry strategy with exponential backoff
- [ ] Dead-letter queue functional
- [ ] Job visibility 100%

**Batch Processing:**
- [ ] Transactional batch operations
- [ ] Checkpointing and resume working
- [ ] Idempotency keys implemented
- [ ] Progress tracking with ETA
- [ ] Error analysis and triage

**Service Quality:**
- [ ] Advanced rate limiting (sliding window)
- [ ] Token bucket quota system
- [ ] Service contracts defined
- [ ] SLA monitoring active
- [ ] Graceful degradation tested

---

## Key Files Created/Modified

### New Files:
```
app/engines/coherence_engine.py
app/engines/pacing_engine.py
app/engines/emotional_arc.py
app/queue/celery_app.py
app/queue/tasks/generation.py
app/queue/tasks/media.py
app/queue/tasks/processing.py
app/queue/retry_strategy.py
app/queue/job_state.py
app/batch/transaction_manager.py
app/batch/checkpoint.py
app/batch/idempotency.py
app/batch/progress.py
app/core/rate_limiting.py
app/core/quota_system.py
app/contracts/service_contracts.py
app/core/graceful_degradation.py
docs/COHERENCE.md
docs/QUEUE_GUIDE.md
docs/SLA.md
```

---

## Effort Estimate
- **Week 9**: 40 hours (coherence & pacing)
- **Week 10**: 42 hours (queue modernization)
- **Week 11**: 38 hours (batch processing)
- **Week 12**: 35 hours (service quality)
- **Total Phase 3**: 155 hours

**Cumulative: 430 hours**

---

## Success Criteria for Phase 3

✅ **By Apr 21, 2026:**
- Script-hook coherence 90%+
- Celery queue operational
- Batch processing transactional
- Rate limiting enforced
- Service contracts defined
- Ready for Phase 4 (Workflow Automation)

