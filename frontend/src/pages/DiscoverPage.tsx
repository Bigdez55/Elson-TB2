import React, { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import { Skeleton, SkeletonCard, SkeletonListItem } from '../components/common/Skeleton';

interface Stock {
  symbol: string;
  name: string;
  price: number;
  change: number;
  changePercent: number;
  volume: number;
  marketCap: number;
  sector: string;
}

interface Sector {
  name: string;
  performance: number;
  companies: number;
}

const DiscoverPage: React.FC = () => {
  const [selectedCategory, setSelectedCategory] = useState<'trending' | 'gainers' | 'losers' | 'volume'>('trending');
  const [selectedSector, setSelectedSector] = useState<string>('all');
  const [priceRange, setPriceRange] = useState<{ min: number; max: number }>({ min: 0, max: 1000 });
  const [isLoading, setIsLoading] = useState(true);

  // Simulate loading for future API integration
  useEffect(() => {
    const timer = setTimeout(() => setIsLoading(false), 800);
    return () => clearTimeout(timer);
  }, []);

  // Mock trending stocks
  const trendingStocks: Stock[] = [
    { symbol: 'TSLA', name: 'Tesla Inc', price: 242.84, change: 12.45, changePercent: 5.4, volume: 125000000, marketCap: 770000000000, sector: 'Technology' },
    { symbol: 'NVDA', name: 'NVIDIA Corp', price: 495.22, change: 18.90, changePercent: 4.0, volume: 98000000, marketCap: 1200000000000, sector: 'Technology' },
    { symbol: 'AAPL', name: 'Apple Inc', price: 189.25, change: 3.20, changePercent: 1.7, volume: 85000000, marketCap: 2900000000000, sector: 'Technology' },
    { symbol: 'AMZN', name: 'Amazon.com Inc', price: 178.35, change: 5.60, changePercent: 3.2, volume: 72000000, marketCap: 1800000000000, sector: 'Consumer' },
    { symbol: 'MSFT', name: 'Microsoft Corp', price: 415.26, change: 8.15, changePercent: 2.0, volume: 65000000, marketCap: 3100000000000, sector: 'Technology' },
    { symbol: 'GOOGL', name: 'Alphabet Inc', price: 175.43, change: 4.22, changePercent: 2.5, volume: 58000000, marketCap: 2200000000000, sector: 'Technology' },
  ];

  const topGainers: Stock[] = [
    { symbol: 'GME', name: 'GameStop Corp', price: 24.55, change: 5.20, changePercent: 26.8, volume: 45000000, marketCap: 8500000000, sector: 'Consumer' },
    { symbol: 'AMC', name: 'AMC Entertainment', price: 8.90, change: 1.85, changePercent: 26.2, volume: 62000000, marketCap: 4500000000, sector: 'Entertainment' },
    { symbol: 'PLTR', name: 'Palantir Technologies', price: 28.40, change: 3.80, changePercent: 15.4, volume: 38000000, marketCap: 58000000000, sector: 'Technology' },
  ];

  const topLosers: Stock[] = [
    { symbol: 'RIVN', name: 'Rivian Automotive', price: 18.20, change: -2.85, changePercent: -13.5, volume: 35000000, marketCap: 18000000000, sector: 'Automotive' },
    { symbol: 'LCID', name: 'Lucid Group Inc', price: 3.45, change: -0.48, changePercent: -12.2, volume: 28000000, marketCap: 7500000000, sector: 'Automotive' },
    { symbol: 'COIN', name: 'Coinbase Global', price: 198.50, change: -18.30, changePercent: -8.4, volume: 22000000, marketCap: 48000000000, sector: 'Finance' },
  ];

  const mostActive: Stock[] = [
    { symbol: 'SPY', name: 'SPDR S&P 500 ETF', price: 458.12, change: 2.45, changePercent: 0.5, volume: 180000000, marketCap: 450000000000, sector: 'ETF' },
    { symbol: 'QQQ', name: 'Invesco QQQ Trust', price: 389.55, change: 4.20, changePercent: 1.1, volume: 125000000, marketCap: 220000000000, sector: 'ETF' },
    { symbol: 'TSLA', name: 'Tesla Inc', price: 242.84, change: 12.45, changePercent: 5.4, volume: 125000000, marketCap: 770000000000, sector: 'Technology' },
  ];

  const sectors: Sector[] = [
    { name: 'Technology', performance: 12.5, companies: 1250 },
    { name: 'Healthcare', performance: 8.2, companies: 850 },
    { name: 'Finance', performance: 5.8, companies: 920 },
    { name: 'Consumer', performance: 7.4, companies: 1100 },
    { name: 'Energy', performance: -3.2, companies: 380 },
    { name: 'Industrials', performance: 4.6, companies: 670 },
  ];

  const getCurrentStocks = () => {
    switch (selectedCategory) {
      case 'trending':
        return trendingStocks;
      case 'gainers':
        return topGainers;
      case 'losers':
        return topLosers;
      case 'volume':
        return mostActive;
      default:
        return trendingStocks;
    }
  };

  const formatNumber = (num: number) => {
    if (num >= 1000000000) return `$${(num / 1000000000).toFixed(2)}B`;
    if (num >= 1000000) return `$${(num / 1000000).toFixed(2)}M`;
    if (num >= 1000) return `$${(num / 1000).toFixed(2)}K`;
    return `$${num.toFixed(2)}`;
  };

  const formatVolume = (num: number) => {
    if (num >= 1000000) return `${(num / 1000000).toFixed(1)}M`;
    if (num >= 1000) return `${(num / 1000).toFixed(1)}K`;
    return num.toString();
  };

  // Loading skeleton
  if (isLoading) {
    return (
      <div className="bg-gray-800 min-h-screen p-6">
        {/* Header Skeleton */}
        <div className="mb-8">
          <Skeleton variant="text" width="250px" height="36px" className="mb-2" />
          <Skeleton variant="text" width="400px" height="20px" />
        </div>

        {/* Category Tabs Skeleton */}
        <div className="mb-6">
          <div className="inline-flex space-x-2 bg-gray-900 p-2 rounded-lg">
            {[1, 2, 3, 4].map((i) => (
              <Skeleton key={i} variant="rectangular" width="120px" height="40px" className="rounded-lg" />
            ))}
          </div>
        </div>

        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          {/* Main Stock List Skeleton */}
          <div className="lg:col-span-2">
            <div className="bg-gray-900 rounded-xl overflow-hidden">
              <div className="p-4 border-b border-gray-700">
                <Skeleton variant="text" width="200px" height="28px" />
              </div>
              <div className="divide-y divide-gray-700">
                {[1, 2, 3, 4, 5, 6].map((i) => (
                  <div key={i} className="p-4">
                    <div className="flex items-center justify-between">
                      <div className="flex items-center space-x-3">
                        <Skeleton variant="rectangular" width="40px" height="40px" className="rounded-lg" />
                        <div>
                          <Skeleton variant="text" width="60px" height="20px" className="mb-1" />
                          <Skeleton variant="text" width="120px" height="16px" />
                        </div>
                      </div>
                      <div className="text-right">
                        <Skeleton variant="text" width="80px" height="20px" className="mb-1" />
                        <Skeleton variant="text" width="100px" height="16px" />
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          </div>

          {/* Sidebar Skeleton */}
          <div className="space-y-6">
            {/* Sector Performance Skeleton */}
            <div className="bg-gray-900 rounded-xl p-4">
              <Skeleton variant="text" width="180px" height="24px" className="mb-4" />
              {[1, 2, 3, 4, 5, 6].map((i) => (
                <div key={i} className="bg-gray-800 rounded-lg p-3 mb-3">
                  <div className="flex justify-between mb-2">
                    <Skeleton variant="text" width="80px" height="18px" />
                    <Skeleton variant="text" width="50px" height="18px" />
                  </div>
                  <Skeleton variant="rectangular" width="100%" height="8px" className="rounded-full" />
                </div>
              ))}
            </div>

            {/* Market Stats Skeleton */}
            <div className="bg-gray-900 rounded-xl p-4">
              <Skeleton variant="text" width="150px" height="24px" className="mb-4" />
              {[1, 2, 3].map((i) => (
                <div key={i} className="bg-gray-800 rounded-lg p-3 mb-3">
                  <Skeleton variant="text" width="60px" height="14px" className="mb-1" />
                  <Skeleton variant="text" width="100px" height="28px" className="mb-1" />
                  <Skeleton variant="text" width="80px" height="14px" />
                </div>
              ))}
            </div>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="bg-gray-800 min-h-screen p-6">
      {/* Header */}
      <div className="mb-8">
        <h1 className="text-3xl font-bold text-white mb-2">Discover Markets</h1>
        <p className="text-gray-400">
          Explore trending stocks, market movers, and sector performance
        </p>
      </div>

      {/* Category Tabs */}
      <div className="mb-6">
        <div className="flex space-x-2 bg-gray-900 p-2 rounded-lg inline-flex">
          {[
            { key: 'trending', label: '🔥 Trending', icon: '📈' },
            { key: 'gainers', label: '📈 Top Gainers', icon: '⬆️' },
            { key: 'losers', label: '📉 Top Losers', icon: '⬇️' },
            { key: 'volume', label: '📊 Most Active', icon: '🔊' },
          ].map((cat) => (
            <button
              key={cat.key}
              onClick={() => setSelectedCategory(cat.key as any)}
              className={`px-4 py-2 rounded-lg transition-colors ${
                selectedCategory === cat.key
                  ? 'bg-purple-600 text-white'
                  : 'text-gray-400 hover:bg-gray-800'
              }`}
            >
              {cat.label}
            </button>
          ))}
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Main Stock List */}
        <div className="lg:col-span-2">
          <div className="bg-gray-900 rounded-xl overflow-hidden">
            <div className="p-4 border-b border-gray-700">
              <h2 className="text-xl font-semibold text-white">
                {selectedCategory === 'trending' && '🔥 Trending Now'}
                {selectedCategory === 'gainers' && '📈 Top Gainers Today'}
                {selectedCategory === 'losers' && '📉 Top Losers Today'}
                {selectedCategory === 'volume' && '📊 Most Active'}
              </h2>
            </div>
            <div className="divide-y divide-gray-700">
              {getCurrentStocks().map((stock) => (
                <Link
                  key={stock.symbol}
                  to={`/paper/trading/${stock.symbol}`}
                  className="block p-4 hover:bg-gray-800 transition-colors"
                >
                  <div className="flex items-center justify-between">
                    <div className="flex-1">
                      <div className="flex items-center space-x-3">
                        <div className="w-10 h-10 bg-gradient-to-br from-purple-500 to-blue-500 rounded-lg flex items-center justify-center">
                          <span className="text-white font-bold text-sm">{stock.symbol.substring(0, 2)}</span>
                        </div>
                        <div>
                          <h3 className="text-white font-semibold">{stock.symbol}</h3>
                          <p className="text-sm text-gray-400">{stock.name}</p>
                        </div>
                      </div>
                    </div>
                    <div className="text-right mr-6">
                      <div className="text-white font-semibold">${stock.price.toFixed(2)}</div>
                      <div className={`text-sm font-medium ${stock.change >= 0 ? 'text-green-400' : 'text-red-400'}`}>
                        {stock.change >= 0 ? '+' : ''}{stock.change.toFixed(2)} ({stock.changePercent.toFixed(2)}%)
                      </div>
                    </div>
                    <div className="text-right">
                      <div className="text-sm text-gray-400">Vol: {formatVolume(stock.volume)}</div>
                      <div className="text-sm text-gray-400">Cap: {formatNumber(stock.marketCap)}</div>
                    </div>
                  </div>
                </Link>
              ))}
            </div>
          </div>
        </div>

        {/* Sidebar */}
        <div className="space-y-6">
          {/* Sector Performance */}
          <div className="bg-gray-900 rounded-xl p-4">
            <h3 className="text-lg font-semibold text-white mb-4">📊 Sector Performance</h3>
            <div className="space-y-3">
              {sectors.map((sector) => (
                <div key={sector.name} className="bg-gray-800 rounded-lg p-3">
                  <div className="flex items-center justify-between mb-2">
                    <span className="text-white font-medium">{sector.name}</span>
                    <span className={`text-sm font-semibold ${sector.performance >= 0 ? 'text-green-400' : 'text-red-400'}`}>
                      {sector.performance >= 0 ? '+' : ''}{sector.performance.toFixed(1)}%
                    </span>
                  </div>
                  <div className="w-full bg-gray-700 rounded-full h-2">
                    <div
                      className={`h-2 rounded-full ${sector.performance >= 0 ? 'bg-green-500' : 'bg-red-500'}`}
                      style={{ width: `${Math.min(100, Math.abs(sector.performance) * 5)}%` }}
                    />
                  </div>
                  <div className="text-xs text-gray-400 mt-1">{sector.companies} companies</div>
                </div>
              ))}
            </div>
          </div>

          {/* Market Stats */}
          <div className="bg-gray-900 rounded-xl p-4">
            <h3 className="text-lg font-semibold text-white mb-4">📈 Market Overview</h3>
            <div className="space-y-3">
              <div className="bg-gray-800 rounded-lg p-3">
                <div className="text-sm text-gray-400">S&P 500</div>
                <div className="text-xl font-bold text-white">4,567.89</div>
                <div className="text-sm text-green-400">+0.8% (+34.52)</div>
              </div>
              <div className="bg-gray-800 rounded-lg p-3">
                <div className="text-sm text-gray-400">Nasdaq</div>
                <div className="text-xl font-bold text-white">14,234.56</div>
                <div className="text-sm text-green-400">+1.2% (+168.42)</div>
              </div>
              <div className="bg-gray-800 rounded-lg p-3">
                <div className="text-sm text-gray-400">Dow Jones</div>
                <div className="text-xl font-bold text-white">35,678.90</div>
                <div className="text-sm text-red-400">-0.3% (-107.25)</div>
              </div>
            </div>
          </div>

          {/* AI Recommendations */}
          <div className="bg-gradient-to-br from-purple-900 to-blue-900 rounded-xl p-4">
            <h3 className="text-lg font-semibold text-white mb-2">🤖 AI Picks</h3>
            <p className="text-sm text-gray-300 mb-3">
              Based on your portfolio and risk profile
            </p>
            <div className="space-y-2">
              <div className="bg-white/10 backdrop-blur rounded-lg p-2">
                <div className="text-white font-medium">NVDA</div>
                <div className="text-xs text-gray-300">Strong Buy - 95% confidence</div>
              </div>
              <div className="bg-white/10 backdrop-blur rounded-lg p-2">
                <div className="text-white font-medium">MSFT</div>
                <div className="text-xs text-gray-300">Buy - 88% confidence</div>
              </div>
            </div>
            <Link
              to="/paper/trading"
              className="mt-3 block text-center bg-white/20 hover:bg-white/30 text-white text-sm py-2 rounded-lg transition-colors"
            >
              View All Recommendations
            </Link>
          </div>
        </div>
      </div>
    </div>
  );
};

export default DiscoverPage;
