# Auto-Scaling Strategy and Configuration Guide

## Overview
This document outlines the auto-scaling strategy for YT Video Creator, targeting **1-100 pod scaling** and **5000 req/s** sustained load capacity.

---

## Horizontal Pod Autoscaling (HPA)

### API Service Scaling
**Target**: 2-50 pods  
**Metrics**: CPU (70%), Memory (80%)

```yaml
Scaling Behavior:
  Scale-Up:
    - Immediate (0s stabilization)
    - Rate: 100% or 4 pods/15s (whichever is larger)
    - Example: 10 → 20 pods in 15s, 20 → 24 pods in 15s
  
  Scale-Down:
    - Gradual (5min stabilization)
    - Rate: 50%/15s max
    - Example: 20 → 10 pods over 5+ minutes
```

**Triggers:**
- CPU > 70%: Add pods
- Memory > 80%: Add pods
- CPU < 50% for 5min: Remove pods

### Worker Service Scaling
**Target**: 2-100 pods  
**Primary Metric**: Queue depth (100 jobs/pod)  
**Fallback**: CPU (70%)

```yaml
Scaling Behavior:
  Scale-Up:
    - Immediate (0s stabilization)
    - Rate: 200% or 10 pods/30s (aggressive)
    - Example: Queue at 5000 jobs → Scale from 20 to 50 pods
  
  Scale-Down:
    - Very gradual (10min stabilization)
    - Rate: 25%/60s max (conservative)
    - Example: Queue cleared → Wait 10min, then slowly scale down
```

**Queue-Based Logic:**
```
Target: 100 jobs per pod
Current Queue: 5000 jobs
Required Pods: 5000 / 100 = 50 pods

If current pods = 20:
  Need to add: 30 pods
  Scale-up rate: 200% or 10 pods
  Time to reach 50 pods: ~3-5 minutes
```

---

## Cluster Autoscaling

### Node Provisioning
**Trigger**: Pods in "Pending" state due to insufficient resources  
**Scale-Up Time**: 2-5 minutes (AWS node provisioning)  
**Max Nodes**: 10 (configurable per node group)

**Node Groups:**
1. **General** (on-demand): t3.large, 3-10 nodes
2. **Spot Workers** (spot): c5.xlarge mix, 0-50 nodes

**Scaling Parameters:**
```yaml
Scale-Up:
  - Trigger: Unschedulable pods
  - Timeout: 15 minutes max provision time
  - Strategy: least-waste (cost-effective node selection)

Scale-Down:
  - Trigger: Node utilization < 50%
  - Delay: 10 minutes after scale-up
  - Wait: 10 minutes before removal
  - Safety: Respects Pod Disruption Budgets
```

### Spot Instance Strategy
**Cost Savings**: ~70-80% vs on-demand  
**Workloads**: Batch processing, workers  
**Risk Mitigation**:
- Diversified instance types (c5.xlarge, c5a.xlarge, c5n.xlarge, c5d.xlarge)
- Graceful handling of spot interruptions
- Fallback to on-demand if spots unavailable

---

## Queue-Based Scaling Architecture

### Components
1. **Queue Metrics Exporter** (`app/observability/queue_metrics.py`)
   - Exports queue depth to Prometheus every 15s
   - Monitors: celery, video-processing, default queues
   
2. **Prometheus Adapter**
   - Exposes custom metrics to Kubernetes
   - Converts `celery_queue_depth` → HPA metric
   
3. **Worker HPA**
   - Consumes queue depth metric
   - Scales workers based on jobs/pod target

### Data Flow
```
Redis Queue
    ↓
Queue Metrics Exporter (every 15s)
    ↓
Prometheus (stores metric)
    ↓
Prometheus Adapter (exposes to K8s)
    ↓
Worker HPA (scales deployment)
    ↓
Worker Pods (process jobs)
```

---

## Load Testing Scenarios

### Scenario 1: Sustained Load
**Goal**: Validate system can handle 1000 req/s for 10 minutes

```python
Duration: 10 minutes (600s)
Total Requests: 600,000
Concurrency: 100
Expected Scaling: 2 → 15-20 pods
```

**Success Criteria:**
- Error rate: <0.1%
- P99 latency: <200ms
- All pods healthy

### Scenario 2: Spike Test
**Goal**: Test rapid scale-up/down

```python
Phase 1: Warmup (100 req/s, 2 min) → 2-5 pods
Phase 2: Spike (10,000 req/s, 1 min) → 30-50 pods
Phase 3: Cooldown (100 req/s, 2 min) → 2-5 pods
```

**Success Criteria:**
- Scale-up: <2 minutes to 50 pods
- No pod crashes during spike
- Scale-down: Gradual (5-10 min)

### Scenario 3: Gradual Ramp
**Goal**: Test scaling at each level

```python
Minute 1: 500 req/s → 3-5 pods
Minute 2: 1000 req/s → 5-8 pods
Minute 3: 1500 req/s → 8-12 pods
...
Minute 10: 5000 req/s → 30-40 pods
```

**Success Criteria:**
- Linear scaling with load
- P99 latency stable at each level
- No request timeouts

---

## Cost Optimization Strategies

### 1. Right-Sizing Resources
| Component | Old | New | Savings |
|-----------|-----|-----|---------|
| API Pods | cpu: 1000m | cpu: 500m | 50% |
| API Pods | mem: 2Gi | mem: 1Gi | 50% |
| Worker Pods | cpu: 2000m | cpu: 1000m | 50% |

**Impact**: 40-50% reduction in baseline costs

### 2. Spot Instances
```yaml
Workloads on Spot:
  - Video processing workers
  - Batch jobs
  - Non-critical tasks

Cost Savings: 70-80% vs on-demand
Risk: 2-3% interruption rate (acceptable for batch)
```

### 3. Scheduled Scaling
**Non-Production Environments:**
```yaml
Staging:
  Weekday 9AM-6PM: 5 pods
  Nights/Weekends: 1 pod
  Savings: ~60%

Development:
  Business hours: 3 pods
  Off-hours: 0 pods
  Savings: ~70%
```

### 4. Auto-Shutdown Idle Resources
- Scale workers to 0 when queue empty for 1 hour
- Scale staging to 0 on weekends
- Delete old EBS snapshots >90 days

**Total Cost Reduction**: 30-40% vs static provisioning

---

## Monitoring & Alerts

### Key Metrics
```yaml
HPA Metrics:
  - Current replicas
  - Desired replicas
  - CPU/Memory utilization
  - Queue depth
  - Scaling events

Cluster Autoscaler Metrics:
  - Node count
  - Pending pods
  - Unschedulable pods
  - Scale-up/down events
```

### Alerts
```yaml
- HPA at max replicas (50/100)
  Severity: Warning
  Action: Review if more capacity needed

- Cluster Autoscaler failing to provision
  Severity: Critical
  Action: Check AWS quotas, node group config

- High latency despite scaling
  Severity: Warning
  Action: Investigate bottlenecks (DB, external API)
```

---

## Scaling Limits

### Pod Limits
```yaml
API:
  Min: 2 (HA)
  Max: 50 (cost control)
  Target CPU: 70%

Workers:
  Min: 2 (HA)
  Max: 100 (processing capacity)
  Target: 100 jobs/pod
```

### Node Limits
```yaml
General:
  Min: 3 (1 per AZ)
  Max: 10

Spot Workers:
  Min: 0 (scale to zero)
  Max: 50 (cost control)
```

### Resource Quotas (per namespace)
```yaml
production:
  CPU: 200 cores
  Memory: 400 GiB
  Pods: 200

staging:
  CPU: 50 cores
  Memory: 100 GiB
  Pods: 50
```

---

## Performance Benchmarks

### Target Performance
| Load | Pods | Latency (P99) | Error Rate |
|------|------|---------------|------------|
| 100 req/s | 2-5 | <50ms | <0.01% |
| 1000 req/s | 15-20 | <100ms | <0.1% |
| 5000 req/s | 30-40 | <200ms | <0.1% |
| 10000 req/s | 50+ | <500ms | <1% |

### Resource Efficiency
```yaml
Cost per 1M requests: $50
Pods per 1000 req/s: 15-20
CPU per 1000 req/s: 10-15 cores
Memory per 1000 req/s: 20-30 GiB
```

---

## Troubleshooting

### HPA Not Scaling
```bash
# Check HPA status
kubectl get hpa -n production

# View HPA events
kubectl describe hpa api-hpa -n production

# Verify metrics
kubectl get --raw /apis/metrics.k8s.io/v1beta1/pods
```

### Cluster Autoscaler Not Adding Nodes
```bash
# Check autoscaler logs
kubectl logs -n kube-system deployment/cluster-autoscaler

# Common issues:
# - AWS IAM permissions
# - Node group at max size
# - No suitable node group for pending pods
```

### Queue-Based Scaling Not Working
```bash
# Check queue metrics
curl http://queue-metrics-exporter:8000/metrics

# Verify Prometheus Adapter
kubectl get --raw /apis/custom.metrics.k8s.io/v1beta1

# Check HPA is getting metric
kubectl describe hpa worker-hpa -n production
```

---

**Document Version**: 1.0  
**Last Updated**: January 28, 2026  
**Owner**: Infrastructure Team  
**Review Cycle**: Monthly
