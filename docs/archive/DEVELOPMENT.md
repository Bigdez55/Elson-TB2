# Development Guide

## 🚀 Getting Started

This guide will help you set up and develop the Elson Wealth Platform locally.

## 📋 Prerequisites

### Required Software

- **Python 3.12+** - Backend development
- **Node.js 18+** - Frontend development  
- **PostgreSQL 15+** - Primary database
- **Redis 7+** - Caching and sessions
- **Docker & Docker Compose** - Containerized development
- **Git** - Version control

### Development Tools

- **VS Code** with Python and TypeScript extensions
- **Postman** or **Insomnia** for API testing
- **pgAdmin** or **DBeaver** for database management
- **Redis CLI** or **RedisInsight** for Redis management

## 🔧 Environment Setup

### 1. Clone and Setup Repository

```bash
# Clone the repository
git clone <repository-url>
cd Elson

# Install pre-commit hooks
pip install pre-commit
pre-commit install

# Copy environment configuration
cp config/development.env.example config/development.env
# Edit config/development.env with your settings
```

### 2. Backend Setup

```bash
cd Elson/backend

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
pip install -r requirements-dev.txt

# Set up database
createdb elson_dev
alembic upgrade head

# Initialize sample data (optional)
python -m app.scripts.init_sample_data
```

### 3. Frontend Setup

```bash
cd Elson/frontend

# Install dependencies
npm install

# Start development server
npm run dev
```

### 4. Database Setup

```bash
# Create PostgreSQL databases
createdb elson_dev
createdb elson_test

# Run database migrations
cd Elson/backend
alembic upgrade head
```

### 5. Redis Setup

```bash
# Start Redis server
redis-server

# Verify Redis is running
redis-cli ping
# Should return: PONG
```

## 🐳 Docker Development

### Quick Start with Docker Compose

```bash
# Start all services
docker-compose -f development/docker/docker-compose.dev.yml up

# Start specific services
docker-compose up postgres redis

# Stop all services
docker-compose down
```

### Individual Service Setup

```bash
# Backend only
cd Elson/backend
docker build -f Dockerfile.dev -t elson-backend-dev .
docker run -p 8000:8000 --env-file ../config/development.env elson-backend-dev

# Frontend only
cd Elson/frontend
docker build -f Dockerfile.dev -t elson-frontend-dev .
docker run -p 3000:3000 elson-frontend-dev
```

## 🏃‍♂️ Running the Application

### Development Servers

```bash
# Backend (FastAPI with auto-reload)
cd Elson/backend
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

# Frontend (Vite with HMR)
cd Elson/frontend
npm run dev

# WebSocket Server (if needed separately)
cd Elson/backend
python run_websocket.py
```

### Access Points

- **Frontend:** http://localhost:3000
- **Backend API:** http://localhost:8000
- **API Documentation:** http://localhost:8000/docs
- **WebSocket:** ws://localhost:8001

## 📁 Project Structure Deep Dive

### Backend Architecture

```
backend/
├── app/
│   ├── core/                   # Core functionality
│   │   ├── auth/              # Authentication & authorization
│   │   ├── config.py          # Configuration management
│   │   ├── database.py        # Database setup
│   │   ├── security.py        # Security utilities
│   │   └── middleware.py      # FastAPI middleware
│   ├── models/                # SQLAlchemy models
│   │   ├── user.py           # User and authentication
│   │   ├── portfolio.py      # Portfolio and positions
│   │   ├── trade.py          # Trading and orders
│   │   └── account.py        # Account management
│   ├── routes/               # API route definitions
│   │   ├── api_v1/          # Version 1 API endpoints
│   │   └── websocket/       # WebSocket endpoints
│   ├── services/            # Business logic layer
│   │   ├── broker/          # Broker integrations
│   │   ├── external_api/    # External API clients
│   │   ├── trading.py       # Trading logic
│   │   └── portfolio.py     # Portfolio management
│   ├── schemas/             # Pydantic schemas
│   └── tests/               # Test suites
├── alembic/                 # Database migrations
└── scripts/                 # Utility scripts
```

### Frontend Architecture

```
frontend/src/
├── app/                     # Main application
│   ├── components/         # React components
│   │   ├── common/        # Reusable components
│   │   ├── auth/          # Authentication components
│   │   ├── trading/       # Trading interface
│   │   └── portfolio/     # Portfolio management
│   ├── hooks/             # Custom React hooks
│   ├── services/          # API service layer
│   ├── store/             # Redux store and slices
│   └── utils/             # Utility functions
├── pages/                 # Page components
└── types/                 # TypeScript type definitions
```

### Trading Engine Architecture

```
trading_engine/
├── strategies/            # Trading strategies
├── ai_model_engine/      # AI/ML models
├── engine/               # Core trading engine
├── backtesting/          # Strategy backtesting
└── tests/                # Trading engine tests
```

## 🧪 Testing Strategy

### Backend Testing

```bash
cd Elson/backend

# Run all tests
pytest

# Run with coverage
pytest --cov=app --cov-report=html

# Run specific test categories
pytest app/tests/unit/
pytest app/tests/integration/
pytest app/tests/e2e/

# Run specific test file
pytest app/tests/test_auth.py -v
```

### Frontend Testing

```bash
cd Elson/frontend

# Run all tests
npm test

# Run tests in watch mode
npm run test:watch

# Run tests with coverage
npm run test:coverage

# Run specific test file
npm test -- --run Portfolio.test.tsx
```

### Trading Engine Testing

```bash
cd Elson

# Run trading engine tests
python -m pytest trading_engine/tests/ -v

# Run strategy backtests
python -m pytest trading_engine/backtesting/ -v
```

## 🔍 Debugging

### Backend Debugging

#### VS Code Launch Configuration

```json
{
    "name": "FastAPI Debug",
    "type": "python",
    "request": "launch",
    "program": "${workspaceFolder}/Elson/backend/app/main.py",
    "console": "integratedTerminal",
    "envFile": "${workspaceFolder}/config/development.env",
    "args": ["--reload"]
}
```

#### Debug with pdb

```python
import pdb; pdb.set_trace()

# Or use ipdb for enhanced debugging
import ipdb; ipdb.set_trace()
```

### Frontend Debugging

#### Browser DevTools
- **React DevTools** - Component inspection
- **Redux DevTools** - State debugging
- **Network Tab** - API call debugging

#### VS Code Debugging

```json
{
    "name": "Frontend Debug",
    "type": "node",
    "request": "launch",
    "program": "${workspaceFolder}/Elson/frontend/node_modules/.bin/vite",
    "args": ["--host", "0.0.0.0"],
    "console": "integratedTerminal"
}
```

## 📊 Database Management

### Migrations

```bash
cd Elson/backend

# Create new migration
alembic revision --autogenerate -m "Description of changes"

# Apply migrations
alembic upgrade head

# Downgrade migration
alembic downgrade -1

# Check current revision
alembic current

# View migration history
alembic history
```

### Database Utilities

```bash
# Reset database (development only)
python -m app.scripts.reset_database

# Seed sample data
python -m app.scripts.seed_data

# Backup database
python -m app.scripts.backup_database

# Check data integrity
python -m app.scripts.check_data_integrity
```

## 🔧 Development Workflows

### Feature Development

1. **Create feature branch**
   ```bash
   git checkout -b feature/your-feature-name
   ```

2. **Implement feature**
   - Write tests first (TDD approach)
   - Implement functionality
   - Ensure tests pass

3. **Quality checks**
   ```bash
   # Backend
   cd Elson/backend
   black . && isort . && flake8 .
   pytest

   # Frontend  
   cd Elson/frontend
   npm run lint && npm run typecheck
   npm test
   ```

4. **Commit and push**
   ```bash
   git add .
   git commit -m "feat: implement your feature"
   git push origin feature/your-feature-name
   ```

5. **Create pull request**

### Hot Reloading

Both backend and frontend support hot reloading:

- **Backend:** FastAPI auto-reloads on file changes
- **Frontend:** Vite HMR updates components instantly
- **WebSocket:** Restart required for WebSocket server changes

## 🔒 Security Considerations

### Development Security

- **Never commit secrets** to version control
- **Use .env files** for local configuration
- **Rotate API keys** regularly
- **Use HTTPS** even in development when possible

### Testing Security

```bash
# Run security scans
bandit -r app/
safety check
npm audit

# Check for secrets in code
git secrets --scan
```

## 🐛 Common Issues & Solutions

### Backend Issues

**Issue:** Database connection errors
```bash
# Solution: Check PostgreSQL service
sudo service postgresql start
psql -U postgres -l
```

**Issue:** Redis connection errors
```bash
# Solution: Start Redis server
redis-server
redis-cli ping
```

**Issue:** Import errors
```bash
# Solution: Check PYTHONPATH
export PYTHONPATH="${PYTHONPATH}:$(pwd)"
```

### Frontend Issues

**Issue:** Node modules issues
```bash
# Solution: Clean install
rm -rf node_modules package-lock.json
npm install
```

**Issue:** TypeScript errors
```bash
# Solution: Check TypeScript configuration
npm run typecheck
```

**Issue:** Build failures
```bash
# Solution: Clear cache and rebuild
npm run clean
npm run build
```

## 📈 Performance Monitoring

### Backend Monitoring

```python
# Add performance logging
import time
start_time = time.time()
# Your code here
logger.info(f"Operation took {time.time() - start_time:.2f} seconds")
```

### Frontend Monitoring

```javascript
// Use React DevTools Profiler
// Monitor component render times
// Check for unnecessary re-renders
```

### Database Monitoring

```sql
-- Check slow queries
SELECT query, mean_time, calls
FROM pg_stat_statements
ORDER BY mean_time DESC
LIMIT 10;
```

## 🤝 Getting Help

- **Documentation:** Check the `docs/` directory
- **API Reference:** http://localhost:8000/docs
- **Issues:** Create GitHub issues for bugs
- **Discussions:** Use GitHub Discussions for questions

---

Happy coding! 🚀