#!/bin/bash

# Deploy script for Elson project

# Set root directory
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" &> /dev/null && pwd)"
ROOT_DIR="$(dirname "$SCRIPT_DIR")"

# Output colorization
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# Default values
ENVIRONMENT="dev"
BUILD_IMAGES=true
PUSH_IMAGES=false
DEPLOY=false
TAG="latest"
DOCKER_REGISTRY="docker.io"
DOCKER_NAMESPACE="elson"

# Display usage information
usage() {
    echo "Usage: $0 [options]"
    echo ""
    echo "Options:"
    echo "  --environment, -e <env>     Deployment environment (dev, staging, prod) [default: dev]"
    echo "  --tag, -t <tag>             Docker image tag [default: latest]"
    echo "  --build, -b                 Build Docker images [default: true]"
    echo "  --push, -p                  Push Docker images to registry [default: false]"
    echo "  --deploy, -d                Deploy to Kubernetes [default: false]"
    echo "  --registry, -r <registry>   Docker registry [default: docker.io]"
    echo "  --namespace, -n <namespace> Docker namespace [default: elson]"
    echo "  --help, -h                  Display this help message"
    echo ""
    echo "Examples:"
    echo "  $0 -e staging -t v1.0.0 -b -p -d  # Build, push, and deploy v1.0.0 to staging"
    echo "  $0 -e prod -t v1.0.0 -d          # Deploy existing v1.0.0 images to production"
}

# Parse command-line arguments
while [[ $# -gt 0 ]]; do
    case "$1" in
        --environment|-e)
            ENVIRONMENT="$2"
            shift 2
            ;;
        --tag|-t)
            TAG="$2"
            shift 2
            ;;
        --build|-b)
            BUILD_IMAGES=true
            shift
            ;;
        --no-build)
            BUILD_IMAGES=false
            shift
            ;;
        --push|-p)
            PUSH_IMAGES=true
            shift
            ;;
        --deploy|-d)
            DEPLOY=true
            shift
            ;;
        --registry|-r)
            DOCKER_REGISTRY="$2"
            shift 2
            ;;
        --namespace|-n)
            DOCKER_NAMESPACE="$2"
            shift 2
            ;;
        --help|-h)
            usage
            exit 0
            ;;
        *)
            echo -e "${RED}Unknown option: $1${NC}"
            usage
            exit 1
            ;;
    esac
done

# Validate environment
if [[ ! "$ENVIRONMENT" =~ ^(dev|staging|prod)$ ]]; then
    echo -e "${RED}Invalid environment: $ENVIRONMENT. Must be dev, staging, or prod.${NC}"
    exit 1
fi

# Show deployment information
echo -e "${GREEN}Deployment Configuration:${NC}"
echo -e "  Environment:      ${YELLOW}$ENVIRONMENT${NC}"
echo -e "  Tag:              ${YELLOW}$TAG${NC}"
echo -e "  Docker Registry:  ${YELLOW}$DOCKER_REGISTRY${NC}"
echo -e "  Docker Namespace: ${YELLOW}$DOCKER_NAMESPACE${NC}"
echo -e "  Build Images:     ${YELLOW}$BUILD_IMAGES${NC}"
echo -e "  Push Images:      ${YELLOW}$PUSH_IMAGES${NC}"
echo -e "  Deploy:           ${YELLOW}$DEPLOY${NC}"
echo

# Confirm deployment
read -p "Are you sure you want to proceed? (y/n) " -n 1 -r
echo
if [[ ! $REPLY =~ ^[Yy]$ ]]; then
    echo -e "${YELLOW}Deployment canceled.${NC}"
    exit 0
fi

# Build docker images
if [ "$BUILD_IMAGES" = true ]; then
    echo -e "\n${GREEN}Building Docker images...${NC}"
    
    echo -e "${YELLOW}Building backend image...${NC}"
    docker build -t $DOCKER_REGISTRY/$DOCKER_NAMESPACE/elson-backend:$TAG -f $ROOT_DIR/Elson/backend/Dockerfile $ROOT_DIR/Elson/backend
    
    echo -e "${YELLOW}Building frontend image...${NC}"
    docker build -t $DOCKER_REGISTRY/$DOCKER_NAMESPACE/elson-frontend:$TAG -f $ROOT_DIR/Elson/frontend/Dockerfile $ROOT_DIR/Elson/frontend
    
    echo -e "${YELLOW}Building trading engine image...${NC}"
    docker build -t $DOCKER_REGISTRY/$DOCKER_NAMESPACE/elson-trading-engine:$TAG -f $ROOT_DIR/Elson/trading_engine/Dockerfile $ROOT_DIR/Elson/trading_engine
fi

# Push Docker images
if [ "$PUSH_IMAGES" = true ]; then
    echo -e "\n${GREEN}Pushing Docker images...${NC}"
    
    # Check if user is logged in to Docker registry
    if ! docker info | grep -q "Username"; then
        echo -e "${YELLOW}Not logged in to Docker registry. Please login:${NC}"
        docker login $DOCKER_REGISTRY
    fi
    
    echo -e "${YELLOW}Pushing backend image...${NC}"
    docker push $DOCKER_REGISTRY/$DOCKER_NAMESPACE/elson-backend:$TAG
    
    echo -e "${YELLOW}Pushing frontend image...${NC}"
    docker push $DOCKER_REGISTRY/$DOCKER_NAMESPACE/elson-frontend:$TAG
    
    echo -e "${YELLOW}Pushing trading engine image...${NC}"
    docker push $DOCKER_REGISTRY/$DOCKER_NAMESPACE/elson-trading-engine:$TAG
fi

# Deploy to Kubernetes
if [ "$DEPLOY" = true ]; then
    echo -e "\n${GREEN}Deploying to Kubernetes...${NC}"
    
    # Check if kubectl is installed
    if ! command -v kubectl &> /dev/null; then
        echo -e "${RED}kubectl is not installed. Please install kubectl and try again.${NC}"
        exit 1
    fi
    
    # Set environment variables for Kubernetes deployment
    export DOCKER_REGISTRY=$DOCKER_REGISTRY
    export DOCKER_NAMESPACE=$DOCKER_NAMESPACE
    export DOCKER_TAG=$TAG
    
    # Apply Kubernetes configurations
    echo -e "${YELLOW}Creating namespace...${NC}"
    kubectl apply -f $ROOT_DIR/Elson/infrastructure/kubernetes/namespace.yaml
    
    echo -e "${YELLOW}Applying secrets...${NC}"
    # Load environment variables from file based on environment
    ENV_FILE="$ROOT_DIR/Elson/.env.$ENVIRONMENT"
    if [ -f "$ENV_FILE" ]; then
        # Export environment variables
        export $(grep -v '^#' $ENV_FILE | xargs)
        # Apply secrets with environment variable substitution
        envsubst < $ROOT_DIR/Elson/infrastructure/kubernetes/secrets.yaml | kubectl apply -f -
    else
        echo -e "${RED}Environment file $ENV_FILE not found.${NC}"
        exit 1
    fi
    
    echo -e "${YELLOW}Deploying database...${NC}"
    envsubst < $ROOT_DIR/Elson/infrastructure/kubernetes/postgres.yaml | kubectl apply -f -
    
    echo -e "${YELLOW}Deploying Redis...${NC}"
    kubectl apply -f $ROOT_DIR/Elson/infrastructure/kubernetes/redis.yaml
    
    echo -e "${YELLOW}Deploying backend...${NC}"
    envsubst < $ROOT_DIR/Elson/infrastructure/kubernetes/backend.yaml | kubectl apply -f -
    
    echo -e "${YELLOW}Deploying frontend...${NC}"
    envsubst < $ROOT_DIR/Elson/infrastructure/kubernetes/frontend.yaml | kubectl apply -f -
    
    echo -e "${YELLOW}Deploying trading engine...${NC}"
    envsubst < $ROOT_DIR/Elson/infrastructure/kubernetes/trading-engine.yaml | kubectl apply -f -
    
    echo -e "${YELLOW}Deploying ingress...${NC}"
    kubectl apply -f $ROOT_DIR/Elson/infrastructure/kubernetes/ingress.yaml
    
    echo -e "${GREEN}Deployment to Kubernetes completed!${NC}"
fi

echo -e "\n${GREEN}Deployment process completed!${NC}"