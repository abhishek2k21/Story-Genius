# Multi-Region Architecture Documentation

## Overview
YT Video Creator is deployed across two AWS regions for high availability, disaster recovery, and global performance optimization.

---

## Architecture Diagram

```
                      ┌─────────────────────────────────┐
                      │       Route53 Global DNS        │
                      │   Latency-Based Routing         │
                      └────────────┬───────┬────────────┘
                                   │       │
                    ┌──────────────┘       └──────────────┐
                    │                                     │
         ┌──────────▼──────────┐              ┌──────────▼──────────┐
         │   us-east-1         │              │   us-west-2         │
         │   (Primary)         │◄────Peering──►  (Secondary)        │
         └─────────────────────┘              └─────────────────────┘
                    │                                     │
         ┌──────────▼──────────┐              ┌──────────▼──────────┐
         │  EKS Cluster        │              │  EKS Cluster        │
         │  - 3 AZs            │              │  - 3 AZs            │
         │  - 3-10 nodes       │              │  - 2-8 nodes        │
         │  - 2-50 API pods    │              │  - 2-50 API pods    │
         │  - 2-100 workers    │              │  - 2-100 workers    │
         └─────────────────────┘              └─────────────────────┘
                    │                                     │
         ┌──────────▼──────────┐              ┌──────────▼──────────┐
         │  Aurora Global DB   │              │  Aurora Global DB   │
         │  (Primary)          │─────Repl────►│  (Read Replica)     │
         │  Read/Write         │   <5s lag    │  Read-Only          │
         └─────────────────────┘              └─────────────────────┘
```

---

## Regional Configuration

### Primary Region: us-east-1

**Purpose**: Main production environment, handles majority of traffic

**Infrastructure:**
```yaml
EKS Cluster:
  Name: yt-video-creator-prod
  Version: 1.28
  Availability Zones: us-east-1a, us-east-1b, us-east-1c
  
Node Groups:
  General:
    Instance Type: t3.large
    Capacity Type: ON_DEMAND
    Min: 3, Max: 10, Desired: 3
  
  Spot Workers:
    Instance Type: c5.xlarge (mixed)
    Capacity Type: SPOT
    Min: 0, Max: 50, Desired: 0

VPC:
  CIDR: 10.0.0.0/16
  Private Subnets: 10.0.11-13.0/24
  Public Subnets: 10.0.1-3.0/24
  NAT Gateways: 3 (one per AZ)

Database:
  Type: Aurora PostgreSQL 15.3
  Instances: 3 (db.r6g.large)
  Role: Primary (read/write)
  Backup: 7 days retention
```

**Workload Distribution:**
- API requests: 60-70% (US East Coast, Europe)
- Worker jobs: 60-70%
- Database: All writes + reads

---

### Secondary Region: us-west-2

**Purpose**: Disaster recovery, global reach (US West Coast, Asia-Pacific)

**Infrastructure:**
```yaml
EKS Cluster:
  Name: yt-video-creator-west
  Version: 1.28
  Availability Zones: us-west-2a, us-west-2b, us-west-2c
  
Node Groups:
  General:
    Instance Type: t3.large
    Capacity Type: ON_DEMAND
    Min: 2, Max: 8, Desired: 2
  
  Spot Workers:
    Instance Type: c5.xlarge (mixed)
    Capacity Type: SPOT
    Min: 0, Max: 20, Desired: 0

VPC:
  CIDR: 10.1.0.0/16
  Private Subnets: 10.1.11-13.0/24
  Public Subnets: 10.1.1-3.0/24
  NAT Gateways: 3 (one per AZ)

Database:
  Type: Aurora PostgreSQL 15.3
  Instances: 2 (db.r6g.large)
  Role: Read Replica
  Replication Lag: <5 seconds
```

**Workload Distribution:**
- API requests: 30-40% (US West Coast, Asia-Pacific)
- Worker jobs: 30-40%
- Database: Read-only (can promote to read/write during failover)

---

## Cross-Region Components

### VPC Peering

**Purpose**: Allow direct communication between regions

```hcl
Connection:
  us-east-1 (10.0.0.0/16) ↔ us-west-2 (10.1.0.0/16)
  
Use Cases:
  - Cross-region service calls
  - Database replication traffic
  - Internal monitoring
  
Security:
  - Security groups allow specific ports only
  - Encrypted in transit (AWS backbone)
```

### Aurora Global Database

**Replication Architecture:**
```
Primary (us-east-1)
    ├── Instance 1 (Writer)
    ├── Instance 2 (Reader)
    └── Instance 3 (Reader)
         │
         │ Asynchronous Replication
         │ Target Lag: <5 seconds
         ▼
Secondary (us-west-2)
    ├── Instance 1 (Reader)
    └── Instance 2 (Reader)
```

**Features:**
- Global write forwarding enabled
- Millisecond replication lag (typical: 1-3 seconds)
- Automatic failover capability
- Point-in-time recovery (PITR)

**Monitoring:**
```python
# Replication lag monitoring
replication_lag_gauge.labels(
    source_region='us-east-1',
    target_region='us-west-2'
).set(lag_seconds)

# Alert if lag > 10 seconds
```

---

## Global Load Balancing (Route53)

### Latency-Based Routing

**How it works:**
1. User makes DNS query for `api.ytvideocreator.com`
2. Route53 measures latency to both regions
3. Returns IP of region with lowest latency
4. User connects to nearest region

**Traffic Distribution:**
```
User Location → Routed To
US East Coast → us-east-1 (20-30ms latency)
US West Coast → us-west-2 (15-25ms latency)
Europe        → us-east-1 (80-100ms latency)
Asia-Pacific  → us-west-2 (100-150ms latency)
```

### Health Checks

**Configuration:**
```yaml
Health Checks:
  Interval: 30 seconds
  Timeout: 5 seconds
  Failure Threshold: 3 consecutive failures
  Path: /health
  Protocol: HTTPS
  Port: 443

Health Check Logic:
  - If us-east-1 fails: Route all traffic to us-west-2
  - If us-west-2 fails: Route all traffic to us-east-1
  - If both fail: Critical alert, manual intervention
```

### DNS Records

```
api.ytvideocreator.com (Latency-based)
  ├── us-east-1 (A record, set_identifier="us-east-1")
  │   └── Health Check: us-east-1-health-check
  └── us-west-2 (A record, set_identifier="us-west-2")
      └── Health Check: us-west-2-health-check

Direct Access:
  api-east.ytvideocreator.com → us-east-1 (always)
  api-west.ytvideocreator.com → us-west-2 (always)
```

---

## Disaster Recovery

### Failure Scenarios

#### Scenario 1: Single AZ Failure
```
Impact: 1/3 of capacity in one region
Response: Automatic (Kubernetes redistributes pods)
RTO: 2-5 minutes
RPO: 0 (no data loss)
```

#### Scenario 2: Single Region Failure
```
Impact: 50-70% of capacity
Response: Automated or manual failover
RTO: 15 minutes
RPO: <5 minutes (replication lag)
```

#### Scenario 3: Database Failure
```
Impact: Writes blocked, reads continue
Response: Promote secondary to primary
RTO: 5 minutes
RPO: <5 minutes
```

### Automated Failover

**Trigger Conditions:**
- Route53 health checks failing for >5 minutes
- Manual initiation via DR script

**Failover Steps:**
1. Promote us-west-2 database to primary (2-3 min)
2. Scale up us-west-2 cluster (2-5 min)
3. Update Route53 (route all traffic to us-west-2)
4. Verify services healthy

**Total Time: 10-12 minutes** (within 15 min RTO)

---

## Performance Optimization

### Latency Improvements

**Before Multi-Region:**
```
US East Coast: 30ms (good)
US West Coast: 80ms (poor)
Europe: 100ms (acceptable)
Asia: 200ms (poor)
```

**After Multi-Region:**
```
US East Coast: 30ms (good) ✅ No change
US West Coast: 20ms (excellent) ✅ 75% improvement
Europe: 100ms (acceptable) ✅ No change
Asia: 120ms (good) ✅ 40% improvement
```

**Overall**: 30-50% latency improvement for users >1000 miles from primary region

### Auto-Scaling per Region

**us-east-1 (Primary):**
- API: 2-50 pods (larger capacity)
- Workers: 2-100 pods
- Nodes: 3-10 on-demand, 0-50 spot

**us-west-2 (Secondary):**
- API: 2-50 pods (same range, lower baseline)
- Workers: 2-100 pods
- Nodes: 2-8 on-demand, 0-20 spot

**Cost Optimization:**
- Secondary region: 30-40% smaller baseline
- Scales up during failover or high regional load
- Spot instances for flexible workloads

---

## Monitoring & Observability

### Multi-Region Metrics

**Prometheus Metrics:**
```yaml
Infrastructure:
  - node_count{region="us-east-1"}
  - node_count{region="us-west-2"}
  - pod_count{region, namespace, deployment}

Database:
  - postgres_replication_lag_seconds{source, target}
  - postgres_connections{region}
  - postgres_transactions_per_second{region}

Application:
  - http_requests_total{region, status}
  - http_request_duration_seconds{region, quantile}
  - worker_queue_depth{region, queue}

Route53:
  - route53_health_check_status{region}
  - route53_health_check_latency{region}
```

### Dashboards

**Global Overview Dashboard:**
- Total requests per region
- Latency per region (P50, P95, P99)
- Error rate per region
- Database replication lag
- Health check status

**Regional Dashboards:**
- us-east-1 specific metrics
- us-west-2 specific metrics
- Auto-scaling behavior
- Resource utilization

---

## Cost Analysis

### Monthly Infrastructure Costs

**us-east-1 (Primary):**
```
EKS Control Plane: $73
Nodes (on-demand): ~$300 (average 5 nodes)
Spot instances: ~$50 (average usage)
Database: ~$500 (3 instances)
Data transfer: ~$100
Total: ~$1,023/month
```

**us-west-2 (Secondary):**
```
EKS Control Plane: $73
Nodes (on-demand): ~$150 (average 3 nodes)
Spot instances: ~$30 (average usage)
Database: ~$350 (2 instances)
Data transfer: ~$80
Total: ~$683/month
```

**Cross-Region:**
```
VPC Peering: $0.01/GB (~$20/month)
Route53: ~$10/month
Total: ~$30/month
```

**Grand Total: ~$1,736/month**

**Cost vs. Benefit:**
- Single region cost: ~$1,200/month
- Multi-region premium: $536/month (45% increase)
- **Benefits**: 99.9% uptime, DR capability, 30-50% latency improvement globally

---

## Security Considerations

### Cross-Region Security

**VPC Peering:**
- Traffic stays on AWS backbone (encrypted)
- Security groups restrict access
- No public internet exposure

**Database Replication:**
- Encrypted in transit (TLS)
- Encrypted at rest (KMS)
- Separate KMS keys per region

**IAM Roles:**
- Region-specific roles
- Least privilege access
- Cross-account not required (same account)

---

## Operational Procedures

### Deployment Strategy

**1. Deploy to us-west-2 First:**
```bash
# Test in secondary (lower traffic)
helm upgrade app-backend ./infra/helm/app-backend \
  --namespace production \
  --kubeconfig ~/.kube/config-west

# Verify
curl https://api-west.ytvideocreator.com/health

# Then deploy to us-east-1
helm upgrade app-backend ./infra/helm/app-backend \
  --namespace production \
  --kubeconfig ~/.kube/config-east
```

**2. Gradual Rollout:**
- us-west-2: Deploy new version (10% of traffic)
- Monitor for 30 minutes
- us-east-1: Deploy new version (90% of traffic)
- Monitor for 1 hour
- Complete

### Maintenance Windows

**Regional Maintenance:**
- Can update one region at a time
- Other region handles traffic
- Zero-downtime deployments

**Global Maintenance:**
- Schedule during low-traffic hours
- Notify users via status page
- Expected: <5 min downtime (rare)

---

## Future Enhancements

**Phase 8 (Weeks 29-32):**
- Add third region (eu-west-1) for European users
- Implement active-active writes across regions
- Enhanced global monitoring

**Potential Regions:**
```
Third region: eu-west-1 (Europe)
Fourth region: ap-southeast-1 (Asia-Pacific)
```

---

**Document Version**: 1.0  
**Last Updated**: January 28, 2026  
**Owner**: Infrastructure Team  
**Review Cycle**: Quarterly
