#!/bin/bash

# One-click deployment script for Elson development environment
# This script handles environment setup, Docker container management,
# and development environment configuration.

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
echo -e "${GREEN}Wealth App Development Environment${NC}\n"

# Set project root directory
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" &> /dev/null && pwd)"
PROJECT_ROOT="$SCRIPT_DIR"

# Check prerequisites
echo -e "${BLUE}Checking prerequisites...${NC}"

# Check Docker
if ! command -v docker &> /dev/null; then
    echo -e "${RED}Docker is not installed. Please install Docker first.${NC}"
    exit 1
fi

# Check Docker Compose
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

# Free up disk space by pruning unused Docker resources
echo -e "${BLUE}Freeing up disk space...${NC}"
docker system prune -af --volumes
echo -e "${GREEN}Disk space freed.${NC}"

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

# Build and start the Docker containers
echo -e "${BLUE}Building and starting containers...${NC}"
cd "$PROJECT_ROOT"
docker-compose -f docker-compose.dev.yml build
docker-compose -f docker-compose.dev.yml up -d

# Wait for services to be ready
echo -e "${BLUE}Waiting for services to be ready...${NC}"
echo -e "${YELLOW}This may take a few minutes for the first startup...${NC}"
sleep 10

# Apply database migrations
echo -e "${BLUE}Applying database migrations...${NC}"
docker-compose -f docker-compose.dev.yml exec backend alembic upgrade head

echo -e "${GREEN}=====================================${NC}"
echo -e "${GREEN}Environment successfully deployed!${NC}"
echo -e "${GREEN}=====================================${NC}"
echo
echo -e "${YELLOW}Services:${NC}"
echo -e "${BLUE}Backend API:${NC} http://localhost:8000"
echo -e "${BLUE}Frontend:${NC}   http://localhost:3000"
echo -e "${BLUE}PostgreSQL:${NC} localhost:5432"
echo -e "${BLUE}Redis:${NC}      localhost:6379"
echo
echo -e "${YELLOW}Commands:${NC}"
echo -e "${BLUE}View logs:${NC} docker-compose -f docker-compose.dev.yml logs -f"
echo -e "${BLUE}Stop:${NC}     docker-compose -f docker-compose.dev.yml down"
echo
echo -e "${YELLOW}Testing WebSocket functionality:${NC}"
echo -e "1. Open your browser to ${BLUE}http://localhost:3000${NC}"
echo -e "2. Login with the default credentials"
echo -e "3. Navigate to the Trading page to see live WebSocket data"
echo -e "4. Create a paper trading portfolio to test trading features"
echo
echo -e "${GREEN}Happy coding!${NC}"

# Make the script executable
chmod +x "$PROJECT_ROOT/deploy-dev.sh"