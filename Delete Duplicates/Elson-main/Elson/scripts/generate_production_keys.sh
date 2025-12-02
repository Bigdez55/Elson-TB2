#!/bin/bash
#
# Production Key Generation Script for Elson Wealth Platform
# This script generates secure keys and secrets for production deployment
#
# DO NOT COMMIT THE OUTPUT OF THIS SCRIPT TO VERSION CONTROL
# STORE THE GENERATED KEYS SECURELY IN A PASSWORD MANAGER OR SECRET STORE
#

set -e
echo "Elson Wealth Platform - Production Key Generation"
echo "================================================="
echo ""
echo "This script will generate secure random keys for production use."
echo "The generated keys should be stored securely and used during deployment."
echo ""

# Create a temporary directory
TEMP_DIR=$(mktemp -d)
echo "Working in temporary directory: $TEMP_DIR"
cd "$TEMP_DIR"

# Generate a secure random SECRET_KEY (64 characters)
echo "Generating SECRET_KEY for application authentication..."
SECRET_KEY=$(openssl rand -hex 32)
echo "SECRET_KEY=$SECRET_KEY"
echo ""

# Generate JWT secret key
echo "Generating JWT_SECRET_KEY for token signing..."
JWT_SECRET_KEY=$(openssl rand -hex 32)
echo "JWT_SECRET_KEY=$JWT_SECRET_KEY"
echo ""

# Generate encryption keys
echo "Generating ENCRYPTION_KEY for field encryption..."
ENCRYPTION_KEY=$(openssl rand -base64 32)
echo "ENCRYPTION_KEY=$ENCRYPTION_KEY"
echo ""

# Generate Redis password
echo "Generating REDIS_PASSWORD..."
REDIS_PASSWORD=$(openssl rand -hex 20)
echo "REDIS_PASSWORD=$REDIS_PASSWORD"
echo ""

# Generate admin credentials
echo "Generating initial admin password..."
ADMIN_PASSWORD=$(openssl rand -base64 15)
echo "ADMIN_PASSWORD=$ADMIN_PASSWORD"
echo ""

# Generate webhook signing secrets
echo "Generating WEBHOOK_SECRET for secure callbacks..."
WEBHOOK_SECRET=$(openssl rand -hex 24)
echo "WEBHOOK_SECRET=$WEBHOOK_SECRET"
echo ""

# Generate self-signed TLS certificates for development/staging
echo "Generating self-signed TLS certificates for Vault..."
# Generate CA
openssl genrsa -out ca.key 4096
openssl req -new -x509 -key ca.key -out ca.crt -days 3650 -subj "/CN=ElsonWealthCA/O=Elson Wealth"

# Generate Vault certificate
openssl genrsa -out vault.key 2048
openssl req -new -key vault.key -out vault.csr -subj "/CN=vault.elson.svc.cluster.local/O=Elson"
openssl x509 -req -in vault.csr -CA ca.crt -CAkey ca.key -CAcreateserial -out vault.crt -days 3650

# Create Kubernetes secrets in YAML format
echo "Creating Kubernetes secret YAML files..."

# Application secrets
cat > app-secrets.yaml << EOF
apiVersion: v1
kind: Secret
metadata:
  name: app-secrets
  namespace: elson
type: Opaque
stringData:
  SECRET_KEY: "${SECRET_KEY}"
  JWT_SECRET_KEY: "${JWT_SECRET_KEY}"
  ENCRYPTION_KEY: "${ENCRYPTION_KEY}"
EOF

# Database secrets
cat > db-secrets.yaml << EOF
apiVersion: v1
kind: Secret
metadata:
  name: db-secrets
  namespace: elson
type: Opaque
stringData:
  POSTGRES_USER: "elson_prod"
  POSTGRES_PASSWORD: "$(openssl rand -hex 16)"
  POSTGRES_DB: "elson_production"
EOF

# Redis secrets
cat > redis-secrets.yaml << EOF
apiVersion: v1
kind: Secret
metadata:
  name: redis-secrets
  namespace: elson
type: Opaque
stringData:
  REDIS_PASSWORD: "${REDIS_PASSWORD}"
EOF

# Vault TLS
cat > vault-tls.yaml << EOF
apiVersion: v1
kind: Secret
metadata:
  name: vault-tls
  namespace: elson
type: kubernetes.io/tls
data:
  tls.crt: $(cat vault.crt | base64 -w 0)
  tls.key: $(cat vault.key | base64 -w 0)
  ca.crt: $(cat ca.crt | base64 -w 0)
EOF

echo ""
echo "Generated secrets in YAML format in $TEMP_DIR:"
ls -la *.yaml

echo ""
echo "===================================================================="
echo "IMPORTANT: These are your production credentials."
echo "Keep these secure and do not commit them to version control."
echo "Store them in a secure password manager or HashiCorp Vault."
echo "===================================================================="
echo ""
echo "Next steps:"
echo "1. Apply these secrets to your Kubernetes cluster:"
echo "   kubectl apply -f $TEMP_DIR/*.yaml"
echo ""
echo "2. Initialize Vault after deployment:"
echo "   kubectl exec -it vault-0 -- vault operator init"
echo ""
echo "3. Unseal Vault with the keys provided in the previous step"
echo "   kubectl exec -it vault-0 -- vault operator unseal <key1>"
echo "   kubectl exec -it vault-0 -- vault operator unseal <key2>"
echo "   kubectl exec -it vault-0 -- vault operator unseal <key3>"
echo ""
echo "4. Store your production secrets in Vault:"
echo "   kubectl exec -it vault-0 -- /bin/sh"
echo "   vault login <root-token>"
echo "   vault secrets enable -path=kv kv-v2"
echo "   vault kv put kv/app secret_key='$SECRET_KEY' redis_url='redis://:$REDIS_PASSWORD@redis:6379/0'"
echo ""