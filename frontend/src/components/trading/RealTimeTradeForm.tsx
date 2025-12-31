import React, { useState, useEffect, useMemo, useCallback, memo } from 'react';
import { useMarketWebSocket, MarketQuote } from '../../hooks/useMarketWebSocket';
import { Button } from '../common/Button';
import { Input } from '../common/Input';
import { Select } from '../common/Select';
import { formatCurrency, formatNumber } from '../../utils/formatters';
import { LoadingSpinner } from '../common/LoadingSpinner';
import { tradingService } from '../../services/tradingService';

interface RealTimeTradeFormProps {
  portfolioId: number;
  onTradeComplete?: () => void;
  darkMode?: boolean;
}

export const RealTimeTradeForm: React.FC<RealTimeTradeFormProps> = memo(({
  portfolioId,
  onTradeComplete,
  darkMode = true
}) => {
  // Form state
  const [symbol, setSymbol] = useState('');
  const [quantity, setQuantity] = useState('');
  const [orderType, setOrderType] = useState('market');
  const [limitPrice, setLimitPrice] = useState('');
  const [side, setSide] = useState('buy');
  
  // Form processing
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [error, setError] = useState('');
  const [success, setSuccess] = useState('');
  
  // Market data connection with optimized settings
  const { isConnected, quotes, subscribe, unsubscribe } = useMarketWebSocket({
    autoConnect: true,
    cacheEnabled: true,
    cacheTTL: 60 // 1 minute cache for trading quotes
  });
  
  // Memoized current quote to prevent unnecessary re-renders
  const currentQuote = useMemo(() => 
    symbol ? quotes[symbol.toUpperCase()] : null,
    [symbol, quotes]
  );
  
  // Subscribe to symbol when it changes
  useEffect(() => {
    if (symbol) {
      subscribe([symbol]);
    }
    
    return () => {
      if (symbol) {
        unsubscribe([symbol]);
      }
    };
  }, [symbol, subscribe, unsubscribe]);
  
  // Calculate estimated cost
  const calculatedCost = useMemo(() => {
    if (!symbol || !quantity || isNaN(parseFloat(quantity))) {
      return null;
    }
    
    const price = orderType === 'limit' && limitPrice 
      ? parseFloat(limitPrice)
      : currentQuote?.price;
      
    if (!price) {
      return null;
    }
    
    return parseFloat(quantity) * price;
  }, [symbol, quantity, orderType, limitPrice, currentQuote]);
  
  // Memoized handlers to prevent unnecessary re-renders
  const handleSymbolChange = useCallback((e: React.ChangeEvent<HTMLInputElement>) => {
    const value = e.target.value.trim().toUpperCase();
    setSymbol(value);
  }, []);
  
  const handleQuantityChange = useCallback((e: React.ChangeEvent<HTMLInputElement>) => {
    setQuantity(e.target.value);
  }, []);
  
  const handleLimitPriceChange = useCallback((e: React.ChangeEvent<HTMLInputElement>) => {
    setLimitPrice(e.target.value);
  }, []);
  
  const handleOrderTypeChange = useCallback((e: React.ChangeEvent<HTMLSelectElement>) => {
    setOrderType(e.target.value);
  }, []);
  
  const handleSideChange = useCallback((side: 'buy' | 'sell') => {
    setSide(side);
  }, []);
  
  // Memoized form submission handler
  const handleSubmit = useCallback(async (e: React.FormEvent) => {
    e.preventDefault();
    
    // Reset messages
    setError('');
    setSuccess('');
    
    // Basic validation
    if (!symbol) {
      setError('Symbol is required');
      return;
    }
    
    if (!quantity || isNaN(parseFloat(quantity)) || parseFloat(quantity) <= 0) {
      setError('Please enter a valid quantity');
      return;
    }
    
    if (orderType === 'limit' && (!limitPrice || isNaN(parseFloat(limitPrice)) || parseFloat(limitPrice) <= 0)) {
      setError('Please enter a valid limit price');
      return;
    }
    
    try {
      setIsSubmitting(true);
      
      // Prepare order data
      const orderData = {
        symbol: symbol.toUpperCase(),
        order_type: orderType.toLowerCase() as 'market' | 'limit' | 'stop' | 'stop_limit',
        side: side.toLowerCase() as 'buy' | 'sell',
        amount: parseFloat(quantity),
        limit_price: orderType === 'limit' ? parseFloat(limitPrice) : undefined,
      };

      // Place order
      const result = await tradingService.placeOrder(orderData);
      
      // Show success
      setSuccess(`Order placed successfully! Order ID: ${result.id}`);
      
      // Reset form
      if (side === 'buy') {
        setQuantity('');
        setLimitPrice('');
      }
      
      // Call completion callback
      if (onTradeComplete) {
        onTradeComplete();
      }
    } catch (err: any) {
      setError(err.message || 'Failed to place order');
    } finally {
      setIsSubmitting(false);
    }
  }, [symbol, quantity, limitPrice, orderType, side, onTradeComplete]);
  
  // Memoized price class
  const priceClass = useMemo(() => {
    if (!currentQuote) return '';
    
    if (darkMode) {
      return 'text-gray-100'; // Neutral color for dark mode
    } else {
      return 'text-gray-800'; // Neutral color for light mode
    }
  }, [currentQuote, darkMode]);
  
  // UI based on theme
  if (darkMode) {
    return (
      <div className="bg-gray-900 rounded-lg p-6 shadow-lg">
        <h2 className="text-xl font-semibold text-white mb-4">Real-Time Trading</h2>
        
        {/* Connection status */}
        <div className="mb-4 flex items-center">
          <div className={`w-2 h-2 rounded-full mr-2 ${isConnected ? 'bg-green-500' : 'bg-red-500'}`}></div>
          <span className="text-sm text-gray-400">
            {isConnected ? 'Connected to market data' : 'Connecting to market data...'}
          </span>
        </div>
        
        {/* Success message */}
        {success && (
          <div className="mb-4 p-3 bg-green-900/30 border border-green-700 text-green-300 rounded">
            {success}
          </div>
        )}
        
        {/* Error message */}
        {error && (
          <div className="mb-4 p-3 bg-red-900/30 border border-red-700 text-red-300 rounded">
            {error}
          </div>
        )}
        
        <form onSubmit={handleSubmit}>
          <div className="space-y-4">
            {/* Symbol input */}
            <div>
              <label className="block text-sm font-medium text-gray-300 mb-1">
                Symbol
              </label>
              <Input
                type="text"
                value={symbol}
                onChange={handleSymbolChange}
                placeholder="AAPL, MSFT, etc."
                className="w-full bg-gray-800 border-gray-700 text-white"
                autoComplete="off"
              />
            </div>
            
            {/* Current price display */}
            {symbol && (
              <div className="p-3 bg-gray-800 rounded">
                <div className="flex justify-between items-center">
                  <span className="text-gray-400">Current Price:</span>
                  <span className={`text-lg font-semibold ${priceClass}`}>
                    {currentQuote ? (
                      formatCurrency(currentQuote.price)
                    ) : (
                      <LoadingSpinner size="sm" className="h-4 w-4 text-gray-400" />
                    )}
                  </span>
                </div>
                {currentQuote && (
                  <div className="flex justify-between items-center mt-1 text-sm">
                    <span className="text-gray-500">Last Updated:</span>
                    <span className="text-gray-400">
                      {new Date(currentQuote.timestamp).toLocaleTimeString()}
                    </span>
                  </div>
                )}
              </div>
            )}
            
            {/* Order type selection */}
            <div>
              <label className="block text-sm font-medium text-gray-300 mb-1">
                Order Type
              </label>
              <Select
                value={orderType}
                onChange={handleOrderTypeChange}
                className="w-full bg-gray-800 border-gray-700 text-white"
              >
                <option value="market">Market Order</option>
                <option value="limit">Limit Order</option>
              </Select>
            </div>
            
            {/* Limit price (conditional) */}
            {orderType === 'limit' && (
              <div>
                <label className="block text-sm font-medium text-gray-300 mb-1">
                  Limit Price
                </label>
                <div className="relative">
                  <div className="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none">
                    <span className="text-gray-500 sm:text-sm">$</span>
                  </div>
                  <Input
                    type="number"
                    value={limitPrice}
                    onChange={handleLimitPriceChange}
                    placeholder="0.00"
                    className="pl-7 w-full bg-gray-800 border-gray-700 text-white"
                    step="0.01"
                    min="0"
                  />
                </div>
              </div>
            )}
            
            {/* Order side selection */}
            <div>
              <label className="block text-sm font-medium text-gray-300 mb-1">
                Side
              </label>
              <div className="flex space-x-4">
                <label className="flex items-center">
                  <input
                    type="radio"
                    value="buy"
                    checked={side === 'buy'}
                    onChange={() => handleSideChange('buy')}
                    className="h-4 w-4 text-green-600 bg-gray-800 border-gray-700"
                  />
                  <span className="ml-2 text-gray-300">Buy</span>
                </label>
                <label className="flex items-center">
                  <input
                    type="radio"
                    value="sell"
                    checked={side === 'sell'}
                    onChange={() => handleSideChange('sell')}
                    className="h-4 w-4 text-red-600 bg-gray-800 border-gray-700"
                  />
                  <span className="ml-2 text-gray-300">Sell</span>
                </label>
              </div>
            </div>
            
            {/* Quantity input */}
            <div>
              <label className="block text-sm font-medium text-gray-300 mb-1">
                Quantity
              </label>
              <Input
                type="number"
                value={quantity}
                onChange={handleQuantityChange}
                placeholder="0"
                className="w-full bg-gray-800 border-gray-700 text-white"
                step="1"
                min="1"
              />
            </div>
            
            {/* Estimated cost */}
            {calculatedCost !== null && (
              <div className="p-3 bg-gray-800 rounded">
                <div className="flex justify-between items-center">
                  <span className="text-gray-400">Estimated {side === 'buy' ? 'Cost' : 'Proceeds'}:</span>
                  <span className="text-lg font-semibold text-gray-100">
                    {formatCurrency(calculatedCost)}
                  </span>
                </div>
              </div>
            )}
            
            {/* Submit button */}
            <div className="pt-2">
              <Button
                type="submit"
                className={`w-full ${
                  side === 'buy' 
                    ? 'bg-green-600 hover:bg-green-700' 
                    : 'bg-red-600 hover:bg-red-700'
                } text-white`}
                disabled={isSubmitting || !isConnected}
              >
                {isSubmitting ? (
                  <span className="flex items-center justify-center">
                    <LoadingSpinner size="sm" className="mr-2" />
                    Placing Order...
                  </span>
                ) : (
                  `${side === 'buy' ? 'Buy' : 'Sell'} ${symbol ? symbol.toUpperCase() : ''}`
                )}
              </Button>
            </div>
          </div>
        </form>
        
        <div className="mt-4 text-xs text-gray-500 text-center">
          All trades are executed in real-time with current market prices
        </div>
      </div>
    );
  }
  
  // Light mode version
  return (
    <div className="bg-white rounded-lg p-6 shadow-md">
      <h2 className="text-xl font-semibold text-gray-800 mb-4">Real-Time Trading</h2>
      
      {/* Connection status */}
      <div className="mb-4 flex items-center">
        <div className={`w-2 h-2 rounded-full mr-2 ${isConnected ? 'bg-green-500' : 'bg-red-500'}`}></div>
        <span className="text-sm text-gray-500">
          {isConnected ? 'Connected to market data' : 'Connecting to market data...'}
        </span>
      </div>
      
      {/* Success message */}
      {success && (
        <div className="mb-4 p-3 bg-green-50 border border-green-200 text-green-800 rounded">
          {success}
        </div>
      )}
      
      {/* Error message */}
      {error && (
        <div className="mb-4 p-3 bg-red-50 border border-red-200 text-red-800 rounded">
          {error}
        </div>
      )}
      
      <form onSubmit={handleSubmit}>
        <div className="space-y-4">
          {/* Symbol input */}
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              Symbol
            </label>
            <Input
              type="text"
              value={symbol}
              onChange={handleSymbolChange}
              placeholder="AAPL, MSFT, etc."
              className="w-full"
              autoComplete="off"
            />
          </div>
          
          {/* Current price display */}
          {symbol && (
            <div className="p-3 bg-gray-50 rounded border border-gray-200">
              <div className="flex justify-between items-center">
                <span className="text-gray-500">Current Price:</span>
                <span className={`text-lg font-semibold ${priceClass}`}>
                  {currentQuote ? (
                    formatCurrency(currentQuote.price)
                  ) : (
                    <LoadingSpinner size="sm" className="h-4 w-4 text-gray-400" />
                  )}
                </span>
              </div>
              {currentQuote && (
                <div className="flex justify-between items-center mt-1 text-sm">
                  <span className="text-gray-500">Last Updated:</span>
                  <span className="text-gray-600">
                    {new Date(currentQuote.timestamp).toLocaleTimeString()}
                  </span>
                </div>
              )}
            </div>
          )}
          
          {/* Order type selection */}
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              Order Type
            </label>
            <Select
              value={orderType}
              onChange={handleOrderTypeChange}
              className="w-full"
            >
              <option value="market">Market Order</option>
              <option value="limit">Limit Order</option>
            </Select>
          </div>
          
          {/* Limit price (conditional) */}
          {orderType === 'limit' && (
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Limit Price
              </label>
              <div className="relative">
                <div className="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none">
                  <span className="text-gray-500 sm:text-sm">$</span>
                </div>
                <Input
                  type="number"
                  value={limitPrice}
                  onChange={handleLimitPriceChange}
                  placeholder="0.00"
                  className="pl-7 w-full"
                  step="0.01"
                  min="0"
                />
              </div>
            </div>
          )}
          
          {/* Order side selection */}
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              Side
            </label>
            <div className="flex space-x-4">
              <label className="flex items-center">
                <input
                  type="radio"
                  value="buy"
                  checked={side === 'buy'}
                  onChange={() => handleSideChange('buy')}
                  className="h-4 w-4 text-green-600"
                />
                <span className="ml-2 text-gray-700">Buy</span>
              </label>
              <label className="flex items-center">
                <input
                  type="radio"
                  value="sell"
                  checked={side === 'sell'}
                  onChange={() => handleSideChange('sell')}
                  className="h-4 w-4 text-red-600"
                />
                <span className="ml-2 text-gray-700">Sell</span>
              </label>
            </div>
          </div>
          
          {/* Quantity input */}
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              Quantity
            </label>
            <Input
              type="number"
              value={quantity}
              onChange={handleQuantityChange}
              placeholder="0"
              className="w-full"
              step="1"
              min="1"
            />
          </div>
          
          {/* Estimated cost */}
          {calculatedCost !== null && (
            <div className="p-3 bg-gray-50 rounded border border-gray-200">
              <div className="flex justify-between items-center">
                <span className="text-gray-500">Estimated {side === 'buy' ? 'Cost' : 'Proceeds'}:</span>
                <span className="text-lg font-semibold text-gray-800">
                  {formatCurrency(calculatedCost)}
                </span>
              </div>
            </div>
          )}
          
          {/* Submit button */}
          <div className="pt-2">
            <Button
              type="submit"
              className={`w-full ${
                side === 'buy' 
                  ? 'bg-green-600 hover:bg-green-700' 
                  : 'bg-red-600 hover:bg-red-700'
              } text-white`}
              disabled={isSubmitting || !isConnected}
            >
              {isSubmitting ? (
                <span className="flex items-center justify-center">
                  <LoadingSpinner size="sm" className="mr-2" />
                  Placing Order...
                </span>
              ) : (
                `${side === 'buy' ? 'Buy' : 'Sell'} ${symbol ? symbol.toUpperCase() : ''}`
              )}
            </Button>
          </div>
        </div>
      </form>
      
      <div className="mt-4 text-xs text-gray-500 text-center">
        All trades are executed in real-time with current market prices
      </div>
    </div>
  );
}, (prevProps, nextProps) => {
  // Only re-render if the essential props have changed
  return (
    prevProps.portfolioId === nextProps.portfolioId &&
    prevProps.darkMode === nextProps.darkMode &&
    // Only consider onTradeComplete function changes if defined/undefined state changes
    ((!!prevProps.onTradeComplete === !!nextProps.onTradeComplete))
  );
});

export default RealTimeTradeForm;