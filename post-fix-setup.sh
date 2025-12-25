#!/bin/bash
# Post-Fix Setup Script
# Run this after pulling the latest fixes

echo "=== Elson Trading Platform - Post-Fix Setup ==="
echo ""

# Colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# Check if we're in the right directory
if [ ! -f "README.md" ]; then
    echo -e "${RED}Error: Please run this script from the repository root${NC}"
    exit 1
fi

echo -e "${YELLOW}Step 1: Backend Setup${NC}"
cd backend

# Create virtual environment if it doesn't exist
if [ ! -d "venv" ]; then
    echo "Creating Python virtual environment..."
    python3 -m venv venv
fi

# Activate virtual environment
echo "Activating virtual environment..."
source venv/bin/activate

# Install dependencies
echo "Installing Python dependencies..."
pip install -r ../requirements.txt

# Generate database migration
echo "Generating Alembic migration..."
alembic revision --autogenerate -m "Apply all model fixes and add subscription models"

# Apply migration
echo "Applying database migration..."
alembic upgrade head

# Test database initialization
echo "Testing database initialization..."
python -c "from app.db.init_db import init_db; init_db(); print('✓ Database initialized successfully')"

# Test model imports
echo "Testing model imports..."
python -c "from app.models import user, portfolio, trade, market_data, holding, notification, subscription; print('✓ All models imported successfully')"

echo -e "${GREEN}✓ Backend setup complete${NC}"
echo ""

cd ..

echo -e "${YELLOW}Step 2: Frontend Setup${NC}"
cd frontend

# Install dependencies (already done, but check)
if [ ! -d "node_modules" ]; then
    echo "Installing Node dependencies..."
    npm install
fi

# Run audit fix
echo "Fixing npm security issues..."
npm audit fix || echo -e "${YELLOW}⚠ Some vulnerabilities require manual review${NC}"

# Test TypeScript compilation
echo "Testing TypeScript compilation..."
npx tsc --noEmit && echo -e "${GREEN}✓ TypeScript compilation successful${NC}" || echo -e "${RED}✗ TypeScript has errors${NC}"

# Run tests
echo "Running frontend tests..."
CI=true npm test -- --passWithNoTests && echo -e "${GREEN}✓ Frontend tests passed${NC}" || echo -e "${YELLOW}⚠ Some tests failed${NC}"

# Build production bundle
echo "Building production bundle..."
npm run build && echo -e "${GREEN}✓ Production build successful${NC}" || echo -e "${RED}✗ Build failed${NC}"

echo -e "${GREEN}✓ Frontend setup complete${NC}"
echo ""

cd ..

echo -e "${YELLOW}Step 3: Environment Configuration${NC}"

# Check if .env exists
if [ ! -f ".env" ]; then
    echo "Creating .env file from .env.example..."
    cp .env.example .env
    echo -e "${YELLOW}⚠ Please edit .env and add your API keys:${NC}"
    echo "  - ALPACA_API_KEY"
    echo "  - ALPACA_SECRET_KEY"
    echo "  - ALPHA_VANTAGE_API_KEY (optional)"
    echo "  - POLYGON_API_KEY (optional)"
    echo "  - STRIPE_API_KEY (optional, for payments)"
    echo "  - SECRET_KEY (generate a secure random string)"
else
    echo -e "${GREEN}✓ .env file already exists${NC}"
fi

echo ""
echo -e "${YELLOW}Step 4: Verification${NC}"

# Run backend tests
echo "Running backend tests..."
cd backend
pytest || echo -e "${YELLOW}⚠ Some backend tests failed${NC}"
cd ..

echo ""
echo -e "${GREEN}=== Setup Complete ===${NC}"
echo ""
echo "Next steps:"
echo "1. Edit .env and add your API keys"
echo "2. Start the backend: cd backend && python -m app.main"
echo "3. Start the frontend: cd frontend && npm start"
echo "4. Open http://localhost:3000 in your browser"
echo ""
echo "For production deployment, see DEPLOYMENT_GUIDE.md"
