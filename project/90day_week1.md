# Week 1: Core Infrastructure & Exception Hierarchy
## Phase 1: Foundation Hardening
**Dates:** Jan 28 - Feb 3, 2026  
**Hours:** 30 hours (6 days × 5 hours)  
**Focus:** Exception handling, core infrastructure, logging setup

---

## 🎯 Week North Star
By end of Week 1:
> **Exception hierarchy implemented, structured logging configured, database connection pooling ready**

---

## Daily Breakdown

### **DAY 1 (Mon, Jan 28) — Exception Hierarchy Architecture**

**Morning (9am-12pm):**
- [ ] Design exception system
  - [ ] Create `app/core/exceptions.py`
  - [ ] Plan exception hierarchy
  - [ ] Define base `CustomException` class
  - [ ] Document exception usage patterns

**Afternoon (1pm-5pm):**
- [ ] Create base exceptions
  - [ ] Implement `CustomException` base
  - [ ] Create `ValidationError`
  - [ ] Create `NotFoundError`
  - [ ] Create `UnauthorizedError`
  - [ ] Create `RateLimitError`

**Deliverables:**
- [ ] `app/core/exceptions.py` created
- [ ] 5+ exception types defined
- [ ] Docstrings for each exception

**Success Criteria:**
- [ ] All exceptions inherit from `CustomException`
- [ ] Code compiles without errors
- [ ] Clear error messages

---

### **DAY 2 (Tue, Jan 29) — Exception Hierarchy Expansion**

**Morning (9am-12pm):**
- [ ] Create service-specific exceptions
  - [ ] `VeoGenerationError`
  - [ ] `ImagenGenerationError`
  - [ ] `VertexAIError`
  - [ ] `BatchProcessingError`
  - [ ] `SchedulingError`

**Afternoon (1pm-5pm):**
- [ ] Create database exceptions
  - [ ] `DatabaseError`
  - [ ] `ConnectionError`
  - [ ] `TransactionError`
  - [ ] `QueryError`
  - [ ] Write tests for all exceptions (15+ test cases)

**Deliverables:**
- [ ] 10+ service exceptions defined
- [ ] 5+ database exceptions defined
- [ ] Test file: `app/tests/unit/test_exceptions.py`

**Success Criteria:**
- [ ] All exceptions tested
- [ ] 100% code coverage for exceptions module

---

### **DAY 3 (Wed, Jan 30) — Structured Logging Configuration**

**Morning (9am-12pm):**
- [ ] Configure logging infrastructure
  - [ ] Update `app/core/logging.py`
  - [ ] Setup JSON logging format
  - [ ] Configure log levels
  - [ ] Add context fields

**Afternoon (1pm-5pm):**
- [ ] Implement structured logging
  - [ ] Add request context (request_id, user_id)
  - [ ] Add exception context in log messages
  - [ ] Setup log rotation
  - [ ] Configure log output (stdout + file)

**Deliverables:**
- [ ] `app/core/logging.py` updated
- [ ] JSON logging configured
- [ ] Log context middleware

**Success Criteria:**
- [ ] Logs output as valid JSON
- [ ] Request context in every log
- [ ] Timestamps ISO 8601 format

---

### **DAY 4 (Thu, Jan 31) — Database Connection Pooling**

**Morning (9am-12pm):**
- [ ] Setup connection pooling
  - [ ] Create `app/core/database.py`
  - [ ] Configure SQLAlchemy engine
  - [ ] Setup pool size and overflow
  - [ ] Configure pool pre-ping

**Afternoon (1pm-5pm):**
- [ ] Implement database initialization
  - [ ] Setup Base model
  - [ ] Create `get_db()` dependency
  - [ ] Setup async support (if using)
  - [ ] Test connection pooling

**Deliverables:**
- [ ] `app/core/database.py` created
- [ ] Connection pool configured
- [ ] `get_db()` dependency working

**Success Criteria:**
- [ ] 10+ concurrent connections work
- [ ] Pool auto-expands under load
- [ ] Connection timeouts handled

---

### **DAY 5 (Fri, Feb 1) — Error Handling Integration**

**Morning (9am-12pm):**
- [ ] Create error handlers
  - [ ] Global exception handler middleware
  - [ ] HTTP error response formatting
  - [ ] Error logging with full context
  - [ ] Sensitive data masking

**Afternoon (1pm-5pm):**
- [ ] Test error handling
  - [ ] Write integration tests for exceptions
  - [ ] Test error responses (20+ cases)
  - [ ] Verify logging captures errors
  - [ ] Test sensitive data masking

**Deliverables:**
- [ ] Exception handler middleware
- [ ] Error response formatter
- [ ] Integration tests (20+ cases)

**Success Criteria:**
- [ ] All errors caught and logged
- [ ] Consistent error response format
- [ ] No sensitive data in error messages

---

## Week 1 Completion Checklist

**Exception Handling:**
- [ ] Exception hierarchy complete (15+ exception types)
- [ ] All exceptions inherit from base class
- [ ] Exception docstrings clear
- [ ] Tests passing (100% coverage)

**Logging:**
- [ ] JSON logging configured
- [ ] Request context in all logs
- [ ] Log rotation working
- [ ] Sensitive data masked

**Database:**
- [ ] Connection pooling configured
- [ ] Pool size optimized
- [ ] Connection tests passing
- [ ] Health checks working

**Error Handling:**
- [ ] Global exception handler
- [ ] Error responses formatted
- [ ] Error logging complete
- [ ] Integration tests passing

---

## Files Created

```
app/core/
├── exceptions.py          # 15+ exception types
├── logging.py             # JSON logging config
└── database.py            # Connection pooling

app/tests/unit/
└── test_exceptions.py     # Exception tests (20+ cases)

app/tests/integration/
└── test_error_handling.py # Error handler tests (20+ cases)
```

---

## Effort Summary
- **Total Hours:** 30 hours
- **Code Lines:** 400-500 lines
- **Tests Written:** 40+ test cases
- **Coverage:** 80%+ for core modules

---

## Success Metrics
✅ All custom exceptions tested  
✅ Logging structured and centralized  
✅ Database connections pooled  
✅ Errors handled gracefully  
✅ No secrets in logs  
✅ Ready for Phase 1 Week 2

---

## Next Week (Week 2) Preview
- Service layer stability
- Distributed locking
- Circuit breaker pattern
- Health checks
- Token security

