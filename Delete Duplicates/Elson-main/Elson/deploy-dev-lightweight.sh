#!/bin/bash

# Lightweight deployment script for Elson development environment
# Optimized for environments with limited disk space

set -e

# Color codes for better output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Print banner
echo -e "${BLUE}"
echo "███████╗██╗     ███████╗ ██████╗ ███╗   ██╗"
echo "██╔════╝██║     ██╔════╝██╔═══██╗████╗  ██║"
echo "█████╗  ██║     ███████╗██║   ██║██╔██╗ ██║"
echo "██╔══╝  ██║     ╚════██║██║   ██║██║╚██╗██║"
echo "███████╗███████╗███████║╚██████╔╝██║ ╚████║"
echo "╚══════╝╚══════╝╚══════╝ ╚═════╝ ╚═╝  ╚═══╝"
echo -e "${NC}"
echo -e "${GREEN}Lightweight Development Environment${NC}\n"

# Set project root directory
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" &> /dev/null && pwd)"
PROJECT_ROOT="$SCRIPT_DIR"

# Check prerequisites
echo -e "${BLUE}Checking prerequisites...${NC}"
if ! command -v docker &> /dev/null; then
    echo -e "${RED}Docker is not installed. Please install Docker first.${NC}"
    exit 1
fi
if ! command -v docker-compose &> /dev/null; then
    echo -e "${RED}Docker Compose is not installed. Please install Docker Compose first.${NC}"
    exit 1
fi
echo -e "${GREEN}Prerequisites met.${NC}"

# Create necessary directories
echo -e "${BLUE}Setting up directories...${NC}"
mkdir -p "$PROJECT_ROOT/logs/postgres"
mkdir -p "$PROJECT_ROOT/logs/redis"
echo -e "${GREEN}Directories created.${NC}"

# Clean up any existing containers
echo -e "${BLUE}Cleaning up existing environment...${NC}"
cd "$PROJECT_ROOT"
docker-compose -f docker-compose.dev.yml down 2>/dev/null || true
echo -e "${GREEN}Environment cleaned.${NC}"

# Aggressive disk space cleanup
echo -e "${BLUE}Performing aggressive disk space cleanup...${NC}"

# Remove all unused containers, networks, images, and volumes
echo -e "${YELLOW}Removing all unused Docker resources...${NC}"
docker system prune -af --volumes

# Remove all dangling images
echo -e "${YELLOW}Removing dangling images...${NC}"
docker rmi $(docker images -f "dangling=true" -q) 2>/dev/null || true

# Remove all exited containers
echo -e "${YELLOW}Removing exited containers...${NC}"
docker rm $(docker ps -a -f status=exited -q) 2>/dev/null || true

# Remove build cache
echo -e "${YELLOW}Cleaning Docker build cache...${NC}"
docker builder prune -af

# Check available space
available_space=$(df -h / | awk 'NR==2 {print $4}')
echo -e "${GREEN}Available disk space after cleanup: ${available_space}${NC}"

# Modify the docker-compose file for lightweight deployment
echo -e "${BLUE}Configuring for lightweight deployment...${NC}"

# Create a lightweight version of docker-compose.dev.yml
cat > "$PROJECT_ROOT/docker-compose.lightweight.yml" << EOF
version: '3.8'
services:
  db:
    image: postgres:14-alpine
    environment:
      POSTGRES_USER: \${DB_USER:-elson}
      POSTGRES_PASSWORD: \${DB_PASSWORD:-elsondev}
      POSTGRES_DB: \${DB_NAME:-elson_trading}
    ports:
      - "5432:5432"
    volumes:
      - postgres_data:/var/lib/postgresql/data
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U \${DB_USER:-elson}"]
      interval: 5s
      timeout: 5s
      retries: 5

  redis:
    image: redis:alpine
    ports:
      - "6379:6379"
    volumes:
      - redis_data:/data
    healthcheck:
      test: ["CMD", "redis-cli", "ping"]
      interval: 5s
      timeout: 5s
      retries: 5

volumes:
  postgres_data:
  redis_data:
EOF

echo -e "${GREEN}Lightweight configuration created.${NC}"

# Fix the frontend Dockerfile.dev if needed
echo -e "${BLUE}Checking frontend Dockerfile...${NC}"
DOCKERFILE="$PROJECT_ROOT/frontend/Dockerfile.dev"
if grep -q "unsafe-perm" "$DOCKERFILE"; then
    echo -e "${YELLOW}Fixing unsafe-perm issue in frontend Dockerfile.dev...${NC}"
    sed -i 's/npm config set unsafe-perm true && \\//g' "$DOCKERFILE"
    echo -e "${GREEN}Dockerfile fixed.${NC}"
else
    echo -e "${GREEN}Dockerfile already fixed.${NC}"
fi

# Check & set up environment variables
echo -e "${BLUE}Setting up environment variables...${NC}"
ENV_FILE="$PROJECT_ROOT/.env"
if [ ! -f "$ENV_FILE" ]; then
    echo -e "${YELLOW}Creating default .env file...${NC}"
    cat > "$ENV_FILE" << EOF
# Database settings
DB_USER=elson
DB_PASSWORD=elsondev
DB_NAME=elson_trading

# Security
SECRET_KEY=development_secret_key_do_not_use_in_production
SECRET_BACKEND=env

# Integration settings
SCHWAB_API_KEY=dummy_key
SCHWAB_SECRET=dummy_secret

# Alerting
SLACK_ENABLED=false
PAGERDUTY_ENABLED=false
ON_CALL_ROTATION_ENABLED=false

# Debug settings
DEBUG=true
EOF
    echo -e "${GREEN}.env file created.${NC}"
else
    echo -e "${GREEN}.env file already exists.${NC}"
fi

# Build and start the lightweight containers
echo -e "${BLUE}Starting lightweight environment (database and cache only)...${NC}"
cd "$PROJECT_ROOT"
docker-compose -f docker-compose.lightweight.yml up -d

# Wait for services to be ready
echo -e "${BLUE}Waiting for basic services to be ready...${NC}"
sleep 10

echo -e "${GREEN}=====================================${NC}"
echo -e "${GREEN}Lightweight environment deployed!${NC}"
echo -e "${GREEN}=====================================${NC}"
echo
echo -e "${YELLOW}Services:${NC}"
echo -e "${BLUE}PostgreSQL:${NC} localhost:5432"
echo -e "${BLUE}Redis:${NC}      localhost:6379"
echo
echo -e "${YELLOW}Next steps:${NC}"
echo -e "1. ${BLUE}Run the backend locally:${NC}"
echo -e "   cd $PROJECT_ROOT/backend"
echo -e "   pip install -r requirements.txt"
echo -e "   uvicorn app.main:app --reload --host 0.0.0.0 --port 8000"
echo
echo -e "2. ${BLUE}Run the frontend locally:${NC}"
echo -e "   cd $PROJECT_ROOT/frontend"
echo -e "   npm install"
echo -e "   npm run dev"
echo
echo -e "${YELLOW}Commands:${NC}"
echo -e "${BLUE}View logs:${NC} docker-compose -f docker-compose.lightweight.yml logs -f"
echo -e "${BLUE}Stop:${NC}     docker-compose -f docker-compose.lightweight.yml down"
echo
echo -e "${GREEN}Happy coding!${NC}"

# Make the script executable
chmod +x "$PROJECT_ROOT/deploy-dev-lightweight.sh"