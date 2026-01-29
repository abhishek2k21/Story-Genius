#!/bin/bash
# Vault Setup and Configuration Script

set -e

echo "🔐 Initializing HashiCorp Vault..."

# Wait for Vault to be ready
kubectl wait --for=condition=ready pod -l app.kubernetes.io/name=vault -n vault --timeout=300s

# Get Vault pod
VAULT_POD=$(kubectl get pods -n vault -l app.kubernetes.io/name=vault,component=server -o jsonpath='{.items[0].metadata.name}')

echo "Using Vault pod: $VAULT_POD"

# Initialize Vault (only on first run)
echo "Initializing Vault..."
kubectl exec -n vault $VAULT_POD -- vault operator init \
  -key-shares=5 \
  -key-threshold=3 \
  -format=json > vault-keys.json

echo "✅ Vault initialized. Keys saved to vault-keys.json"
echo "⚠️  IMPORTANT: Store vault-keys.json securely and delete it from this server!"

# Vault should auto-unseal with AWS KMS
sleep 5

# Enable Kubernetes auth
echo "Enabling Kubernetes authentication..."
kubectl exec -n vault $VAULT_POD -- vault auth enable kubernetes

# Configure Kubernetes auth
echo "Configuring Kubernetes auth..."
kubectl exec -n vault $VAULT_POD -- vault write auth/kubernetes/config \
  kubernetes_host="https://kubernetes.default.svc:443"

# Create policies
echo "Creating Vault policies..."

# API Backend policy
kubectl exec -n vault $VAULT_POD -- vault policy write app-backend - <<EOF
# Allow reading secrets
path "secret/data/app-backend/*" {
  capabilities = ["read"]
}

# Allow listing secrets
path "secret/metadata/app-backend/*" {
  capabilities = ["list"]
}

# Allow reading database credentials
path "database/creds/app-backend" {
  capabilities = ["read"]
}
EOF

# Worker policy
kubectl exec -n vault $VAULT_POD  -- vault policy write worker - <<EOF
# Allow reading secrets
path "secret/data/worker/*" {
  capabilities = ["read"]
}

# Allow reading database credentials
path "database/creds/worker" {
  capabilities = ["read"]
}

# Allow reading AWS credentials
path "aws/creds/worker" {
  capabilities = ["read"]
}
EOF

# Create Kubernetes auth roles
echo "Creating Kubernetes auth roles..."

# API Backend role
kubectl exec -n vault $VAULT_POD -- vault write auth/kubernetes/role/app-backend \
  bound_service_account_names=api-service-account \
  bound_service_account_namespaces=production \
  policies=app-backend \
  ttl=1h

# Worker role
kubectl exec -n vault $VAULT_POD -- vault write auth/kubernetes/role/worker \
  bound_service_account_names=worker-service-account \
  bound_service_account_namespaces=production \
  policies=worker \
  ttl=1h

# Enable KV secrets engine
echo "Enabling KV secrets engine..."
kubectl exec -n vault $VAULT_POD -- vault secrets enable -version=2 -path=secret kv

# Enable database secrets engine
echo "Enabling database secrets engine..."
kubectl exec -n vault $VAULT_POD -- vault secrets enable database

# Configure PostgreSQL connection
echo "Configuring PostgreSQL connection..."
kubectl exec -n vault $VAULT_POD -- vault write database/config/postgresql \
  plugin_name=postgresql-database-plugin \
  allowed_roles="app-backend,worker" \
  connection_url="postgresql://{{username}}:{{password}}@postgres-ha:5432/yt_video_creator?sslmode=require" \
  username="vault" \
  password="VAULT_DB_PASSWORD"

# Create database role for app-backend
kubectl exec -n vault $VAULT_POD -- vault write database/roles/app-backend \
  db_name=postgresql \
  creation_statements="CREATE ROLE \"{{name}}\" WITH LOGIN PASSWORD '{{password}}' VALID UNTIL '{{expiration}}'; \
    GRANT SELECT, INSERT, UPDATE, DELETE ON ALL TABLES IN SCHEMA public TO \"{{name}}\";" \
  default_ttl="1h" \
  max_ttl="24h"

# Create database role for worker
kubectl exec -n vault $VAULT_POD -- vault write database/roles/worker \
  db_name=postgresql \
  creation_statements="CREATE ROLE \"{{name}}\" WITH LOGIN PASSWORD '{{password}}' VALID UNTIL '{{expiration}}'; \
    GRANT SELECT, INSERT, UPDATE, DELETE ON ALL TABLES IN SCHEMA public TO \"{{name}}\";" \
  default_ttl="1h" \
  max_ttl="24h"

# Write initial secrets
echo "Writing initial secrets..."
kubectl exec -n vault $VAULT_POD -- vault kv put secret/app-backend/config \
  database_url="postgresql://app:password@postgres-ha:5432/yt_video_creator" \
  redis_url="redis://redis-ha:6379/0" \
  jwt_secret="CHANGE_ME_IN_PRODUCTION" \
  api_key="CHANGE_ME_IN_PRODUCTION"

kubectl exec -n vault $VAULT_POD -- vault kv put secret/worker/config \
  database_url="postgresql://worker:password@postgres-ha:5432/yt_video_creator" \
  redis_url="redis://redis-ha:6379/0" \
  aws_access_key_id="CHANGE_ME" \
  aws_secret_access_key="CHANGE_ME"

echo "✅ Vault setup complete!"
echo ""
echo "Next steps:"
echo "1. Securely store vault-keys.json"
echo "2. Update secrets with production values"
echo "3. Configure automatic secret rotation"
echo "4. Deploy Vault Secrets Operator"
