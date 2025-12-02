#!/bin/bash

# Start development environment for Elson

# Set root directory
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" &> /dev/null && pwd)"
ROOT_DIR="$(dirname "$SCRIPT_DIR")"

# Output colorization
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "${GREEN}Starting Elson development environment...${NC}"

# Create log directories if they don't exist
mkdir -p "$ROOT_DIR/logs/postgres"
mkdir -p "$ROOT_DIR/logs/redis"

# Check if docker-compose is installed
if ! command -v docker-compose &> /dev/null; then
    echo -e "${YELLOW}docker-compose could not be found. Please install Docker and docker-compose.${NC}"
    exit 1
fi

# Start docker containers
echo -e "${GREEN}Starting Docker containers...${NC}"
cd "$ROOT_DIR" && docker-compose -f docker-compose.dev.yml up -d

# Wait for services to be ready
echo -e "${GREEN}Waiting for services to be ready...${NC}"
sleep 5

# Apply database migrations
echo -e "${GREEN}Applying database migrations...${NC}"
docker-compose -f docker-compose.dev.yml exec backend alembic upgrade head

echo -e "${GREEN}Development environment is ready!${NC}"
echo -e "${GREEN}Backend API: http://localhost:8000${NC}"
echo -e "${GREEN}Frontend:    http://localhost:5173${NC}"
echo -e "${GREEN}pgAdmin:     http://localhost:5050${NC}"
echo -e "${GREEN}PostgreSQL:  localhost:5432${NC}"
echo -e "${GREEN}Redis:       localhost:6379${NC}"

echo
echo -e "${YELLOW}To view logs:${NC}"
echo -e "docker-compose -f docker-compose.dev.yml logs -f"
echo
echo -e "${YELLOW}To stop the environment:${NC}"
echo -e "docker-compose -f docker-compose.dev.yml down"