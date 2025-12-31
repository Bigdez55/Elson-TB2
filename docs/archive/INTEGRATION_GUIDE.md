# Integration Guide

## Quick Start

### 1. Frontend Setup
```bash
cd ui/
npm install
npm run dev
```

### 2. Backend Setup
```bash
pip install -r config/requirements.txt
# Set environment variables
export DATABASE_URL="postgresql://user:pass@localhost/elson"
export REDIS_URL="redis://localhost:6379"
export SECRET_KEY="your-secret-key"
```

### 3. Trading Engine Setup
```python
# Configure trading engine
from trading_strategies.trading_engine.strategies.base import BaseStrategy

class CustomStrategy(BaseStrategy):
    def execute(self):
        # Your trading logic here
        pass
```

## Component Integration

### Risk Management Integration
```python
from risk_management.risk_management import RiskManager

risk_manager = RiskManager()
risk_manager.validate_trade(trade_request)
```

### ML Models Integration
```python
from ml_models.anomaly_detector import AnomalyDetector

detector = AnomalyDetector()
anomalies = detector.detect(market_data)
```

### Sentiment Analysis Integration
```python
from sentiment_analysis.sentiment_sources import SentimentAnalyzer

analyzer = SentimentAnalyzer()
sentiment = analyzer.analyze_news_sentiment("AAPL")
```

## API Endpoints

### Trading
- `POST /api/v1/trading/place-order`
- `GET /api/v1/trading/positions`
- `GET /api/v1/trading/history`

### Risk Management
- `GET /api/v1/risk/parameters`
- `POST /api/v1/risk/validate`

### AI/ML
- `POST /api/v1/ai/portfolio-optimization`
- `GET /api/v1/ai/recommendations`

## Environment Configuration

### Required Environment Variables
```bash
# Database
DATABASE_URL=postgresql://localhost/elson
REDIS_URL=redis://localhost:6379

# Security
SECRET_KEY=your-secret-key
JWT_SECRET_KEY=your-jwt-secret

# Trading APIs
ALPHA_VANTAGE_API_KEY=your-api-key
IEX_CLOUD_API_KEY=your-api-key

# Broker APIs
INTERACTIVE_BROKERS_HOST=localhost
INTERACTIVE_BROKERS_PORT=7497
```

## WebSocket Connections

### Market Data Feed
```javascript
const ws = new WebSocket('ws://localhost:8000/ws/market-feed');
ws.onmessage = (event) => {
    const data = JSON.parse(event.data);
    // Handle real-time market data
};
```

## Testing

### Unit Tests
```bash
pytest trading_strategies/tests/
pytest ml_models/tests/
```

### Integration Tests
```bash
pytest --integration
```

## Monitoring

### Metrics Collection
- Trade execution metrics
- System performance
- User activity
- Error rates

### Health Checks
- Database connectivity
- Redis connectivity
- External API status
- WebSocket connections