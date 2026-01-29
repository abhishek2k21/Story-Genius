# Monitoring & Observability Guide

**Version**: 1.0  
**Last Updated**: January 28, 2026  
**Phase**: Phase 2 Complete

---

## Overview

This guide covers the complete observability stack for the Creative AI Shorts Platform, including metrics, dashboards, logging, and tracing.

---

## Table of Contents

1. [Prometheus Metrics](#prometheus-metrics)
2. [Grafana Dashboards](#grafana-dashboards)
3. [Alerting](#alerting)
4. [Structured Logging](#structured-logging)
5. [Distributed Tracing](#distributed-tracing)
6. [Troubleshooting](#troubleshooting)

---

## Prometheus Metrics

### Accessing Metrics

**Endpoint**: `GET http://localhost:8000/metrics`

**Format**: Prometheus exposition format

### Available Metrics

#### Counters (9 metrics)
```
llm_requests_total{model, status}
cache_hits_total
cache_misses_total
jobs_created_total{job_type}
jobs_completed_total{job_type, status}
batches_created_total
batches_completed_total{status}
```

#### Gauges (3 metrics)
```
active_jobs
cache_entries
active_users
```

#### Histograms (4 metrics)
```
job_duration_seconds{job_type}
llm_latency_seconds{model}
batch_processing_seconds
tokens_used{model}
```

### Example Queries

**Success Rate**:
```promql
(sum(rate(jobs_completed_total{status="success"}[5m])) 
 / sum(rate(jobs_completed_total[5m]))) * 100
```

**p95 Latency**:
```promql
histogram_quantile(0.95, 
  sum(rate(job_duration_seconds_bucket[5m])) by (le, job_type)
)
```

**Cache Hit Rate**:
```promql
(sum(rate(cache_hits_total[5m])) 
 / (sum(rate(cache_hits_total[5m])) + sum(rate(cache_misses_total[5m])))) * 100
```

---

## Grafana Dashboards

### Access

**URL**: http://localhost:3000  
**Default Auth**: Anonymous enabled

### Available Dashboards

#### 1. Main Dashboard
- Success rate (24h)
- Error rate (1h)
- Active jobs gauge
- Cache hit rate
- Latency (p50, p95, p99)
- Request rate graph

**Use Case**: Overall system health monitoring

#### 2. Services Dashboard
- LLM request rate by model
- LLM latency (p95) by model
- LLM error rate
- Batch processing time
- Cache performance
- Cache size

**Use Case**: Service-level monitoring

#### 3. Cost Dashboard
- Token usage (24h) by model
- LLM API calls count
- Total jobs created
- Token distribution (pie chart)
- Estimated cost (USD)
- Cache savings

**Use Case**: Cost tracking and optimization

---

## Alerting

### Alert Rules

File: `prometheus/alert.rules.yml`

#### Critical Alerts (2)
1. **BatchProcessingFailure** - Any batch fails (1m)
2. **ServiceDown** - Service not responding (1m)
3. **DatabaseConnectionIssue** - DB errors > 5 (2m)

#### Warning Alerts (4)
1. **HighErrorRate** - Job failures > 5% (5m)
2. **HighLatency** - p99 > 30s (10m)
3. **LLMHighErrorRate** - LLM errors > 10% (5m)
4. **HighActiveJobs** - Active jobs > 100 (5m)

#### Info Alerts (1)
1. **LowCacheHitRate** - Cache hits < 50% (15m)

### Alert Response

**When alert fires:**
1. Check Grafana dashboards for context
2. Review logs with trace_id
3. Check service health
4. Escalate if critical

---

## Structured Logging

### Log Format

**JSON Structure**:
```json
{
  "timestamp": "2026-01-28T15:30:00Z",
  "level": "INFO",
  "logger": "app.api.main",
  "message": "Request processed",
  "trace_id": "trace_abc123",
  "request_id": "req_456",
  "user_id": "user_789",
  "job_id": "job_999",
  "batch_id": "batch_111",
  "duration_ms": 450,
  "status_code": 200
}
```

### Querying Logs

**By Trace ID**:
```bash
cat logs/app.log | jq 'select(.trace_id == "trace_abc123")'
```

**By Error Level**:
```bash
cat logs/app.log | jq 'select(.level == "ERROR")'
```

**By User**:
```bash
cat logs/app.log | jq 'select(.user_id == "user_789")'
```

### Log Levels

- **DEBUG**: Detailed diagnostic information
- **INFO**: General informational messages
- **WARNING**: Warning messages, system still functioning
- **ERROR**: Error messages, request failed
- **CRITICAL**: Critical issues, system unstable

---

## Distributed Tracing

### Trace Context

**Fields**:
- `trace_id` - Unique trace identifier
- `request_id` - Request-specific ID
- `user_id` - User performing action
- `job_id` - Job being processed
- `batch_id` - Batch being processed

### Trace Propagation

**Flow**:
```
1. Request arrives → TracingMiddleware
2. Generate trace_id, request_id
3. Store in ContextVar (async-safe)
4. All logs include trace context
5. Response includes X-Trace-ID header
```

### Response Headers

```
X-Trace-ID: trace_abc123def456
X-Request-ID: req_789xyz
```

### E2E Tracing

**Example**: Track a video generation request

1. Client sends request
2. Receive `X-Trace-ID` from response headers
3. Query logs for that `trace_id`:
   ```bash
   grep "trace_abc123" logs/app.log | jq .
   ```
4. See complete request flow across all services

---

## Troubleshooting

### High Error Rate

**Symptoms**: `HighErrorRate` alert firing

**Steps**:
1. Check Grafana main dashboard → Error Rate panel
2. Query recent errors:
   ```bash
   tail -1000 logs/app.log | jq 'select(.level == "ERROR")'
   ```
3. Identify error patterns (error_code)
4. Check service health dashboard
5. Review circuit breaker states

### High Latency

**Symptoms**: `HighLatency` alert firing

**Steps**:
1. Check Grafana main dashboard → Latency panel
2. Identify slow service (LLM, Veo, DB)
3. Check service dashboard for bottleneck
4. Review p95/p99 metrics
5. Check active jobs count

### Low Cache Hit Rate

**Symptoms**: `LowCacheHitRate` alert (info level)

**Steps**:
1. Check cache size: `cache_entries` metric
2. Review cache TTL settings
3. Analyze request patterns
4. Consider cache warming strategy

### Service Down

**Symptoms**: `ServiceDown` alert firing (critical)

**Steps**:
1. Check service health: `GET /health`
2. Review recent errors in logs
3. Check database connectivity
4. Restart service if needed
5. Escalate to on-call engineer

---

## Best Practices

### Monitoring
- Set up alerts for critical metrics
- Review dashboards regularly
- Establish baseline performance
- Monitor trends over time

### Logging
- Always include trace_id in logs
- Use structured fields (not free-text)
- Log at appropriate levels
- Never log sensitive data

### Tracing
- Propagate trace_id to all services
- Include trace_id in external API calls
- Use trace_id for customer support
- Keep trace_id in response headers

---

## Metrics Reference

### Key Performance Indicators (KPIs)

| Metric | Target | Alert Threshold |
|--------|--------|----------------|
| Success Rate | >95% | <95% |
| p95 Latency | <2s | >5s |
| p99 Latency | <5s | >30s |
| Error Rate | <5% | >5% |
| Cache Hit Rate | >60% | <50% |
| Active Jobs | <50 | >100 |

---

## Support

**Documentation**: `/docs`  
**Metrics**: http://localhost:8000/metrics  
**Dashboards**: http://localhost:3000  
**Health Check**: http://localhost:8000/health

---

**Maintained by**: Platform Team  
**Last Review**: January 28, 2026
