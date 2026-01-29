# 90-Day Modernization Plan: Week 1-4
## Phase 1: Foundation Hardening (January 28 - February 24, 2026)

---

## Week 1: Core Infrastructure Modernization (Jan 28 - Feb 3)

### 🎯 North Star
By end of Week 1:
> **Custom exception hierarchy implemented, structured logging with context working, database transaction manager functional**

---

### 📋 Day-by-Day Breakdown

#### **DAY 1 (Mon, Jan 28) — Exception Hierarchy Architecture**

**Morning (9am-12pm):**
- [ ] Design exception hierarchy
  - [ ] Create `app/core/exceptions.py`
  - [ ] Define base `VideoCreationError`, `LLMError`, `AuthError`, `RateLimitError`
  - [ ] Add error codes (VIDEO_GEN_TIMEOUT=1001, LLM_MALFORMED=2001, etc.)
  - [ ] Document error semantics

**Afternoon (1pm-5pm):**
- [ ] Create error fingerprinting system
  - [ ] Create `app/core/error_fingerprint.py`
  - [ ] Implement hash-based deduplication (error_type + message hash)
  - [ ] Add timestamp tracking
- [ ] Update `app/core/logging.py`
  - [ ] Add `error_code` field to all logs
  - [ ] Add error context (line number, function name)

**Deliverables:**
- [ ] `app/core/exceptions.py` (150 lines)
- [ ] Error code constants file
- [ ] Unit test: `app/tests/unit/test_exceptions.py`

---

#### **DAY 2 (Tue, Jan 29) — Structured Logging with Context**

**Morning (9am-12pm):**
- [ ] Create context management system
  - [ ] Create `app/core/context.py`
  - [ ] Use `contextvars` for request_id, job_id, batch_id, user_id
  - [ ] Implement context manager for request lifecycle
  - [ ] Add trace ID generation (UUID4)

**Afternoon (1pm-5pm):**
- [ ] Update logging formatter
  - [ ] JSON output with all context fields
  - [ ] Timestamp in ISO format
  - [ ] Log level, logger name, message
  - [ ] Test with sample logs
- [ ] Integrate with FastAPI
  - [ ] Create middleware to capture context
  - [ ] Add context to request response

**Deliverables:**
- [ ] `app/core/context.py` (100 lines)
- [ ] Updated logging configuration
- [ ] Integration test showing context propagation

---

#### **DAY 3 (Wed, Jan 30) — Database Infrastructure: Alembic Setup**

**Morning (9am-12pm):**
- [ ] Initialize Alembic
  - [ ] Run `alembic init migrations`
  - [ ] Configure `alembic.ini` with database URL
  - [ ] Create `env.py` for auto-migration detection
- [ ] Create base migration
  - [ ] Generate initial schema migration
  - [ ] Verify existing tables captured

**Afternoon (1pm-5pm):**
- [ ] Test migration workflow
  - [ ] Create test database
  - [ ] Run migration upgrade
  - [ ] Verify schema
  - [ ] Test rollback
- [ ] Document migration process
  - [ ] Create `docs/MIGRATIONS.md`

**Deliverables:**
- [ ] Alembic configured and initialized
- [ ] First migration file created
- [ ] Migration documentation

---

#### **DAY 4 (Thu, Jan 31) — Database Transactions & Pooling**

**Morning (9am-12pm):**
- [ ] Create transaction context manager
  - [ ] Create `app/core/transactions.py`
  - [ ] Implement `@transactional` decorator
  - [ ] Support nested transactions with savepoints
  - [ ] Add automatic rollback on exception

**Afternoon (1pm-5pm):**
- [ ] Add connection pooling
  - [ ] Update `app/core/database.py`
  - [ ] Configure SQLAlchemy connection pool (size=20, overflow=10)
  - [ ] Add pool timeout (30s)
  - [ ] Add health check for connections
- [ ] Test transaction isolation
  - [ ] Write tests for transaction rollback
  - [ ] Test concurrent transactions

**Deliverables:**
- [ ] Transaction manager with decorator
- [ ] Connection pool configured
- [ ] Integration tests: `app/tests/integration/test_transactions.py`

---

#### **DAY 5 (Fri, Feb 1) — Database Health & Indexes**

**Morning (9am-12pm):**
- [ ] Create database health check
  - [ ] Add `/health/db` endpoint
  - [ ] Measure connection time, query time
  - [ ] Add liveness/readiness probes
- [ ] Plan index strategy
  - [ ] Identify hot columns (user_id, batch_id, job_id, status)
  - [ ] Plan composite indexes (user_id + status, batch_id + created_at)

**Afternoon (1pm-5pm):**
- [ ] Create index migration
  - [ ] Generate Alembic migration
  - [ ] Add indexes for hot columns
  - [ ] Test index effectiveness with EXPLAIN ANALYZE
- [ ] Document indexing strategy
  - [ ] Create performance baseline
  - [ ] Document query optimization guidelines

**Deliverables:**
- [ ] Database health endpoint
- [ ] Index migration file
- [ ] Performance baseline document

---

### 🔄 Week 1 Summary & Validation

**Friday EOD Checklist:**
- [ ] All custom exceptions used in codebase (audit with grep)
- [ ] JSON logs contain: timestamp, level, logger, message, job_id, trace_id
- [ ] Alembic migrations run without error
- [ ] Transaction tests pass (rollback on exception)
- [ ] Connection pool metrics visible
- [ ] Index migration applied successfully

**Success Metrics:**
- ✅ 0 generic `except Exception:` remaining
- ✅ All logs parseable as JSON
- ✅ 100% of DB operations wrapped in transactions
- ✅ Connection pool utilization visible (add to metrics)

---

## Week 2: Service Layer Stability (Feb 4-10)

### 🎯 North Star
By end of Week 2:
> **Distributed locking prevents duplicate batch execution, circuit breakers handle service failures gracefully, token security hardened**

---

### 📋 Day-by-Day Breakdown

#### **DAY 6 (Mon, Feb 3) — Distributed Locking for Schedulers**

**Morning (9am-12pm):**
- [ ] Migrate BatchSchedule to database
  - [ ] Update `app/scheduling/models.py`
  - [ ] Add fields: status, next_run_at, last_run_at, updated_at
  - [ ] Create migration for new columns
- [ ] Design lock strategy
  - [ ] Use Redis (or Celery lock)
  - [ ] Lock key: `batch_schedule:{schedule_id}:lock`
  - [ ] TTL: 5 minutes (prevent deadlock)

**Afternoon (1pm-5pm):**
- [ ] Implement lock manager
  - [ ] Create `app/scheduling/lock_manager.py`
  - [ ] `acquire_lock(key, timeout=10s)` method
  - [ ] `release_lock(key)` method
  - [ ] Automatic cleanup on timeout
- [ ] Integrate into scheduler
  - [ ] Update `app/scheduling/service.py`
  - [ ] Wrap execution in lock

**Deliverables:**
- [ ] `app/scheduling/lock_manager.py` (80 lines)
- [ ] Updated batch schedule models
- [ ] Integration test: concurrent scheduler test

---

#### **DAY 7 (Tue, Feb 4) — Circuit Breaker Pattern**

**Morning (9am-12pm):**
- [ ] Design circuit breaker
  - [ ] States: CLOSED (normal), OPEN (failing), HALF_OPEN (testing recovery)
  - [ ] Transitions: CLOSED→OPEN (on failure threshold), OPEN→HALF_OPEN (after timeout), HALF_OPEN→CLOSED (on success)
  - [ ] Configurable thresholds

**Afternoon (1pm-5pm):**
- [ ] Implement circuit breaker
  - [ ] Create `app/core/circuit_breaker.py`
  - [ ] Track failure count, success count, last failure time
  - [ ] Add health check method
- [ ] Integrate with LLM service
  - [ ] Wrap Vertex AI calls in circuit breaker
  - [ ] Fallback to secondary model if open

**Deliverables:**
- [ ] `app/core/circuit_breaker.py` (120 lines)
- [ ] Tests: state transitions, fallback behavior

---

#### **DAY 8 (Wed, Feb 5) — Service Health & Fallbacks**

**Morning (9am-12pm):**
- [ ] Implement fallback strategy
  - [ ] Define model hierarchy: Gemini 2.0-flash → Gemini 1.5-pro → Gemini 1.5-flash
  - [ ] Define video generation fallback (Veo → simpler method)
- [ ] Create health check service
  - [ ] Measure each service response time
  - [ ] Track error rates
  - [ ] Update circuit breaker state based on metrics

**Afternoon (1pm-5pm):**
- [ ] Extend health check endpoint
  - [ ] Update `/health` to include service health
  - [ ] Add response times per service
  - [ ] Add circuit breaker state
- [ ] Create service health dashboard
  - [ ] Metrics endpoint for monitoring

**Deliverables:**
- [ ] Updated health checks with service status
- [ ] Fallback logic in LLM and media services
- [ ] Dashboard metrics

---

#### **DAY 9 (Thu, Feb 6) — Auth Token Security**

**Morning (9am-12pm):**
- [ ] Remove hardcoded secrets
  - [ ] Audit codebase for hardcoded API keys
  - [ ] Move to environment variables
  - [ ] Plan secrets manager integration
- [ ] Implement token refresh
  - [ ] Short-lived access tokens (15 min)
  - [ ] Long-lived refresh tokens (7 days)
  - [ ] Token rotation mechanism

**Afternoon (1pm-5pm):**
- [ ] Create refresh endpoint
  - [ ] `POST /v1/auth/refresh`
  - [ ] Accept refresh token, return new access token
  - [ ] Validate token signature
- [ ] Add API key rotation
  - [ ] Create endpoint to generate new API keys
  - [ ] Keep old keys valid for 30 days
  - [ ] Test backward compatibility

**Deliverables:**
- [ ] Token refresh endpoint
- [ ] API key rotation logic
- [ ] Tests: token refresh, key rotation

---

#### **DAY 10 (Fri, Feb 7) — CORS & Token Security Hardening**

**Morning (9am-12pm):**
- [ ] Fix CORS configuration
  - [ ] Remove wildcard `*`
  - [ ] Define allowed origins from config
  - [ ] Add environment-specific origins
- [ ] Add token revocation
  - [ ] Create token blacklist (Redis)
  - [ ] Endpoint: `POST /v1/auth/revoke`
  - [ ] Check blacklist on token validation

**Afternoon (1pm-5pm):**
- [ ] Document auth flow
  - [ ] Create `docs/AUTH_FLOW.md`
  - [ ] Flow diagram: login → access token + refresh token → refresh flow
  - [ ] Token expiry policy
- [ ] End-to-end auth test
  - [ ] Test login → token generation → refresh → revocation

**Deliverables:**
- [ ] CORS whitelist configured
- [ ] Token revocation working
- [ ] Auth documentation
- [ ] E2E auth test

**Week 2 Summary:**
- [ ] Locks prevent duplicate batch execution
- [ ] Circuit breakers active for Vertex AI, Veo
- [ ] Token refresh working
- [ ] No hardcoded secrets in config
- [ ] CORS restricted to known origins

---

## Week 3: Service Layer Stability (Feb 11-17)

### 📋 Day-by-Day Breakdown

#### **DAY 11 (Mon, Feb 10) — API Response Standardization**

**Morning (9am-12pm):**
- [ ] Define response schemas
  - [ ] Success: `{data: T, status: "success", timestamp: string}`
  - [ ] Error: `{error: string, code: string, details: object, timestamp: string}`
  - [ ] Create Pydantic models

**Afternoon (1pm-5pm):**
- [ ] Create response wrapper
  - [ ] `APIResponse[T]` generic class
  - [ ] Auto-wrap all endpoint returns
  - [ ] Update OpenAPI schema
- [ ] Implement in FastAPI
  - [ ] Response middleware
  - [ ] Test with existing endpoints

**Deliverables:**
- [ ] `app/api/schemas.py` with response models
- [ ] Response middleware
- [ ] Updated OpenAPI docs

---

#### **DAY 12 (Tue, Feb 11) — Input Validation Layer**

**Morning (9am-12pm):**
- [ ] Create validators
  - [ ] Content length validation
  - [ ] Audience compatibility checking
  - [ ] Platform constraint validation
- [ ] Implement middleware
  - [ ] Validate all requests
  - [ ] Return helpful error messages

**Afternoon (1pm-5pm):**
- [ ] Add sanitization
  - [ ] Escape HTML
  - [ ] Remove dangerous tags
  - [ ] Prevent prompt injection
- [ ] Test with examples

**Deliverables:**
- [ ] `app/api/validators.py`
- [ ] Validation middleware
- [ ] Tests with edge cases

---

#### **DAY 13 (Wed, Feb 12) — Batch Transactional Guarantees**

**Morning (9am-12pm):**
- [ ] Design batch transaction flow
  - [ ] Create batch → Process items → Aggregate results → Commit/Rollback
  - [ ] Error handling for partial failures
- [ ] Implement result aggregation
  - [ ] Track success count, failure count, error types
  - [ ] Create `BatchResult` model

**Afternoon (1pm-5pm):**
- [ ] Add batch-level retries
  - [ ] Exponential backoff (1s, 2s, 4s, 8s, 16s)
  - [ ] Max retry limit per batch
  - [ ] Log retry attempts
- [ ] Test transaction isolation
  - [ ] Verify all-or-nothing semantics

**Deliverables:**
- [ ] Transactional batch processing
- [ ] Batch result model and aggregation
- [ ] Retry strategy with exponential backoff
- [ ] Integration tests

---

#### **DAY 14-15 (Thu-Fri, Feb 13-14) — Integration Testing & Validation**

**Morning:**
- [ ] Write integration tests
  - [ ] Test batch creation → processing → completion
  - [ ] Test transaction rollback
  - [ ] Test lock timeout scenarios

**Afternoon:**
- [ ] Run full integration suite
- [ ] Performance baseline
  - [ ] Measure batch processing time
  - [ ] Database query performance
  - [ ] Memory usage under load

**Deliverables:**
- [ ] Full integration test suite
- [ ] Performance baseline document
- [ ] Load test with 100 concurrent requests

---

## Week 4: Batch Processing & API Foundation (Feb 18-24)

### 📋 Day-by-Day Breakdown

#### **DAY 16 (Mon, Feb 17) — Advanced Batch Processing Continued**

- [ ] Finalize batch status tracking (draft → processing → completed → archived)
- [ ] Create batch monitoring endpoints
- [ ] Add cost estimation for batches

#### **DAY 17 (Tue, Feb 18) — Rate Limiting & Quota System**

**Morning:**
- [ ] Implement per-user rate limiting
  - [ ] 100 requests/hour per user
  - [ ] 5 batch creations/hour per user
  - [ ] Different limits per plan (free, pro, enterprise)

**Afternoon:**
- [ ] Create quota enforcement
  - [ ] 10 videos/month (free tier)
  - [ ] 100 videos/month (pro tier)
  - [ ] Unlimited (enterprise)
  - [ ] Block requests when quota exceeded

**Deliverables:**
- [ ] Rate limiter decorator
- [ ] Quota manager
- [ ] Quota endpoints

#### **DAY 18 (Wed, Feb 19) — Error Response Standardization**

- [ ] Create error code constants
  - [ ] LLM_TIMEOUT, VIDEO_GEN_FAILED, RATE_LIMITED, QUOTA_EXCEEDED, etc.
- [ ] Update all endpoints to use standard error responses
- [ ] Generate error code documentation

#### **DAY 19 (Thu, Feb 20) — API Documentation**

- [ ] Generate OpenAPI schema
- [ ] Create API documentation
  - [ ] Endpoint list
  - [ ] Request/response examples
  - [ ] Error codes explained
- [ ] Add to API docs website

#### **DAY 20 (Fri, Feb 21) — Week 4 Validation & Planning**

**EOD Checklist:**
- [ ] All 4 weeks tasks completed
- [ ] 70+ hours of development completed
- [ ] Phase 1 foundation ready for Phase 2

**Success Metrics:**
- ✅ Exception hierarchy fully adopted
- ✅ Structured logging in all modules
- ✅ Database transactions working
- ✅ Distributed locks preventing duplicates
- ✅ Circuit breakers active
- ✅ Token security hardened
- ✅ API responses standardized
- ✅ Input validation working
- ✅ Batch processing transactional

---

## Phase 1 Completion Checklist

**Infrastructure:**
- [ ] Custom exception hierarchy (10+ exception types)
- [ ] Structured JSON logging with context
- [ ] Database transactions and connection pooling
- [ ] Alembic migrations functional
- [ ] Database indexes on hot columns

**Reliability:**
- [ ] Distributed locks (no duplicate batch execution)
- [ ] Circuit breakers for Vertex AI, Veo, EdgeTTS
- [ ] Service health checks
- [ ] Graceful fallbacks

**Security:**
- [ ] No hardcoded secrets
- [ ] Token refresh mechanism
- [ ] CORS whitelist
- [ ] Token revocation
- [ ] Input validation and sanitization

**API Quality:**
- [ ] Standardized response format
- [ ] Error response schema
- [ ] Rate limiting per user
- [ ] Quota enforcement
- [ ] OpenAPI documentation

**Testing:**
- [ ] Unit tests for core modules (60%+ coverage)
- [ ] Integration tests for services
- [ ] Transaction isolation tests
- [ ] Lock concurrency tests
- [ ] Performance baseline established

---

## Key Files Created/Modified

### New Files:
```
app/core/exceptions.py           # Custom exceptions
app/core/context.py              # Context management
app/core/transactions.py         # Transaction manager
app/scheduling/lock_manager.py   # Distributed locks
app/core/circuit_breaker.py      # Circuit breaker pattern
app/api/schemas.py               # API response schemas
app/api/validators.py            # Request validators
app/api/rate_limiter.py          # Rate limiting
app/api/quota_manager.py         # Quota enforcement
migrations/versions/*            # Alembic migrations
app/tests/unit/*                 # Unit tests
app/tests/integration/*          # Integration tests
docs/MIGRATIONS.md               # Migration guide
docs/AUTH_FLOW.md                # Auth documentation
```

### Modified Files:
```
app/core/logging.py              # JSON formatting
app/core/database.py             # Connection pooling
app/scheduling/models.py         # Persistence
app/scheduling/service.py        # Lock integration
app/engines/llm.py               # Circuit breaker
app/media/video_service.py       # Fallback logic
app/api/main.py                  # Middleware, response wrapper
app/auth/service.py              # Token refresh
app/auth/models.py               # Refresh token model
```

---

## Effort Estimate
- **Week 1**: 40 hours (infrastructure focus)
- **Week 2**: 35 hours (stability focus)
- **Week 3**: 30 hours (services focus)
- **Week 4**: 25 hours (API focus)
- **Total Phase 1**: 130 hours

---

## Success Criteria for Phase 1

✅ **By Feb 24, 2026:**
- All Phase 1 tasks completed
- 60%+ test coverage achieved
- 0 critical issues
- Ready to start Phase 2 (Quality & Observability)
- Team trained on new patterns
