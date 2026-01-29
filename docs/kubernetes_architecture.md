# Kubernetes Architecture

## Overview
Production-ready Kubernetes deployment on AWS EKS for the YT Video Creator platform.

## Cluster Configuration

### Control Plane
- **Provider**: AWS EKS (Managed Kubernetes)
- **Version**: 1.28
- **Region**: us-east-1
- **High Availability**: Multi-AZ deployment across 3 availability zones

### Worker Nodes
- **Initial Size**: 3 nodes
- **Auto-scaling Range**: 3-10 nodes
- **Availability Zones**: us-east-1a, us-east-1b, us-east-1c

## Node Pools

### 1. General Purpose Pool
- **Instance Type**: t3.large
- **vCPU**: 2
- **Memory**: 8 GB
- **Use Case**: API services, general workloads
- **Initial Count**: 2 nodes

### 2. Compute Optimized Pool
- **Instance Type**: c5.xlarge
- **vCPU**: 4
- **Memory**: 8 GB
- **Use Case**: Video processing, CPU-intensive tasks
- **Initial Count**: 1 node
- **Auto-scaling**: Based on queue depth

### 3. Memory Optimized Pool (Optional)
- **Instance Type**: r5.large
- **vCPU**: 2
- **Memory**: 16 GB
- **Use Case**: Analytics, large datasets
- **Initial Count**: 0 nodes (on-demand)

## Namespaces

### Production (`production`)
**Purpose**: Production workloads
**Services**:
- API Gateway
- Worker Pods (video generation)
- Scheduler
- Background Jobs

**Resource Quotas**:
- CPU: 20 cores
- Memory: 40 GB
- Pods: 100
- Services: 50

### Staging (`staging`)
**Purpose**: Pre-production testing
**Resource Quotas**:
- CPU: 10 cores
- Memory: 20 GB
- Pods: 50

### System (`system`)
**Purpose**: Cluster infrastructure services
**Components**:
- NGINX Ingress Controller
- cert-manager (Let's Encrypt)
- External DNS
- Metrics Server

### Monitoring (`monitoring`)
**Purpose**: Observability stack
**Components**:
- Prometheus
- Grafana
- AlertManager
- Jaeger (distributed tracing)

## Storage Classes

### 1. General Purpose SSD (`gp3`)
- **Type**: AWS EBS gp3
- **IOPS**: 3,000
- **Throughput**: 125 MB/s
- **Reclaim Policy**: Retain
- **Use Case**: Database volumes, logs
- **Volume Expansion**: Enabled

### 2. Provisioned IOPS SSD (`io2`)
- **Type**: AWS EBS io2
- **IOPS**: 10,000+
- **Use Case**: High-performance databases
- **Reclaim Policy**: Retain

### 3. Elastic File System (`efs`)
- **Type**: AWS EFS
- **Access Mode**: ReadWriteMany
- **Use Case**: Shared storage, video files
- **Performance Mode**: General Purpose

## Network Architecture

### VPC Configuration
- **CIDR Block**: 10.0.0.0/16
- **Public Subnets**: 10.0.1.0/24, 10.0.2.0/24, 10.0.3.0/24 (3 AZs)
- **Private Subnets**: 10.0.11.0/24, 10.0.12.0/24, 10.0.13.0/24 (3 AZs)

### Security Groups
- **Control Plane SG**: API server access (443)
- **Worker Node SG**: Pod communication, NodePort services
- **Database SG**: PostgreSQL (5432), Redis (6379)

### Network Policies
- Default deny all ingress
- Allow egress to internet (NAT Gateway)
- Allow inter-pod communication within namespace
- Allow ingress from ingress controller

## Ingress Configuration

### NGINX Ingress Controller
- **Type**: LoadBalancer (AWS NLB)
- **SSL Termination**: Yes (Let's Encrypt)
- **Rate Limiting**: 100 req/s per IP
- **Timeout**: 60 seconds

### Routes
```
api.ytvideocreator.com → api-service:8000
app.ytvideocreator.com → frontend-service:3000
admin.ytvideocreator.com → admin-service:8000
```

## Resource Quotas (Production Namespace)

```yaml
spec:
  hard:
    requests.cpu: "20"
    requests.memory: 40Gi
    limits.cpu: "40"
    limits.memory: 80Gi
    pods: "100"
    services: "50"
    persistentvolumeclaims: "20"
```

## Pod Resource Allocation

### API Service
- **Requests**: CPU 500m, Memory 1Gi
- **Limits**: CPU 2000m, Memory 4Gi
- **Replicas**: 3-10 (HPA)

### Worker Service
- **Requests**: CPU 1000m, Memory 2Gi
- **Limits**: CPU 4000m, Memory 8Gi
- **Replicas**: 2-50 (Queue-based scaling)

### Database (PostgreSQL)
- **Requests**: CPU 1000m, Memory 4Gi
- **Limits**: CPU 2000m, Memory 8Gi
- **Replicas**: 1 (StatefulSet)
- **Storage**: 50 GB (gp3)

## High Availability

### Pod Distribution
- **Anti-affinity**: Spread pods across nodes
- **Topology Spread**: Distribute across AZs
- **Pod Disruption Budget**: Min available 2 pods

### Health Checks
- **Liveness Probe**: HTTP GET /health (30s delay, 10s interval)
- **Readiness Probe**: HTTP GET /ready (5s delay, 5s interval)

## Disaster Recovery

### Backup Strategy
- **Database Backups**: Daily at 2 AM UTC (AWS Backup)
- **Retention**: 30 days
- **Cross-region Copy**: us-west-2
- **EBS Snapshots**: Automated daily

### Recovery Objectives
- **RTO** (Recovery Time Objective): 1 hour
- **RPO** (Recovery Point Objective): 24 hours

## Monitoring & Logging

### Metrics
- **Cluster Metrics**: Node CPU, memory, disk
- **Pod Metrics**: Container CPU, memory, restarts
- **Application Metrics**: Request rate, latency, errors

### Logging
- **Control Plane Logs**: API server, audit, authenticator
- **Application Logs**: stdout/stderr → CloudWatch Logs
- **Retention**: 30 days

### Alerting
- Node down
- Pod crash loop
- High CPU/memory (>80%)
- High latency (p99 > 1s)

## Scaling Strategy

### Horizontal Pod Autoscaling (HPA)
- **Metric**: CPU utilization (target 70%)
- **Min Replicas**: 2
- **Max Replicas**: 50
- **Scale Up**: 1 pod/30s
- **Scale Down**: 1 pod/5min

### Cluster Autoscaling
- **Scale Up**: When pods are unschedulable
- **Scale Down**: When node utilization < 50% for 10 minutes
- **Max Nodes**: 10

## Security

### Authentication
- **AWS IAM**: Service accounts with IRSA (IAM Roles for Service Accounts)
- **RBAC**: Role-based access control per namespace

### Secrets Management
- **AWS Secrets Manager**: Database credentials, API keys
- **Sealed Secrets**: Encrypted secrets in Git
- **Volume Mounts**: Secrets mounted as files

### Image Security
- **Image Scanning**: Trivy (vulnerability scanning)
- **Image Signing**: Cosign (container signing)
- **Private Registry**: AWS ECR

## Cost Optimization

### Instance Selection
- **On-Demand**: Control plane nodes (stability)
- **Spot Instances**: Worker nodes (80% cost saving)
- **Reserved Instances**: Long-term workloads (40% saving)

### Resource Efficiency
- **Right-sizing**: Match requests to actual usage
- **Auto-scaling**: Scale down during off-peak
- **Storage Lifecycle**: Archive old backups to S3 Glacier

### Estimated Monthly Cost
- **EKS Control Plane**: $73
- **EC2 Instances** (3x t3.large): ~$150
- **EBS Storage** (100 GB): ~$10
- **Load Balancer**: ~$20
- **Data Transfer**: ~$50
- **Total**: ~$300/month (baseline)

## Deployment Strategy

### Blue-Green Deployment
- Deploy to staging namespace
- Run smoke tests
- Switch traffic to new version
- Keep old version for 1 hour (rollback)

### Canary Deployment
- Route 10% traffic to new version
- Monitor error rates
- Gradually increase to 100%

### Rollback Procedure
- Helm rollback to previous release
- Deployment reversal via kubectl
- Target rollback time: < 5 minutes

## Success Metrics

- ✅ Cluster uptime: 99.9%
- ✅ Pod startup time: < 60 seconds
- ✅ Deployment time: < 10 minutes
- ✅ Auto-scaling response: < 2 minutes
- ✅ Request latency (p99): < 200ms
- ✅ Monthly cost: < $500

---

**Document Version**: 1.0  
**Last Updated**: January 28, 2026  
**Owner**: Infrastructure Team
