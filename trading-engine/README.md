# Elson Trading Engine

AI-powered trading engine for the Elson Wealth Platform.

## Features

- **Circuit Breakers**: Real-time risk management and trading halts
- **Trading Strategies**: Modular strategy framework (Moving Average, etc.)
- **Trade Execution**: Robust trade execution with error handling
- **Risk Configuration**: Configurable risk parameters

## Installation

### Development Installation

```bash
# From repository root
pip install -e ./trading-engine
```

### With Optional Dependencies

```bash
# Development tools
pip install -e "./trading-engine[dev]"

# Quantum models
pip install -e "./trading-engine[quantum]"
```

## Usage

```python
from trading_engine.strategies.moving_average import MovingAverageStrategy
from trading_engine.engine.circuit_breaker import CircuitBreaker

# Initialize strategy
strategy = MovingAverageStrategy(
    short_window=50,
    long_window=200
)

# Use circuit breaker for risk management
breaker = CircuitBreaker()
if not breaker.is_active():
    # Execute trades
    pass
```

## Testing

```bash
cd trading-engine
pytest
```

## License

Proprietary - Elson Wealth Platform
