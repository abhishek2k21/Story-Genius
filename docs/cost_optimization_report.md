# Infrastructure Cost Optimization Report

**Date**: January 28, 2026  
**Week**: Week 35 (Day 175)  
**Target**: Reduce monthly costs by 20-30%

---

## Current Monthly Costs Breakdown

| Service | Component | Monthly Cost | % of Total |
|---------|-----------|--------------|------------|
| **Compute** | EKS cluster (3x m5.large) | $800 | 26.7% |
| | Worker nodes (2x c5.xlarge) | $400 | 13.3% |
| **Database** | RDS PostgreSQL (db.r5.large) | $600 | 20.0% |
| | RDS backup storage | $200 | 6.7% |
| **Storage** | S3 Standard (video storage) | $300 | 10.0% |
| | S3 requests/data transfer | $100 | 3.3% |
| **CDN** | CloudFront | $200 | 6.7% |
| **Monitoring** | Prometheus/Grafana (t3.medium) | $100 | 3.3% |
| | CloudWatch logs | $50 | 1.7% |
| **Other** | Load balancers | $150 | 5.0% |
| | Data transfer | $100 | 3.3% |
| **TOTAL** | | **$3,000** | **100%** |

---

## Optimization Strategies

### 1. Compute Optimization (Save $360/month - 30%)

#### Current State
- 3x m5.large nodes (24/7) = $800/month
- 2x c5.xlarge worker nodes (24/7) = $400/month
- Total: $1,200/month

#### Optimizations

**A. Use Spot Instances for Workers** (-50% on workers)
```yaml
# EKS Node Group Config
spot_instances:
  enabled: true
  instance_types:
    - c5.xlarge
    - c5a.xlarge
    - c5n.xlarge
  capacity:
    min: 1
    max: 5
    desired: 2
  savings: 50%

Savings: $200/month
```

**B. Right-size API Pods** (-20% on API nodes)
```yaml
# Current: m5.large (2 vCPU, 8 GB)
# Actual usage: 1.2 vCPU, 4 GB

# New: m5.medium (1 vCPU, 4 GB) + autoscale
resources:
  api-pods:
    requests:
      cpu: 500m
      memory: 1Gi
    limits:
      cpu: 1000m
      memory: 2Gi

Savings: $160/month
```

**New Compute Cost**: $840/month  
**Savings**: $360/month (30%)

---

### 2. Storage Optimization (Save $120/month - 30%)

#### Current State
- S3 Standard: $300/month (2TB)
- S3 Requests: $100/month
- Total: $400/month

#### Optimizations

**A. S3 Lifecycle Policies**
```json
{
  "Rules": [
    {
      "Id": "MoveToIA",
      "Status": "Enabled",
      "Transitions": [
        {
          "Days": 30,
          "StorageClass": "STANDARD_IA"
        }
      ]
    },
    {
      "Id": "DeleteTemp",
      "Status": "Enabled",
      "Filter": {
        "Prefix": "temp/"
      },
      "Expiration": {
        "Days": 7
      }
    }
  ]
}

Savings on storage: $90/month (30% of videos > 30 days old)
```

**B. Compress Videos Before Storage**
```python
# Use H.265 (HEVC) instead of H.264
# Average compression: 40% smaller files

ffmpeg_settings = {
    "codec": "libx265",
    "crf": 28,  # Quality
    "preset": "medium"
}

Savings on storage: $30/month (10% file size reduction)
```

**New Storage Cost**: $280/month  
**Savings**: $120/month (30%)

---

### 3. Database Optimization (Save $200/month - 25%)

#### Current State
- RDS PostgreSQL db.r5.large: $600/month
- RDS Backup: $200/month
- Total: $800/month

#### Optimizations

**A. Optimize Connection Pooling** (-10% on instance size)
```python
# Current: 100 connections, underutilized
# New: PgBouncer with connection pooling

pgbouncer_config = {
    "max_client_conn": 1000,
    "default_pool_size": 20,
    "pool_mode": "transaction"
}

# Can downsize to db.r5.medium
Savings: $300/month
```

**B. Archive Old Data** (-25% on backup storage)
```sql
-- Archive jobs older than 90 days
CREATE TABLE jobs_archive AS
SELECT * FROM jobs WHERE created_at < NOW() - INTERVAL '90 days';

DELETE FROM jobs WHERE created_at < NOW() - INTERVAL '90 days';

-- Reduce backup storage
Savings: $50/month
```

**C. Use Read Replicas for Analytics** (instead of main DB)
```yaml
# Offload analytics queries to read replica
# Reduces main DB load by 40%
# Can downsize main instance

read_replica:
  instance_class: db.t3.medium  # $50/month
  purpose: analytics_only
```

**New Database Cost**: $600/month  
**Savings**: $200/month (25%)

---

### 4. CDN Optimization (Already Optimized) 

Current: $200/month - No changes needed
- Already using CloudFront efficiently
- Cache hit ratio: 85%
- Keep as is

---

### 5. Monitoring Optimization (Save $30/month - 20%)

#### Current State
- Dedicated t3.medium for Prometheus: $100/month
- CloudWatch logs: $50/month
- Total: $150/month

#### Optimizations

**A. Use Managed Prometheus** (-30%)
```yaml
# Switch to Amazon Managed Prometheus
# Pay only for active metrics

managed_prometheus:
  active_series: 10000
  cost_per_month: $70

Savings: $30/month
```

**B. Optimize Log Retention**
```yaml
# Reduce CloudWatch log retention
log_retention:
  application_logs: 7 days  # was 30 days
  access_logs: 3 days       # was 14 days

Savings: $20/month
```

**New Monitoring Cost**: $120/month  
**Savings**: $30/month (20%)

---

## Cost Optimization Summary

| Category | Current | Optimized | Savings | % Saved |
|----------|---------|-----------|---------|---------|
| **Compute** | $1,200 | $840 | $360 | 30% |
| **Database** | $800 | $600 | $200 | 25% |
| **Storage** | $400 | $280 | $120 | 30% |
| **CDN** | $200 | $200 | $0 | 0% |
| **Monitoring** | $150 | $120 | $30 | 20% |
| **Other** | $250 | $250 | $0 | 0% |
| **TOTAL** | **$3,000** | **$2,290** | **$710** | **23.7%** |

---

## Implementation Plan

### Phase 1: Immediate Wins (Week 1)
1. Enable S3 lifecycle policies
2. Implement temporary file cleanup
3. Optimize CloudWatch log retention
**Expected Savings**: $140/month

### Phase 2: Infrastructure Changes (Week 2)
1. Implement PgBouncer
2. Switch to Spot instances for workers
3. Right-size API pods
**Expected Savings**: $560/month

### Phase 3: Database Optimization (Week 3)
1. Archive old data
2. Set up read replicas
3. Downsize main database instance
**Expected Savings**: $200/month

### Phase 4: Monitoring Migration (Week 4)
1. Migrate to Managed Prometheus
2. Finalize log optimization
**Expected Savings**: $30/month

---

## Annual Savings Projection

- **Monthly Savings**: $710
- **Annual Savings**: $8,520 (23.7%)
- **3-Year Savings**: $25,560

---

## Risk Assessment

| Optimization | Risk Level | Mitigation |
|--------------|------------|------------|
| Spot instances | Medium | Diverse instance types, graceful shutdown |
| Database downsize | Low | Monitor performance, can upsize quickly |
| S3 lifecycle | Low | Test on subset first, reversible |
| Log retention | Low | Archive critical logs separately |

---

## Success Metrics

### Week 1 After Implementation
- [ ] S3 costs reduced by 15%
- [ ] Log costs reduced by 30%
- [ ] No performance degradation

### Week 2 After Implementation
- [ ] Compute costs reduced by 25%
- [ ] API response times maintained < 200ms
- [ ] No spot instance disruptions

### Week 4 After Implementation
- [ ] Total costs at or below $2,300/month
- [ ] Database query performance maintained < 100ms
- [ ] 99.9% uptime maintained

---

## Monitoring Plan

```yaml
dashboards:
  - name: "Cost Optimization Dashboard"
    panels:
      - Monthly spend by service
      - Spot instance interruption rate
      - Database connection pool usage
      - S3 storage class distribution
      - API response times
      - Database query performance
    
alerts:
  - Spot interruption rate > 5%
  - Database connections > 80%
  - API p95 latency > 250ms
  - Query time > 150ms
```

---

## Conclusion

By implementing these optimizations, we can reduce infrastructure costs by **$710/month ($8,520/year)** - a **23.7% reduction** - while maintaining performance and reliability.

**Key Benefits**:
- ✅ Lower operational costs
- ✅ Better resource utilization
- ✅ Maintained performance SLAs
- ✅ Improved scalability
- ✅ Environmentally friendly (less compute)

**Next Steps**: Approve plan and begin Phase 1 implementation.

---

**Report Generated**: January 28, 2026  
**Target Implementation**: Week 35-38  
**Expected ROI**: $8,520/year
