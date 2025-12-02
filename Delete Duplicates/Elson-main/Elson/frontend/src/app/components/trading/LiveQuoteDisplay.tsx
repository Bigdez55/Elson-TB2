import React, { useState, useEffect, useMemo, memo } from 'react';
import { useMarketWebSocket, MarketQuote } from '../../hooks/useMarketWebSocket';
import { formatCurrency, formatNumber } from '../../utils/formatters';
import { LoadingSpinner } from '../common/LoadingSpinner';

interface LiveQuoteDisplayProps {
  symbols: string[];
  className?: string;
  darkMode?: boolean;
  compact?: boolean;
  onQuoteUpdate?: (quotes: Record<string, MarketQuote>) => void;
}

export const LiveQuoteDisplay: React.FC<LiveQuoteDisplayProps> = memo(({
  symbols,
  className = '',
  darkMode = true,
  compact = false,
  onQuoteUpdate
}) => {
  // Connect to market websocket
  const { isConnected, error, quotes, subscribe, unsubscribe } = useMarketWebSocket({
    autoConnect: true
  });
  
  // Format quotes for display
  const formattedQuotes = useMemo(() => {
    return symbols.map(symbol => {
      const quote = quotes[symbol];
      if (!quote) {
        return {
          symbol,
          price: null,
          timestamp: null,
          formattedPrice: '—',
          formattedChange: '—',
          changeDirection: 'neutral',
          formattedTime: '—',
          age: null
        };
      }
      
      // Format values for display
      const price = quote.price;
      const change = 0; // We don't have change yet, would need to track previous price
      
      // Format timestamp
      const timestamp = new Date(quote.timestamp);
      const now = new Date();
      const ageMs = now.getTime() - timestamp.getTime();
      const formattedTime = timestamp.toLocaleTimeString();
      
      return {
        symbol,
        price,
        timestamp,
        formattedPrice: formatCurrency(price),
        formattedChange: change === 0 ? '0.00%' : `${change > 0 ? '+' : ''}${(change * 100).toFixed(2)}%`,
        changeDirection: change > 0 ? 'up' : change < 0 ? 'down' : 'neutral',
        formattedTime,
        age: ageMs
      };
    });
  }, [symbols, quotes]);
  
  // Call onQuoteUpdate callback whenever quotes change
  useEffect(() => {
    if (onQuoteUpdate) {
      onQuoteUpdate(quotes);
    }
  }, [quotes, onQuoteUpdate]);
  
  // Subscribe to symbols when they change
  useEffect(() => {
    subscribe(symbols);
    
    return () => {
      unsubscribe(symbols);
    };
  }, [symbols, subscribe, unsubscribe]);
  
  // Determine if data is fresh
  const isDataFresh = useMemo(() => {
    // Consider data fresh if we have at least one quote and it's less than 10 seconds old
    const freshQuotes = formattedQuotes.filter(q => q.age !== null && q.age < 10000);
    return freshQuotes.length > 0;
  }, [formattedQuotes]);
  
  if (darkMode) {
    return (
      <div className={`bg-gray-900 rounded-lg overflow-hidden ${className}`}>
        <div className="px-4 py-3 bg-gray-800">
          <div className="flex items-center justify-between">
            <h3 className="text-white font-medium">Live Market Data</h3>
            <div className="flex items-center">
              {isConnected ? (
                <span className="flex items-center">
                  <span className="h-2 w-2 rounded-full bg-green-500 mr-2"></span>
                  <span className="text-xs text-gray-400">Connected</span>
                </span>
              ) : (
                <span className="flex items-center">
                  <span className="h-2 w-2 rounded-full bg-red-500 mr-2"></span>
                  <span className="text-xs text-gray-400">Disconnected</span>
                </span>
              )}
            </div>
          </div>
        </div>
        
        {error && (
          <div className="px-4 py-2 bg-red-900/30 border-l-4 border-red-500 text-sm text-red-200">
            {error}
          </div>
        )}
        
        <div className="divide-y divide-gray-800">
          {formattedQuotes.map((quote) => (
            <div key={quote.symbol} className="px-4 py-3 hover:bg-gray-800/50 transition-colors">
              <div className="flex justify-between items-center">
                <div className="flex items-center">
                  <span className="font-medium text-gray-100">{quote.symbol}</span>
                  {quote.price === null && (
                    <span className="ml-2 text-xs text-gray-500">Waiting for data...</span>
                  )}
                </div>
                <div className="flex items-center">
                  <span className="text-lg font-medium text-gray-100">
                    {quote.price !== null ? quote.formattedPrice : (
                      <LoadingSpinner size="sm" className="h-4 w-4 text-gray-400" />
                    )}
                  </span>
                </div>
              </div>
              
              {!compact && (
                <div className="mt-1 flex justify-between text-xs">
                  <div>
                    <span className={
                      quote.changeDirection === 'up' ? 'text-green-400' :
                      quote.changeDirection === 'down' ? 'text-red-400' :
                      'text-gray-400'
                    }>
                      {quote.formattedChange}
                    </span>
                  </div>
                  <div className="text-gray-500">
                    {quote.formattedTime}
                  </div>
                </div>
              )}
            </div>
          ))}
        </div>
        
        {symbols.length === 0 && (
          <div className="p-4 text-center text-gray-500 text-sm">
            No symbols selected for real-time quotes
          </div>
        )}
        
        <div className="px-4 py-2 bg-gray-800/50 text-xs text-gray-500 flex justify-between items-center">
          <span>
            {isDataFresh ? (
              <span className="text-green-500">Live Data</span>
            ) : (
              <span>Waiting for updates...</span>
            )}
          </span>
          <span>
            Powered by WebSocket Streaming
          </span>
        </div>
      </div>
    );
  }
  
  // Light mode version
  return (
    <div className={`bg-white rounded-lg shadow-md overflow-hidden ${className}`}>
      <div className="px-4 py-3 bg-gray-50 border-b border-gray-200">
        <div className="flex items-center justify-between">
          <h3 className="font-medium text-gray-700">Live Market Data</h3>
          <div className="flex items-center">
            {isConnected ? (
              <span className="flex items-center">
                <span className="h-2 w-2 rounded-full bg-green-500 mr-2"></span>
                <span className="text-xs text-gray-500">Connected</span>
              </span>
            ) : (
              <span className="flex items-center">
                <span className="h-2 w-2 rounded-full bg-red-500 mr-2"></span>
                <span className="text-xs text-gray-500">Disconnected</span>
              </span>
            )}
          </div>
        </div>
      </div>
      
      {error && (
        <div className="px-4 py-2 bg-red-50 border-l-4 border-red-500 text-sm text-red-700">
          {error}
        </div>
      )}
      
      <div className="divide-y divide-gray-100">
        {formattedQuotes.map((quote) => (
          <div key={quote.symbol} className="px-4 py-3 hover:bg-gray-50 transition-colors">
            <div className="flex justify-between items-center">
              <div className="flex items-center">
                <span className="font-medium text-gray-800">{quote.symbol}</span>
                {quote.price === null && (
                  <span className="ml-2 text-xs text-gray-500">Waiting for data...</span>
                )}
              </div>
              <div className="flex items-center">
                <span className="text-lg font-medium text-gray-800">
                  {quote.price !== null ? quote.formattedPrice : (
                    <LoadingSpinner size="sm" className="h-4 w-4 text-gray-400" />
                  )}
                </span>
              </div>
            </div>
            
            {!compact && (
              <div className="mt-1 flex justify-between text-xs">
                <div>
                  <span className={
                    quote.changeDirection === 'up' ? 'text-green-600' :
                    quote.changeDirection === 'down' ? 'text-red-600' :
                    'text-gray-500'
                  }>
                    {quote.formattedChange}
                  </span>
                </div>
                <div className="text-gray-500">
                  {quote.formattedTime}
                </div>
              </div>
            )}
          </div>
        ))}
      </div>
      
      {symbols.length === 0 && (
        <div className="p-4 text-center text-gray-500 text-sm">
          No symbols selected for real-time quotes
        </div>
      )}
      
      <div className="px-4 py-2 bg-gray-50 text-xs text-gray-500 flex justify-between items-center">
        <span>
          {isDataFresh ? (
            <span className="text-green-600">Live Data</span>
          ) : (
            <span>Waiting for updates...</span>
          )}
        </span>
        <span>
          Powered by WebSocket Streaming
        </span>
      </div>
    </div>
  );
}, (prevProps, nextProps) => {
  // Only re-render if symbols array has changed (by reference or content)
  if (prevProps.symbols !== nextProps.symbols) {
    if (prevProps.symbols.length !== nextProps.symbols.length) {
      return false; // Definitely changed
    }
    // Check if array contents are the same
    for (let i = 0; i < prevProps.symbols.length; i++) {
      if (prevProps.symbols[i] !== nextProps.symbols[i]) {
        return false; // Found a change
      }
    }
  }
  
  // Check if other props have changed
  if (prevProps.darkMode !== nextProps.darkMode || 
      prevProps.compact !== nextProps.compact ||
      prevProps.className !== nextProps.className) {
    return false;
  }
  
  // Only consider onQuoteUpdate change if either is undefined and the other isn't
  if ((!prevProps.onQuoteUpdate && nextProps.onQuoteUpdate) || 
      (prevProps.onQuoteUpdate && !nextProps.onQuoteUpdate)) {
    return false;
  }
  
  // No changes detected, skip re-render
  return true;
});

export default LiveQuoteDisplay;