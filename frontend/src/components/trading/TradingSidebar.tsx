import React, { useState } from 'react';
import { Toggle } from '../common/Toggle';

interface TradingSidebarProps {
  onPaperTradingChange?: (enabled: boolean) => void;
  onSymbolSearch?: (query: string) => void;
  onAssetTypeChange?: (type: string) => void;
  className?: string;
}

export const TradingSidebar: React.FC<TradingSidebarProps> = ({
  onPaperTradingChange,
  onSymbolSearch,
  onAssetTypeChange,
  className = '',
}) => {
  const [paperTradingEnabled, setPaperTradingEnabled] = useState(false);
  const [activeAssetType, setActiveAssetType] = useState('All');
  const [searchQuery, setSearchQuery] = useState('');

  const handlePaperTradingToggle = (enabled: boolean) => {
    setPaperTradingEnabled(enabled);
    onPaperTradingChange?.(enabled);
  };

  const handleAssetTypeChange = (type: string) => {
    setActiveAssetType(type);
    onAssetTypeChange?.(type);
  };

  const handleSearchChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const query = e.target.value;
    setSearchQuery(query);
    onSymbolSearch?.(query);
  };

  const assetTypes = ['All', 'Stocks', 'ETFs', 'Crypto'];

  const watchlistItems = [
    { symbol: 'AAPL', name: 'Apple Inc.', change: '+1.7%', positive: true, bgColor: 'bg-blue-900', textColor: 'text-blue-300' },
    { symbol: 'TSLA', name: 'Tesla Inc.', change: '+8.6%', positive: true, bgColor: 'bg-green-900', textColor: 'text-green-300' },
    { symbol: 'VOO', name: 'Vanguard S&P 500', change: '+1.7%', positive: true, bgColor: 'bg-purple-900', textColor: 'text-purple-300' },
    { symbol: 'MSFT', name: 'Microsoft Corp.', change: '-1.6%', positive: false, bgColor: 'bg-red-900', textColor: 'text-red-300' },
  ];

  const aiRecommendations = [
    { symbol: 'ICLN', name: 'iShares Clean Energy', change: '+3.5%', positive: true, bgColor: 'bg-yellow-900', textColor: 'text-yellow-300' },
    { symbol: 'NVDA', name: 'NVIDIA Corp.', change: '+4.2%', positive: true, bgColor: 'bg-blue-900', textColor: 'text-blue-300' },
    { symbol: 'AMZN', name: 'Amazon.com Inc.', change: '+2.3%', positive: true, bgColor: 'bg-purple-900', textColor: 'text-purple-300' },
  ];

  const marketInsights = [
    { name: 'S&P 500', change: '+1.2%', positive: true },
    { name: 'Nasdaq', change: '+1.8%', positive: true },
    { name: 'Dow Jones', change: '+0.9%', positive: true },
    { name: 'Bitcoin', change: '-2.3%', positive: false },
  ];

  return (
    <div className={`bg-gray-900 min-h-screen p-4 ${className}`} style={{ width: '280px' }}>
      {/* Paper Trading Toggle */}
      <div className="mb-6 p-4 bg-gray-800 rounded-xl">
        <Toggle
          checked={paperTradingEnabled}
          onChange={handlePaperTradingToggle}
          label="Paper Trading"
          description="Practice trading without real money"
        />
      </div>

      {/* Search */}
      <div className="mb-6">
        <div className="relative">
          <input
            type="text"
            placeholder="Search for stocks, ETFs, crypto..."
            value={searchQuery}
            onChange={handleSearchChange}
            className="bg-gray-800 border border-gray-700 rounded-lg pl-10 pr-4 py-2 w-full text-gray-300 focus:outline-none focus:border-purple-500 transition-colors"
          />
          <svg className="absolute left-3 top-2.5 h-5 w-5 text-gray-500" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z" />
          </svg>
        </div>
      </div>

      {/* Asset Types */}
      <div className="mb-6">
        <div className="flex space-x-2">
          {assetTypes.map((type) => (
            <button
              key={type}
              onClick={() => handleAssetTypeChange(type)}
              className={`px-3 py-1 rounded-lg text-sm transition-colors ${
                activeAssetType === type
                  ? 'bg-purple-600 text-white'
                  : 'bg-gray-800 text-gray-400 hover:bg-purple-600 hover:text-white'
              }`}
            >
              {type}
            </button>
          ))}
        </div>
      </div>

      {/* Watchlists */}
      <div className="mb-6">
        <div className="flex items-center justify-between mb-3">
          <h3 className="text-sm font-medium text-gray-400 uppercase tracking-wider">Watchlists</h3>
          <button className="text-purple-400 hover:text-purple-300 transition-colors">
            <svg className="h-4 w-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M12 6v6m0 0v6m0-6h6m-6 0H6" />
            </svg>
          </button>
        </div>
        
        <div className="bg-gray-800 rounded-lg p-3 mb-3">
          <h4 className="text-white font-medium mb-2">My Watchlist</h4>
          <ul className="space-y-2">
            {watchlistItems.map((item) => (
              <li key={item.symbol} className="flex justify-between items-center">
                <div className="flex items-center">
                  <div className={`h-8 w-8 ${item.bgColor} rounded-md flex items-center justify-center ${item.textColor} font-bold text-xs`}>
                    {item.symbol}
                  </div>
                  <span className="ml-2 text-gray-300 text-sm">{item.name}</span>
                </div>
                <span className={`text-sm ${item.positive ? 'text-green-400' : 'text-red-400'}`}>
                  {item.change}
                </span>
              </li>
            ))}
          </ul>
        </div>

        <div className="bg-gray-800 rounded-lg p-3">
          <h4 className="text-white font-medium mb-2">AI Recommendations</h4>
          <ul className="space-y-2">
            {aiRecommendations.map((item) => (
              <li key={item.symbol} className="flex justify-between items-center">
                <div className="flex items-center">
                  <div className={`h-8 w-8 ${item.bgColor} rounded-md flex items-center justify-center ${item.textColor} font-bold text-xs`}>
                    {item.symbol}
                  </div>
                  <span className="ml-2 text-gray-300 text-sm">{item.name}</span>
                </div>
                <span className={`text-sm ${item.positive ? 'text-green-400' : 'text-red-400'}`}>
                  {item.change}
                </span>
              </li>
            ))}
          </ul>
        </div>
      </div>

      {/* Market Insights */}
      <div>
        <h3 className="text-sm font-medium text-gray-400 mb-3 uppercase tracking-wider">Market Insights</h3>
        <div className="bg-gray-800 rounded-lg p-3">
          {marketInsights.map((market, index) => (
            <div key={market.name} className={`flex items-center justify-between ${index < marketInsights.length - 1 ? 'mb-2' : ''}`}>
              <span className="text-gray-300 text-sm">{market.name}</span>
              <div className="flex items-center">
                <span className={`text-sm mr-1 ${market.positive ? 'text-green-400' : 'text-red-400'}`}>
                  {market.change}
                </span>
                <svg className={`h-3 w-3 ${market.positive ? 'text-green-400' : 'text-red-400'}`} fill="currentColor" viewBox="0 0 20 20">
                  <path fillRule="evenodd" d={market.positive 
                    ? "M5.293 9.707a1 1 0 010-1.414l4-4a1 1 0 011.414 0l4 4a1 1 0 01-1.414 1.414L11 7.414V15a1 1 0 11-2 0V7.414L6.707 9.707a1 1 0 01-1.414 0z"
                    : "M14.707 10.293a1 1 0 010 1.414l-4 4a1 1 0 01-1.414 0l-4-4a1 1 0 111.414-1.414L9 12.586V5a1 1 0 012 0v7.586l2.293-2.293a1 1 0 011.414 0z"
                  } clipRule="evenodd" />
                </svg>
              </div>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
};