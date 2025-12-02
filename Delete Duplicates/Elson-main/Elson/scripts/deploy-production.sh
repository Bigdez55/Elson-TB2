#!/bin/bash
# Production Deployment Script for Elson Wealth App
# This script sets up the production environment and performs validation checks before deployment

set -e

# Define colors for better readability
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "${GREEN}===== Elson Wealth App Production Deployment =====${NC}"
echo -e "${YELLOW}This script will perform the following actions:${NC}"
echo "1. Validate environment configuration"
echo "2. Check and create Kubernetes secrets"
echo "3. Apply Kubernetes manifests"
echo "4. Execute database migrations"
echo "5. Verify deployment status"
echo ""

# Validate environment settings
validate_environment() {
    echo -e "${GREEN}Validating environment settings...${NC}"
    
    # Check if .env.production exists
    if [ ! -f "./backend/.env.production" ]; then
        echo -e "${RED}Error: ./backend/.env.production not found.${NC}"
        echo "Create this file with appropriate production settings before continuing."
        exit 1
    fi
    
    # Run validation script
    cd backend && python -m app.scripts.validate_env --env-file .env.production
    
    # Check if validation passes
    if [ $? -ne 0 ]; then
        echo -e "${RED}Environment validation failed. Please fix the issues before deploying.${NC}"
        exit 1
    fi
    
    echo -e "${GREEN}Environment validation successful.${NC}"
    cd ..
}

# Check and create Kubernetes secrets
setup_kubernetes_secrets() {
    echo -e "${GREEN}Setting up Kubernetes secrets...${NC}"
    
    echo -e "${YELLOW}Checking kubectl access...${NC}"
    kubectl get namespace elson 2>/dev/null || kubectl create namespace elson
    
    echo -e "${YELLOW}Checking HashiCorp Vault access...${NC}"
    if ! command -v vault &> /dev/null; then
        echo -e "${RED}Error: HashiCorp Vault CLI not found. Please install it first.${NC}"
        echo "Visit https://www.vaultproject.io/downloads for installation instructions."
        exit 1
    fi
    
    # Check Vault authentication
    echo -e "${YELLOW}Authenticating with Vault...${NC}"
    
    # This is a placeholder. In a real production environment, you would:
    # 1. Authenticate with Vault using appropriate method (token, approle, kubernetes, etc.)
    # 2. Retrieve secrets from Vault
    # 3. Create Kubernetes secrets using the retrieved values
    
    echo -e "${YELLOW}This is a simulation - in real production deployment:${NC}"
    echo "Would authenticate with Vault and retrieve secrets"
    echo "Would use kubectl create secret to create actual secrets with Vault values"
    echo "Would validate secret creation"
    
    # Example of how to create a real secret (commented out for simulation)
    # kubectl create secret generic backend-secrets \
    #   --namespace=elson \
    #   --from-literal=DATABASE_URL="$(vault kv get -field=DATABASE_URL elson/secrets/prod)" \
    #   --from-literal=SECRET_KEY="$(vault kv get -field=SECRET_KEY elson/secrets/prod)" \
    #   --from-literal=REDIS_URL="$(vault kv get -field=REDIS_URL elson/secrets/prod)" \
    #   --from-literal=REDIS_PASSWORD="$(vault kv get -field=REDIS_PASSWORD elson/secrets/prod)" \
    #   --dry-run=client -o yaml | kubectl apply -f -
    
    echo -e "${GREEN}Kubernetes secrets setup completed.${NC}"
}

# Apply Kubernetes manifests
apply_kubernetes_manifests() {
    echo -e "${GREEN}Applying Kubernetes manifests...${NC}"
    
    echo -e "${YELLOW}Applying ConfigMaps...${NC}"
    kubectl apply -f ./infrastructure/kubernetes/production/configmaps.yaml
    
    echo -e "${YELLOW}Applying Secrets (placeholder values for demo)...${NC}"
    # In production, secrets would be handled by a secure process, not directly applied
    kubectl apply -f ./infrastructure/kubernetes/production/secrets.yaml
    
    echo -e "${YELLOW}Applying Postgres resources...${NC}"
    kubectl apply -f ./infrastructure/kubernetes/production/postgres-statefulset.yaml
    kubectl apply -f ./infrastructure/kubernetes/production/postgres-service.yaml
    kubectl apply -f ./infrastructure/kubernetes/production/postgres-pvc.yaml
    
    echo -e "${YELLOW}Applying Redis resources...${NC}"
    kubectl apply -f ./infrastructure/kubernetes/production/redis-statefulset.yaml
    kubectl apply -f ./infrastructure/kubernetes/production/redis-service.yaml
    kubectl apply -f ./infrastructure/kubernetes/production/redis-pvc.yaml
    
    echo -e "${YELLOW}Applying Backend Deployment...${NC}"
    kubectl apply -f ./infrastructure/kubernetes/production/backend-deployment.yaml
    kubectl apply -f ./infrastructure/kubernetes/production/backend-service.yaml
    
    echo -e "${YELLOW}Applying WebSocket Deployment...${NC}"
    kubectl apply -f ./infrastructure/kubernetes/production/websocket-deployment.yaml
    kubectl apply -f ./infrastructure/kubernetes/production/websocket-service.yaml
    
    echo -e "${YELLOW}Applying Frontend Deployment...${NC}"
    kubectl apply -f ./infrastructure/kubernetes/production/frontend-deployment.yaml
    kubectl apply -f ./infrastructure/kubernetes/production/frontend-service.yaml
    
    echo -e "${YELLOW}Applying Trading Engine Deployment...${NC}"
    kubectl apply -f ./infrastructure/kubernetes/production/trading-engine-deployment.yaml
    kubectl apply -f ./infrastructure/kubernetes/production/trading-engine-service.yaml
    
    echo -e "${YELLOW}Applying Network Policies...${NC}"
    kubectl apply -f ./infrastructure/kubernetes/production/network-policies.yaml
    
    echo -e "${YELLOW}Applying Horizontal Pod Autoscalers...${NC}"
    kubectl apply -f ./infrastructure/kubernetes/production/hpa.yaml
    
    echo -e "${YELLOW}Applying Pod Disruption Budgets...${NC}"
    kubectl apply -f ./infrastructure/kubernetes/production/pdb.yaml
    
    echo -e "${YELLOW}Applying Ingress Resources...${NC}"
    kubectl apply -f ./infrastructure/kubernetes/production/ingress.yaml
    
    echo -e "${YELLOW}Applying Recurring Jobs...${NC}"
    kubectl apply -f ./infrastructure/kubernetes/production/recurring-jobs.yaml
    
    echo -e "${GREEN}Kubernetes manifests applied successfully.${NC}"
}

# Execute database migrations
execute_database_migrations() {
    echo -e "${GREEN}Executing database migrations...${NC}"
    
    # Wait for backend to be ready
    echo -e "${YELLOW}Waiting for backend deployment to be ready...${NC}"
    kubectl rollout status deployment/elson-backend -n elson
    
    # Execute migrations
    echo -e "${YELLOW}Running database migrations...${NC}"
    kubectl exec -it -n elson $(kubectl get pods -n elson -l app=elson-backend -o jsonpath="{.items[0].metadata.name}") -- alembic upgrade head
    
    echo -e "${GREEN}Database migrations completed successfully.${NC}"
}

# Verify deployment status
verify_deployment() {
    echo -e "${GREEN}Verifying deployment status...${NC}"
    
    echo -e "${YELLOW}Checking deployments...${NC}"
    kubectl get deployments -n elson
    
    echo -e "${YELLOW}Checking services...${NC}"
    kubectl get services -n elson
    
    echo -e "${YELLOW}Checking pods...${NC}"
    kubectl get pods -n elson
    
    echo -e "${YELLOW}Checking persistent volume claims...${NC}"
    kubectl get pvc -n elson
    
    echo -e "${YELLOW}Checking ingress...${NC}"
    kubectl get ingress -n elson
    
    # Check health endpoints
    echo -e "${YELLOW}Checking backend health endpoint...${NC}"
    # This would typically use the ingress URL, but for simulation we're checking locally
    echo "Simulating health check at https://api.elsonwealth.com/health"
    
    echo -e "${YELLOW}Checking WebSocket health endpoint...${NC}"
    echo "Simulating health check at https://ws.elsonwealth.com/health"
    
    # Check WebSocket connectivity
    echo -e "${YELLOW}Testing WebSocket connectivity...${NC}"
    echo "Simulating WebSocket connection test to wss://ws.elsonwealth.com/ws/market/feed"
    
    echo -e "${GREEN}Deployment verification completed.${NC}"
}

# Main execution flow
main() {
    validate_environment
    
    # Ask for confirmation before proceeding
    read -p "Continue with production deployment? (y/n) " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        echo -e "${YELLOW}Deployment cancelled.${NC}"
        exit 0
    fi
    
    setup_kubernetes_secrets
    apply_kubernetes_manifests
    execute_database_migrations
    verify_deployment
    
    echo -e "${GREEN}===== Production deployment completed successfully! =====${NC}"
    echo -e "${YELLOW}Important post-deployment steps:${NC}"
    echo "1. Monitor application logs for any errors"
    echo "2. Verify front-end functionality"
    echo "3. Check database performance and connections"
    echo "4. Verify payment processing with test transactions"
    echo "5. Test WebSocket real-time market data"
}

# Execute main function
main