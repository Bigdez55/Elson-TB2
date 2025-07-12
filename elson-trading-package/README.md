# Elson Trading Platform Components Package

This package contains the core components, configurations, and algorithms from the Elson trading platform organized for easy integration and reference.

## Package Structure

```
elson-trading-package/
├── ui/                          # Frontend UI Components
│   ├── components/             # React components
│   ├── core/                   # Core configuration
│   ├── hooks/                  # Custom React hooks
│   ├── services/               # API services
│   ├── store/                  # State management
│   └── utils/                  # Utility functions
│
├── risk-management/            # Risk Parameters & Trading Preferences
│   ├── config.py              # Core configuration
│   ├── failover.py            # Failover mechanisms
│   ├── risk_management.py     # Risk management logic
│   ├── risk.py                # Risk API endpoints
│   └── broker/                # Broker configurations
│
├── ml-models/                  # ML Models & AI Components
│   ├── anomaly_detector.py    # Anomaly detection
│   ├── ai_portfolio_manager.py # AI portfolio management
│   ├── ai.py                  # AI API endpoints
│   ├── models/                # Data models
│   └── frontend/              # AI frontend components
│
├── sentiment-analysis/         # Sentiment Sources & Analysis
│   ├── sentiment_sources.py   # Sentiment analysis configuration
│   ├── websocket/             # Real-time market feeds
│   └── data_engine/           # Data processing engine
│
├── trading-strategies/         # Trading Strategies & Algorithms
│   ├── trading_engine/        # Core trading engine
│   ├── trading_service.py     # Trading services
│   ├── trading.py             # Trading logic
│   ├── paper_trading_service.py # Paper trading
│   └── frontend/              # Trading UI components
│
├── config/                    # Global Configuration Files
└── docs/                      # Documentation
```

## Key Components

### UI Components (`ui/`)
- **Trading Interface**: Order forms, portfolio displays, live quotes
- **Charts**: Candlestick, volume, and indicator charts
- **AI Integration**: Portfolio rebalancing tools, recommendations
- **Dashboard**: Performance metrics, trading stats
- **Authentication**: Login, signup, password management

### Risk Management (`risk-management/`)
- **Risk Parameters**: Position sizing, stop-loss configurations
- **Trading Preferences**: User-defined trading rules
- **Broker Integration**: Multi-broker support and configuration
- **Failover Systems**: Redundancy and backup mechanisms

### ML Models (`ml-models/`)
- **Anomaly Detection**: Market anomaly identification
- **AI Portfolio Manager**: Automated portfolio optimization
- **Quantum Models**: Advanced mathematical trading models
- **Performance Analytics**: Model evaluation and metrics

### Sentiment Analysis (`sentiment-analysis/`)
- **News Sources**: Financial news sentiment processing
- **Social Media**: Reddit, Twitter sentiment analysis
- **Market Indicators**: Fear & Greed index, VIX analysis
- **Real-time Feeds**: WebSocket-based market data streams

### Trading Strategies (`trading-strategies/`)
- **Strategy Engine**: Base strategy framework
- **Moving Average**: Technical analysis strategies
- **Combined Strategies**: Multi-factor trading algorithms
- **Backtesting**: Historical performance evaluation
- **Paper Trading**: Risk-free strategy testing

## Configuration Files

### Environment Variables
- Frontend: `.env.production`
- Backend: `.env.production.example`

### Package Management
- Frontend: `package.json` with all dependencies
- Backend: `requirements.txt` with Python packages

## Usage

### Frontend Integration
```bash
cd ui/
npm install
npm start
```

### Backend Services
```bash
pip install -r requirements.txt
python -m uvicorn main:app --reload
```

### Trading Engine
```python
from trading_engine.strategies.base import BaseStrategy
from trading_engine.strategies.moving_average import MovingAverageStrategy

# Initialize strategy
strategy = MovingAverageStrategy(symbol="AAPL")
strategy.execute()
```

### ML Models
```python
from ml_models.anomaly_detector import AnomalyDetector
from ml_models.ai_portfolio_manager import AIPortfolioManager

# Anomaly detection
detector = AnomalyDetector()
anomalies = detector.detect(market_data)

# Portfolio optimization
manager = AIPortfolioManager()
recommendations = manager.optimize_portfolio(portfolio)
```

## Dependencies

### Frontend
- React 18+
- TypeScript
- Tailwind CSS
- Redux Toolkit
- Chart.js/TradingView

### Backend
- FastAPI
- SQLAlchemy
- Redis
- NumPy/Pandas
- Scikit-learn
- TA-Lib

### Trading Engine
- QuantLib
- Zipline
- Backtrader
- Alpha Vantage API
- Interactive Brokers API

## Security Features

- JWT Authentication
- API Rate Limiting
- Input Validation
- Secure WebSocket Connections
- Environment-based Configuration

## Monitoring & Metrics

- Performance tracking
- Error monitoring
- Trade execution metrics
- System health monitoring
- User activity analytics

## License

This package contains proprietary trading algorithms and components. Usage is restricted to authorized personnel only.

## Support

For technical support or integration questions, please refer to the original Elson platform documentation.