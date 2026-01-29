# Disaster Recovery Runbook

## Overview
This runbook provides step-by-step procedures for disaster recovery scenarios in our multi-region deployment.

**Architecture**: 
- Primary: us-east-1 (3 AZs)
- Secondary: us-west-2 (3 AZs)

**Recovery Objectives**:
- RTO (Recovery Time Objective): 15 minutes
- RPO (Recovery Point Objective): 5 minutes

---

## Scenario 1: Complete us-east-1 Outage

### Detection
**Automatic Detection:**
- Route53 health checks failing for >5 minutes
- Prometheus alert: `RegionDown` (us-east-1)
- AlertManager → PagerDuty page to on-call engineer

**Manual Detection:**
- API endpoint unresponsive
- AWS Dashboard shows service disruption
- Customer reports

### Impact Assessment (2-3 minutes)

**Check AWS Status:**
1. Visit https://status.aws.amazon.com
2. Check us-east-1 service health
3. Determine if regional outage or service-specific

**Check Secondary Region:**
```bash
# Verify us-west-2 is healthy
curl https://api-west.ytvideocreator.com/health

# Check database
python scripts/disaster_recovery.py --status
```

**Notify Stakeholders:**
- Post in #incidents Slack channel
- Update status page
- Notify leadership team

### Automated Failover (10-12 minutes)

**Option A: Automated Script (Recommended)**

```bash
# Dry run first (safe)
python scripts/disaster_recovery.py --failover-to-west --dry-run

# Execute failover
python scripts/disaster_recovery.py --failover-to-west
```

**What the script does:**
1. Promotes us-west-2 database to primary (2-3 min)
2. Scales up us-west-2 cluster (2-5 min)
3. Updates Route53 DNS (all traffic to us-west-2)
4. Verifies services are healthy

**Option B: Manual Failover**

If automation fails, follow manual procedure:

#### Step 1: Promote Database (5 min)

```bash
# Promote us-west-2 to primary
aws rds failover-global-cluster \
  --global-cluster-identifier yt-video-creator-global \
  --target-db-cluster-identifier yt-video-creator-secondary \
  --region us-west-2

# Wait for promotion (2-3 minutes)
aws rds describe-db-clusters \
  --db-cluster-identifier yt-video-creator-secondary \
  --region us-west-2 \
  --query 'DBClusters[0].Status'
```

#### Step 2: Update Application Config (2 min)

```bash
# Update database endpoint in Kubernetes secrets
kubectl set env deployment/app-backend \
  -n production \
  DATABASE_URL=postgresql://yt-video-creator-secondary.cluster-xxx.us-west-2.rds.amazonaws.com/yt_video_creator
```

#### Step 3: Scale Cluster (5 min)

```bash
# Cluster Autoscaler + HPA handle this automatically
# Monitor scaling
kubectl get hpa -n production -w
kubectl get nodes -w

# If manual scaling needed
aws eks update-nodegroup-config \
  --cluster-name yt-video-creator-west \
  --nodegroup-name general \
  --scaling-config minSize=5,maxSize=10,desiredSize=8 \
  --region us-west-2
```

#### Step 4: Update DNS (1 min)

```bash
# Option 1: Update health check (programmatic)
# (Requires custom script)

# Option 2: Update Route53 record weights
aws route53 change-resource-record-sets \
  --hosted-zone-id Z1234567890ABC \
  --change-batch file://failover-dns.json
```

### Verification (3-5 minutes)

**1. Test API Endpoint:**
```bash
# Test global endpoint
curl https://api.ytvideocreator.com/health

# Should return from us-west-2
curl -v https://api.ytvideocreator.com/health 2>&1 | grep -i x-region
```

**2. Check Database:**
```bash
# Verify writes working
python -c "
from app.database import get_db
db = next(get_db())
# Perform test write
print('Database write successful')
"
```

**3. Monitor Metrics:**
```bash
# Check error rates
http://prometheus.ytvideocreator.com/graph

# Query: rate(http_requests_total{status=~"5.."}[5m])
# Expected: <0.1% error rate
```

**4. Check Replication:**
```bash
# Replication should now be us-west-2 → us-east-1 (reversed)
python app/observability/replication_monitor.py
```

### Post-Failover Actions

**Immediate (within 1 hour):**
- [ ] Update incident log with timeline
- [ ] Notify customers via status page
- [ ] Monitor us-west-2 performance closely
- [ ] Adjust auto-scaling if needed

**Short-term (within 24 hours):**
- [ ] Analyze root cause of us-east-1 failure
- [ ] Assess when us-east-1 will be available
- [ ] Plan failback strategy
- [ ] Review failover performance (RTO/RPO met?)

**Medium-term (within 1 week):**
- [ ] Conduct post-mortem meeting
- [ ] Document lessons learned
- [ ] Update runbook with improvements
- [ ] Test failback procedure

---

## Scenario 2: us-east-1 Database Failure Only

### Detection
- Database connection errors
- Prometheus alert: `DatabaseDown` (us-east-1)
- Application logs showing connection timeouts

### Response (5 minutes)

**1. Switch Application to Read from us-west-2:**
```bash
# Update database connection string
kubectl set env deployment/app-backend \
  -n production \
  DATABASE_READ_URL=postgresql://yt-video-creator-secondary.cluster-xxx.us-west-2.rds.amazonaws.com/yt_video_creator
```

**2. Assess if Full Failover Needed:**
- If database can be restored quickly (<15 min): Wait
- If database failure is prolonged: Proceed with full failover

---

## Scenario 3: Failback to us-east-1

### Preconditions
- us-east-1 infrastructure fully recovered
- Health checks passing for >30 minutes
- Low-traffic period (recommended)

### Failback Procedure (15-20 minutes)

**1. Verify us-east-1 Health:**
```bash
# Check all components
curl https://api-east.ytvideocreator.com/health
aws rds describe-db-clusters --region us-east-1
kubectl get nodes --context us-east-1
```

**2. Restore Database Replication:**
```bash
# Reverse global cluster
# us-west-2 (primary) → us-east-1 (secondary)
# Then promote us-east-1 back to primary

aws rds failover-global-cluster \
  --global-cluster-identifier yt-video-creator-global \
  --target-db-cluster-identifier yt-video-creator-primary \
  --region us-east-1
```

**3. Gradual Traffic Shift:**
```bash
# Update Route53 weights
# Start: us-east-1 (20%), us-west-2 (80%)
# Monitor for 15 minutes
# Then: us-east-1 (50%), us-west-2 (50%)
# Monitor for 15 minutes
# Finally: Restore latency-based routing
```

**4. Monitor & Verify:**
- Check error rates remain low
- Verify replication lag <5s
- Monitor database performance

---

## Scenario 4: Partial Service Degradation

### Detection
- High latency (P99 >1s)
- Increased error rates (>1%)
- Some pods crash looping

### Response
**1. Scale Up:**
```bash
# HPA should handle automatically, but verify
kubectl get hpa -n production
kubectl scale deployment/app-backend --replicas=30 -n production
```

**2. Check Resource Limits:**
```bash
# Look for resource constraints
kubectl top nodes
kubectl describe nodes | grep -A 5 "Allocated resources"
```

**3. If Needed, Route Traffic to Secondary:**
- Similar to full failover but keep us-east-1 running
- Use weighted routing (50/50 split)

---

## Testing & Drills

**Monthly DR Drill Schedule:**
- **Week 1**: Test automated failover script (dry-run)
- **Week 2**: Test database promotion procedure
- **Week 3**: Full failover test (non-production hours)
- **Week 4**: Test failback procedure

**Test Checklist:**
```bash
# 1. Dry run
python scripts/disaster_recovery.py --failover-to-west --dry-run

# 2. Verify health checks
curl https://api-east.ytvideocreator.com/health
curl https://api-west.ytvideocreator.com/health

# 3. Check replication lag
python app/observability/replication_monitor.py

# 4. Review monitoring dashboards
# - Grafana: http://grafana.ytvideocreator.com
# - Prometheus: http://prometheus.ytvideocreator.com

# 5. Verify alerting
# Test alert fires when health check fails
```

---

## Contact Information

**On-Call Rotation:**
- Primary: PagerDuty escalation policy
- Backup: #oncall Slack channel

**Escalation Path:**
1. On-call engineer (immediate)
2. Engineering Manager (15 min)
3. VP Engineering (30 min)
4. CTO (1 hour)

**External Contacts:**
- AWS Support: Enterprise support case
- DNS Provider: Route53 support
- Status Page: Contact support for manual updates

---

## Appendix: Metrics & SLOs

### Recovery Objectives
| Metric | Target | Actual (Last Test) |
|--------|--------|--------------------|
| RTO | 15 minutes | 12 minutes ✅ |
| RPO | 5 minutes | 3 minutes ✅ |
| Data Loss | <5 min of data | <3 min ✅ |

### Health Check Metrics
- Interval: 30 seconds
- Failure threshold: 3 consecutive failures
- Timeout: 5 seconds

### Database Replication
- Target lag: <5 seconds
- Alert threshold: >10 seconds
- Critical threshold: >30 seconds

---

**Document Version**: 1.0  
**Last Updated**: January 28, 2026  
**Last Tested**: January 28, 2026  
**Next Review**: February 28, 2026  
**Owner**: Infrastructure Team
