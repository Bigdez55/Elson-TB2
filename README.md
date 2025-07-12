# Elson Personal Trading Platform

A comprehensive AI-driven personal trading and portfolio management platform designed for individual traders and investors.

## 🎯 Overview

The Elson Personal Trading Platform is a sophisticated, self-hosted trading solution that combines artificial intelligence, real-time market data, and portfolio optimization to provide personal wealth management capabilities.

### Key Features

- **AI-Powered Trading**: Machine learning models for market analysis and trading signals
- **Portfolio Management**: Comprehensive tracking and optimization of your investments
- **Real-Time Market Data**: Integration with multiple data providers (Alpha Vantage, Polygon)
- **Paper Trading**: Risk-free testing of strategies before live deployment
- **Security-First**: JWT authentication, rate limiting, and comprehensive security measures
- **Cloud-Ready**: Optimized for Google Cloud Run deployment

## 🏗️ Architecture

### Backend (FastAPI)
- **API Layer**: RESTful APIs for all platform functionality
- **Services**: Market data aggregation, trading execution, portfolio management
- **Models**: SQLAlchemy ORM with SQLite database
- **Security**: JWT authentication, input validation, rate limiting

### Frontend (React + TypeScript)
- **Dashboard**: Portfolio overview and performance metrics
- **Trading Interface**: Order placement and management
- **Market Data**: Real-time charts and market information
- **Responsive Design**: Mobile-friendly interface

### Infrastructure
- **Database**: SQLite for personal use (easily upgradable to PostgreSQL)
- **Deployment**: Docker containers on Google Cloud Run
- **CI/CD**: GitHub Actions for automated testing and deployment
- **Security**: 
  - Dependabot for automated dependency updates
  - CodeQL for code security analysis
  - Trivy for vulnerability scanning
  - Gitleaks for secret detection

## 🚀 Quick Start

### Prerequisites

- Python 3.12+
- Node.js 20+
- Docker (optional)
- Google Cloud Platform account (for deployment)

### Environment Setup

1. **Clone the repository**
   ```bash
   git clone https://github.com/yourusername/Elson-TB2.git
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
   pip install -r ../requirements.txt
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

## 📊 API Documentation

Once the backend is running, visit:
- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc

## 🔧 Configuration

### Required Environment Variables

```env
# Security
SECRET_KEY=your-super-secret-key-here
ACCESS_TOKEN_EXPIRE_MINUTES=4320

# Database
DATABASE_URL=sqlite:///./elson_trading.db

# Market Data APIs
ALPHA_VANTAGE_API_KEY=your-alpha-vantage-key
POLYGON_API_KEY=your-polygon-key

# Trading (Paper Trading by default)
ALPACA_API_KEY=your-alpaca-key
ALPACA_SECRET_KEY=your-alpaca-secret
ALPACA_BASE_URL=https://paper-api.alpaca.markets
```

## 🧪 Testing

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

## 🚀 Deployment

### Google Cloud Run

1. **Build and push Docker image**
   ```bash
   gcloud builds submit --tag gcr.io/PROJECT_ID/elson-trading
   ```

2. **Deploy to Cloud Run**
   ```bash
   gcloud run deploy elson-trading \
     --image gcr.io/PROJECT_ID/elson-trading \
     --platform managed \
     --region us-central1 \
     --allow-unauthenticated
   ```

### GitHub Actions

The repository includes automated CI/CD pipelines that:
- Run comprehensive tests
- Perform security scans
- Build Docker images
- Deploy to Google Cloud Run (on main branch)

## 🔒 Security

- **Authentication**: JWT-based with secure token management
- **API Security**: Rate limiting, input validation, CORS protection
- **Container Security**: Non-root user, minimal base images
- **Dependency Management**: Automated security updates via Dependabot
- **Vulnerability Scanning**: Regular security scans with Trivy

See [SECURITY.md](.github/SECURITY.md) for detailed security information.

## 📈 Trading Features

### Market Data
- Real-time quotes and historical data
- Multiple provider support with failover
- WebSocket connections for live updates

### Portfolio Management
- Asset allocation tracking
- Performance analytics
- Risk assessment and optimization
- Rebalancing recommendations

### Trading Engine
- Paper trading for strategy testing
- Risk management controls
- Order types: Market, Limit, Stop
- Position sizing and validation

### AI/ML Components
- Volatility detection models
- Sentiment analysis integration
- Portfolio optimization algorithms
- Anomaly detection for market events

## 🛠️ Development

### Project Structure
```
├── backend/
│   ├── app/
│   │   ├── api/          # API endpoints
│   │   ├── core/         # Configuration and security
│   │   ├── models/       # Database models
│   │   ├── schemas/      # Pydantic schemas
│   │   └── services/     # Business logic
│   └── tests/            # Backend tests
├── frontend/
│   ├── src/
│   │   ├── components/   # React components
│   │   ├── pages/        # Page components
│   │   ├── services/     # API clients
│   │   └── store/        # Redux store
├── .github/
│   └── workflows/        # CI/CD pipelines
└── docs/                 # Additional documentation
```

### Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests
5. Run linting and tests
6. Submit a pull request

## 📋 Roadmap

### Phase 1: Foundation ✅
- [x] Core backend API
- [x] Basic frontend interface
- [x] Authentication system
- [x] Market data integration
- [x] Paper trading

### Phase 2: Enhanced Features (In Progress)
- [ ] Advanced AI/ML models
- [ ] Real-time WebSocket updates
- [ ] Enhanced portfolio analytics
- [ ] Mobile optimization

### Phase 3: Advanced Capabilities
- [ ] Quantum computing integration
- [ ] Advanced risk management
- [ ] Multi-asset support
- [ ] Tax optimization features

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🤝 Support

For support, feature requests, or bug reports:
- Create an issue on GitHub
- Contact: support@elson-trading.com

---

**Disclaimer**: This platform is for educational and personal use. Past performance does not guarantee future results. Always consult with financial advisors and understand the risks involved in trading.
