# Elson Personal Trading Platform 📈

> **A comprehensive, AI-powered personal trading and portfolio management platform designed for individual traders and investors.**

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![Python 3.12+](https://img.shields.io/badge/python-3.12+-blue.svg)](https://www.python.org/downloads/)
[![React 18](https://img.shields.io/badge/react-18.2.0-61dafb.svg)](https://reactjs.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.104.1-009688.svg)](https://fastapi.tiangolo.com/)
[![TypeScript](https://img.shields.io/badge/TypeScript-4.9.5-blue.svg)](https://www.typescriptlang.org/)

---

## 🎯 What is Elson-TB2?

**Elson-TB2** is a sophisticated, self-hosted trading platform that combines **artificial intelligence**, **real-time market data**, and **advanced portfolio optimization** to deliver professional-grade trading tools at a fraction of the cost of commercial solutions.

Think of it as your **personal Bloomberg Terminal** - but modern, customizable, and affordable ($0-5/month vs $24,000/year).

### Why Elson-TB2?

- 🤖 **AI-Powered**: Multiple ML models (XGBoost, TensorFlow, PyTorch) for intelligent trading signals
- 📊 **Professional Tools**: Technical analysis, portfolio optimization, risk management
- 💰 **Cost-Effective**: $0-5/month vs thousands for commercial platforms
- 🔒 **Self-Hosted**: You own your data, code, and infrastructure
- 📈 **Paper Trading**: Test strategies risk-free with real market data
- 🚀 **Production-Ready**: Docker, CI/CD, security scanning, automated deployment
- 🎨 **Modern Stack**: FastAPI, React, TypeScript, Tailwind CSS
- 🌐 **Cloud-Ready**: One-command deployment to Google Cloud Run

### Live Demo

**Domain**: [elsontb.com](https://elsontb.com) (deployment in progress)

**API Documentation**: [elsontb.com/docs](https://elsontb.com/docs)

---

## ✨ Key Features

### 🤖 AI & Machine Learning

- **XGBoost Models**: Price prediction and signal generation
- **Neural Networks**: Deep learning with TensorFlow & PyTorch
- **Quantum ML**: Portfolio optimization using Qiskit
- **Sentiment Analysis**: NLP on news and social media (TextBlob, VADER)
- **Pattern Recognition**: Automated chart pattern detection
- **Anomaly Detection**: Identify unusual market behavior

### 📊 Portfolio Management

- **Multi-Portfolio Support**: Track multiple portfolios simultaneously
- **Real-Time Tracking**: Live portfolio value and P&L updates
- **Asset Allocation**: Visualize and optimize asset distribution
- **Performance Analytics**: Returns, Sharpe ratio, max drawdown
- **Rebalancing**: Automatic recommendations based on targets
- **Cost Basis Tracking**: FIFO, LIFO, specific lot methods

### 📈 Technical Analysis

**50+ Built-In Indicators:**
- Trend: SMA, EMA, MACD, ADX, Parabolic SAR
- Momentum: RSI, Stochastic, Williams %R, ROC
- Volatility: Bollinger Bands, ATR, Keltner Channels
- Volume: OBV, VWAP, Money Flow Index
- Support/Resistance: Fibonacci, Pivot Points

**Auto-Generated Signals:**
- Buy/Sell recommendations
- Confidence scores
- Entry/exit targets
- Stop-loss suggestions

### 💹 Trading Engine

- **Paper Trading**: Risk-free strategy testing with real market data
- **Order Types**: Market, Limit, Stop-Loss, Stop-Limit
- **Risk Management**: Position sizing, circuit breakers, daily loss limits
- **Strategy Framework**: Build and backtest custom strategies
- **Execution**: Integration with Alpaca Markets API

### 📡 Market Data

**Multiple Data Providers:**
- **Alpha Vantage**: Real-time quotes, historical data, fundamentals
- **Polygon.io**: High-frequency data, options, news
- **Alpaca**: Trading execution and account data
- **Yahoo Finance**: Free backup data source

**Data Types:**
- Real-time quotes (1-minute intervals)
- Historical OHLCV data
- Company fundamentals
- Economic indicators
- News and sentiment
- Earnings reports

### 🎨 Modern Dashboard

- **Portfolio Overview**: Charts, performance metrics, holdings
- **Live Trading**: Real-time order entry and monitoring
- **Watchlists**: Track favorite stocks
- **News Feed**: Relevant financial news
- **Advanced Trading**: AI signals, risk dashboard
- **Mobile Responsive**: Works on all devices

---

## 🏗️ Technology Stack

### Backend

| Technology | Version | Purpose |
|------------|---------|---------|
| **FastAPI** | 0.104.1 | High-performance API framework |
| **Python** | 3.12+ | Runtime |
| **SQLAlchemy** | 2.0.23 | Database ORM |
| **Uvicorn/Gunicorn** | Latest | ASGI/WSGI servers |
| **Pydantic** | 2.11.7 | Data validation |
| **JWT/Passlib** | Latest | Authentication & security |

### Frontend

| Technology | Version | Purpose |
|------------|---------|---------|
| **React** | 18.2.0 | UI framework |
| **TypeScript** | 4.9.5 | Type-safe JavaScript |
| **Redux Toolkit** | 1.9.7 | State management |
| **Tailwind CSS** | 3.3.5 | Styling |
| **Recharts** | 2.8.0 | Data visualization |
| **Axios** | 1.5.1 | HTTP client |

### Data & Analytics

| Technology | Purpose |
|------------|---------|
| **NumPy** | Numerical computing |
| **Pandas** | Data manipulation |
| **Scikit-Learn** | Machine learning |
| **XGBoost** | Gradient boosting |
| **TensorFlow** | Deep learning |
| **PyTorch** | Neural networks |
| **TA-Lib** | Technical indicators |
| **QuantLib** | Quantitative finance |
| **Qiskit** | Quantum computing |

### Infrastructure

| Technology | Purpose |
|------------|---------|
| **Docker** | Containerization |
| **Google Cloud Run** | Serverless deployment |
| **PostgreSQL/SQLite** | Database |
| **Redis** | Caching |
| **GitHub Actions** | CI/CD |
| **Nginx** | Web server (production) |

---

## 🚀 Quick Start

### Prerequisites

- **Python 3.12+** - [Download](https://www.python.org/downloads/)
- **Node.js 18+** - [Download](https://nodejs.org/)
- **Docker** (optional) - [Download](https://www.docker.com/)

### Option 1: Local Development (5 minutes)

```bash
# 1. Clone the repository
git clone https://github.com/Bigdez55/Elson-TB2.git
cd Elson-TB2

# 2. Set up environment (API keys included in .env)
# The .env file is already configured!

# 3. Install backend dependencies
pip install -r requirements.txt

# 4. Install frontend dependencies
cd frontend && npm install && cd ..

# 5. Start backend (Terminal 1)
cd backend
python -m uvicorn app.main:app --reload --port 8000

# 6. Start frontend (Terminal 2)
cd frontend
npm start
```

**Access:**
- 🌐 Frontend: http://localhost:3000
- 📚 API Docs: http://localhost:8000/docs
- ❤️ Health Check: http://localhost:8000/health

### Option 2: Docker Compose (2 minutes)

```bash
docker-compose up --build
```

**Access:** http://localhost:8080

### Option 3: Deploy to Cloud (20 minutes)

```bash
# See QUICK_START.md for complete guide

# Quick deploy
./deploy-to-cloud-run.sh
```

**Complete deployment guides:**
- [QUICK_START.md](QUICK_START.md) - Simple 3-step guide
- [DEPLOYMENT_GUIDE.md](DEPLOYMENT_GUIDE.md) - All deployment options
- [GITHUB_SECRETS_SETUP.md](GITHUB_SECRETS_SETUP.md) - Automated CI/CD
- [NAMECHEAP_DNS_SETUP.md](NAMECHEAP_DNS_SETUP.md) - Domain configuration

---

## 🔧 Configuration

### Required API Keys

The platform uses these services (all have free tiers):

#### 1. Alpha Vantage (Market Data) - FREE
- **Sign up**: https://www.alphavantage.co/support/#api-key
- **Free tier**: 5 calls/minute, 500/day
- **Get key in**: 1 minute

#### 2. Alpaca (Paper Trading) - FREE
- **Sign up**: https://alpaca.markets/
- **Paper trading**: Unlimited, free forever
- **No money required**: Virtual trading only
- **Get key in**: 5 minutes

#### 3. Polygon.io (Optional) - PAID
- **Sign up**: https://polygon.io/
- **Free tier**: Limited
- **Recommended for**: High-frequency trading

### Environment Variables

Edit `.env` with your API keys:

```env
# Security (already generated)
SECRET_KEY=ohrPrvz4l_lXPE5gHIPZAAfmrqbyCHebX9VXpJgjTzA

# Market Data
ALPHA_VANTAGE_API_KEY=your-alpha-vantage-key
POLYGON_API_KEY=your-polygon-key  # Optional

# Paper Trading
ALPACA_API_KEY=your-alpaca-key
ALPACA_SECRET_KEY=your-alpaca-secret
ALPACA_BASE_URL=https://paper-api.alpaca.markets

# Database (SQLite for local, PostgreSQL for production)
DATABASE_URL=sqlite:///./elson_trading.db

# Redis (Optional - for caching)
REDIS_URL=redis://localhost:6379
```

---

## 📚 Comprehensive Documentation

| Guide | Description | Time |
|-------|-------------|------|
| [**QUICK_START.md**](QUICK_START.md) | 👈 **Start here!** Choose your deployment path | 5 min |
| [SETUP_GUIDE.md](SETUP_GUIDE.md) | Complete local development setup | 20 min |
| [DEPLOYMENT_GUIDE.md](DEPLOYMENT_GUIDE.md) | All deployment options explained | Reference |
| [GITHUB_SECRETS_SETUP.md](GITHUB_SECRETS_SETUP.md) | Automated deployment with GitHub Actions | 30 min |
| [NAMECHEAP_DNS_SETUP.md](NAMECHEAP_DNS_SETUP.md) | Custom domain configuration | 15 min |
| [LAUNCH_CHECKLIST.md](LAUNCH_CHECKLIST.md) | Pre-launch verification | Checklist |
| [DEPLOYMENT_COMPLETE.md](DEPLOYMENT_COMPLETE.md) | Deployment status & next steps | Reference |

---

## 💼 Use Cases

### For Individual Investors

**Scenario**: Sarah wants to start investing but is afraid of losing money.

**Solution**:
1. Creates paper trading account ($100k virtual)
2. Uses AI to suggest portfolio allocation
3. Practices buying stocks with real prices
4. Tracks performance over months
5. Learns from mistakes without risk
6. Switches to real trading when confident

### For Algorithmic Traders

**Scenario**: Mike wants to automate a trading strategy.

**Solution**:
```python
# Create custom strategy
class MikesStrategy(TradingStrategy):
    def generate_signal(self, data):
        if data.rsi < 30 and data.macd_cross:
            return "BUY"
        return "HOLD"

# Backtest on historical data
results = backtest(MikesStrategy(), 'AAPL', '2020-01-01')

# Deploy to paper trading
deploy(MikesStrategy(), mode='paper')
```

### For Portfolio Managers

**Scenario**: Lisa manages her retirement portfolio.

**Solution**:
1. Imports existing holdings
2. Analyzes current allocation
3. Gets optimization suggestions
4. Calculates risk metrics
5. Receives rebalancing recommendations
6. Tracks performance vs benchmarks

### For Day Traders

**Scenario**: John wants to day trade with technical analysis.

**Solution**:
1. Real-time price updates (1-minute intervals)
2. Live technical indicators
3. Entry/exit signals
4. Risk management (stop losses)
5. P&L tracking
6. Quick order execution

---

## 🎓 Features in Detail

### Portfolio Optimization

Uses **Modern Portfolio Theory (MPT)** to optimize holdings:

```python
Features:
- Mean-variance optimization
- Efficient frontier calculation
- Sharpe ratio maximization
- Risk-adjusted returns
- Rebalancing recommendations
- Tax-loss harvesting opportunities
```

### Risk Management

Comprehensive risk controls:

```python
Circuit Breakers:
- Daily loss limits (default: 5%)
- Position size limits
- Rapid trade detection
- Volatility monitoring

Position Sizing:
- Kelly Criterion
- Fixed fractional
- Volatility-based
- Risk parity

Risk Metrics:
- Value at Risk (VaR)
- Maximum Drawdown
- Sharpe Ratio
- Sortino Ratio
- Beta vs market
```

### Backtesting Engine

Test strategies on historical data:

```python
strategy = MovingAverageStrategy(short=50, long=200)
results = backtest(
    strategy=strategy,
    symbol='AAPL',
    start='2020-01-01',
    end='2023-12-31',
    initial_capital=10000
)

print(f"Total Return: {results.total_return}")
print(f"Sharpe Ratio: {results.sharpe_ratio}")
print(f"Max Drawdown: {results.max_drawdown}")
```

---

## 🧪 Testing

### Backend Tests

```bash
cd backend

# Run all tests with coverage
pytest tests/ -v --cov=app --cov-report=html

# Run specific test
pytest tests/test_trading.py -v

# Check code quality
flake8 app/
black app/ --check
isort app/ --check-only
```

### Frontend Tests

```bash
cd frontend

# Run tests
npm test

# Run tests with coverage
npm test -- --coverage --watchAll=false

# Lint code
npm run lint

# Type check
npx tsc --noEmit

# Build production
npm run build
```

---

## 🚀 Deployment Options

### Option 1: Google Cloud Run (Recommended)

**Best for**: Production, automatic scaling, HTTPS

```bash
# Automated deployment script
./deploy-to-cloud-run.sh

# Or manual
gcloud builds submit --config cloudbuild.yaml
```

**Features**:
- ✅ Auto-scaling (0 to 100+ instances)
- ✅ HTTPS automatic (Google-managed SSL)
- ✅ Custom domain support
- ✅ Pay-per-use pricing
- ✅ 99.9% uptime SLA

**Cost**: $0-10/month for low traffic

**Guide**: [DEPLOYMENT_GUIDE.md](DEPLOYMENT_GUIDE.md)

### Option 2: GitHub Actions (Automated)

**Best for**: Continuous deployment

```bash
# Set up once (30 minutes)
# See GITHUB_SECRETS_SETUP.md

# Then just push to deploy
git push origin main
```

**Features**:
- ✅ Auto-deploy on push to main
- ✅ Run tests before deploy
- ✅ Security scanning
- ✅ Zero-downtime deployments

**Guide**: [GITHUB_SECRETS_SETUP.md](GITHUB_SECRETS_SETUP.md)

### Option 3: Self-Hosted VPS

**Best for**: Full control, lowest cost

```bash
# Deploy to DigitalOcean, AWS, etc.
# See DEPLOYMENT_GUIDE.md for complete guide
```

**Cost**: $5-10/month (VPS only)

### Option 4: Local Only

**Best for**: Development, testing, privacy

```bash
# Already set up!
python -m uvicorn app.main:app --reload --port 8000
npm start
```

**Cost**: $0 (just your computer)

---

## 💰 Cost Comparison

### Your Platform (Elson-TB2)

| Component | Cost |
|-----------|------|
| Alpha Vantage (Market Data) | FREE |
| Alpaca Paper Trading | FREE |
| Google Cloud Run | $0-10/month |
| Domain (elsontb.com) | Already owned |
| SSL Certificate | FREE (auto) |
| **Total** | **$0-10/month** |

### Commercial Alternatives

| Platform | Cost | Notes |
|----------|------|-------|
| Bloomberg Terminal | $24,000/year | $2,000/month |
| Refinitiv Eikon | $20,000/year | Enterprise |
| TradingView Pro+ | $60/month | Limited features |
| QuantConnect | $20-200/month | Cloud-only |
| Interactive Brokers | Free* | Limited API |

**Your savings**: $23,940/year+ 🎉

---

## 🔒 Security

### Built-In Security Features

- ✅ **JWT Authentication**: Secure token-based auth
- ✅ **Password Hashing**: bcrypt with salt
- ✅ **Rate Limiting**: 100 requests/minute
- ✅ **CORS Protection**: Whitelisted domains
- ✅ **Input Validation**: Pydantic schemas
- ✅ **SQL Injection Prevention**: ORM-based queries
- ✅ **XSS Protection**: Sanitized inputs
- ✅ **HTTPS**: Automatic SSL/TLS
- ✅ **Non-Root Containers**: Docker security
- ✅ **Secrets Management**: Environment variables

### Automated Security Scanning

**GitHub Actions CI/CD includes**:
- 🔍 **Trivy**: Vulnerability scanning
- 🔍 **CodeQL**: Code security analysis
- 🔍 **Dependabot**: Dependency updates
- 🔍 **Gitleaks**: Secret detection

See [SECURITY.md](.github/SECURITY.md) for detailed security information.

---

## 📊 System Architecture

```
┌─────────────────────────────────────────────────────────┐
│                    Elson-TB2 Platform                   │
├─────────────────────────────────────────────────────────┤
│                                                         │
│  Frontend (React + TypeScript + Tailwind)              │
│  ┌─────────────────────────────────────────────┐      │
│  │  Dashboard  │  Trading  │  Portfolio  │ AI  │      │
│  └─────────────────────────────────────────────┘      │
│                        ↕ HTTP/REST                      │
│  Backend (FastAPI + Python)                            │
│  ┌─────────────────────────────────────────────┐      │
│  │  Auth  │  Trading  │  Portfolio  │  AI/ML   │      │
│  │  ────────────────────────────────────────── │      │
│  │  Services  │  Models  │  Schemas  │  Core   │      │
│  └─────────────────────────────────────────────┘      │
│                        ↕                                │
│  Database (PostgreSQL / SQLite)                        │
│  ┌─────────────────────────────────────────────┐      │
│  │  Users  │  Portfolios  │  Trades  │  Data   │      │
│  └─────────────────────────────────────────────┘      │
│                        ↕                                │
│  External Services                                     │
│  ┌─────────────────────────────────────────────┐      │
│  │  Alpha Vantage  │  Alpaca  │  Polygon.io    │      │
│  └─────────────────────────────────────────────┘      │
│                                                         │
│  Infrastructure                                        │
│  ┌─────────────────────────────────────────────┐      │
│  │  Docker  │  Redis  │  Cloud Run  │  GitHub  │      │
│  └─────────────────────────────────────────────┘      │
└─────────────────────────────────────────────────────────┘
```

---

## 🛠️ Development

### Project Structure

```
Elson-TB2/
├── backend/                    # FastAPI Backend
│   ├── app/
│   │   ├── api/               # API endpoints
│   │   │   └── api_v1/
│   │   │       ├── api.py     # Router
│   │   │       └── endpoints/ # Auth, Trading, Portfolio, etc.
│   │   ├── core/              # Configuration, Security
│   │   ├── db/                # Database setup
│   │   ├── models/            # SQLAlchemy models
│   │   ├── schemas/           # Pydantic schemas
│   │   ├── services/          # Business logic
│   │   ├── trading_engine/    # Strategy framework
│   │   └── ml_models/         # AI/ML models
│   └── tests/                 # Backend tests
│
├── frontend/                   # React Frontend
│   ├── src/
│   │   ├── components/        # React components
│   │   ├── pages/             # Page components
│   │   ├── services/          # API clients
│   │   ├── store/             # Redux store
│   │   └── types/             # TypeScript types
│   └── public/                # Static assets
│
├── .github/
│   └── workflows/             # CI/CD pipelines
│
├── docs/                      # Documentation
│   ├── QUICK_START.md
│   ├── SETUP_GUIDE.md
│   ├── DEPLOYMENT_GUIDE.md
│   └── ...
│
├── Dockerfile                 # Backend container
├── docker-compose.yml         # Local development
├── cloudbuild.yaml           # Google Cloud Build
├── requirements.txt          # Python dependencies
└── .env.example              # Environment template
```

### Adding Custom Strategies

```python
# backend/app/trading_engine/strategies/my_strategy.py

from app.trading_engine.strategies.base import TradingStrategy

class MyCustomStrategy(TradingStrategy):
    """
    Your custom trading strategy
    """

    def __init__(self, param1, param2):
        super().__init__()
        self.param1 = param1
        self.param2 = param2

    def analyze(self, market_data):
        """
        Analyze market data and generate signals
        """
        # Your logic here
        pass

    def generate_signals(self, symbol, data):
        """
        Generate buy/sell signals
        """
        signal = self.analyze(data)

        if signal == "BUY":
            return {
                "action": "BUY",
                "symbol": symbol,
                "confidence": 0.85,
                "reason": "Custom signal triggered"
            }

        return {"action": "HOLD"}
```

### Contributing

We welcome contributions! Please follow these steps:

1. **Fork** the repository
2. **Create** a feature branch (`git checkout -b feature/amazing-feature`)
3. **Commit** your changes (`git commit -m 'Add amazing feature'`)
4. **Push** to the branch (`git push origin feature/amazing-feature`)
5. **Open** a Pull Request

**Before submitting**:
- ✅ Add tests for new features
- ✅ Run `pytest` and ensure tests pass
- ✅ Run linting: `black`, `flake8`, `isort`
- ✅ Update documentation
- ✅ Follow existing code style

---

## 📋 Roadmap

### ✅ Phase 1: Foundation (Complete)

- [x] Core backend API (FastAPI)
- [x] Frontend dashboard (React + TypeScript)
- [x] Authentication system (JWT)
- [x] Market data integration (Alpha Vantage, Alpaca)
- [x] Paper trading
- [x] Basic AI/ML models
- [x] Docker containerization
- [x] CI/CD pipeline
- [x] Deployment automation

### 🚧 Phase 2: Enhanced Features (In Progress)

- [x] Advanced AI/ML models (XGBoost, TensorFlow)
- [x] Portfolio optimization (MPT)
- [x] Technical analysis engine
- [x] Risk management system
- [ ] Real-time WebSocket updates
- [ ] Mobile optimization
- [ ] Advanced charting

### 🔮 Phase 3: Advanced Capabilities (Planned)

- [ ] Quantum computing integration (Qiskit)
- [ ] Options trading
- [ ] Multi-asset support (crypto, forex, futures)
- [ ] Social features (strategy sharing)
- [ ] Mobile app (React Native)
- [ ] Tax reporting (1099-B, 8949)
- [ ] Backtesting dashboard
- [ ] Strategy marketplace

---

## 🤝 Community & Support

### Get Help

- 📖 **Documentation**: See guides in `/docs/`
- 🐛 **Bug Reports**: [GitHub Issues](https://github.com/Bigdez55/Elson-TB2/issues)
- 💡 **Feature Requests**: [GitHub Issues](https://github.com/Bigdez55/Elson-TB2/issues)
- 📧 **Email**: support@elsontb.com

### Useful Resources

- [FastAPI Documentation](https://fastapi.tiangolo.com/)
- [React Documentation](https://react.dev/)
- [Alpha Vantage API](https://www.alphavantage.co/documentation/)
- [Alpaca API](https://alpaca.markets/docs/)
- [TA-Lib Documentation](https://ta-lib.org/)

---

## 📄 License

This project is licensed under the **MIT License** - see the [LICENSE](LICENSE) file for details.

### Disclaimer

**⚠️ IMPORTANT: This platform is for educational and personal use only.**

- This software is provided "as is" without warranty
- Past performance does not guarantee future results
- Trading involves substantial risk of loss
- Not suitable for every investor
- Always consult with qualified financial advisors
- Test strategies thoroughly using paper trading
- Never invest more than you can afford to lose

The authors and contributors shall not be held liable for any losses, damages, or claims arising from the use of this software.

---

## 🌟 Acknowledgments

Built with amazing open-source technologies:

- [FastAPI](https://fastapi.tiangolo.com/) - Modern API framework
- [React](https://react.dev/) - UI library
- [Scikit-Learn](https://scikit-learn.org/) - Machine learning
- [TA-Lib](https://ta-lib.org/) - Technical analysis
- [Alpha Vantage](https://www.alphavantage.co/) - Market data
- [Alpaca](https://alpaca.markets/) - Trading API

Special thanks to the open-source community! 🙏

---

## 📞 Contact

- **Website**: [elsontb.com](https://elsontb.com)
- **GitHub**: [@Bigdez55](https://github.com/Bigdez55)
- **Email**: support@elsontb.com

---

## 🚀 Ready to Get Started?

1. **Read**: [QUICK_START.md](QUICK_START.md) (5 minutes)
2. **Setup**: Follow one of the deployment paths
3. **Trade**: Start with paper trading (risk-free!)
4. **Optimize**: Use AI to improve your strategies
5. **Deploy**: Launch on elsontb.com

**Happy Trading! 📈**

---

<div align="center">

**Made with ❤️ by traders, for traders**

[⬆ Back to Top](#elson-personal-trading-platform-)

</div>
