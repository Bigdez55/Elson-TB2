import React, { useState, useEffect, useCallback } from 'react';
import { useSelector } from 'react-redux';
import { RootState } from '../../store/store';
import { useAccessibility } from '../../hooks/useAccessibility';
import { useTradingContext } from '../../contexts/TradingContext';
import { useGetBatchDataQuery, useGetOrderHistoryQuery } from '../../services/tradingApi';
import LoadingSpinner from '../common/LoadingSpinner';
import { Link } from 'react-router-dom';

/**
 * Mobile-optimized Trading component
 * Designed for small screens with touch-friendly interface and simplified UI
 */
export default function MobileTrading() {
  const [activeTab, setActiveTab] = useState('market');
  const [selectedSymbol, setSelectedSymbol] = useState('');
  const [orderType, setOrderType] = useState('market');
  const [isBuy, setIsBuy] = useState(true);
  const [quantity, setQuantity] = useState('1');
  const [isOrderFormVisible, setIsOrderFormVisible] = useState(false);
  const [watchlistSymbols, setWatchlistSymbols] = useState<string[]>([]);
  const [watchlistData, setWatchlistData] = useState<any[]>([]);
  const [loadingWatchlist, setLoadingWatchlist] = useState(false);

  // Accessibility context for user preferences
  const { announce } = useAccessibility();

  // Get trading mode and real data
  const { mode } = useTradingContext();
  const { data: batchData, isLoading } = useGetBatchDataQuery({ mode });
  const { data: orders } = useGetOrderHistoryQuery({ mode, limit: 10 });

  // Load watchlist from localStorage and fetch quotes
  const loadWatchlist = useCallback(async () => {
    try {
      setLoadingWatchlist(true);
      const savedSymbols = JSON.parse(localStorage.getItem('watchlist') || '[]') as string[];
      setWatchlistSymbols(savedSymbols);

      if (savedSymbols.length === 0) {
        setWatchlistData([]);
        setLoadingWatchlist(false);
        return;
      }

      const token = localStorage.getItem('token');
      const baseUrl = process.env.REACT_APP_API_URL || '/api/v1';

      const response = await fetch(`${baseUrl}/market-data/quotes`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${token}`,
        },
        body: JSON.stringify(savedSymbols),
      });

      if (response.ok) {
        const data = await response.json();
        const formattedData = (data.quotes || []).map((quote: any) => ({
          symbol: quote.symbol,
          name: quote.symbol,
          price: `$${quote.price?.toFixed(2) || '0.00'}`,
          change: `${quote.change >= 0 ? '+' : ''}$${quote.change?.toFixed(2) || '0.00'} (${quote.change_percent?.toFixed(2) || '0.00'}%)`,
          trend: quote.change >= 0 ? 'up' : 'down',
        }));
        setWatchlistData(formattedData);
      }
    } catch (err) {
      console.error('Error loading watchlist:', err);
    } finally {
      setLoadingWatchlist(false);
    }
  }, []);

  useEffect(() => {
    loadWatchlist();
    const interval = setInterval(loadWatchlist, 60000);
    return () => clearInterval(interval);
  }, [loadWatchlist]);

  // Handle tab changes and announce for screen readers
  const handleTabChange = (tab: string) => {
    setActiveTab(tab);
    announce(`${tab} tab selected`, false);
  };

  // Handle symbol selection
  const handleSymbolSelect = (symbol: string) => {
    setSelectedSymbol(symbol);
    announce(`Selected ${symbol}`, false);
  };

  // Toggle order form visibility
  const toggleOrderForm = () => {
    setIsOrderFormVisible(!isOrderFormVisible);
    if (!isOrderFormVisible) {
      announce('Order form opened', false);
    } else {
      announce('Order form closed', false);
    }
  };

  // Get quote data for selected symbol
  const getQuoteData = () => {
    const stock = watchlistData.find(s => s.symbol === selectedSymbol);
    if (!stock) {
      return {
        symbol: selectedSymbol || 'Select a symbol',
        name: 'No symbol selected',
        price: '$0.00',
        change: '$0.00 (0.00%)',
        trend: 'neutral',
      };
    }
    return stock;
  };

  const quoteData = getQuoteData();

  // Loading indicator for mobile
  if (isLoading) {
    return (
      <div className="flex items-center justify-center min-h-[70vh]">
        <LoadingSpinner size="large" color="text-purple-600" text="Loading trading data..." />
      </div>
    );
  }

  return (
    <div className="mobile-trading pb-16 prevent-pull-refresh">
      {/* Symbol quick view - shows selected symbol */}
      <div className="bg-gray-900 p-4 mb-4 rounded-xl">
        <div className="flex justify-between items-start">
          <div>
            <h2 className="text-xl font-bold text-white">{quoteData.symbol}</h2>
            <p className="text-gray-400 text-sm">{quoteData.name}</p>
          </div>
          <div className="text-right">
            <p className="text-xl font-bold text-white">{quoteData.price}</p>
            <p className={`text-sm ${quoteData.trend === 'up' ? 'text-green-400' : 'text-red-400'}`}>
              {quoteData.change}
            </p>
          </div>
        </div>

        {/* Quick Trade Buttons */}
        {selectedSymbol && (
          <div className="flex gap-2 mt-4">
            <button
              className="flex-1 bg-green-600 hover:bg-green-700 text-white py-3 rounded-lg font-medium transition-colors"
              onClick={() => { setIsBuy(true); toggleOrderForm(); }}
            >
              Buy
            </button>
            <button
              className="flex-1 bg-red-600 hover:bg-red-700 text-white py-3 rounded-lg font-medium transition-colors"
              onClick={() => { setIsBuy(false); toggleOrderForm(); }}
            >
              Sell
            </button>
          </div>
        )}
      </div>

      {/* Tab navigation */}
      <div className="bg-gray-900 rounded-xl mb-4 overflow-hidden">
        <div className="flex border-b border-gray-800">
          <button
            className={`flex-1 py-3 text-sm font-medium ${activeTab === 'market' ? 'text-purple-400 border-b-2 border-purple-400' : 'text-gray-400'}`}
            onClick={() => handleTabChange('market')}
            aria-selected={activeTab === 'market'}
            role="tab"
          >
            Watchlist
          </button>
          <button
            className={`flex-1 py-3 text-sm font-medium ${activeTab === 'orders' ? 'text-purple-400 border-b-2 border-purple-400' : 'text-gray-400'}`}
            onClick={() => handleTabChange('orders')}
            aria-selected={activeTab === 'orders'}
            role="tab"
          >
            Orders
          </button>
          <button
            className={`flex-1 py-3 text-sm font-medium ${activeTab === 'positions' ? 'text-purple-400 border-b-2 border-purple-400' : 'text-gray-400'}`}
            onClick={() => handleTabChange('positions')}
            aria-selected={activeTab === 'positions'}
            role="tab"
          >
            Positions
          </button>
        </div>

        {/* Tab content - Watchlist */}
        {activeTab === 'market' && (
          <div className="p-4" role="tabpanel" aria-label="Watchlist tab">
            <div className="flex justify-between items-center mb-3">
              <h3 className="text-base font-semibold text-white">Your Watchlist</h3>
            </div>

            {loadingWatchlist ? (
              <div className="text-center py-8">
                <LoadingSpinner size="small" color="text-purple-400" />
              </div>
            ) : watchlistData.length === 0 ? (
              <div className="text-center py-8">
                <p className="text-gray-400 mb-4">No symbols in watchlist</p>
                <p className="text-gray-500 text-sm">Add symbols from the trading page to track them here</p>
              </div>
            ) : (
              <div className="max-h-[350px] overflow-y-auto hide-scrollbar">
                {watchlistData.map((stock) => (
                  <button
                    key={stock.symbol}
                    className={`w-full py-3 border-b border-gray-800 last:border-b-0 text-left ${selectedSymbol === stock.symbol ? 'bg-purple-900/30' : ''}`}
                    onClick={() => handleSymbolSelect(stock.symbol)}
                  >
                    <div className="flex justify-between items-center">
                      <div>
                        <p className="text-white font-medium">{stock.symbol}</p>
                        <p className="text-xs text-gray-400">{stock.name}</p>
                      </div>
                      <div className="text-right">
                        <p className="text-white font-medium">{stock.price}</p>
                        <p className={`text-xs ${stock.trend === 'up' ? 'text-green-400' : 'text-red-400'}`}>
                          {stock.change}
                        </p>
                      </div>
                    </div>
                  </button>
                ))}
              </div>
            )}
          </div>
        )}

        {/* Tab content - Orders */}
        {activeTab === 'orders' && (
          <div className="p-4" role="tabpanel" aria-label="Orders tab">
            <h3 className="text-base font-semibold text-white mb-3">Recent Orders</h3>

            {!orders || orders.length === 0 ? (
              <div className="text-center py-8">
                <p className="text-gray-400">No orders yet</p>
              </div>
            ) : (
              <div className="max-h-[350px] overflow-y-auto hide-scrollbar">
                {orders.map((order) => (
                  <div key={order.id} className="py-3 border-b border-gray-800 last:border-b-0">
                    <div className="flex justify-between items-start">
                      <div>
                        <span className={`text-xs px-2 py-1 rounded ${order.trade_type === 'BUY' ? 'bg-green-900/50 text-green-400' : 'bg-red-900/50 text-red-400'}`}>
                          {order.trade_type}
                        </span>
                        <span className="text-white font-medium ml-2">{order.symbol}</span>
                        <p className="text-xs text-gray-400 mt-1">{order.quantity} shares</p>
                      </div>
                      <div className="text-right">
                        <p className={`text-xs px-2 py-1 rounded ${order.status === 'FILLED' ? 'bg-green-900/30 text-green-400' : 'bg-yellow-900/30 text-yellow-400'}`}>
                          {order.status}
                        </p>
                        <p className="text-xs text-gray-400 mt-1">{new Date(order.created_at).toLocaleDateString()}</p>
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            )}
          </div>
        )}

        {/* Tab content - Positions */}
        {activeTab === 'positions' && (
          <div className="p-4" role="tabpanel" aria-label="Positions tab">
            <h3 className="text-base font-semibold text-white mb-3">Your Positions</h3>

            {!batchData?.positions || batchData.positions.length === 0 ? (
              <div className="text-center py-8">
                <p className="text-gray-400 mb-4">No positions yet</p>
                <p className="text-gray-500 text-sm">Start trading to build your portfolio</p>
              </div>
            ) : (
              <div className="max-h-[350px] overflow-y-auto hide-scrollbar">
                {batchData.positions.map((position) => (
                  <div key={position.id} className="py-3 border-b border-gray-800 last:border-b-0">
                    <div className="flex justify-between items-start">
                      <div>
                        <p className="text-white font-medium">{position.symbol}</p>
                        <p className="text-xs text-gray-400">{position.quantity.toFixed(4)} shares</p>
                      </div>
                      <div className="text-right">
                        <p className="text-white font-medium">${position.market_value.toFixed(2)}</p>
                        <p className={`text-xs ${position.unrealized_pnl >= 0 ? 'text-green-400' : 'text-red-400'}`}>
                          {position.unrealized_pnl >= 0 ? '+' : ''}${position.unrealized_pnl.toFixed(2)}
                        </p>
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            )}
          </div>
        )}
      </div>

      {/* Order Form Modal */}
      {isOrderFormVisible && selectedSymbol && (
        <div className="fixed inset-0 bg-black/80 z-50 flex items-end">
          <div className="bg-gray-900 w-full rounded-t-2xl p-4 pb-8">
            <div className="flex justify-between items-center mb-4">
              <h3 className="text-lg font-bold text-white">
                {isBuy ? 'Buy' : 'Sell'} {selectedSymbol}
              </h3>
              <button onClick={toggleOrderForm} className="text-gray-400 p-2">
                <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M6 18L18 6M6 6l12 12" />
                </svg>
              </button>
            </div>

            <div className="space-y-4">
              <div>
                <label className="text-gray-400 text-sm mb-1 block">Order Type</label>
                <select
                  className="w-full bg-gray-800 text-white p-3 rounded-lg"
                  value={orderType}
                  onChange={(e) => setOrderType(e.target.value)}
                >
                  <option value="market">Market Order</option>
                  <option value="limit">Limit Order</option>
                </select>
              </div>

              <div>
                <label className="text-gray-400 text-sm mb-1 block">Quantity</label>
                <input
                  type="number"
                  className="w-full bg-gray-800 text-white p-3 rounded-lg"
                  value={quantity}
                  onChange={(e) => setQuantity(e.target.value)}
                  min="1"
                />
              </div>

              <Link
                to={`/${mode}/trading/${selectedSymbol}`}
                className={`w-full py-3 rounded-lg font-medium text-center block ${isBuy ? 'bg-green-600' : 'bg-red-600'} text-white`}
                onClick={toggleOrderForm}
              >
                Go to Full Trading View
              </Link>
            </div>
          </div>
        </div>
      )}

      {/* Floating Action Button */}
      <Link
        to={`/${mode}/trading`}
        className="fixed bottom-20 right-4 w-14 h-14 bg-purple-600 rounded-full flex items-center justify-center shadow-lg"
      >
        <svg className="w-6 h-6 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M12 6v6m0 0v6m0-6h6m-6 0H6" />
        </svg>
      </Link>
    </div>
  );
}
