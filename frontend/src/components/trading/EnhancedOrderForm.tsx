import React, { useState, useEffect } from 'react';
import { useTradingContext } from '../../contexts/TradingContext';
import { useExecuteTradeMutation, useGetTradingAccountQuery } from '../../services/tradingApi';
import { TradeRiskAssessment } from '../risk/TradeRiskAssessment';
import { TradingSafeguardWrapper } from '../trading/TradingSafeguards';
import { LoadingSpinner } from '../common/LoadingSpinner';

interface EnhancedOrderFormProps {
  symbol: string;
  currentPrice: number;
  className?: string;
  onOrderSubmitted?: (orderId: string) => void;
}

type OrderType = 'MARKET' | 'LIMIT' | 'STOP_LOSS' | 'STOP_LIMIT';
type TradeType = 'BUY' | 'SELL';
type TimeInForce = 'DAY' | 'GTC' | 'IOC' | 'FOK';

export const EnhancedOrderForm: React.FC<EnhancedOrderFormProps> = ({
  symbol,
  currentPrice,
  className = '',
  onOrderSubmitted,
}) => {
  const { mode, isBlocked, dailyLimits } = useTradingContext();
  
  // Form state
  const [tradeType, setTradeType] = useState<TradeType>('BUY');
  const [orderType, setOrderType] = useState<OrderType>('MARKET');
  const [quantity, setQuantity] = useState<number>(0);
  const [limitPrice, setLimitPrice] = useState<number>(currentPrice);
  const [stopPrice, setStopPrice] = useState<number>(currentPrice);
  const [timeInForce, setTimeInForce] = useState<TimeInForce>('DAY');
  const [dollarsToInvest, setDollarsToInvest] = useState<number>(0);
  const [useDoLLars, setUseDollars] = useState<boolean>(false);
  
  // UI state
  const [showAdvanced, setShowAdvanced] = useState<boolean>(false);
  const [riskAssessment, setRiskAssessment] = useState<any>(null);
  const [orderConfirmation, setOrderConfirmation] = useState<boolean>(false);

  // API hooks
  const [executeTrade, { isLoading: isExecuting }] = useExecuteTradeMutation();
  const { data: account } = useGetTradingAccountQuery({ mode });

  // Update limit/stop prices when current price changes
  useEffect(() => {
    if (orderType === 'LIMIT') {
      setLimitPrice(currentPrice);
    }
    if (orderType === 'STOP_LOSS' || orderType === 'STOP_LIMIT') {
      setStopPrice(currentPrice * (tradeType === 'BUY' ? 1.02 : 0.98));
    }
  }, [currentPrice, orderType, tradeType]);

  // Calculate quantities
  useEffect(() => {
    if (useDoLLars && dollarsToInvest > 0) {
      const price = orderType === 'MARKET' ? currentPrice : limitPrice;
      setQuantity(Math.floor(dollarsToInvest / price));
    }
  }, [useDoLLars, dollarsToInvest, currentPrice, limitPrice, orderType]);

  const getEstimatedTotal = () => {
    const price = orderType === 'MARKET' ? currentPrice : limitPrice;
    const baseTotal = quantity * price;
    const estimatedFees = baseTotal * 0.0001; // 0.01% estimated fees
    return baseTotal + estimatedFees;
  };

  const getMaxBuyingPower = () => {
    return account?.buying_power || 0;
  };

  const getAvailableShares = () => {
    // This would come from positions data - placeholder for now
    return 0;
  };

  const validateOrder = () => {
    const errors: string[] = [];
    
    if (!symbol) errors.push('Symbol is required');
    if (quantity <= 0) errors.push('Quantity must be greater than 0');
    if (orderType === 'LIMIT' && limitPrice <= 0) errors.push('Limit price must be greater than 0');
    if ((orderType === 'STOP_LOSS' || orderType === 'STOP_LIMIT') && stopPrice <= 0) {
      errors.push('Stop price must be greater than 0');
    }
    
    if (tradeType === 'BUY') {
      const total = getEstimatedTotal();
      const buyingPower = getMaxBuyingPower();
      if (total > buyingPower) {
        errors.push(`Insufficient buying power. Available: $${buyingPower.toLocaleString()}`);
      }
    }
    
    if (tradeType === 'SELL') {
      const availableShares = getAvailableShares();
      if (quantity > availableShares) {
        errors.push(`Insufficient shares. Available: ${availableShares}`);
      }
    }
    
    if (isBlocked) {
      errors.push('Trading is currently blocked');
    }
    
    if (dailyLimits.ordersRemaining <= 0) {
      errors.push('Daily order limit reached');
    }

    return errors;
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    
    const validationErrors = validateOrder();
    if (validationErrors.length > 0) {
      alert('Order validation failed:\n' + validationErrors.join('\n'));
      return;
    }

    // Show confirmation for live trades or high-risk orders
    if (mode === 'live' || (riskAssessment && riskAssessment.risk_level === 'high')) {
      setOrderConfirmation(true);
      return;
    }

    await executeOrder();
  };

  const executeOrder = async () => {
    try {
      const orderData = {
        symbol: symbol.toUpperCase(),
        trade_type: tradeType,
        order_type: orderType,
        quantity,
        price: orderType === 'LIMIT' || orderType === 'STOP_LIMIT' ? limitPrice : undefined,
        stop_price: orderType === 'STOP_LOSS' || orderType === 'STOP_LIMIT' ? stopPrice : undefined,
        time_in_force: timeInForce,
        mode,
      };

      const result = await executeTrade(orderData).unwrap();
      
      // Reset form
      setQuantity(0);
      setDollarsToInvest(0);
      setOrderConfirmation(false);
      
      // Notify parent component
      onOrderSubmitted?.(result.trade_id);
      
      // Show success message
      alert(`Order submitted successfully! Order ID: ${result.trade_id}`);
      
    } catch (error: any) {
      console.error('Order execution failed:', error);
      alert('Order failed: ' + (error.data?.detail || error.message || 'Unknown error'));
    }
  };

  const formatCurrency = (amount: number) => {
    return new Intl.NumberFormat('en-US', {
      style: 'currency',
      currency: 'USD',
    }).format(amount);
  };

  return (
    <div className={`bg-gray-900 rounded-xl p-6 ${className}`}>
      {/* Header */}
      <div className="flex items-center justify-between mb-6">
        <h3 className="text-lg font-medium text-white">
          {tradeType} {symbol}
        </h3>
        <div className={`px-3 py-1 rounded-full text-sm font-medium ${
          mode === 'paper' 
            ? 'bg-yellow-900 text-yellow-300' 
            : 'bg-red-900 text-red-300'
        }`}>
          {mode.toUpperCase()}
        </div>
      </div>

      <form onSubmit={handleSubmit} className="space-y-6">
        {/* Trade Type Toggle */}
        <div className="flex bg-gray-800 rounded-lg p-1">
          <button
            type="button"
            onClick={() => setTradeType('BUY')}
            className={`flex-1 py-2 px-4 rounded-lg font-medium transition-colors ${
              tradeType === 'BUY'
                ? 'bg-green-600 text-white'
                : 'text-gray-400 hover:text-white'
            }`}
          >
            Buy
          </button>
          <button
            type="button"
            onClick={() => setTradeType('SELL')}
            className={`flex-1 py-2 px-4 rounded-lg font-medium transition-colors ${
              tradeType === 'SELL'
                ? 'bg-red-600 text-white'
                : 'text-gray-400 hover:text-white'
            }`}
          >
            Sell
          </button>
        </div>

        {/* Order Type */}
        <div>
          <label className="block text-gray-400 text-sm mb-2">Order Type</label>
          <select
            value={orderType}
            onChange={(e) => setOrderType(e.target.value as OrderType)}
            className="w-full bg-gray-800 border border-gray-700 rounded-lg p-3 text-white focus:outline-none focus:border-purple-500"
          >
            <option value="MARKET">Market Order</option>
            <option value="LIMIT">Limit Order</option>
            <option value="STOP_LOSS">Stop Loss</option>
            <option value="STOP_LIMIT">Stop Limit</option>
          </select>
        </div>

        {/* Quantity/Dollar Toggle */}
        <div className="flex items-center space-x-4 mb-4">
          <button
            type="button"
            onClick={() => setUseDollars(false)}
            className={`px-4 py-2 rounded-lg text-sm font-medium transition-colors ${
              !useDoLLars
                ? 'bg-purple-600 text-white'
                : 'bg-gray-700 text-gray-300 hover:bg-gray-600'
            }`}
          >
            Shares
          </button>
          <button
            type="button"
            onClick={() => setUseDollars(true)}
            className={`px-4 py-2 rounded-lg text-sm font-medium transition-colors ${
              useDoLLars
                ? 'bg-purple-600 text-white'
                : 'bg-gray-700 text-gray-300 hover:bg-gray-600'
            }`}
          >
            Dollars
          </button>
        </div>

        {/* Quantity/Dollar Input */}
        {useDoLLars ? (
          <div>
            <label className="block text-gray-400 text-sm mb-2">Amount to Invest</label>
            <input
              type="number"
              value={dollarsToInvest || ''}
              onChange={(e) => setDollarsToInvest(Number(e.target.value))}
              step="0.01"
              min="0"
              className="w-full bg-gray-800 border border-gray-700 rounded-lg p-3 text-white focus:outline-none focus:border-purple-500"
              placeholder="0.00"
            />
            <div className="text-gray-500 text-sm mt-1">
              Estimated shares: {quantity.toLocaleString()}
            </div>
          </div>
        ) : (
          <div>
            <label className="block text-gray-400 text-sm mb-2">Quantity</label>
            <input
              type="number"
              value={quantity || ''}
              onChange={(e) => setQuantity(Number(e.target.value))}
              step="1"
              min="0"
              className="w-full bg-gray-800 border border-gray-700 rounded-lg p-3 text-white focus:outline-none focus:border-purple-500"
              placeholder="0"
            />
          </div>
        )}

        {/* Limit Price (for LIMIT and STOP_LIMIT orders) */}
        {(orderType === 'LIMIT' || orderType === 'STOP_LIMIT') && (
          <div>
            <label className="block text-gray-400 text-sm mb-2">Limit Price</label>
            <input
              type="number"
              value={limitPrice || ''}
              onChange={(e) => setLimitPrice(Number(e.target.value))}
              step="0.01"
              min="0"
              className="w-full bg-gray-800 border border-gray-700 rounded-lg p-3 text-white focus:outline-none focus:border-purple-500"
              placeholder="0.00"
            />
          </div>
        )}

        {/* Stop Price (for STOP_LOSS and STOP_LIMIT orders) */}
        {(orderType === 'STOP_LOSS' || orderType === 'STOP_LIMIT') && (
          <div>
            <label className="block text-gray-400 text-sm mb-2">Stop Price</label>
            <input
              type="number"
              value={stopPrice || ''}
              onChange={(e) => setStopPrice(Number(e.target.value))}
              step="0.01"
              min="0"
              className="w-full bg-gray-800 border border-gray-700 rounded-lg p-3 text-white focus:outline-none focus:border-purple-500"
              placeholder="0.00"
            />
          </div>
        )}

        {/* Advanced Options */}
        <div>
          <button
            type="button"
            onClick={() => setShowAdvanced(!showAdvanced)}
            className="text-purple-400 hover:text-purple-300 text-sm transition-colors"
          >
            {showAdvanced ? 'Hide' : 'Show'} Advanced Options
          </button>
          
          {showAdvanced && (
            <div className="mt-4 space-y-4">
              <div>
                <label className="block text-gray-400 text-sm mb-2">Time in Force</label>
                <select
                  value={timeInForce}
                  onChange={(e) => setTimeInForce(e.target.value as TimeInForce)}
                  className="w-full bg-gray-800 border border-gray-700 rounded-lg p-3 text-white focus:outline-none focus:border-purple-500"
                >
                  <option value="DAY">Day Order</option>
                  <option value="GTC">Good Till Canceled</option>
                  <option value="IOC">Immediate or Cancel</option>
                  <option value="FOK">Fill or Kill</option>
                </select>
              </div>
            </div>
          )}
        </div>

        {/* Risk Assessment */}
        {quantity > 0 && (
          <TradeRiskAssessment
            symbol={symbol}
            tradeType={tradeType}
            quantity={quantity}
            price={orderType === 'MARKET' ? currentPrice : limitPrice}
            onRiskAssessment={setRiskAssessment}
          />
        )}

        {/* Order Summary */}
        {quantity > 0 && (
          <div className="bg-gray-800 rounded-lg p-4">
            <h4 className="text-white font-medium mb-3">Order Summary</h4>
            <div className="space-y-2 text-sm">
              <div className="flex justify-between">
                <span className="text-gray-400">Order Type:</span>
                <span className="text-white">{orderType}</span>
              </div>
              <div className="flex justify-between">
                <span className="text-gray-400">Quantity:</span>
                <span className="text-white">{quantity.toLocaleString()} shares</span>
              </div>
              <div className="flex justify-between">
                <span className="text-gray-400">Estimated Price:</span>
                <span className="text-white">
                  {formatCurrency(orderType === 'MARKET' ? currentPrice : limitPrice)}
                </span>
              </div>
              <div className="flex justify-between">
                <span className="text-gray-400">Estimated Total:</span>
                <span className="text-white font-medium">
                  {formatCurrency(getEstimatedTotal())}
                </span>
              </div>
            </div>
          </div>
        )}

        {/* Submit Button */}
        <TradingSafeguardWrapper
          requiresConfirmation={mode === 'live'}
          actionType="order"
          title={`Confirm ${tradeType} Order`}
          message={`Are you sure you want to ${tradeType.toLowerCase()} ${quantity} shares of ${symbol}?`}
          orderDetails={{
            symbol,
            action: tradeType.toLowerCase() as any,
            quantity,
            price: orderType === 'MARKET' ? currentPrice : limitPrice,
            orderType,
          }}
          onExecute={executeOrder}
          disabled={isBlocked || quantity <= 0 || isExecuting}
        >
          <button
            type="submit"
            disabled={isBlocked || quantity <= 0 || isExecuting}
            className={`w-full py-3 px-4 rounded-lg font-medium transition-colors ${
              isBlocked || quantity <= 0 || isExecuting
                ? 'bg-gray-600 text-gray-400 cursor-not-allowed'
                : tradeType === 'BUY'
                ? 'bg-green-600 hover:bg-green-700 text-white'
                : 'bg-red-600 hover:bg-red-700 text-white'
            }`}
          >
            {isExecuting ? (
              <div className="flex items-center justify-center">
                <LoadingSpinner size="sm" />
                <span className="ml-2">Executing Order...</span>
              </div>
            ) : (
              `${tradeType} ${symbol}`
            )}
          </button>
        </TradingSafeguardWrapper>
      </form>

      {/* Account Info */}
      {account && (
        <div className="mt-6 pt-6 border-t border-gray-700">
          <div className="grid grid-cols-2 gap-4 text-sm">
            <div>
              <span className="text-gray-400">Buying Power:</span>
              <span className="text-white ml-2 font-medium">
                {formatCurrency(account.buying_power)}
              </span>
            </div>
            <div>
              <span className="text-gray-400">Cash Balance:</span>
              <span className="text-white ml-2 font-medium">
                {formatCurrency(account.cash_balance)}
              </span>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default EnhancedOrderForm;