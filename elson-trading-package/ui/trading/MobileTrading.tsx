import React, { useState, useEffect } from 'react';
import { useSelector } from 'react-redux';
import { useAccessibility } from '../../hooks/useAccessibility';
import { useWebSocket } from '../../hooks/useWebSocket';
import LoadingSpinner from '../common/LoadingSpinner';

/**
 * Mobile-optimized Trading component
 * Designed for small screens with touch-friendly interface and simplified UI
 */
export default function MobileTrading() {
  const [activeTab, setActiveTab] = useState('market');
  const [selectedSymbol, setSelectedSymbol] = useState('AAPL');
  const [orderType, setOrderType] = useState('market');
  const [isBuy, setIsBuy] = useState(true);
  const [isLoading, setIsLoading] = useState(false);
  const [quantity, setQuantity] = useState('1');
  const [isOrderFormVisible, setIsOrderFormVisible] = useState(false);
  
  // Accessibility context for user preferences
  const { isDarkMode, prefersReducedMotion, announce } = useAccessibility();
  
  // Initialize WebSocket connection for live market data
  useWebSocket(['market', 'trades']);

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

  // Mock data for stocks
  const watchlist = [
    { symbol: 'AAPL', name: 'Apple Inc.', price: '$175.84', change: '+$2.47 (1.42%)', trend: 'up' },
    { symbol: 'MSFT', name: 'Microsoft Corp.', price: '$310.87', change: '+$3.52 (1.14%)', trend: 'up' },
    { symbol: 'GOOGL', name: 'Alphabet Inc.', price: '$134.99', change: '+$1.89 (1.42%)', trend: 'up' },
    { symbol: 'AMZN', name: 'Amazon.com Inc.', price: '$128.61', change: '-$0.42 (-0.33%)', trend: 'down' },
    { symbol: 'TSLA', name: 'Tesla, Inc.', price: '$242.21', change: '+$5.38 (2.27%)', trend: 'up' },
    { symbol: 'META', name: 'Meta Platforms', price: '$312.95', change: '+$1.23 (0.39%)', trend: 'up' },
    { symbol: 'BRK.B', name: 'Berkshire Hathaway', price: '$351.14', change: '-$0.92 (-0.26%)', trend: 'down' },
    { symbol: 'NVDA', name: 'NVIDIA Corp.', price: '$476.57', change: '+$14.66 (3.18%)', trend: 'up' },
  ];

  const orders = [
    { id: 1, symbol: 'AAPL', action: 'Buy', quantity: '5', price: '$175.84', total: '$879.20', status: 'Completed', date: 'Nov 15, 2023' },
    { id: 2, symbol: 'MSFT', action: 'Buy', quantity: '2', price: '$310.87', total: '$621.74', status: 'Completed', date: 'Nov 14, 2023' },
    { id: 3, symbol: 'TSLA', action: 'Sell', quantity: '3', price: '$240.32', total: '$720.96', status: 'Completed', date: 'Nov 12, 2023' },
    { id: 4, symbol: 'GOOGL', action: 'Buy', quantity: '4', price: '$133.75', total: '$535.00', status: 'Pending', date: 'Nov 15, 2023' },
  ];

  const recurrings = [
    { id: 1, symbol: 'VTI', frequency: 'Weekly', amount: '$100', nextDate: 'Nov 20, 2023', status: 'Active' },
    { id: 2, symbol: 'AAPL', frequency: 'Monthly', amount: '$250', nextDate: 'Dec 1, 2023', status: 'Active' },
  ];

  // Mock quote data for selected symbol
  const getQuoteData = () => {
    const stock = watchlist.find(s => s.symbol === selectedSymbol);
    return {
      symbol: selectedSymbol,
      name: stock?.name || 'Unknown Stock',
      price: stock?.price || '$0.00',
      change: stock?.change || '$0.00 (0.00%)',
      trend: stock?.trend || 'neutral',
      bid: '$' + (parseFloat(stock?.price.substring(1) || '0') - 0.01).toFixed(2),
      ask: '$' + (parseFloat(stock?.price.substring(1) || '0') + 0.01).toFixed(2),
      high: '$' + (parseFloat(stock?.price.substring(1) || '0') + 3.25).toFixed(2),
      low: '$' + (parseFloat(stock?.price.substring(1) || '0') - 2.15).toFixed(2),
      open: '$' + (parseFloat(stock?.price.substring(1) || '0') - 1.05).toFixed(2),
      marketCap: '$' + (parseFloat(stock?.price.substring(1) || '0') * 25).toFixed(2) + 'B',
      volume: '42.3M',
    };
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
      {/* Tab navigation */}
      <div className="bg-gray-900 rounded-xl mb-4 overflow-hidden">
        <div className="flex border-b border-gray-800">
          <button 
            className={`flex-1 py-3 text-sm font-medium ${activeTab === 'market' ? 'text-purple-400 border-b-2 border-purple-400' : 'text-gray-400'}`}
            onClick={() => handleTabChange('market')}
            aria-selected={activeTab === 'market'}
            role="tab"
          >
            Market
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
            className={`flex-1 py-3 text-sm font-medium ${activeTab === 'recurring' ? 'text-purple-400 border-b-2 border-purple-400' : 'text-gray-400'}`}
            onClick={() => handleTabChange('recurring')}
            aria-selected={activeTab === 'recurring'}
            role="tab"
          >
            Recurring
          </button>
        </div>

        {/* Market Tab Content */}
        {activeTab === 'market' && (
          <div className="p-4" role="tabpanel" aria-label="Market tab">
            {/* Search bar */}
            <div className="relative mb-4">
              <input 
                type="text" 
                placeholder="Search stocks, ETFs, crypto..." 
                className="w-full bg-gray-800 rounded-lg px-4 py-2 pl-10 text-white text-sm focus:ring-2 focus:ring-purple-500 focus:outline-none"
              />
              <svg className="h-5 w-5 absolute left-3 top-2.5 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z"></path>
              </svg>
            </div>
            
            {/* Watchlist */}
            <h3 className="text-base font-semibold text-white mb-3">Watchlist</h3>
            <div className="max-h-[400px] overflow-y-auto hide-scrollbar mb-4">
              {watchlist.map((stock) => (
                <div 
                  key={stock.symbol} 
                  className={`py-3 px-2 border-b border-gray-800 last:border-b-0 active:bg-gray-800 transition-colors ${selectedSymbol === stock.symbol ? 'bg-gray-800' : ''}`}
                  onClick={() => handleSymbolSelect(stock.symbol)}
                >
                  <div className="flex justify-between items-start">
                    <div>
                      <div className="flex items-center">
                        <span className="text-white font-medium">{stock.symbol}</span>
                      </div>
                      <p className="text-xs text-gray-400">{stock.name}</p>
                    </div>
                    <div className="text-right">
                      <p className="text-white font-medium">{stock.price}</p>
                      <p className={`text-xs ${stock.trend === 'up' ? 'text-green-400' : 'text-red-400'}`}>
                        {stock.change}
                      </p>
                    </div>
                  </div>
                </div>
              ))}
            </div>
            
            {/* Quote Details for Selected Stock */}
            {selectedSymbol && (
              <div className="bg-gray-800 rounded-lg p-4 mb-4">
                <div className="flex justify-between items-start mb-3">
                  <div>
                    <h3 className="text-white font-bold text-lg">{quoteData.symbol}</h3>
                    <p className="text-gray-400 text-xs">{quoteData.name}</p>
                  </div>
                  <div className="text-right">
                    <p className="text-white font-bold text-lg">{quoteData.price}</p>
                    <p className={`text-xs ${quoteData.trend === 'up' ? 'text-green-400' : 'text-red-400'}`}>
                      {quoteData.change}
                    </p>
                  </div>
                </div>
                
                <div className="grid grid-cols-2 gap-3 mb-4">
                  <div>
                    <p className="text-gray-400 text-xs mb-1">Bid</p>
                    <p className="text-white text-sm">{quoteData.bid}</p>
                  </div>
                  <div>
                    <p className="text-gray-400 text-xs mb-1">Ask</p>
                    <p className="text-white text-sm">{quoteData.ask}</p>
                  </div>
                  <div>
                    <p className="text-gray-400 text-xs mb-1">High</p>
                    <p className="text-white text-sm">{quoteData.high}</p>
                  </div>
                  <div>
                    <p className="text-gray-400 text-xs mb-1">Low</p>
                    <p className="text-white text-sm">{quoteData.low}</p>
                  </div>
                  <div>
                    <p className="text-gray-400 text-xs mb-1">Volume</p>
                    <p className="text-white text-sm">{quoteData.volume}</p>
                  </div>
                  <div>
                    <p className="text-gray-400 text-xs mb-1">Market Cap</p>
                    <p className="text-white text-sm">{quoteData.marketCap}</p>
                  </div>
                </div>
                
                <div className="flex gap-2">
                  <button 
                    className="bg-green-700 text-white px-4 py-2 rounded-lg text-sm flex-1 active:bg-green-800 transition-colors"
                    onClick={() => {
                      setIsBuy(true);
                      toggleOrderForm();
                    }}
                  >
                    Buy
                  </button>
                  <button 
                    className="bg-red-700 text-white px-4 py-2 rounded-lg text-sm flex-1 active:bg-red-800 transition-colors"
                    onClick={() => {
                      setIsBuy(false);
                      toggleOrderForm();
                    }}
                  >
                    Sell
                  </button>
                </div>
              </div>
            )}
            
            {/* Order form */}
            {isOrderFormVisible && (
              <div className="bg-gray-800 rounded-lg p-4">
                <div className="flex justify-between items-center mb-4">
                  <h3 className="text-white font-medium">{isBuy ? 'Buy' : 'Sell'} {selectedSymbol}</h3>
                  <button 
                    className="text-gray-400 hover:text-white"
                    onClick={toggleOrderForm}
                  >
                    <svg className="h-5 w-5" fill="none" stroke="currentColor" viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M6 18L18 6M6 6l12 12"></path>
                    </svg>
                  </button>
                </div>
                
                <div className="mb-4">
                  <label className="block text-gray-400 text-xs mb-1">Order Type</label>
                  <div className="flex bg-gray-900 rounded-lg p-1">
                    <button 
                      className={`text-xs rounded px-3 py-1.5 flex-1 ${orderType === 'market' ? 'bg-purple-800 text-white' : 'text-gray-400'}`}
                      onClick={() => setOrderType('market')}
                    >
                      Market
                    </button>
                    <button 
                      className={`text-xs rounded px-3 py-1.5 flex-1 ${orderType === 'limit' ? 'bg-purple-800 text-white' : 'text-gray-400'}`}
                      onClick={() => setOrderType('limit')}
                    >
                      Limit
                    </button>
                  </div>
                </div>
                
                <div className="mb-4">
                  <label className="block text-gray-400 text-xs mb-1">Quantity</label>
                  <div className="flex items-center">
                    <button 
                      className="bg-gray-900 rounded-l-lg px-3 py-2 text-white"
                      onClick={() => setQuantity((prev) => Math.max(1, parseInt(prev) - 1).toString())}
                    >
                      -
                    </button>
                    <input 
                      type="text" 
                      value={quantity} 
                      onChange={(e) => {
                        const value = e.target.value.replace(/[^0-9]/g, '');
                        setQuantity(value || '1');
                      }}
                      className="bg-gray-900 text-center text-white w-full py-2 focus:outline-none"
                    />
                    <button 
                      className="bg-gray-900 rounded-r-lg px-3 py-2 text-white"
                      onClick={() => setQuantity((prev) => (parseInt(prev) + 1).toString())}
                    >
                      +
                    </button>
                  </div>
                </div>
                
                {orderType === 'limit' && (
                  <div className="mb-4">
                    <label className="block text-gray-400 text-xs mb-1">Limit Price</label>
                    <input 
                      type="text" 
                      defaultValue={quoteData.price} 
                      className="w-full bg-gray-900 rounded-lg px-4 py-2 text-white text-sm focus:ring-2 focus:ring-purple-500 focus:outline-none"
                    />
                  </div>
                )}
                
                <div className="mb-4">
                  <div className="flex justify-between text-sm mb-1">
                    <span className="text-gray-400">Current Price:</span>
                    <span className="text-white">{quoteData.price}</span>
                  </div>
                  <div className="flex justify-between text-sm mb-1">
                    <span className="text-gray-400">Estimated Cost:</span>
                    <span className="text-white">
                      ${(parseFloat(quoteData.price.substring(1)) * parseInt(quantity)).toFixed(2)}
                    </span>
                  </div>
                </div>
                
                <button 
                  className={`w-full py-3 rounded-lg text-white font-medium ${isBuy ? 'bg-green-700 active:bg-green-800' : 'bg-red-700 active:bg-red-800'} transition-colors`}
                >
                  {isBuy ? 'Buy' : 'Sell'} {quantity} {selectedSymbol}
                </button>
              </div>
            )}
          </div>
        )}

        {/* Orders Tab Content */}
        {activeTab === 'orders' && (
          <div className="p-4" role="tabpanel" aria-label="Orders tab">
            <h3 className="text-base font-semibold text-white mb-3">Recent Orders</h3>
            <div className="max-h-[400px] overflow-y-auto hide-scrollbar">
              {orders.map((order) => (
                <div key={order.id} className="py-3 border-b border-gray-800 last:border-b-0">
                  <div className="flex justify-between items-start mb-1">
                    <div>
                      <div className="flex items-center">
                        <span className="text-white font-medium">{order.symbol}</span>
                        <span className={`ml-2 text-xs px-2 py-0.5 rounded-full ${order.action === 'Buy' ? 'bg-green-900 text-green-300' : 'bg-red-900 text-red-300'}`}>
                          {order.action}
                        </span>
                      </div>
                      <p className="text-xs text-gray-400">{order.date}</p>
                    </div>
                    <div className="text-right">
                      <p className="text-white font-medium">{order.total}</p>
                      <p className={`text-xs ${order.status === 'Completed' ? 'text-green-400' : 'text-yellow-400'}`}>{order.status}</p>
                    </div>
                  </div>
                  <div className="flex justify-between text-xs text-gray-400 mt-1">
                    <span>{order.quantity} shares @ {order.price}</span>
                    <button className="text-purple-400">Details</button>
                  </div>
                </div>
              ))}
            </div>

            <div className="mt-4">
              <button className="w-full py-2 bg-gray-800 text-purple-400 rounded-lg text-sm active:bg-gray-700 transition-colors">
                View All Orders
              </button>
            </div>
          </div>
        )}

        {/* Recurring Tab Content */}
        {activeTab === 'recurring' && (
          <div className="p-4" role="tabpanel" aria-label="Recurring tab">
            <div className="flex justify-between items-center mb-3">
              <h3 className="text-base font-semibold text-white">Recurring Investments</h3>
              <button className="text-purple-400 text-sm">+ New</button>
            </div>
            
            {recurrings.length > 0 ? (
              <div className="max-h-[400px] overflow-y-auto hide-scrollbar">
                {recurrings.map((item) => (
                  <div key={item.id} className="py-3 border-b border-gray-800 last:border-b-0">
                    <div className="flex justify-between items-start mb-1">
                      <div>
                        <div className="flex items-center">
                          <span className="text-white font-medium">{item.symbol}</span>
                          <span className="ml-2 text-xs bg-purple-900 text-purple-300 px-2 py-0.5 rounded-full">
                            {item.frequency}
                          </span>
                        </div>
                        <p className="text-xs text-gray-400">Next: {item.nextDate}</p>
                      </div>
                      <div className="text-right">
                        <p className="text-white font-medium">{item.amount}</p>
                        <p className="text-xs text-green-400">{item.status}</p>
                      </div>
                    </div>
                    <div className="flex justify-end gap-2 mt-2">
                      <button className="text-xs bg-gray-700 text-white px-2 py-1 rounded">Edit</button>
                      <button className="text-xs bg-gray-700 text-white px-2 py-1 rounded">Pause</button>
                    </div>
                  </div>
                ))}
              </div>
            ) : (
              <div className="bg-gray-800 rounded-lg p-4 text-center">
                <svg className="h-12 w-12 mx-auto mb-3 text-gray-600" fill="none" stroke="currentColor" viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z"></path>
                </svg>
                <p className="text-gray-400 mb-3">No recurring investments set up yet</p>
                <button className="bg-purple-700 text-white px-4 py-2 rounded-lg text-sm active:bg-purple-800 transition-colors">
                  Set Up Recurring Investment
                </button>
              </div>
            )}
            
            <div className="mt-4 bg-gray-800 rounded-lg p-4">
              <h4 className="text-white font-medium mb-2">Why set up recurring investments?</h4>
              <ul className="text-sm text-gray-400 space-y-2">
                <li className="flex items-start">
                  <svg className="h-5 w-5 text-green-400 mr-2 flex-shrink-0" fill="none" stroke="currentColor" viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M5 13l4 4L19 7"></path>
                  </svg>
                  <span>Dollar-cost averaging reduces impact of market volatility</span>
                </li>
                <li className="flex items-start">
                  <svg className="h-5 w-5 text-green-400 mr-2 flex-shrink-0" fill="none" stroke="currentColor" viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M5 13l4 4L19 7"></path>
                  </svg>
                  <span>Automate your investment strategy with set-and-forget setup</span>
                </li>
                <li className="flex items-start">
                  <svg className="h-5 w-5 text-green-400 mr-2 flex-shrink-0" fill="none" stroke="currentColor" viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M5 13l4 4L19 7"></path>
                  </svg>
                  <span>Build wealth consistently over time without emotional decisions</span>
                </li>
              </ul>
            </div>
          </div>
        )}
      </div>

      {/* Quick Actions */}
      <div className="fixed bottom-0 left-0 right-0 bg-gray-900 border-t border-gray-800 px-4 py-3 z-10">
        <div className="flex justify-between">
          <button className="flex flex-col items-center justify-center text-xs text-purple-400 active:text-purple-300 transition-colors w-1/4">
            <svg className="h-6 w-6 mb-1" fill="none" stroke="currentColor" viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M7 12l3-3 3 3 4-4M8 21l4-4 4 4M3 4h18M4 4h16v12a1 1 0 01-1 1H5a1 1 0 01-1-1V4z"></path>
            </svg>
            <span>Watchlist</span>
          </button>
          <button className="flex flex-col items-center justify-center text-xs text-gray-400 active:text-gray-300 transition-colors w-1/4">
            <svg className="h-6 w-6 mb-1" fill="none" stroke="currentColor" viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z"></path>
            </svg>
            <span>Orders</span>
          </button>
          <button className="flex flex-col items-center justify-center text-xs text-gray-400 active:text-gray-300 transition-colors w-1/4">
            <svg className="h-6 w-6 mb-1" fill="none" stroke="currentColor" viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z"></path>
            </svg>
            <span>Recurring</span>
          </button>
          <button className="flex flex-col items-center justify-center text-xs text-gray-400 active:text-gray-300 transition-colors w-1/4">
            <svg className="h-6 w-6 mb-1" fill="none" stroke="currentColor" viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M10.325 4.317c.426-1.756 2.924-1.756 3.35 0a1.724 1.724 0 002.573 1.066c1.543-.94 3.31.826 2.37 2.37a1.724 1.724 0 001.065 2.572c1.756.426 1.756 2.924 0 3.35a1.724 1.724 0 00-1.066 2.573c.94 1.543-.826 3.31-2.37 2.37a1.724 1.724 0 00-2.572 1.065c-.426 1.756-2.924 1.756-3.35 0a1.724 1.724 0 00-2.573-1.066c-1.543.94-3.31-.826-2.37-2.37a1.724 1.724 0 00-1.065-2.572c-1.756-.426-1.756-2.924 0-3.35a1.724 1.724 0 001.066-2.573c-.94-1.543.826-3.31 2.37-2.37.996.608 2.296.07 2.572-1.065z"></path>
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M15 12a3 3 0 11-6 0 3 3 0 016 0z"></path>
            </svg>
            <span>Settings</span>
          </button>
        </div>
      </div>

      {/* Accessibility - Add skip to content link for screen readers */}
      <div className="sr-only">
        <a href="#main-content" className="skip-nav">Skip to main content</a>
      </div>
    </div>
  );
}