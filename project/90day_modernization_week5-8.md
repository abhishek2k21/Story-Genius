# 90-Day Modernization Plan: Week 5-8
## Phase 2: Quality & Observability (Feb 25 - Mar 24, 2026)

---

## Week 5: Prompt Management & Evaluation (Feb 25 - Mar 3)

### 🎯 North Star
By end of Week 5:
> **All LLM prompts centralized in versioned system, prompt caching reducing token usage by 40%**

---

### 📋 Day-by-Day Breakdown

#### **DAY 21 (Mon, Feb 24) — Centralized Prompt Architecture**

**Morning (9am-12pm):**
- [ ] Design prompt system
  - [ ] Create `app/core/prompts/` folder structure
  - [ ] Plan Jinja2 template system
  - [ ] Design versioning schema (v1.0, v1.1, v2.0)
  - [ ] Document prompt variables and validation rules

**Afternoon (1pm-5pm):**
- [ ] Create base prompt module
  - [ ] Create `app/core/prompts/__init__.py`
  - [ ] Create `app/core/prompts/base_prompts.py`
  - [ ] Define prompt types: HOOK, SCRIPT, CRITIC, STRATEGY
  - [ ] Create prompt data structures

**Deliverables:**
- [ ] Prompt system architecture document
- [ ] Base prompt module with 5+ base prompts

---

#### **DAY 22 (Tue, Feb 25) — Prompt Templates & Rendering**

**Morning (9am-12pm):**
- [ ] Create template system
  - [ ] Create `app/core/prompts/prompt_templates.py`
  - [ ] Implement Jinja2 template rendering
  - [ ] Support variables: {audience}, {genre}, {platform}, {tone}, etc.
  - [ ] Add template validation

**Afternoon (1pm-5pm):**
- [ ] Migrate existing prompts
  - [ ] Extract from `app/critic/service.py` (20-30 prompts)
  - [ ] Extract from intelligence modules (15-20 prompts)
  - [ ] Extract from script generation (10-15 prompts)
  - [ ] Test that generated prompts match original behavior

**Deliverables:**
- [ ] Template rendering engine
- [ ] 50+ prompts migrated to central system
- [ ] Tests showing identical output to original

---

#### **DAY 23 (Wed, Feb 26) — Prompt Versioning System**

**Morning (9am-12pm):**
- [ ] Design versioning
  - [ ] Create `app/core/prompts/prompt_versioning.py`
  - [ ] Schema: {prompt_id: uuid, version: string, created_at, author, changes}
  - [ ] Support rollback mechanism
  - [ ] Track performance correlation with version

**Afternoon (1pm-5pm):**
- [ ] Implement version tracking
  - [ ] Store prompt versions in database
  - [ ] Create migration for prompt version table
  - [ ] Add audit logging for prompt changes
  - [ ] Create version comparison endpoint

**Deliverables:**
- [ ] Prompt versioning table
- [ ] Version tracking API
- [ ] Rollback mechanism
- [ ] Change audit log

---

#### **DAY 24 (Thu, Feb 27) — Prompt Validation**

**Morning (9am-12pm):**
- [ ] Create validation system
  - [ ] Create `app/core/prompts/prompt_validation.py`
  - [ ] Character limit checks
  - [ ] Required variable validation
  - [ ] Format validation (Jinja2 syntax)

**Afternoon (1pm-5pm):**
- [ ] Implement validators
  - [ ] Length constraints per prompt type
  - [ ] Variable presence validation
  - [ ] Template syntax validation
  - [ ] Performance warnings (token count estimates)

**Deliverables:**
- [ ] Prompt validation engine
- [ ] Validation tests for all prompt types
- [ ] Token count estimation

---

#### **DAY 25 (Fri, Feb 28) — LLM Output Validation & Caching Setup**

**Morning (9am-12pm):**
- [ ] Create LLM validator
  - [ ] Create `app/engines/llm_validator.py`
  - [ ] Implement Pydantic validators for responses
  - [ ] JSON parsing with fallback
  - [ ] Field presence and type validation

**Afternoon (1pm-5pm):**
- [ ] Plan caching strategy
  - [ ] Create `app/engines/llm_cache.py`
  - [ ] Use Vertex AI prompt caching (if available)
  - [ ] Fallback to Redis caching
  - [ ] Design cache key strategy: hash(model, prompt, temperature)

**Deliverables:**
- [ ] LLM output validator
- [ ] Cache infrastructure design
- [ ] Cache implementation (Redis-based)

---

## Week 6: Testing & Monitoring Infrastructure (Mar 4-10)

### 🎯 North Star
By end of Week 6:
> **Pytest infrastructure with 60%+ coverage, Prometheus metrics exposed, Grafana dashboards live**

---

### 📋 Day-by-Day Breakdown

#### **DAY 26 (Mon, Mar 3) — Test Framework Initialization**

**Morning (9am-12pm):**
- [ ] Initialize pytest
  - [ ] Create `app/tests/` directory structure
  - [ ] Create `app/tests/conftest.py` with fixtures
  - [ ] Create `pytest.ini` with configuration
  - [ ] Add `pyproject.toml` pytest config

**Afternoon (1pm-5pm):**
- [ ] Create fixture library
  - [ ] Mock Vertex AI responses
  - [ ] Mock Veo video generation
  - [ ] Mock database (SQLite in-memory)
  - [ ] Mock external API calls
  - [ ] Create test user and batch fixtures

**Deliverables:**
- [ ] Pytest initialized with config
- [ ] Comprehensive fixture library (20+ fixtures)
- [ ] Sample test using fixtures

---

#### **DAY 27 (Tue, Mar 4) — Unit Tests for Core Modules**

**Morning (9am-12pm):**
- [ ] Write config tests
  - [ ] Create `app/tests/unit/test_config.py`
  - [ ] Test all config values load correctly
  - [ ] Test default values
  - [ ] Test environment override

**Afternoon (1pm-5pm):**
- [ ] Write model tests
  - [ ] Create `app/tests/unit/test_models.py`
  - [ ] Test Pydantic model validation
  - [ ] Test serialization/deserialization
  - [ ] Test edge cases (empty strings, null values)

**Deliverables:**
- [ ] Config tests (20+ test cases)
- [ ] Model tests (40+ test cases)
- [ ] 80%+ coverage for both modules

---

#### **DAY 28 (Wed, Mar 5) — Integration Tests**

**Morning (9am-12pm):**
- [ ] Write orchestrator tests
  - [ ] Create `app/tests/integration/test_orchestrator.py`
  - [ ] Test job creation and lifecycle
  - [ ] Test job state transitions
  - [ ] Test error handling

**Afternoon (1pm-5pm):**
- [ ] Write batch tests
  - [ ] Create `app/tests/integration/test_batch.py`
  - [ ] Test batch creation and processing
  - [ ] Test transaction rollback
  - [ ] Test result aggregation

**Deliverables:**
- [ ] Orchestrator integration tests (15+ cases)
- [ ] Batch processing tests (15+ cases)
- [ ] Coverage report generated

---

#### **DAY 29 (Thu, Mar 6) — CI/CD Pipeline Setup**

**Morning (9am-12pm):**
- [ ] Create GitHub Actions workflow
  - [ ] Create `.github/workflows/test.yml`
  - [ ] Configure pytest to run on push
  - [ ] Configure coverage reporting
  - [ ] Fail on coverage < 60%

**Afternoon (1pm-5pm):**
- [ ] Set up coverage tracking
  - [ ] Integrate with coverage.py
  - [ ] Generate HTML coverage report
  - [ ] Add badges to README
  - [ ] Track coverage trends

**Deliverables:**
- [ ] GitHub Actions workflow
- [ ] Coverage badge
- [ ] Coverage report (HTML)
- [ ] Build passing locally

---

#### **DAY 30 (Fri, Mar 7) — Monitoring & Metrics Infrastructure**

**Morning (9am-12pm):**
- [ ] Set up Prometheus metrics
  - [ ] Create `app/observability/prometheus_exporter.py`
  - [ ] Create `/metrics` endpoint
  - [ ] Expose Counter, Gauge, Histogram metrics
  - [ ] Add custom metrics: job_success_rate, batch_latency, token_usage

**Afternoon (1pm-5pm):**
- [ ] Configure Prometheus server
  - [ ] Add to `docker-compose.yml`
  - [ ] Configure scrape interval (30s)
  - [ ] Configure retention (15 days)
  - [ ] Test metrics collection

**Deliverables:**
- [ ] Prometheus exporter integrated
- [ ] `/metrics` endpoint working
- [ ] Prometheus server running
- [ ] Sample metrics collected

---

## Week 7: Structured Logging & Observability (Mar 11-17)

### 📋 Day-by-Day Breakdown

#### **DAY 31 (Mon, Mar 10) — Grafana Dashboards**

**Morning (9am-12pm):**
- [ ] Design dashboard structure
  - [ ] Main dashboard: success rate, latency, error rate
  - [ ] Service dashboard: Vertex AI, Veo, Database health
  - [ ] Cost dashboard: token usage, API calls, storage

**Afternoon (1pm-5pm):**
- [ ] Build dashboards
  - [ ] Create `grafana/dashboards/main.json`
  - [ ] Create `grafana/dashboards/services.json`
  - [ ] Create `grafana/dashboards/cost.json`
  - [ ] Add to docker-compose
  - [ ] Test data visualization

**Deliverables:**
- [ ] 3+ Grafana dashboards
- [ ] Dashboards showing live metrics
- [ ] Alert thresholds configured

---

#### **DAY 32 (Tue, Mar 11) — Alerting Rules**

**Morning (9am-12pm):**
- [ ] Create alert rules
  - [ ] Create `prometheus/alert.rules.yml`
  - [ ] Alert: error_rate > 5%
  - [ ] Alert: latency_p99 > 30s
  - [ ] Alert: batch_failure

**Afternoon (1pm-5pm):**
- [ ] Set up notification channels
  - [ ] Integrate with Slack (optional) or PagerDuty
  - [ ] Configure email notifications
  - [ ] Test alert firing

**Deliverables:**
- [ ] Alert rules file
- [ ] Alert notifications working
- [ ] Test alert firing in Grafana

---

#### **DAY 33 (Wed, Mar 12) — Structured Logging Setup**

**Morning (9am-12pm):**
- [ ] Configure JSON logging
  - [ ] Update `app/core/logging.py`
  - [ ] Output JSON format with all context
  - [ ] Add structured fields: timestamp, level, logger, message
  - [ ] Add context fields: job_id, batch_id, user_id, trace_id

**Afternoon (1pm-5pm):**
- [ ] Set up log aggregation
  - [ ] Choose: ELK stack or GCP Cloud Logging
  - [ ] Add to docker-compose (if ELK)
  - [ ] Configure log parsing rules
  - [ ] Test log collection

**Deliverables:**
- [ ] JSON logging configured
- [ ] Log aggregation running
- [ ] Logs searchable by job_id, error_code

---

#### **DAY 34 (Thu, Mar 13) — Log Aggregation Dashboards**

**Morning (9am-12pm):**
- [ ] Build log search UI
  - [ ] Filter by job_id, batch_id, error_code
  - [ ] Time range selection
  - [ ] Aggregate error counts

**Afternoon (1pm-5pm):**
- [ ] Configure log-based alerts
  - [ ] Alert on error rate spike
  - [ ] Alert on specific error codes
  - [ ] Set up notification channels

**Deliverables:**
- [ ] Log search dashboard
- [ ] Log-based alert rules
- [ ] Alerts firing on error spike

---

#### **DAY 35 (Fri, Mar 14) — Trace ID Propagation & Week 7 Validation**

**Morning (9am-12pm):**
- [ ] Implement trace ID propagation
  - [ ] Generate trace ID for each request
  - [ ] Include in all logs for that request
  - [ ] Propagate across async calls

**Afternoon (1pm-5pm):**
- [ ] Week 7 validation
  - [ ] Run full integration test suite
  - [ ] Verify all metrics visible
  - [ ] Verify all logs aggregated
  - [ ] Document monitoring setup

**Deliverables:**
- [ ] Trace ID propagation working
- [ ] E2E tracing visible in logs
- [ ] Monitoring documentation

---

## Week 8: Quality Assurance & Hardening (Mar 18-24)

### 📋 Day-by-Day Breakdown

#### **DAY 36-40 (Mon-Fri, Mar 17-21) — Comprehensive QA & Testing**

**Focus Areas:**
- [ ] Run full integration test suite (all tests passing)
- [ ] Performance testing (response time < 2s for API calls)
- [ ] Load testing (100 concurrent requests without error)
- [ ] Security scanning (OWASP ZAP scan)
- [ ] Code quality check (linting, formatting)
- [ ] Documentation review and updates
- [ ] Playbook creation for common issues

**Daily Deliverables:**
- [ ] Day 36: QA test plan finalized
- [ ] Day 37: All tests passing, coverage > 60%
- [ ] Day 38: Performance baselines established
- [ ] Day 39: Security scan results reviewed
- [ ] Day 40: Phase 2 completion checklist signed off

---

## Phase 2 Completion Checklist

**Prompt Management:**
- [ ] 100+ prompts centralized in system
- [ ] Versioning system functional
- [ ] Prompt validation working
- [ ] Token usage tracking enabled

**Testing Infrastructure:**
- [ ] Pytest configured with 60%+ coverage
- [ ] 100+ unit tests written
- [ ] 50+ integration tests written
- [ ] CI/CD pipeline running on every push

**Monitoring & Observability:**
- [ ] Prometheus metrics exposed
- [ ] Grafana dashboards live (5+ dashboards)
- [ ] Alert rules configured
- [ ] Slack/email notifications working

**Structured Logging:**
- [ ] JSON logging in all modules
- [ ] Log aggregation working
- [ ] Log search functional
- [ ] Trace ID propagation working

**Documentation:**
- [ ] Monitoring guide created
- [ ] Testing guide created
- [ ] Alert runbook created
- [ ] Deployment guide updated

---

## Key Files Created/Modified

### New Files:
```
app/core/prompts/base_prompts.py      # Base prompts
app/core/prompts/prompt_templates.py  # Jinja2 templates
app/core/prompts/prompt_versioning.py # Version tracking
app/core/prompts/prompt_validation.py # Validation
app/engines/llm_validator.py          # Output validation
app/engines/llm_cache.py              # Cache layer
app/tests/conftest.py                 # Pytest fixtures
app/tests/unit/test_config.py         # Config tests
app/tests/unit/test_models.py         # Model tests
app/tests/integration/test_orchestrator.py
app/tests/integration/test_batch.py
app/observability/prometheus_exporter.py
.github/workflows/test.yml            # CI/CD
prometheus/alert.rules.yml            # Alert rules
grafana/dashboards/main.json
grafana/dashboards/services.json
grafana/dashboards/cost.json
docs/MONITORING.md                    # Monitoring guide
docs/TESTING.md                       # Testing guide
```

---

## Effort Estimate
- **Week 5**: 40 hours (prompt system)
- **Week 6**: 38 hours (testing framework)
- **Week 7**: 35 hours (monitoring)
- **Week 8**: 32 hours (QA & hardening)
- **Total Phase 2**: 145 hours

**Cumulative: 275 hours**

---

## Success Criteria for Phase 2

✅ **By Mar 24, 2026:**
- 60%+ test coverage achieved
- All 4 weeks tasks completed
- Monitoring fully operational
- Ready for Phase 3 (Content Engine & Services)
- Team trained on monitoring/observability

---

## Next Phase Preview (Week 9-12)
- Script-hook coherence validation
- Pacing and emotion curve integration
- Genre and persona expansion
- Job queue modernization (Celery)
- Batch transactional processing
- Advanced rate limiting & quotas
