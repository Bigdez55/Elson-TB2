# CLAUDE.md - AI Assistant Guide for Elson Trading Platform

This document provides essential context for AI assistants working on the Elson Personal Trading Platform codebase.

## Project Overview

Elson is an AI-driven personal trading and portfolio management platform designed for individual traders. It combines machine learning models for market analysis, real-time market data integration, and portfolio optimization.

**Key Features:**
- AI/ML-powered trading signals and portfolio optimization
- Paper trading for risk-free strategy testing
- Real-time market data from multiple providers (Alpha Vantage, Polygon, yfinance)
- JWT-based authentication with rate limiting
- Cloud-ready deployment (Google Cloud Run, Vercel)

## Architecture

### Monorepo Structure
```
Elson-TB2/
├── backend/                 # FastAPI Python backend
│   ├── app/
│   │   ├── api/            # REST API endpoints
│   │   │   └── api_v1/     # Versioned API (v1)
│   │   │       └── endpoints/  # Route handlers
│   │   ├── core/           # Config, security, logging
│   │   ├── db/             # Database setup and migrations
│   │   ├── models/         # SQLAlchemy ORM models
│   │   ├── schemas/        # Pydantic request/response schemas
│   │   ├── services/       # Business logic layer
│   │   ├── ml_models/      # Machine learning models
│   │   └── config/         # YAML configuration files
│   ├── alembic/            # Database migrations
│   └── tests/              # Backend tests
├── frontend/               # React TypeScript frontend
│   ├── src/
│   │   ├── components/     # React components
│   │   │   ├── common/     # Reusable UI components
│   │   │   ├── charts/     # Chart components (Chart.js)
│   │   │   ├── trading/    # Trading-specific components
│   │   │   └── AdvancedTrading/  # Advanced trading features
│   │   ├── pages/          # Page components
│   │   ├── services/       # API client functions
│   │   ├── store/          # Redux store and slices
│   │   ├── hooks/          # Custom React hooks
│   │   ├── types/          # TypeScript type definitions
│   │   └── utils/          # Utility functions
│   └── public/             # Static assets
├── .github/
│   └── workflows/          # CI/CD pipelines
├── requirements.txt        # Full Python dependencies
├── requirements-docker.txt # Minimal dependencies for Docker
└── Dockerfile              # Multi-stage Docker build
```

## Tech Stack

### Backend
- **Framework**: FastAPI 0.104.1
- **Python**: 3.12+
- **Database**: SQLAlchemy 2.0 ORM with SQLite (upgradable to PostgreSQL)
- **Migrations**: Alembic
- **Authentication**: JWT via python-jose, bcrypt password hashing
- **Validation**: Pydantic v2
- **ML Libraries**: scikit-learn, XGBoost, pandas, numpy
- **Market Data**: yfinance, alpaca-trade-api, alpha-vantage
- **Logging**: structlog
- **Caching**: Redis (optional)

### Frontend
- **Framework**: React 18 with TypeScript
- **State Management**: Redux Toolkit
- **Routing**: React Router v6
- **HTTP Client**: Axios
- **Charts**: Chart.js with react-chartjs-2
- **Styling**: Tailwind CSS
- **Icons**: Lucide React
- **Testing**: Jest, React Testing Library

## Development Setup

### Backend
```bash
cd backend
pip install -r ../requirements.txt
python -m uvicorn app.main:app --reload --port 8000
```

### Frontend
```bash
cd frontend
npm install
npm start  # Starts on port 3000, proxies API to localhost:8080
```

### Environment Variables
Create `.env` in root directory:
```env
SECRET_KEY=your-secret-key-change-in-production
DATABASE_URL=sqlite:///./elson_trading.db
ALPHA_VANTAGE_API_KEY=your-key
POLYGON_API_KEY=your-key
ALPACA_API_KEY=your-key
ALPACA_SECRET_KEY=your-secret
ALPACA_BASE_URL=https://paper-api.alpaca.markets
REDIS_URL=redis://localhost:6379  # Optional
```

## API Structure

All API endpoints are versioned under `/api/v1/`:

| Prefix | Purpose |
|--------|---------|
| `/auth` | Authentication (login, register, me) |
| `/portfolio` | Portfolio management and holdings |
| `/trading` | Order placement, positions, trade history |
| `/market` | Real-time quotes and historical data |
| `/market-enhanced` | Enhanced market data with analytics |
| `/ai` | AI trading signals and predictions |
| `/ai-portfolio` | AI portfolio optimization |
| `/risk` | Risk management and analysis |
| `/advanced` | Advanced trading features |
| `/monitoring` | System monitoring and metrics |

Health check: `GET /health`

## Code Conventions

### Backend (Python)
- **Formatting**: Black (line length 88)
- **Imports**: isort with Black profile
- **Linting**: flake8 (max line length 88)
- **Type hints**: Required for function signatures
- **Naming**: snake_case for functions/variables, PascalCase for classes
- **Docstrings**: Use for public functions and classes

### Frontend (TypeScript)
- **Formatting**: ESLint with react-app config
- **Components**: Functional components with hooks
- **State**: Redux Toolkit for global state, local state for UI
- **Types**: Define interfaces in `types/index.ts`
- **API calls**: Centralized in `services/` directory
- **Naming**: PascalCase for components, camelCase for functions

### File Organization
- Keep related files together (component + test + styles)
- Place shared utilities in `utils/` directories
- Place shared types in `types/` directories
- Group API endpoints by domain in separate files

## Testing

### Backend Tests
```bash
cd backend
python -m pytest tests/ -v --cov=app
```

### Frontend Tests
```bash
cd frontend
npm test -- --coverage --watchAll=false
```

### Test File Locations
- Backend: `backend/tests/`
- Frontend: Component tests in `__tests__/` subdirectories

## Linting

### Backend
```bash
cd backend
flake8 app/ --count --max-line-length=88 --statistics
black --check app/ --line-length 88
isort --check-only app/ --profile black
```

### Frontend
```bash
cd frontend
npm run lint
npx tsc --noEmit  # Type checking
```

## Deployment

### Deployment Strategy
- **Staging**: Vercel (frontend) - automatic preview deployments
- **Production**: Google Cloud Run (backend) - via GitHub Actions

### Docker Build
```bash
docker build -t elson-trading .
docker run -p 8080:8080 elson-trading
```

### CI/CD Pipeline
The `.github/workflows/ci.yml` runs on push to main/develop:
1. Security scanning (Trivy)
2. Backend linting and tests
3. Frontend linting, type-check, tests, and build
4. Docker image build and push
5. Deploy to Cloud Run (main branch only)

## Database

### Models (backend/app/models/)
- `User`: Authentication, trading preferences
- `Portfolio`: User portfolios with cash balance
- `Holding`: Stock positions within portfolios
- `Trade`: Order history and execution details
- `MarketData`: Cached market data
- `Notification`: User notifications

### Migrations
```bash
cd backend
alembic revision --autogenerate -m "Description"
alembic upgrade head
```

## Security Considerations

- JWT tokens with JTI for revocation support
- Password hashing with bcrypt
- Rate limiting (100 requests/minute, 5 login attempts/5 minutes)
- CORS configured for specific origins
- Input validation via Pydantic
- Non-root Docker user
- Trivy vulnerability scanning in CI
- Dependabot for dependency updates

## Key Services (backend/app/services/)

| Service | Purpose |
|---------|---------|
| `market_data.py` | Market data fetching and caching |
| `market_data_processor.py` | Technical indicators and analytics |
| `neural_network.py` | ML predictions (price, volatility) |
| `ai_portfolio_manager.py` | Portfolio optimization algorithms |
| `ai_trading.py` | AI-powered trading signals |
| `risk_management.py` | Risk analysis and limits |
| `paper_trading.py` | Simulated trading execution |
| `notifications.py` | User notification system |
| `advisor.py` | Investment recommendations |

## Common Tasks

### Adding a New API Endpoint
1. Create schema in `backend/app/schemas/`
2. Create endpoint in `backend/app/api/api_v1/endpoints/`
3. Register router in `backend/app/api/api_v1/api.py`
4. Add frontend API function in `frontend/src/services/`

### Adding a New Frontend Component
1. Create component in appropriate `components/` subdirectory
2. Add TypeScript types in `types/index.ts` if needed
3. Add tests in `__tests__/` subdirectory
4. Export from component index file if shared

### Adding a New Database Model
1. Create model in `backend/app/models/`
2. Import in `backend/app/models/__init__.py`
3. Create corresponding Pydantic schemas
4. Run `alembic revision --autogenerate` and `alembic upgrade head`

## Troubleshooting

### Common Issues
- **CORS errors**: Check `ALLOWED_ORIGINS` in `backend/app/core/config.py`
- **Auth failures**: Verify `SECRET_KEY` is set, check token expiration
- **API 404**: Ensure endpoint is registered in `api.py` router
- **Type errors**: Run `npx tsc --noEmit` to identify TypeScript issues

### Logs
- Backend uses `structlog` - check console output
- Frontend uses custom logger in `utils/logger.ts`

## References

- API Documentation (when running): http://localhost:8000/docs
- Security Policy: `.github/SECURITY.md`
- Implementation Progress: `IMPLEMENTATION_PROGRESS.md`
