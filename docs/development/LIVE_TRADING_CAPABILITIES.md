# Live Trading Capabilities - Alpaca API Integration

## Overview

The Elson Trading Platform has been successfully upgraded from paper trading to full live Alpaca API integration while maintaining comprehensive safety controls and risk management features.

## Key Features Added

### 1. Live Trading Support
- **Real Order Execution**: Execute actual trades on Alpaca's live trading API
- **Dual Mode Operation**: Seamlessly switch between paper and live trading
- **Environment Safety**: Automatic paper trading enforcement in development environments
- **Credential Validation**: Comprehensive API key validation before trading

### 2. Enhanced Safety Controls

#### Pre-Trade Validation
- **Symbol Validation**: Verify symbols are tradeable on Alpaca
- **Market Hours Check**: Confirm market is open before executing trades
- **Buying Power Verification**: Ensure sufficient funds before trade execution
- **Position Size Limits**: Configurable maximum position sizes ($50,000 default)
- **Order Parameter Validation**: Validate all required fields and prices

#### Pattern Day Trader (PDT) Compliance
- **PDT Status Monitoring**: Track account PDT classification
- **Daily Trade Counting**: Monitor day trades for compliance
- **Account Value Checks**: Verify minimum equity requirements
- **Compliance Warnings**: Alert when approaching day trade limits

### 3. Fractional Shares Support
- **Dollar-Based Investing**: Support investment by dollar amount
- **Fractional Quantities**: Handle partial share purchases
- **Notional Value Orders**: Use Alpaca's notional order feature
- **Micro-Investment Ready**: Perfect for small-dollar investing

### 4. Advanced Order Types
- **Bracket Orders**: Entry + take profit + stop loss in one order
- **Trailing Stops**: Dynamic stop losses that follow price movements
- **All Standard Types**: Market, limit, stop, stop-limit orders
- **Extended Hours**: Support for pre-market and after-hours trading

### 5. Real-Time Account Monitoring
- **Live Account Data**: Real-time balance and buying power
- **Position Tracking**: Current holdings with P&L calculations
- **Order Status Updates**: Real-time order execution monitoring
- **Trade History**: Complete historical trade records

## Security Features

### 1. Credential Management
- **Centralized Secrets**: Secure API key management
- **Environment Separation**: Different keys for different environments
- **Credential Masking**: Secure logging that masks sensitive data
- **Validation Layer**: Verify credentials before use

### 2. Environment Controls
- **Development Safety**: Live trading disabled in development
- **Explicit Enable**: Requires `LIVE_TRADING_ENABLED=true` setting
- **Environment Detection**: Automatic paper trading in unsafe environments
- **Audit Logging**: Comprehensive trade execution logging

### 3. Risk Management
- **Position Limits**: Maximum position size enforcement
- **Account Monitoring**: Real-time buying power checks
- **Trade Validation**: Multi-layer validation before execution
- **Error Handling**: Graceful handling of API errors

## Configuration Options

### Environment Variables
```bash
# Alpaca API Credentials
ALPACA_API_KEY=your_api_key
ALPACA_SECRET_KEY=your_secret_key

# Trading Configuration
DEFAULT_BROKER=alpaca
LIVE_TRADING_ENABLED=false  # Set to true for live trading
USE_PAPER_TRADING=true      # Default to paper trading

# Environment
ENVIRONMENT=development     # development/staging/production
```

### Broker Factory Configuration
```python
# Paper Trading (Safe Default)
broker = get_paper_broker()

# Live Trading (With Safety Checks)
broker = get_live_broker()  # Requires proper configuration

# Custom Configuration
broker = BrokerFactory.create_broker(
    broker_name="alpaca",
    use_paper=False  # Live trading
)
```

## Usage Examples

### Basic Live Trading
```python
from app.services.broker import get_live_broker
from app.models.trade import Trade, OrderType, OrderSide

# Create live broker
broker = get_live_broker()

# Create trade
trade = Trade(
    symbol="AAPL",
    side=OrderSide.BUY,
    order_type=OrderType.MARKET,
    quantity=10,
    is_paper_trade=False
)

# Execute with safety checks
result = broker.execute_trade(trade)
```

### Fractional Share Investing
```python
# Dollar-based investment
trade = Trade(
    symbol="TSLA",
    side=OrderSide.BUY,
    order_type=OrderType.MARKET,
    investment_amount=100.0,  # Invest $100
    is_fractional=True
)

result = broker.execute_trade(trade)
```

### Advanced Orders
```python
# Bracket order (buy + profit target + stop loss)
result = broker.place_bracket_order(
    trade=trade,
    take_profit_price=450.0,
    stop_loss_price=400.0
)

# Trailing stop
result = broker.place_trailing_stop(
    trade=sell_trade,
    trail_amount=5.0,  # 5% trailing stop
    trail_type="percent"
)
```

## Safety Mechanisms

### 1. Multi-Layer Validation
1. **Credential Check**: Validate API keys exist and are valid
2. **Environment Check**: Ensure live trading is allowed
3. **Trade Validation**: Validate all trade parameters
4. **Account Check**: Verify sufficient buying power
5. **Symbol Check**: Confirm symbol is tradeable
6. **Market Check**: Verify market is open (or queue for later)

### 2. Error Handling
- **Graceful Degradation**: Safe fallbacks for API failures
- **Detailed Error Messages**: Clear error reporting with codes
- **Retry Logic**: Automatic retries for transient failures
- **Audit Trail**: Complete logging of all operations

### 3. Risk Controls
- **Position Limits**: Maximum $50,000 per position (configurable)
- **Daily Trade Limits**: PDT compliance monitoring
- **Account Monitoring**: Real-time balance checks
- **Market Hours**: Respect trading hours unless explicitly overridden

## Testing and Validation

### Paper Trading Testing
- All features available in paper trading mode
- Zero risk environment for testing strategies
- Real-time market data with simulated execution
- Perfect for development and testing

### Live Trading Validation
- Comprehensive pre-trade validation
- Real-time account monitoring
- Detailed execution reporting
- Full audit trail for compliance

## Migration Path

### From Paper to Live Trading
1. **Verify Credentials**: Ensure live API keys are configured
2. **Set Environment**: Configure `LIVE_TRADING_ENABLED=true`
3. **Test Thoroughly**: Use paper trading for initial testing
4. **Small Positions**: Start with small position sizes
5. **Monitor Closely**: Watch all trades and account status

### Rollback Safety
- **Instant Rollback**: Set `USE_PAPER_TRADING=true` to disable live trading
- **Environment Override**: Development environment always uses paper trading
- **Configuration Control**: All settings controllable via environment variables

## File Changes Summary

### New Files
- `/backend/app/core/secrets.py` - Secure credential management
- `/backend/app/services/broker/factory.py` - Broker factory with safety controls
- `/backend/app/services/broker/examples.py` - Usage examples and documentation

### Enhanced Files
- `/backend/app/services/broker/alpaca.py` - Full live trading capabilities
- `/backend/app/models/trade.py` - Added missing TradeStatus constants
- `/backend/app/core/config.py` - Added broker configuration settings
- `/backend/app/services/broker/__init__.py` - Updated exports

### Key Enhancements
- **Fractional shares support** for dollar-based investing
- **Enhanced safety validation** for live trading
- **Real-time account monitoring** and risk management
- **Pattern Day Trader compliance** monitoring
- **Advanced order types** (bracket, trailing stop)
- **Comprehensive error handling** and logging

## Ready for Production

The enhanced Alpaca broker integration is production-ready with:
- ✅ Comprehensive safety controls
- ✅ Real account and position tracking
- ✅ Live order execution capabilities
- ✅ Advanced order types support
- ✅ Fractional shares for micro-investing
- ✅ PDT compliance monitoring
- ✅ Detailed audit logging
- ✅ Environment-based safety controls
- ✅ Paper trading option maintained for testing

The system maintains the paper trading option for safe testing while providing full live trading capabilities when properly configured and authorized.