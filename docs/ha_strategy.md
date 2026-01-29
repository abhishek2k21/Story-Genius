# High Availability Strategy

## Overview
This document outlines the high availability (HA) strategy for the YT Video Creator platform, targeting **99.9% uptime SLA** (≤43 minutes downtime per month).

## Architecture

### Multi-Zone Deployment
- **3 Availability Zones**: us-east-1a, us-east-1b, us-east-1c
- **Node Distribution**: Minimum 1 node per AZ (3 nodes baseline)
- **Pod Distribution**: Topology spread constraints ensure even distribution
- **Failover Time**: <30 seconds for pod failover

### Component Redundancy

| Component | Replicas | Distribution | Failover | RTO |
|-----------|----------|--------------|----------|-----|
| API Service | 3-10 | 3 AZs | Automatic | <30s |
| Worker Pods | 2-50 | 3 AZs | Automatic | <30s |
| PostgreSQL | 3 | 3 AZs | Patroni | <60s |
| Redis | 3 | 3 AZs | Sentinel | <10s |
| Load Balancer | Multi-AZ | 3 AZs | AWS-managed | <5s |

## Database High Availability

### PostgreSQL with Patroni
- **Architecture**: 1 primary + 2 standby replicas
- **Replication**: Streaming replication (synchronous)
- **Failover**: Automatic via Patroni leader election
- **Connection Routing**: VIP for transparent failover
- **Failover Time**: <60 seconds

**Patroni Configuration:**
```yaml
replicas: 3
role: master/replica (auto-assigned)
health_checks: Every 10 seconds
failover_mode: automatic
```

**Backup Strategy:**
- Daily backups at 2 AM UTC
- 30-day retention
- Point-in-time recovery (PITR) via WAL archiving
- Cross-region backup copy to us-west-2

**Recovery Objectives:**
- RTO (Recovery Time Objective): 1 hour
- RPO (Recovery Point Objective): 24 hours (daily backups)

## Cache High Availability

### Redis with Sentinel
- **Architecture**: 1 master + 2 slaves + 3 sentinels
- **Replication**: Asynchronous master-slave replication
- **Failover**: Automatic via Redis Sentinel (quorum: 2/3)
- **Failover Time**: <10 seconds

**Sentinel Configuration:**
```conf
sentinel monitor mymaster redis-ha-0 6379 2
sentinel down-after-milliseconds mymaster 5000
sentinel failover-timeout mymaster 10000
```

**Caching Strategy:**
- Writes: Master only
- Reads: Slaves (load distribution)
- Invalidation: Pub/Sub for distributed cache clearing

## Load Balancing

### AWS Network Load Balancer
- **Type**: Network Load Balancer (Layer 4)
- **Cross-Zone**: Enabled
- **Health Checks**: Every 10 seconds
- **Unhealthy Threshold**: 2 consecutive failures
- **Healthy Threshold**: 2 consecutive successes

### NGINX Ingress Controller
- **Replicas**: 3 (1 per AZ)
- **Rate Limiting**: 100 req/s per IP
- **Timeout**: 60 seconds
- **SSL/TLS**: Terminated at ingress
- **Certificates**: Let's Encrypt auto-renewal

## Health Checks

### Liveness Probes
- **Endpoint**: `/health`
- **Purpose**: Detect if application is running
- **Interval**: 10 seconds
- **Timeout**: 5 seconds
- **Failure Threshold**: 3
- **Action**: Restart pod

### Readiness Probes
- **Endpoint**: `/ready`
- **Purpose**: Detect if application can serve traffic
- **Interval**: 5 seconds
- **Timeout**: 3 seconds
- **Failure Threshold**: 3
- **Checks**:
  - Database connectivity
  - Cache connectivity
  - Critical dependencies

## Resilience Patterns

### Circuit Breaker
- **Failure Threshold**: 5 consecutive failures
- **Recovery Timeout**: 60 seconds
- **Success Threshold**: 2 consecutive successes
- **Purpose**: Prevent cascading failures

**States:**
- **CLOSED**: Normal operation
- **OPEN**: Service failing, reject requests
- **HALF_OPEN**: Testing recovery

### Pod Disruption Budgets
```yaml
app-backend: minAvailable: 2
postgres-ha: minAvailable: 2
redis-ha: minAvailable: 2
```

**Purpose**: Ensure minimum availability during:
- Cluster upgrades
- Node maintenance
- Voluntary evictions

## Monitoring & Alerting

### Prometheus Metrics
- **Scrape Interval**: 15 seconds
- **Retention**: 30 days
- **Storage**: 50 GB

**Monitored Metrics:**
- Node CPU, memory, disk
- Pod restarts, crashes
- Request latency (p50, p95, p99)
- Error rates
- Database connections
- Cache hit rates

### Alert Rules

| Alert | Threshold | Duration | Severity | Action |
|-------|-----------|----------|----------|--------|
| NodeDown | Node unavailable | 2 min | Critical | Page on-call |
| PodCrashLooping | >0 restarts/15min | 5 min | Warning | Auto-heal |
| HighLatency | P99 > 1s | 5 min | Warning | Investigate |
| DatabaseDown | DB unavailable | 1 min | Critical | Page on-call |
| RedisDown | Cache unavailable | 1 min | Critical | Page on-call |

### AlertManager
- **Slack Integration**: #alerts, #critical-alerts
- **PagerDuty**: For critical alerts
- **Grouping**: By alertname, cluster, service
- **Repeat Interval**: 12 hours

## Failure Scenarios

### AZ Failure
**Scenario**: Complete us-east-1a outage  
**Impact**: 1/3 capacity lost  
**Mitigation**:
1. Pods automatically rescheduled to 1b, 1c
2. Load balancer routes traffic to healthy AZs
3. Database replica in 1b promoted if primary was in 1a

**Failover Time**: <30 seconds  
**Manual Action**: None (automatic)

### Database Primary Failure
**Scenario**: Primary PostgreSQL instance crashes  
**Impact**: Brief write unavailability  
**Mitigation**:
1. Patroni detects primary failure (10s)
2. Standby promoted to primary (30s)
3. VIP updated to new primary
4. Applications reconnect automatically

**Failover Time**: <60 seconds  
**Data Loss**: None (synchronous replication)

### Node Failure
**Scenario**: Worker node crashes  
**Impact**: Pods on that node unavailable  
**Mitigation**:
1. Kubernetes detects node failure (40s)
2. Pods marked for rescheduling
3. New pods created on healthy nodes
4. Load balancer removes unhealthy pods

**Failover Time**: 1-2 minutes  
**Manual Action**: Investigate node issue

### Redis Master Failure
**Scenario**: Redis master crashes  
**Impact**: Brief cache unavailability  
**Mitigation**:
1. Sentinel detects failure (5s)
2. Slave promoted to master (5s)
3. Applications reconnect via Sentinel

**Failover Time**: <10 seconds  
**Data Loss**: Possible (async replication)

## Testing & Validation

### Chaos Engineering
- Monthly AZ failure simulation
- Quarterly database failover drill
- Bi-weekly pod crash testing

### Uptime Calculation
```
Target SLA: 99.9%
Allowed downtime/month: 43 minutes
Allowed downtime/year: 8.76 hours

Current uptime tracking: Prometheus + Alertmanager
```

## Disaster Recovery

### Backup Locations
- **Primary**: S3 us-east-1
- **Secondary**: S3 us-west-2 (cross-region copy)
- **Archives**: Glacier (>90 days)

### Recovery Procedures
1. **Database Recovery**:
   - Restore from latest backup
   - Replay WAL logs to PITR
   - Verify data integrity
   - Promote to primary

2. **Application Recovery**:
   - Deploy from ECR images
   - Restore configuration from Git
   - Run smoke tests
   - Route traffic

3. **Cache Recovery**:
   - Deploy Redis cluster
   - Warm cache from database
   - Verify replication

## Maintenance Windows

### Rolling Updates
- **Strategy**: Blue-green deployment
- **Max Surge**: 25%
- **Max Unavailable**: 0
- **Update Duration**: 15-20 minutes
- **Rollback Time**: <5 minutes

### Planned Maintenance
- **Window**: Sunday 2-4 AM UTC (low traffic)
- **Notification**: 48 hours advance
- **Validation**: Post-maintenance health checks

## SLA Commitments

| Metric | Target | Measurement |
|--------|--------|-------------|
| Uptime | 99.9% | Monthly |
| API Latency (P99) | <200ms | Per request |
| Error Rate | <0.1% | Per request |
| Database Failover | <60s | Per incident |
| Pod Failover | <30s | Per incident |

---

**Document Version**: 1.0  
**Last Updated**: January 28, 2026  
**Owner**: Infrastructure Team  
**Review Cycle**: Quarterly
