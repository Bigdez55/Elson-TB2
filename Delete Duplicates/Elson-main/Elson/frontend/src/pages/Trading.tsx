import React, { useState, useEffect, Suspense, lazy } from 'react';
import CandlestickChart from '../app/components/charts/CandlestickChart';
import OrderForm from '../app/components/trading/OrderForm';
import TradeHistory from '../app/components/trading/TradeHistory';
import Watchlist from '../app/components/trading/Watchlist';
import { useTrading } from '../app/hooks/useTrading';
import { useWebSocket } from '../app/hooks/useWebSocket';
import Button from '../app/components/common/Button';
import Select from '../app/components/common/Select';
import Input from '../app/components/common/Input';
import Loading from '../app/components/common/Loading';
import LoadingSpinner from '../app/components/common/LoadingSpinner';
import { useDispatch } from 'react-redux';
import { useTheme, useMediaQuery } from '@mui/material';

// Import the mobile trading component lazily for better performance
const MobileTrading = lazy(() => import('../app/components/trading/MobileTrading'));

export default function Trading() {
  const dispatch = useDispatch();
  const theme = useTheme();
  const isMobile = useMediaQuery(theme.breakpoints.down('sm'));
  const [selectedSymbol, setSelectedSymbol] = useState('TSLA');
  const [timeframe, setTimeframe] = useState('1M');
  const [isPaperTrading, setIsPaperTrading] = useState(false);
  const [activeAssetType, setActiveAssetType] = useState('All');
  const { marketData, isLoading, error } = useTrading(selectedSymbol);
  
  // Check if we should render the mobile version of the trading interface
  if (isMobile) {
    return (
      <Suspense fallback={<Loading />}>
        <MobileTrading />
      </Suspense>
    );
  }

  useWebSocket(['market', 'trades', 'orderbook'], { symbol: selectedSymbol });

  const handleSymbolChange = (symbol: string) => {
    setSelectedSymbol(symbol);
  };

  const togglePaperTrading = () => {
    setIsPaperTrading(!isPaperTrading);
  };

  // Simulated data for the chart
  const chartData = {
    candles: Array.from({ length: 30 }, (_, i) => ({
      timestamp: new Date(Date.now() - (29 - i) * 24 * 60 * 60 * 1000),
      open: 245 + i * 1.5,
      high: 245 + i * 1.5 + 5,
      low: 245 + i * 1.5 - 3,
      close: [
        245, 248, 252, 249, 251, 258, 262, 260, 255, 250,
        253, 257, 262, 267, 264, 260, 266, 272, 275, 278,
        276, 274, 280, 283, 281, 285, 282, 287, 290, 289
      ][i],
      volume: Math.random() * 1000000
    }))
  };

  const stockInfo = {
    symbol: 'TSLA',
    name: 'Tesla, Inc.',
    exchange: 'NASDAQ',
    category: 'Electric Vehicles & Clean Energy',
    price: 290.38,
    change: 24.91,
    changePercent: 8.58,
    afterHoursPrice: 291.16,
    afterHoursChange: 0.78,
    afterHoursChangePercent: 0.27,
    marketCap: '921.83B',
    peRatio: '83.47',
    weekRange: '$101.81 - $299.29',
    dividendYield: 'N/A'
  };

  // Market insight data
  const marketInsights = [
    { name: 'S&P 500', change: 1.2, isPositive: true },
    { name: 'Nasdaq', change: 1.8, isPositive: true },
    { name: 'Dow Jones', change: 0.9, isPositive: true },
    { name: 'Bitcoin', change: -2.3, isPositive: false }
  ];

  const watchlists = {
    'My Watchlist': [
      { symbol: 'AAPL', name: 'Apple Inc.', change: 1.7, color: 'blue' },
      { symbol: 'TSLA', name: 'Tesla Inc.', change: 8.6, color: 'green' },
      { symbol: 'VOO', name: 'Vanguard S&P 500', change: 1.7, color: 'purple' },
      { symbol: 'MSFT', name: 'Microsoft Corp.', change: -1.6, color: 'red' }
    ],
    'AI Recommendations': [
      { symbol: 'ICLN', name: 'iShares Clean Energy', change: 3.5, color: 'yellow' },
      { symbol: 'NVDA', name: 'NVIDIA Corp.', change: 4.2, color: 'blue' },
      { symbol: 'AMZN', name: 'Amazon.com Inc.', change: 2.3, color: 'purple' }
    ]
  };

  // News articles
  const newsArticles = [
    { title: 'Tesla Reports Record Q3 Deliveries', source: 'Business Insider', timeAgo: '2 hours ago' },
    { title: 'New Gigafactory Planned in Mexico; Production to Begin 2025', source: 'Reuters', timeAgo: '1 day ago' },
    { title: 'Tesla Expands Supercharger Network to New Markets', source: 'Bloomberg', timeAgo: '3 days ago' }
  ];

  if (isLoading) {
    return <Loading />;
  }

  if (error) {
    return (
      <div className="text-red-500 p-4">
        Error loading trading view: {error}
      </div>
    );
  }

  return (
    <div className="flex flex-col">
      {/* Paper Trading Banner */}
      {isPaperTrading && (
        <div className="paper-trading-banner w-full py-2 px-4 text-center z-10 bg-purple-900 bg-opacity-15 border border-purple-600 animate-pulse">
          <div className="flex flex-col sm:flex-row items-center justify-center">
            <div className="flex items-center">
              <svg className="h-5 w-5 text-purple-300 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M9.663 17h4.673M12 3v1m6.364 1.636l-.707.707M21 12h-1M4 12H3m3.343-5.657l-.707-.707m2.828 9.9a5 5 0 117.072 0l-.548.547A3.374 3.374 0 0014 18.469V19a2 2 0 11-4 0v-.531c0-.895-.356-1.754-.988-2.386l-.548-.547z"></path>
              </svg>
              <span className="text-purple-300 font-medium">Paper Trading Mode</span>
            </div>
            <span className="text-purple-200 sm:ml-2 mt-1 sm:mt-0">— You are in simulation mode. No real money will be used.</span>
          </div>
        </div>
      )}

      <div className="flex flex-col lg:flex-row pt-4">
        {/* Left Sidebar - Asset Search and List - Mobile First Design */}
        <div className="w-full lg:w-64 bg-gray-900 p-4 flex-shrink-0 order-2 lg:order-1 mb-4 lg:mb-0 rounded-t-lg lg:rounded-t-none lg:rounded-l-lg">
          {/* Paper Trading Toggle */}
          <div className="mb-6 p-4 bg-gray-800 rounded-xl">
            <div className="flex items-center justify-between">
              <div>
                <h3 className="text-white font-medium mb-1">Paper Trading</h3>
                <p className="text-gray-400 text-xs">Practice trading without real money</p>
              </div>
              <div 
                className={`relative w-12 h-6 rounded-full cursor-pointer transition-colors ${isPaperTrading ? 'bg-purple-600' : 'bg-gray-600'}`}
                onClick={togglePaperTrading}
              >
                <div 
                  className={`absolute top-1 w-4 h-4 bg-white rounded-full transition-all ${isPaperTrading ? 'left-7' : 'left-1'}`}
                ></div>
              </div>
            </div>
          </div>

          {/* Search */}
          <div className="mb-6">
            <div className="relative">
              <Input
                type="text"
                placeholder="Search for stocks, ETFs, crypto..."
                className="pl-10 w-full"
              />
              <svg className="absolute left-3 top-2.5 h-5 w-5 text-gray-500" fill="none" stroke="currentColor" viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z"></path>
              </svg>
            </div>
          </div>

          {/* Asset Types - Scrollable on mobile */}
          <div className="mb-6">
            <div className="flex space-x-2 overflow-x-auto pb-2 -mx-1 px-1">
              {['All', 'Stocks', 'ETFs', 'Crypto'].map(type => (
                <button 
                  key={type}
                  className={`px-3 py-1 rounded-lg text-sm bg-gray-800 whitespace-nowrap flex-shrink-0 ${activeAssetType === type ? 'bg-purple-700 text-white' : 'text-gray-400'}`}
                  onClick={() => setActiveAssetType(type)}
                >
                  {type}
                </button>
              ))}
            </div>
          </div>

          {/* Watchlists */}
          <div className="mb-6">
            <div className="flex items-center justify-between mb-3">
              <h3 className="text-sm font-medium text-gray-400">WATCHLISTS</h3>
              <button className="text-purple-400 hover:text-purple-300">
                <svg className="h-4 w-4" fill="none" stroke="currentColor" viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M12 6v6m0 0v6m0-6h6m-6 0H6"></path>
                </svg>
              </button>
            </div>

            {Object.entries(watchlists).map(([listName, items]) => (
              <div key={listName} className="bg-gray-800 rounded-lg p-3 mb-3">
                <h4 className="text-white font-medium mb-2">{listName}</h4>
                <ul className="space-y-2">
                  {items.map(item => (
                    <li 
                      key={item.symbol} 
                      className="flex justify-between items-center cursor-pointer hover:bg-gray-700 rounded-md p-1"
                      onClick={() => handleSymbolChange(item.symbol)}
                    >
                      <div className="flex items-center">
                        <div className={`h-8 w-8 bg-${item.color}-900 rounded-md flex items-center justify-center text-${item.color}-300 font-bold text-xs`}>
                          {item.symbol}
                        </div>
                        <span className="ml-2 text-gray-300 text-sm hidden sm:inline">{item.name}</span>
                        <span className="ml-2 text-gray-300 text-sm sm:hidden">{item.symbol}</span>
                      </div>
                      <span className={`text-${item.change >= 0 ? 'green' : 'red'}-400 text-sm`}>
                        {item.change >= 0 ? '+' : ''}{item.change}%
                      </span>
                    </li>
                  ))}
                </ul>
              </div>
            ))}
          </div>

          {/* Market Insights */}
          <div>
            <h3 className="text-sm font-medium text-gray-400 mb-3">MARKET INSIGHTS</h3>
            <div className="bg-gray-800 rounded-lg p-3">
              {marketInsights.map(insight => (
                <div key={insight.name} className="flex items-center justify-between mb-2">
                  <span className="text-gray-300 text-sm">{insight.name}</span>
                  <div className="flex items-center">
                    <span className={`text-${insight.isPositive ? 'green' : 'red'}-400 text-sm mr-1`}>
                      {insight.isPositive ? '+' : ''}{insight.change}%
                    </span>
                    <svg 
                      className={`h-3 w-3 text-${insight.isPositive ? 'green' : 'red'}-400`} 
                      fill="currentColor" 
                      viewBox="0 0 20 20" 
                      xmlns="http://www.w3.org/2000/svg"
                    >
                      {insight.isPositive ? (
                        <path fillRule="evenodd" d="M5.293 9.707a1 1 0 010-1.414l4-4a1 1 0 011.414 0l4 4a1 1 0 01-1.414 1.414L11 7.414V15a1 1 0 11-2 0V7.414L6.707 9.707a1 1 0 01-1.414 0z" clipRule="evenodd" />
                      ) : (
                        <path fillRule="evenodd" d="M14.707 10.293a1 1 0 010 1.414l-4 4a1 1 0 01-1.414 0l-4-4a1 1 0 111.414-1.414L9 12.586V5a1 1 0 012 0v7.586l2.293-2.293a1 1 0 011.414 0z" clipRule="evenodd" />
                      )}
                    </svg>
                  </div>
                </div>
              ))}
            </div>
          </div>
        </div>

        {/* Main Content */}
        <div className="flex-1 bg-gray-800 min-h-screen p-4 sm:p-6 order-1 lg:order-2">
          {/* Stock Info Header */}
          <div className="flex flex-col sm:flex-row sm:justify-between sm:items-start mb-6 gap-4">
            <div>
              <div className="flex items-center">
                <div className="h-10 w-10 bg-green-900 rounded-md flex items-center justify-center text-green-300 font-bold text-sm mr-3">
                  {stockInfo.symbol}
                </div>
                <div>
                  <h1 className="text-xl sm:text-2xl font-bold text-white">{stockInfo.name}</h1>
                  <p className="text-gray-400 text-sm sm:text-base">{stockInfo.exchange}: {stockInfo.symbol} • {stockInfo.category}</p>
                </div>
              </div>
            </div>
            <div className="flex space-x-3">
              <Button variant="secondary" className="flex items-center text-sm">
                <svg className="h-4 w-4 mr-1" fill="none" stroke="currentColor" viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M4.318 6.318a4.5 4.5 0 000 6.364L12 20.364l7.682-7.682a4.5 4.5 0 00-6.364-6.364L12 7.636l-1.318-1.318a4.5 4.5 0 00-6.364 0z"></path>
                </svg>
                <span className="hidden sm:inline">Add to Watchlist</span>
                <span className="sm:hidden">Watch</span>
              </Button>
              <Button variant="secondary" className="flex items-center text-sm">
                <svg className="h-4 w-4 mr-1" fill="none" stroke="currentColor" viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M8.684 13.342C8.886 12.938 9 12.482 9 12c0-.482-.114-.938-.316-1.342m0 2.684a3 3 0 110-2.684m0 2.684l6.632 3.316m-6.632-6l6.632-3.316m0 0a3 3 0 105.367-2.684 3 3 0 00-5.367 2.684zm0 9.316a3 3 0 105.368 2.684 3 3 0 00-5.368-2.684z"></path>
                </svg>
                <span className="hidden sm:inline">Share</span>
              </Button>
            </div>
          </div>

          {/* Stock Price & Stats */}
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4 sm:gap-6 mb-6">
            <div className="bg-gray-900 rounded-xl p-4 sm:p-6 md:col-span-2">
              <div className="flex flex-col sm:flex-row sm:justify-between sm:items-center mb-2">
                <div>
                  <h2 className="text-2xl sm:text-3xl font-bold text-white">${stockInfo.price.toFixed(2)}</h2>
                  <div className="flex items-center">
                    <span className="text-green-400 font-medium mr-2">
                      +${stockInfo.change.toFixed(2)} ({stockInfo.changePercent.toFixed(2)}%)
                    </span>
                    <span className="text-gray-400 text-sm">Today</span>
                  </div>
                </div>
                <div className="text-left sm:text-right mt-2 sm:mt-0">
                  <div className="text-green-400 font-medium">
                    <span className="text-sm">After Hours:</span> ${stockInfo.afterHoursPrice.toFixed(2)}
                  </div>
                  <div className="text-gray-400 text-sm">
                    +${stockInfo.afterHoursChange.toFixed(2)} ({stockInfo.afterHoursChangePercent.toFixed(2)}%)
                  </div>
                </div>
              </div>
            </div>

            <div className="bg-gray-900 rounded-xl p-4">
              <h3 className="text-gray-400 text-sm mb-1">Market Cap</h3>
              <p className="text-white font-medium">${stockInfo.marketCap}</p>
              <div className="mt-2">
                <h3 className="text-gray-400 text-sm mb-1">P/E Ratio</h3>
                <p className="text-white font-medium">{stockInfo.peRatio}</p>
              </div>
            </div>

            <div className="bg-gray-900 rounded-xl p-4">
              <h3 className="text-gray-400 text-sm mb-1">52 Week Range</h3>
              <p className="text-white font-medium">{stockInfo.weekRange}</p>
              <div className="mt-2">
                <h3 className="text-gray-400 text-sm mb-1">Dividend Yield</h3>
                <p className="text-white font-medium">{stockInfo.dividendYield}</p>
              </div>
            </div>
          </div>

          {/* Chart & Order Controls */}
          <div className="grid grid-cols-1 lg:grid-cols-3 gap-4 sm:gap-6">
            {/* Chart Section */}
            <div className="bg-gray-900 rounded-xl p-4 sm:p-6 lg:col-span-2">
              <div className="flex flex-col sm:flex-row sm:justify-between sm:items-center mb-6 gap-2">
                <div className="flex flex-wrap gap-2">
                  {['1D', '1W', '1M', '3M', '1Y', '5Y'].map(period => (
                    <button 
                      key={period}
                      className={`px-3 py-1 rounded-lg text-sm ${timeframe === period ? 'bg-purple-800 text-purple-200' : 'bg-gray-800 text-gray-400 hover:bg-purple-800 hover:text-purple-200'}`}
                      onClick={() => setTimeframe(period)}
                    >
                      {period}
                    </button>
                  ))}
                </div>
                <div className="flex space-x-2 self-end sm:self-auto">
                  <button className="px-3 py-1 rounded-lg text-sm bg-gray-800 text-gray-400 hover:bg-gray-700">
                    <svg className="h-5 w-5" fill="none" stroke="currentColor" viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M10.325 4.317c.426-1.756 2.924-1.756 3.35 0a1.724 1.724 0 002.573 1.066c1.543-.94 3.31.826 2.37 2.37a1.724 1.724 0 001.065 2.572c1.756.426 1.756 2.924 0 3.35a1.724 1.724 0 00-1.066 2.573c.94 1.543-.826 3.31-2.37 2.37a1.724 1.724 0 00-2.572 1.065c-.426 1.756-2.924 1.756-3.35 0a1.724 1.724 0 00-2.573-1.066c-1.543.94-3.31-.826-2.37-2.37a1.724 1.724 0 00-1.065-2.572c-1.756-.426-1.756-2.924 0-3.35a1.724 1.724 0 001.066-2.573c-.94-1.543.826-3.31 2.37-2.37.996.608 2.296.07 2.572-1.065z"></path>
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M15 12a3 3 0 11-6 0 3 3 0 016 0z"></path>
                    </svg>
                  </button>
                  <button className="px-3 py-1 rounded-lg text-sm bg-gray-800 text-gray-400 hover:bg-gray-700">
                    <svg className="h-5 w-5" fill="none" stroke="currentColor" viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M4 8V4m0 0h4M4 4l5 5m11-1V4m0 0h-4m4 0l-5 5M4 16v4m0 0h4m-4 0l5-5m11 5l-5-5m5 5v-4m0 4h-4"></path>
                    </svg>
                  </button>
                </div>
              </div>
              <div className="h-[300px] sm:h-[400px]">
                <CandlestickChart
                  data={chartData.candles}
                  width="100%"
                  height="100%"
                  timeframe={timeframe}
                />
              </div>
            </div>

            {/* Order Form */}
            <div className="bg-gray-900 rounded-xl p-4 sm:p-6">
              <div className="flex justify-between items-center mb-6">
                <h3 className="text-lg font-medium text-white">Place Order</h3>
                <div className="flex space-x-2">
                  <button className="px-4 py-1 rounded-lg text-sm bg-green-600 text-white">Buy</button>
                  <button className="px-4 py-1 rounded-lg text-sm bg-gray-800 text-gray-400">Sell</button>
                </div>
              </div>
              
              {/* Micro-Investing Button */}
              <div className="flex items-center mb-3 mt-1 bg-purple-900 bg-opacity-20 p-2 rounded-lg border border-purple-500 border-opacity-30">
                <div className="flex-shrink-0 mr-2">
                  <svg className="h-5 w-5 text-purple-400" fill="none" stroke="currentColor" viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M12 8c-1.657 0-3 .895-3 2s1.343 2 3 2 3 .895 3 2-1.343 2-3 2m0-8c1.11 0 2.08.402 2.599 1M12 8V7m0 1v8m0 0v1m0-1c-1.11 0-2.08-.402-2.599-1M21 12a9 9 0 11-18 0 9 9 0 0118 0z"></path>
                  </svg>
                </div>
                <div className="flex-grow">
                  <div className="text-purple-300 text-xs md:text-sm font-medium">Try Micro-Investing</div>
                  <div className="text-gray-400 text-xs">Invest with as little as $1 in fractional shares</div>
                </div>
                <button 
                  className="bg-purple-700 hover:bg-purple-600 text-white text-xs rounded-md py-1 px-2"
                  onClick={() => window.location.href = '/micro-invest'}
                >
                  Try Now
                </button>
              </div>

              <OrderForm 
                symbol={selectedSymbol}
                currentPrice={stockInfo.price}
              />
            </div>
          </div>

          {/* AI Trading & Company Info */}
          <div className="grid grid-cols-1 lg:grid-cols-3 gap-4 sm:gap-6 mt-6">
            {/* AI Trading */}
            <div className="bg-gray-900 rounded-xl p-4 sm:p-6 order-2 lg:order-1">
              <div className="flex justify-between items-center mb-4">
                <h3 className="text-lg font-medium text-white">AI Trading Assistant</h3>
                <div className="px-2 py-1 bg-purple-900 bg-opacity-60 rounded-full text-xs text-purple-200">
                  Premium
                </div>
              </div>
              
              <div className="space-y-4">
                <div className="bg-gray-800 p-4 rounded-lg">
                  <div className="flex items-center mb-2">
                    <svg className="h-5 w-5 text-purple-400 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M9.663 17h4.673M12 3v1m6.364 1.636l-.707.707M21 12h-1M4 12H3m3.343-5.657l-.707-.707m2.828 9.9a5 5 0 117.072 0l-.548.547A3.374 3.374 0 0014 18.469V19a2 2 0 11-4 0v-.531c0-.895-.356-1.754-.988-2.386l-.548-.547z"></path>
                    </svg>
                    <span className="text-white font-medium">Quantum AI Analysis</span>
                  </div>
                  <p className="text-gray-300 text-sm mb-2">Tesla shows strong bullish momentum with technical indicators suggesting continued upward movement.</p>
                  <div className="flex space-x-2">
                    <div className="px-2 py-1 bg-green-900 bg-opacity-30 rounded-md text-xs text-green-400">
                      Buy Signal
                    </div>
                    <div className="px-2 py-1 bg-purple-900 bg-opacity-30 rounded-md text-xs text-purple-300">
                      87% Confidence
                    </div>
                  </div>
                </div>
                
                <div className="bg-gray-800 p-4 rounded-lg">
                  <div className="flex items-center mb-2">
                    <svg className="h-5 w-5 text-purple-400 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z"></path>
                    </svg>
                    <span className="text-white font-medium">Automated Strategy</span>
                  </div>
                  <p className="text-gray-300 text-sm mb-2">Our AI recommends a gradual buy-in strategy, acquiring 25% of your position now and increasing on dips.</p>
                  <Button variant="primary" className="w-full">
                    Apply AI Strategy
                  </Button>
                </div>
                
                <div className="bg-gray-800 p-4 rounded-lg">
                  <div className="flex items-center mb-2">
                    <svg className="h-5 w-5 text-purple-400 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z"></path>
                    </svg>
                    <span className="text-white font-medium">Risk Assessment</span>
                  </div>
                  <div className="flex items-center mb-2">
                    <div className="flex-1 h-2 bg-gray-700 rounded-full overflow-hidden">
                      <div className="h-full bg-gradient-to-r from-green-500 to-yellow-500" style={{ width: '65%' }}></div>
                    </div>
                    <span className="ml-2 text-gray-300 text-sm">65/100</span>
                  </div>
                  <p className="text-gray-300 text-sm">Medium-high volatility. Consider setting a stop-loss at $265.50.</p>
                </div>
              </div>
            </div>

            {/* Company Info */}
            <div className="bg-gray-900 rounded-xl p-4 sm:p-6 lg:col-span-2 order-1 lg:order-2 mb-4 lg:mb-0">
              <h3 className="text-lg font-medium text-white mb-4">About Tesla, Inc.</h3>
              <p className="text-gray-300 text-sm mb-4">
                Tesla, Inc. designs, develops, manufactures, and sells electric vehicles, energy generation and storage systems. The company operates through Automotive and Energy Generation segments. The Automotive segment includes the design, development, manufacturing, and sales of electric vehicles. The Energy Generation segment includes the design, manufacture, installation, and sale of solar energy systems and energy storage products.
              </p>
              
              <div className="grid grid-cols-1 sm:grid-cols-2 gap-4 mb-6">
                <div>
                  <h4 className="text-gray-400 text-sm">CEO</h4>
                  <p className="text-white">Elon Musk</p>
                </div>
                <div>
                  <h4 className="text-gray-400 text-sm">Founded</h4>
                  <p className="text-white">2003</p>
                </div>
                <div>
                  <h4 className="text-gray-400 text-sm">Headquarters</h4>
                  <p className="text-white">Austin, Texas, USA</p>
                </div>
                <div>
                  <h4 className="text-gray-400 text-sm">Employees</h4>
                  <p className="text-white">~110,000</p>
                </div>
              </div>
              
              <h3 className="text-lg font-medium text-white mb-4">Recent News</h3>
              <div className="space-y-3">
                {newsArticles.map((article, index) => (
                  <div key={index} className="bg-gray-800 p-3 rounded-lg">
                    <h4 className="text-white text-sm font-medium">{article.title}</h4>
                    <div className="flex justify-between items-center mt-1">
                      <p className="text-gray-400 text-xs">{article.source} • {article.timeAgo}</p>
                      <button className="text-purple-400 hover:text-purple-300 text-xs">Read More</button>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}