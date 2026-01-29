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
