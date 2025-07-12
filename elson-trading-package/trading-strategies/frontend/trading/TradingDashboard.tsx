import React, { useState, useEffect, useMemo } from 'react';
import { useAppDispatch, useAppSelector } from '../../store/store';
import { useMarketWebSocket } from '../../hooks/useMarketWebSocket';
import { setWsConnected, updateQuote, addSubscription, removeSubscription } from '../../store/slices/marketSlice';
import { fetchMultipleQuotes, fetchMarketStatus } from '../../store/slices/marketSlice';
import RealTimeTradeForm from './RealTimeTradeForm';
import { LoadingSpinner } from '../common/LoadingSpinner';
import { formatCurrency, formatNumber } from '../../utils/formatters';

interface TradingDashboardProps {
  portfolioId: number;
  darkMode?: boolean;
}

export const TradingDashboard: React.FC<TradingDashboardProps> = ({
  portfolioId,
  darkMode = true
}) => {
  const dispatch = useAppDispatch();
  const { quotes, watchlist, wsConnected, marketStatus, loading, error } = useAppSelector(state => state.market);
  const { user } = useAppSelector(state => state.user);
  
  // Local state
  const [selectedTab, setSelectedTab] = useState<'trade' | 'watchlist' | 'positions'>('trade');
  const [symbolSearch, setSymbolSearch] = useState('');
  
  // Initialize WebSocket connection
  const { isConnected, quotes: wsQuotes, subscribe, unsubscribe } = useMarketWebSocket({
    symbols: watchlist,
    autoConnect: true,
    cacheEnabled: true,
    cacheTTL: 60
  });

  // Sync WebSocket connection status with Redux
  useEffect(() => {
    dispatch(setWsConnected(isConnected));
  }, [isConnected, dispatch]);

  // Handle real-time quote updates
  useEffect(() => {
    Object.values(wsQuotes).forEach(quote => {
      dispatch(updateQuote({
        symbol: quote.symbol,
        price: quote.price,
        bid: quote.bid,
        ask: quote.ask,
        bidSize: quote.bidSize,
        askSize: quote.askSize,
        volume: quote.volume || 0,
        dayChange: quote.dayChange || 0,
        dayChangePercent: quote.dayChangePercent || 0,
        timestamp: quote.timestamp,
        source: quote.source
      }));
    });
  }, [wsQuotes, dispatch]);

  // Fetch initial market data
  useEffect(() => {
    if (watchlist.length > 0) {
      dispatch(fetchMultipleQuotes(watchlist));
    }
    dispatch(fetchMarketStatus());
  }, [dispatch, watchlist]);

  // Handle watchlist symbol subscription
  const handleAddToWatchlist = (symbol: string) => {
    const normalizedSymbol = symbol.toUpperCase();
    dispatch(addSubscription(normalizedSymbol));
    subscribe([normalizedSymbol]);
  };

  const handleRemoveFromWatchlist = (symbol: string) => {
    const normalizedSymbol = symbol.toUpperCase();
    dispatch(removeSubscription(normalizedSymbol));
    unsubscribe([normalizedSymbol]);
  };

  // Memoized watchlist quotes for performance
  const watchlistQuotes = useMemo(() => {
    return watchlist.map(symbol => ({
      symbol,
      quote: quotes[symbol] || null
    }));
  }, [watchlist, quotes]);

  // Market status indicator
  const MarketStatusIndicator = () => (
    <div className={`flex items-center space-x-2 text-sm ${darkMode ? 'text-gray-300' : 'text-gray-600'}`}>
      <div className={`w-2 h-2 rounded-full ${marketStatus?.isOpen ? 'bg-green-500' : 'bg-red-500'}`}></div>
      <span>Market {marketStatus?.isOpen ? 'Open' : 'Closed'}</span>
      <div className={`w-2 h-2 rounded-full ml-4 ${wsConnected ? 'bg-green-500' : 'bg-yellow-500'}`}></div>
      <span>{wsConnected ? 'Live Data' : 'Connecting...'}</span>
    </div>
  );

  // Watchlist component
  const WatchlistView = () => (
    <div className={`${darkMode ? 'bg-gray-800' : 'bg-white'} rounded-lg p-4`}>
      <div className="flex justify-between items-center mb-4">
        <h3 className={`text-lg font-semibold ${darkMode ? 'text-white' : 'text-gray-800'}`}>
          Watchlist
        </h3>
        <div className="flex space-x-2">
          <input
            type="text"
            value={symbolSearch}
            onChange={(e) => setSymbolSearch(e.target.value)}
            placeholder="Add symbol..."
            className={`px-3 py-1 text-sm rounded border ${
              darkMode 
                ? 'bg-gray-700 border-gray-600 text-white placeholder-gray-400' 
                : 'bg-white border-gray-300 text-gray-800'
            }`}
            onKeyPress={(e) => {
              if (e.key === 'Enter' && symbolSearch.trim()) {
                handleAddToWatchlist(symbolSearch.trim());
                setSymbolSearch('');
              }
            }}
          />
        </div>
      </div>

      <div className="space-y-2">
        {watchlistQuotes.map(({ symbol, quote }) => (
          <div
            key={symbol}
            className={`flex justify-between items-center p-3 rounded ${
              darkMode ? 'bg-gray-700 hover:bg-gray-650' : 'bg-gray-50 hover:bg-gray-100'
            } transition-colors cursor-pointer`}
          >
            <div className="flex-1">
              <div className={`font-medium ${darkMode ? 'text-white' : 'text-gray-800'}`}>
                {symbol}
              </div>
              <div className={`text-sm ${darkMode ? 'text-gray-400' : 'text-gray-500'}`}>
                {quote ? `Vol: ${formatNumber(quote.volume)}` : 'Loading...'}
              </div>
            </div>
            
            <div className="text-right">
              {quote ? (
                <>
                  <div className={`font-semibold ${darkMode ? 'text-white' : 'text-gray-800'}`}>
                    {formatCurrency(quote.price)}
                  </div>
                  <div className={`text-sm ${
                    quote.dayChange >= 0 
                      ? 'text-green-500' 
                      : 'text-red-500'
                  }`}>
                    {quote.dayChange >= 0 ? '+' : ''}{formatCurrency(quote.dayChange)} 
                    ({quote.dayChangePercent >= 0 ? '+' : ''}{quote.dayChangePercent.toFixed(2)}%)
                  </div>
                </>
              ) : (
                <LoadingSpinner size="sm" className="h-4 w-4" />
              )}
            </div>

            <button
              onClick={() => handleRemoveFromWatchlist(symbol)}
              className={`ml-3 p-1 rounded hover:bg-red-600 text-red-500 hover:text-white ${
                darkMode ? 'hover:bg-red-600' : 'hover:bg-red-100'
              }`}
            >
              ×
            </button>
          </div>
        ))}

        {watchlist.length === 0 && (
          <div className={`text-center py-8 ${darkMode ? 'text-gray-400' : 'text-gray-500'}`}>
            No symbols in watchlist. Add some symbols to track their real-time prices.
          </div>
        )}
      </div>
    </div>
  );

  // Tab navigation
  const TabNavigation = () => (
    <div className={`flex space-x-1 ${darkMode ? 'bg-gray-800' : 'bg-gray-100'} p-1 rounded-lg`}>
      {[
        { key: 'trade', label: 'Trade' },
        { key: 'watchlist', label: 'Watchlist' },
        { key: 'positions', label: 'Positions' }
      ].map(({ key, label }) => (
        <button
          key={key}
          onClick={() => setSelectedTab(key as any)}
          className={`px-4 py-2 text-sm font-medium rounded-md transition-colors ${
            selectedTab === key
              ? darkMode
                ? 'bg-gray-700 text-white'
                : 'bg-white text-gray-800 shadow-sm'
              : darkMode
                ? 'text-gray-300 hover:text-white hover:bg-gray-700'
                : 'text-gray-600 hover:text-gray-800 hover:bg-gray-50'
          }`}
        >
          {label}
        </button>
      ))}
    </div>
  );

  if (loading && Object.keys(quotes).length === 0) {
    return (
      <div className={`${darkMode ? 'bg-gray-900' : 'bg-white'} rounded-lg p-8 text-center`}>
        <LoadingSpinner size="lg" className="mx-auto mb-4" />
        <p className={darkMode ? 'text-gray-300' : 'text-gray-600'}>
          Loading trading dashboard...
        </p>
      </div>
    );
  }

  return (
    <div className={`${darkMode ? 'bg-gray-900' : 'bg-gray-50'} min-h-screen p-4`}>
      <div className="max-w-7xl mx-auto">
        {/* Header */}
        <div className="mb-6">
          <div className="flex justify-between items-center mb-4">
            <h1 className={`text-2xl font-bold ${darkMode ? 'text-white' : 'text-gray-800'}`}>
              Trading Dashboard
            </h1>
            <MarketStatusIndicator />
          </div>
          
          {/* Error display */}
          {error && (
            <div className={`p-3 rounded mb-4 ${
              darkMode 
                ? 'bg-red-900/30 border border-red-700 text-red-300' 
                : 'bg-red-50 border border-red-200 text-red-800'
            }`}>
              {error}
            </div>
          )}

          <TabNavigation />
        </div>

        {/* Content */}
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          {/* Main content area */}
          <div className="lg:col-span-2">
            {selectedTab === 'trade' && (
              <RealTimeTradeForm 
                portfolioId={portfolioId}
                darkMode={darkMode}
                onTradeComplete={() => {
                  // Refresh positions or other data
                  console.log('Trade completed');
                }}
              />
            )}
            
            {selectedTab === 'watchlist' && <WatchlistView />}
            
            {selectedTab === 'positions' && (
              <div className={`${darkMode ? 'bg-gray-800' : 'bg-white'} rounded-lg p-6`}>
                <h3 className={`text-lg font-semibold mb-4 ${darkMode ? 'text-white' : 'text-gray-800'}`}>
                  Current Positions
                </h3>
                <div className={`text-center py-8 ${darkMode ? 'text-gray-400' : 'text-gray-500'}`}>
                  Position management coming soon...
                </div>
              </div>
            )}
          </div>

          {/* Sidebar */}
          <div className="space-y-6">
            {/* Quick stats */}
            <div className={`${darkMode ? 'bg-gray-800' : 'bg-white'} rounded-lg p-4`}>
              <h3 className={`text-lg font-semibold mb-4 ${darkMode ? 'text-white' : 'text-gray-800'}`}>
                Account Summary
              </h3>
              <div className="space-y-3">
                <div className="flex justify-between">
                  <span className={darkMode ? 'text-gray-400' : 'text-gray-600'}>
                    Portfolio Value
                  </span>
                  <span className={`font-semibold ${darkMode ? 'text-white' : 'text-gray-800'}`}>
                    {formatCurrency(50000)} {/* Placeholder */}
                  </span>
                </div>
                <div className="flex justify-between">
                  <span className={darkMode ? 'text-gray-400' : 'text-gray-600'}>
                    Buying Power
                  </span>
                  <span className={`font-semibold ${darkMode ? 'text-white' : 'text-gray-800'}`}>
                    {formatCurrency(10000)} {/* Placeholder */}
                  </span>
                </div>
                <div className="flex justify-between">
                  <span className={darkMode ? 'text-gray-400' : 'text-gray-600'}>
                    Day P&L
                  </span>
                  <span className="font-semibold text-green-500">
                    +{formatCurrency(250)} {/* Placeholder */}
                  </span>
                </div>
              </div>
            </div>

            {/* Mini watchlist */}
            {selectedTab !== 'watchlist' && watchlist.length > 0 && (
              <div className={`${darkMode ? 'bg-gray-800' : 'bg-white'} rounded-lg p-4`}>
                <h3 className={`text-lg font-semibold mb-4 ${darkMode ? 'text-white' : 'text-gray-800'}`}>
                  Watchlist
                </h3>
                <div className="space-y-2">
                  {watchlist.slice(0, 5).map(symbol => {
                    const quote = quotes[symbol];
                    return (
                      <div key={symbol} className="flex justify-between items-center">
                        <span className={`font-medium ${darkMode ? 'text-white' : 'text-gray-800'}`}>
                          {symbol}
                        </span>
                        <div className="text-right">
                          {quote ? (
                            <>
                              <div className={`text-sm font-semibold ${darkMode ? 'text-white' : 'text-gray-800'}`}>
                                {formatCurrency(quote.price)}
                              </div>
                              <div className={`text-xs ${
                                quote.dayChange >= 0 ? 'text-green-500' : 'text-red-500'
                              }`}>
                                {quote.dayChangePercent >= 0 ? '+' : ''}{quote.dayChangePercent.toFixed(2)}%
                              </div>
                            </>
                          ) : (
                            <LoadingSpinner size="sm" className="h-3 w-3" />
                          )}
                        </div>
                      </div>
                    );
                  })}
                </div>
                {watchlist.length > 5 && (
                  <button
                    onClick={() => setSelectedTab('watchlist')}
                    className={`w-full mt-3 text-sm ${
                      darkMode ? 'text-blue-400 hover:text-blue-300' : 'text-blue-600 hover:text-blue-700'
                    }`}
                  >
                    View all ({watchlist.length})
                  </button>
                )}
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
};

export default TradingDashboard;