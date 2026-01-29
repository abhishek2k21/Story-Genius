# Production Runbooks

**Last Updated**: January 28, 2026  
**Audience**: DevOps, SRE, On-Call Engineers

---

## Table of Contents
1. [Common Incidents](#common-incidents)
2. [Emergency Procedures](#emergency-procedures)
3. [Deployment Procedures](#deployment-procedures)
4. [Rollback Procedures](#rollback-procedures)

---

## Common Incidents

### 🚨 Incident 1: High CPU Usage

**Symptoms**:
- CPU > 80% sustained
- Slow API response times
- Application lag

**Investigation**:
```bash
# 1. Check pod CPU usage
kubectl top pods -n production

# 2. Check HPA status
kubectl get hpa -n production

# 3. Check pod events
kubectl describe pod <pod-name> -n production

# 4. Review Grafana CPU dashboard
# URL: https://grafana.ytvideocreator.com/d/cpu-usage
```

**Resolution**:
```bash
# 1. Scale horizontally (immediate relief)
kubectl scale deployment app-backend --replicas=10 -n production

# 2. Check for CPU-intensive queries
# Connect to database and check slow queries

# 3. Check for infinite loops or memory leaks
kubectl logs <pod-name> -n production --tail=100

# 4. Restart affected pods if needed
kubectl rollout restart deployment app-backend -n production
```

**Prevention**:
- Set resource limits correctly
- Monitor CPU trends
- Optimize expensive operations

---

### 🚨 Incident 2: Database Connection Pool Exhausted

**Symptoms**:
- `FATAL: remaining connection slots are reserved for non-replication superuser connections`
- `Too many connections` errors
- 500 errors from API

**Investigation**:
```sql
-- Check active connections
SELECT count(*) FROM pg_stat_activity;

-- Check connections by state
SELECT state, count(*) 
FROM pg_stat_activity 
GROUP BY state;

-- Find idle connections
SELECT pid, state, query_start 
FROM pg_stat_activity 
WHERE state = 'idle' 
AND query_start < NOW() - INTERVAL '10 minutes';
```

**Resolution**:
```bash
# 1. Increase connection pool (temporary)
# Edit app-backend values.yaml:
# database:
#   pool_size: 100  # from 50

# 2. Kill idle connections (if safe)
SELECT pg_terminate_backend(pid) 
FROM pg_stat_activity 
WHERE state = 'idle' 
AND query_start < NOW() - INTERVAL '30 minutes';

# 3. Restart application pods
kubectl rollout restart deployment app-backend -n production

# 4. Check for connection leaks in code
# Review database session management
```

**Prevention**:
- Use connection pooling correctly
- Close connections properly
- Monitor connection usage
- Set appropriate pool sizes

---

### 🚨 Incident 3: OAuth Token Validation Failing

**Symptoms**:
- Mass 401 Unauthorized errors
- Users unable to authenticate
- "Invalid token" errors

**Investigation**:
```bash
# 1. Check JWT keys secret
kubectl get secret jwt-keys -n production -o yaml

# 2. Verify JWKS endpoint
curl https://api.ytvideocreator.com/oauth/jwks.json

# 3. Check Redis (token revocation list)
kubectl exec -it redis-0 -n production -- redis-cli
> KEYS token:*
> DBSIZE

# 4. Check pod logs
kubectl logs deployment/app-backend -n production | grep -i "jwt\|token"
```

**Resolution**:
```bash
# 1. Verify key rotation didn't break validation
# Check if public/private keys match

# 2. Clear Redis token cache if corrupted
kubectl exec -it redis-0 -n production -- redis-cli
> FLUSHDB

# 3. Restart app pods to reload keys
kubectl rollout restart deployment app-backend -n production

# 4. If keys are corrupted, regenerate
# (LAST RESORT - will invalidate all tokens)
python scripts/generate_jwt_keys.py
kubectl create secret generic jwt-keys \
  --from-file=private=jwt-private.pem \
  --from-file=public=jwt-public.pem \
  --dry-run=client -o yaml | kubectl apply -f -
```

**Prevention**:
- Test key rotation thoroughly
- Have key backup strategy
- Monitor authentication success rate

---

### 🚨 Incident 4: S3 Upload Failures

**Symptoms**:
- Video uploads failing
- 403 Forbidden from S3
- Upload timeout errors

**Investigation**:
```bash
# 1. Check S3 bucket permissions
aws s3api get-bucket-policy --bucket ytvideocreator-media

# 2. Check IAM role
kubectl describe serviceaccount app-backend -n production

# 3. Test S3 access from pod
kubectl exec -it deployment/app-backend -n production -- \
  aws s3 ls s3://ytvideocreator-media/

# 4. Check KMS key access
aws kms describe-key --key-id <key-id>
```

**Resolution**:
```bash
# 1. Verify IAM role has S3 permissions
aws iam get-role-policy --role-name eks-app-backend-role --policy-name S3Access

# 2. Check S3 bucket policy
# Ensure upload policy allows PutObject

# 3. Verify KMS key permissions
# Check key policy allows Encrypt/Decrypt

# 4. Retry failed uploads
# Check upload queue and retry
```

**Prevention**:
- Monitor upload success rate
- Set up CloudWatch alarms for S3 errors
- Test IAM permissions regularly

---

### 🚨 Incident 5: High Memory Usage / OOMKilled

**Symptoms**:
- Pods being OOMKilled
- Memory > 90% sustained
- CrashLoopBackOff

**Investigation**:
```bash
# 1. Check memory usage
kubectl top pods -n production

# 2. Check pod events for OOMKilled
kubectl get events -n production --sort-by='.lastTimestamp' | grep OOM

# 3. Check memory limits
kubectl describe deployment app-backend -n production | grep -A 5 "Limits:"

# 4. Profile application memory usage
# Use memory profiler in staging first
```

**Resolution**:
```bash
# 1. Increase memory limits (if justified)
# Edit values.yaml:
# resources:
#   limits:
#     memory: 2Gi  # from 1Gi

# 2. Scale horizontally to spread load
kubectl scale deployment app-backend --replicas=10 -n production

# 3. Check for memory leaks
kubectl logs <pod-name> -n production --previous

# 4. Restart deployment
kubectl rollout restart deployment app-backend -n production
```

**Prevention**:
- Set appropriate resource limits
- Monitor memory trends
- Fix memory leaks
- Use memory profiling in development

---

## Emergency Procedures

### 🔥 Complete System Outage

**Immediate Actions** (< 5 minutes):
1. **Verify outage**: Check health endpoints, Pingdom, UptimeRobot
2. **Page on-call**: PagerDuty high-urgency alert
3. **Post status**: Update status page (status.ytvideocreator.com)
4. **Check cluster**: `kubectl get nodes`, `kubectl get pods -A`

**Investigation** (5-15 minutes):
```bash
# Check cluster health
kubectl get nodes
kubectl get pods -A --field-selector=status.phase!=Running

# Check ingress
kubectl get ingress -n production
kubectl logs -n ingress-nginx deployment/ingress-nginx-controller

# Check database
kubectl exec -it postgres-0 -n production -- psql -U postgres -c "SELECT 1;"

# Check Redis
kubectl exec -it redis-0 -n production -- redis-cli ping
```

**Resolution**:
1. Fix root cause
2. If unknown cause: rollback last deployment
3. If infrastructure issue: failover to backup region
4. Post-incident review within 48 hours

---

### 🔥 Data Breach Detected

**CRITICAL - Follow Incident Response Plan**

**Immediate Actions** (< 15 minutes):
1.  **Contain**: Isolate affected systems
2. **Notify**: CISO, Legal, PR team
3. **Preserve**: Take snapshots, logs, forensics
4. **Document**: Start incident timeline

**Investigation**:
- Determine scope of breach
- Identify compromised data
- Find attack vector
- Assess impact

**Remediation**:
- Patch vulnerabilities
- Rotate all credentials
- Revoke compromised tokens
- Notify affected users (if PII)
- Notify authorities (GDPR - 72 hours)

**Reference**: `docs/incident_response_plan.md`

---

## Deployment Procedures

### Standard Deployment

```bash
# 1. Merge PR to main (triggers CI/CD)
git checkout main
git merge feature-branch

# 2. CI/CD automatically:
#    - Runs tests
#    - Builds Docker image
#    - Scans for vulnerabilities
#    - Deploys to staging
#    - Runs smoke tests

# 3. Approve production deployment
# Review GitHub Actions workflow
# Click "Approve deployment to production"

# 4. Monitor deployment
kubectl rollout status deployment/app-backend -n production

# 5. Verify health
curl https://api.ytvideocreator.com/health/live

# 6. Run smoke tests
python scripts/smoke_tests.py --env=production
```

---

## Rollback Procedures

### Rollback Deployment

```bash
# 1. Rollback to previous version
helm rollback app-backend -n production

# OR use kubectl
kubectl rollout undo deployment/app-backend -n production

# 2. Verify rollback
kubectl rollout status deployment/app-backend -n production

# 3. Check health
curl https://api.ytvideocreator.com/health/live

# 4. Notify team
# Post in #deployments Slack channel
```

---

## Contact Information

| Role | Contact | Phone | Escalation |
|------|---------|-------|------------|
| **On-Call (Primary)** | PagerDuty auto-rotates | N/A | Auto |
| **On-Call (Secondary)** | PagerDuty auto-rotates | N/A | 30 min |
| **CISO** | security@ytvideocreator.com | +1-XXX-XXX-XXXX | Security incidents |
| **CTO** | cto@ytvideocreator.com | +1-XXX-XXX-XXXX | Critical outages |

---

## Additional Resources

- **Architecture Docs**: `docs/architecture_overview.md`
- **Security Guide**: `docs/security_checklist.md`
- **DR Plan**: `docs/disaster_recovery_plan.md`
- **Monitoring**: https://grafana.ytvideocreator.com
- **Alerts**: https://alertmanager.ytvideocreator.com
- **Status Page**: https://status.ytvideocreator.com
