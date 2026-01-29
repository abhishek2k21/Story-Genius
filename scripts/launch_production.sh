#!/bin/bash
# Production Launch Script
# Automates the production deployment and go-live process

set -e  # Exit on error

echo "========================================="
echo "  PRODUCTION LAUNCH SCRIPT"
echo "========================================="
echo ""

# Colors for output
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Configuration
NAMESPACE="production"
RELEASE_NAME="app-backend"
HELM_CHART="./infra/helm/app-backend"
VALUES_FILE="values-production.yaml"

# Functions
check_prereq() {
    echo -e "${YELLOW}Checking prerequisites...${NC}"
    
    # Check kubectl
    if ! command -v kubectl &> /dev/null; then
        echo -e "${RED}❌ kubectl not found${NC}"
        exit 1
    fi
    
    # Check helm
    if ! command -v helm &> /dev/null; then
        echo -e "${RED}❌ helm not found${NC}"
        exit 1
    fi
    
    # Check cluster connection
    if ! kubectl cluster-info &> /dev/null; then
        echo -e "${RED}❌ Cannot connect to cluster${NC}"
        exit 1
    fi
    
    echo -e "${GREEN}✅ Prerequisites OK${NC}"
}

run_pre_launch_tests() {
    echo -e "${YELLOW}Running pre-launch tests...${NC}"
    
    # Run smoke tests in staging
    python scripts/smoke_tests.py --env=staging
    
    # Run security scan
    echo "Running security scan..."
    trivy image --severity HIGH,CRITICAL app-backend:latest
    
    # Check for vulnerabilities
    echo "Checking dependencies..."
    pip-audit
    
    echo -e "${GREEN}✅ Pre-launch tests passed${NC}"
}

backup_database() {
    echo -e "${YELLOW}Creating database backup...${NC}"
    
    BACKUP_FILE="pre_launch_$(date +%Y%m%d_%H%M%S).dump"
    
    kubectl exec -it postgres-0 -n ${NAMESPACE} -- \
        pg_dump -U postgres -F c -b -v -f /backup/${BACKUP_FILE}
    
    echo -e "${GREEN}✅ Database backup created: ${BACKUP_FILE}${NC}"
}

deploy_to_production() {
    echo -e "${YELLOW}Deploying to production...${NC}"
    
    # Upgrade with Helm
    helm upgrade ${RELEASE_NAME} ${HELM_CHART} \
        --namespace ${NAMESPACE} \
        --values ${VALUES_FILE} \
        --wait \
        --timeout 10m
    
    echo -e "${GREEN}✅ Deployment complete${NC}"
}

verify_deployment() {
    echo -e "${YELLOW}Verifying deployment...${NC}"
    
    # Check rollout status
    kubectl rollout status deployment/${RELEASE_NAME} -n ${NAMESPACE}
    
    # Check all pods are running
    PODS_READY=$(kubectl get pods -n ${NAMESPACE} -l app=${RELEASE_NAME} --field-selector=status.phase=Running --no-headers | wc -l)
    PODS_TOTAL=$(kubectl get pods -n ${NAMESPACE} -l app=${RELEASE_NAME} --no-headers | wc -l)
    
    if [ "$PODS_READY" -eq "$PODS_TOTAL" ]; then
        echo -e "${GREEN}✅ All pods running (${PODS_READY}/${PODS_TOTAL})${NC}"
    else
        echo -e "${RED}❌ Not all pods running (${PODS_READY}/${PODS_TOTAL})${NC}"
        exit 1
    fi
    
    # Check health endpoint
    echo "Checking health endpoint..."
    sleep 10  # Wait for pods to be fully ready
    
    HEALTH_STATUS=$(curl -s -o /dev/null -w "%{http_code}" https://api.ytvideocreator.com/health/live)
    
    if [ "$HEALTH_STATUS" -eq 200 ]; then
        echo -e "${GREEN}✅ Health check passed${NC}"
    else
        echo -e "${RED}❌ Health check failed (HTTP ${HEALTH_STATUS})${NC}"
        exit 1
    fi
}

run_smoke_tests() {
    echo -e "${YELLOW}Running smoke tests...${NC}"
    
    python scripts/smoke_tests.py --env=production
    
    echo -e "${GREEN}✅ Smoke tests passed${NC}"
}

update_status_page() {
    echo -e "${YELLOW}Updating status page...${NC}"
    
    curl -X POST https://status.ytvideocreator.com/api/update \
        -H "Content-Type: application/json" \
        -d '{"status": "operational", "message": "Platform successfully launched to production! 🚀"}'
    
    echo -e "${GREEN}✅ Status page updated${NC}"
}

send_notifications() {
    echo -e "${YELLOW}Sending launch notifications...${NC}"
    
    # Slack notification
    curl -X POST ${SLACK_WEBHOOK_URL} \
        -H "Content-Type: application/json" \
        -d '{
            "text": "🚀 *PRODUCTION LAUNCH SUCCESSFUL!*",
            "attachments": [{
                "color": "good",
                "fields": [
                    {"title": "Status", "value": "✅ Live", "short": true},
                    {"title": "Time", "value": "'"$(date)"'", "short": true},
                    {"title": "URL", "value": "https://ytvideocreator.com", "short": false}
                ]
            }]
        }'
    
    echo -e "${GREEN}✅ Notifications sent${NC}"
}

# Main execution
main() {
    echo "Starting production launch at $(date)"
    echo ""
    
    # Confirmation
    echo -e "${YELLOW}⚠️  This will deploy to PRODUCTION${NC}"
    read -p "Are you sure you want to proceed? (yes/no): " CONFIRM
    
    if [ "$CONFIRM" != "yes" ]; then
        echo "Launch cancelled."
        exit 0
    fi
    
    echo ""
    
    # Execute launch steps
    check_prereq
    echo ""
    
    run_pre_launch_tests
    echo ""
    
    backup_database
    echo ""
    
    deploy_to_production
    echo ""
    
    verify_deployment
    echo ""
    
    run_smoke_tests
    echo ""
    
    update_status_page
    echo ""
    
    send_notifications
    echo ""
    
    echo "========================================="
    echo -e "${GREEN}✅ PRODUCTION LAUNCH COMPLETE!${NC}"
    echo "========================================="
    echo ""
    echo "Next steps:"
    echo "1. Monitor dashboards: https://grafana.ytvideocreator.com"
    echo "2. Check logs: kubectl logs -n ${NAMESPACE} -l app=${RELEASE_NAME} -f"
    echo "3. Run launch monitoring: python scripts/launch_monitoring.py"
    echo "4. Update team in #deployments Slack channel"
    echo ""
    echo "Launch completed at $(date)"
}

# Run main function
main
