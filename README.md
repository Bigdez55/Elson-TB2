# Elson Personal Trading Platform

[![CI/CD Pipeline](https://github.com/Bigdez55/Elson-TB2/actions/workflows/ci.yml/badge.svg)](https://github.com/Bigdez55/Elson-TB2/actions/workflows/ci.yml)
[![Security](https://github.com/Bigdez55/Elson-TB2/actions/workflows/security.yml/badge.svg)](https://github.com/Bigdez55/Elson-TB2/actions/workflows/security.yml)

A comprehensive AI-driven personal trading and portfolio management platform designed for individual traders and investors.

## Overview

The Elson Personal Trading Platform is a sophisticated, self-hosted trading solution that combines artificial intelligence, real-time market data, and portfolio optimization to provide personal wealth management capabilities.

### Key Features

- **AI-Powered Trading**: Machine learning models for market analysis and trading signals
- **Portfolio Management**: Comprehensive tracking and optimization of your investments
- **Real-Time Market Data**: Integration with Yahoo Finance, Alpha Vantage, and other providers
- **Paper Trading**: Risk-free testing of strategies before live deployment
- **Security-First**: PyJWT authentication, rate limiting, and comprehensive security measures
- **Cloud-Ready**: Optimized for Google Cloud Run deployment

## Architecture

### Backend (FastAPI + Python 3.12)
- **API Layer**: RESTful APIs for all platform functionality
- **Services**: Market data aggregation, trading execution, portfolio management
- **Models**: SQLAlchemy ORM with SQLite/PostgreSQL database
- **Security**: PyJWT authentication, bcrypt password hashing, rate limiting
- **Trading Engine**: Separate package with ML models and trading algorithms

### Frontend (React 18 + TypeScript)
- **UI Framework**: Material-UI (MUI) v5 with custom theming
- **State Management**: Redux Toolkit with async middleware
- **Charts**: Chart.js and Recharts for financial visualizations
- **Real-Time**: WebSocket integration for live market data
- **Responsive Design**: Mobile-friendly interface with Tailwind CSS

### Trading Engine
- **ML Models**: Scikit-learn, XGBoost for market predictions
- **Sentiment Analysis**: News and social media sentiment processing
- **Risk Management**: Position sizing, stop-loss, circuit breakers
- **Backtesting**: Strategy validation with historical data

### Infrastructure
- **Database**: SQLite for development, PostgreSQL for production
- **Caching**: Redis for session management and rate limiting
- **Deployment**: Docker containers on Google Cloud Run
- **CI/CD**: GitHub Actions for automated testing and deployment
- **Security**:
  - Dependabot for automated dependency updates (pip, npm, docker, github-actions)
  - CodeQL for static code analysis
  - Trivy for container vulnerability scanning
  - Gitleaks for secret detection

## Quick Start

### Prerequisites

- Python 3.12+
- Node.js 20+
- Docker (optional)
- Google Cloud Platform account (for deployment)

### Local Development

1. **Clone the repository**

   ```bash
   git clone https://github.com/Bigdez55/Elson-TB2.git
   cd Elson-TB2
   ```

2. **Set up environment variables**

   ```bash
   cp .env.example .env
   # Edit .env with your API keys and configuration
   ```

3. **Backend setup**

   ```bash
   cd backend
   pip install -r requirements.txt
   python -m uvicorn app.main:app --reload
   ```

4. **Frontend setup**

   ```bash
   cd frontend
   npm install
   npm start
   ```

### Using Docker Compose

```bash
docker-compose up --build
```

## API Documentation

Once the backend is running, visit:

- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc

## Configuration

### Required Environment Variables

```env
# Security
SECRET_KEY=your-super-secret-key-here
ACCESS_TOKEN_EXPIRE_MINUTES=4320

# Database
DATABASE_URL=sqlite:///./elson_trading.db

# Market Data APIs (optional - uses Yahoo Finance by default)
ALPHA_VANTAGE_API_KEY=your-alpha-vantage-key

# Redis (optional - for caching and rate limiting)
REDIS_URL=redis://localhost:6379
```

## Testing

### Backend Tests

```bash
cd backend
python -m pytest tests/ -v --cov=app
```

### Frontend Tests

```bash
cd frontend
npm test
```

### Linting

```bash
# Backend
cd backend
python -m flake8 app
python -m black app --check
python -m isort app --check-only

# Frontend
cd frontend
npm run lint
```

## Deployment

### Google Cloud Run

The CI/CD pipeline automatically deploys to Cloud Run on pushes to main. For manual deployment:

1. **Set up GCP credentials** (see `.github/workflows/ci.yml` for required setup)

2. **Build and push Docker image**

   ```bash
   gcloud builds submit --tag gcr.io/PROJECT_ID/elson-trading
   ```

3. **Deploy to Cloud Run**

   ```bash
   gcloud run deploy elson-trading \
     --image gcr.io/PROJECT_ID/elson-trading \
     --platform managed \
     --region us-central1 \
     --allow-unauthenticated
   ```

### GitHub Actions Workflows

| Workflow | Purpose |
|----------|---------|
| `ci.yml` | Main CI/CD: tests, builds, deploys to Cloud Run |
| `test.yml` | Python test matrix (3.9, 3.10, 3.11) |
| `security.yml` | CodeQL analysis, Trivy scanning, Gitleaks |
| `docker-publish.yml` | Docker image publishing with signing |

## Security

### Authentication & Authorization

- **JWT Tokens**: PyJWT-based access and refresh tokens
- **Password Hashing**: bcrypt with secure salt rounds
- **Rate Limiting**: Redis-backed request throttling
- **Session Management**: Token revocation and refresh rotation

### Vulnerability Management

- **Dependabot**: Automated security updates for all ecosystems
- **Trivy Scanning**: Container and filesystem vulnerability detection
- **CodeQL**: Static code analysis for security issues
- **Gitleaks**: Secret detection in commits

### Current Security Status

- npm audit: **0 vulnerabilities**
- Python dependencies: Secured with PyJWT (migrated from python-jose)

See [SECURITY.md](.github/SECURITY.md) for detailed security information and reporting procedures.

## Trading Features

### Market Data

- Real-time quotes via Yahoo Finance API
- Historical data for backtesting
- WebSocket connections for live updates
- Multiple provider failover support

### Portfolio Management

- Asset allocation tracking and visualization
- Performance analytics with benchmarks
- Risk assessment metrics (Sharpe, Sortino, VaR)
- Automated rebalancing recommendations

### Trading Engine

- Paper trading for risk-free strategy testing
- Risk management: circuit breakers, position limits
- Order types: Market, Limit, Stop-Loss
- Position sizing based on risk parameters

### AI/ML Components

- Volatility regime detection
- News sentiment analysis (VADER, TextBlob)
- Portfolio optimization (mean-variance, risk parity)
- Anomaly detection for unusual market activity

## Project Structure

```
Elson-TB2/
├── backend/
│   ├── app/
│   │   ├── api/              # FastAPI route handlers
│   │   ├── core/             # Config, security, middleware
│   │   ├── models/           # SQLAlchemy ORM models
│   │   ├── schemas/          # Pydantic request/response schemas
│   │   └── services/         # Business logic layer
│   └── tests/                # Pytest test suite
├── frontend/
│   ├── src/
│   │   ├── components/       # Reusable React components
│   │   ├── pages/            # Route page components
│   │   ├── services/         # API client functions
│   │   ├── store/            # Redux slices and middleware
│   │   └── utils/            # Helper utilities
│   └── public/               # Static assets
├── trading-engine/           # ML models and trading algorithms
│   └── trading_engine/
│       ├── ml_models/        # Prediction models
│       ├── sentiment/        # Sentiment analysis
│       └── strategies/       # Trading strategies
├── .github/
│   ├── workflows/            # CI/CD pipelines
│   └── dependabot.yml        # Dependency updates config
└── docs/                     # Documentation
```

## Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Make your changes
4. Add tests for new functionality
5. Run linting and tests (`npm run lint && npm test`)
6. Commit your changes (`git commit -m 'Add amazing feature'`)
7. Push to the branch (`git push origin feature/amazing-feature`)
8. Open a Pull Request

## Roadmap

### Phase 1: Foundation (Complete)

- [x] Core backend API with FastAPI
- [x] React frontend with Material-UI
- [x] JWT authentication system
- [x] Yahoo Finance market data integration
- [x] Paper trading functionality
- [x] CI/CD with GitHub Actions

### Phase 2: Enhanced Features (In Progress)

- [x] Security hardening (PyJWT migration, vulnerability fixes)
- [ ] Real-time WebSocket market updates
- [ ] Enhanced portfolio analytics dashboard
- [ ] Mobile-responsive optimization

### Phase 3: Advanced Capabilities

- [ ] Advanced ML prediction models
- [ ] Options trading support
- [ ] Tax-loss harvesting automation
- [ ] Multi-broker integration

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Support

For support, feature requests, or bug reports:

- Create an issue on [GitHub](https://github.com/Bigdez55/Elson-TB2/issues)

---

**Disclaimer**: This platform is for educational and personal use only. Trading involves risk and past performance does not guarantee future results. Always consult with qualified financial advisors before making investment decisions.
