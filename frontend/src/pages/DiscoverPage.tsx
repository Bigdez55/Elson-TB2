import React, { useState, useEffect, useCallback } from 'react';
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

// Large pool of popular stocks to cycle through
const ALL_STOCKS_INFO: Record<string, { name: string; sector: string }> = {
  // Technology
  'AAPL': { name: 'Apple Inc', sector: 'Technology' },
  'MSFT': { name: 'Microsoft Corp', sector: 'Technology' },
  'GOOGL': { name: 'Alphabet Inc', sector: 'Technology' },
  'NVDA': { name: 'NVIDIA Corp', sector: 'Technology' },
  'META': { name: 'Meta Platforms', sector: 'Technology' },
  'AVGO': { name: 'Broadcom Inc', sector: 'Technology' },
  'ORCL': { name: 'Oracle Corp', sector: 'Technology' },
  'CRM': { name: 'Salesforce Inc', sector: 'Technology' },
  'AMD': { name: 'AMD Inc', sector: 'Technology' },
  'INTC': { name: 'Intel Corp', sector: 'Technology' },
  'CSCO': { name: 'Cisco Systems', sector: 'Technology' },
  'IBM': { name: 'IBM Corp', sector: 'Technology' },
  // Consumer
  'AMZN': { name: 'Amazon.com Inc', sector: 'Consumer' },
  'WMT': { name: 'Walmart Inc', sector: 'Consumer' },
  'HD': { name: 'Home Depot', sector: 'Consumer' },
  'COST': { name: 'Costco Wholesale', sector: 'Consumer' },
  'NKE': { name: 'Nike Inc', sector: 'Consumer' },
  'MCD': { name: 'McDonalds Corp', sector: 'Consumer' },
  'SBUX': { name: 'Starbucks Corp', sector: 'Consumer' },
  'TGT': { name: 'Target Corp', sector: 'Consumer' },
  // Finance
  'JPM': { name: 'JPMorgan Chase', sector: 'Finance' },
  'BAC': { name: 'Bank of America', sector: 'Finance' },
  'WFC': { name: 'Wells Fargo', sector: 'Finance' },
  'GS': { name: 'Goldman Sachs', sector: 'Finance' },
  'MS': { name: 'Morgan Stanley', sector: 'Finance' },
  'V': { name: 'Visa Inc', sector: 'Finance' },
  'MA': { name: 'Mastercard Inc', sector: 'Finance' },
  'AXP': { name: 'American Express', sector: 'Finance' },
  // Healthcare
  'JNJ': { name: 'Johnson & Johnson', sector: 'Healthcare' },
  'UNH': { name: 'UnitedHealth Group', sector: 'Healthcare' },
  'PFE': { name: 'Pfizer Inc', sector: 'Healthcare' },
  'MRK': { name: 'Merck & Co', sector: 'Healthcare' },
  'ABBV': { name: 'AbbVie Inc', sector: 'Healthcare' },
  'LLY': { name: 'Eli Lilly', sector: 'Healthcare' },
  // Automotive & Industrial
  'TSLA': { name: 'Tesla Inc', sector: 'Automotive' },
  'F': { name: 'Ford Motor', sector: 'Automotive' },
  'GM': { name: 'General Motors', sector: 'Automotive' },
  'CAT': { name: 'Caterpillar Inc', sector: 'Industrial' },
  'BA': { name: 'Boeing Co', sector: 'Industrial' },
  'GE': { name: 'General Electric', sector: 'Industrial' },
  // Energy
  'XOM': { name: 'Exxon Mobil', sector: 'Energy' },
  'CVX': { name: 'Chevron Corp', sector: 'Energy' },
  // Entertainment & Communication
  'DIS': { name: 'Walt Disney Co', sector: 'Entertainment' },
  'NFLX': { name: 'Netflix Inc', sector: 'Entertainment' },
  'T': { name: 'AT&T Inc', sector: 'Communication' },
  'VZ': { name: 'Verizon', sector: 'Communication' },
};

// Function to get random stocks from the pool
const getRandomStocks = (count: number = 8): string[] => {
  const allSymbols = Object.keys(ALL_STOCKS_INFO);
  const shuffled = [...allSymbols].sort(() => Math.random() - 0.5);
  return shuffled.slice(0, count);
};

const DiscoverPage: React.FC = () => {
  const [selectedCategory, setSelectedCategory] = useState<'trending' | 'gainers' | 'losers' | 'volume'>('trending');
  const [selectedSector, setSelectedSector] = useState<string>('all');
  const [priceRange, setPriceRange] = useState<{ min: number; max: number }>({ min: 0, max: 1000 });
  const [isLoading, setIsLoading] = useState(true);
  const [stocks, setStocks] = useState<Stock[]>([]);
  const [error, setError] = useState<string | null>(null);
  // Random stocks selected on component mount - changes on each page visit
  const [selectedSymbols] = useState<string[]>(() => getRandomStocks(8));

  // Fetch real market data from API
  const fetchMarketData = useCallback(async () => {
    try {
      const token = localStorage.getItem('token');
      const baseUrl = process.env.REACT_APP_API_URL || '/api/v1';

      const response = await fetch(`${baseUrl}/market-data/quotes`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${token}`,
        },
        body: JSON.stringify(selectedSymbols),
      });

      if (!response.ok) {
        throw new Error('Failed to fetch market data');
      }

      const data = await response.json();

      const stockData: Stock[] = (data.quotes || []).map((quote: any) => {
        const info = ALL_STOCKS_INFO[quote.symbol] || { name: quote.symbol, sector: 'Unknown' };
        return {
          symbol: quote.symbol,
          name: info.name,
          price: quote.price || 0,
          change: quote.change || 0,
          changePercent: quote.change_percent || 0,
          volume: quote.volume || 0,
          marketCap: 0,
          sector: info.sector,
        };
      });

      setStocks(stockData);
      setError(null);
    } catch (err) {
      console.error('Error fetching market data:', err);
      setError('Unable to load live market data');
    } finally {
      setIsLoading(false);
    }
  }, [selectedSymbols]);

  useEffect(() => {
    fetchMarketData();
    // Refresh market data every 60 seconds
    const interval = setInterval(fetchMarketData, 60000);
    return () => clearInterval(interval);
  }, [fetchMarketData]);

  // Sector performance is calculated from live data
  const sectors: Sector[] = [
    { name: 'Technology', performance: 0, companies: 0 },
    { name: 'Finance', performance: 0, companies: 0 },
    { name: 'Consumer', performance: 0, companies: 0 },
    { name: 'Automotive', performance: 0, companies: 0 },
  ];

  // Get stocks sorted/filtered by category
  const getCurrentStocks = () => {
    if (stocks.length === 0) return [];

    const sortedStocks = [...stocks];
    switch (selectedCategory) {
      case 'gainers':
        return sortedStocks.filter(s => s.changePercent > 0).sort((a, b) => b.changePercent - a.changePercent);
      case 'losers':
        return sortedStocks.filter(s => s.changePercent < 0).sort((a, b) => a.changePercent - b.changePercent);
      case 'volume':
        return sortedStocks.sort((a, b) => b.volume - a.volume);
      case 'trending':
      default:
        return sortedStocks;
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
            {error ? (
              <div className="p-8 text-center">
                <div className="w-16 h-16 bg-red-900/30 rounded-full flex items-center justify-center mx-auto mb-4">
                  <svg className="w-8 h-8 text-red-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M12 8v4m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
                  </svg>
                </div>
                <h3 className="text-white font-medium mb-2">Unable to Load Market Data</h3>
                <p className="text-gray-400 text-sm mb-4">{error}</p>
                <button
                  onClick={() => { setIsLoading(true); fetchMarketData(); }}
                  className="bg-purple-600 hover:bg-purple-700 text-white px-4 py-2 rounded-lg text-sm transition-colors"
                >
                  Try Again
                </button>
              </div>
            ) : getCurrentStocks().length === 0 ? (
              <div className="p-8 text-center">
                <div className="w-16 h-16 bg-gray-800 rounded-full flex items-center justify-center mx-auto mb-4">
                  <span className="text-3xl">📊</span>
                </div>
                <h3 className="text-white font-medium mb-2">No Stocks to Display</h3>
                <p className="text-gray-400 text-sm">
                  {selectedCategory === 'gainers' && 'No stocks are currently showing gains.'}
                  {selectedCategory === 'losers' && 'No stocks are currently showing losses.'}
                  {(selectedCategory === 'trending' || selectedCategory === 'volume') && 'Market data is loading...'}
                </p>
              </div>
            ) : (
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
            )}
          </div>
        </div>

        {/* Sidebar */}
        <div className="space-y-6">
          {/* Sector Performance */}
          <div className="bg-gray-900 rounded-xl p-4">
            <h3 className="text-lg font-semibold text-white mb-4">📊 Sector Performance</h3>
            <p className="text-gray-400 text-sm mb-4">
              Detailed sector analysis and performance metrics coming soon.
            </p>
            <div className="space-y-2">
              {['Technology', 'Finance', 'Consumer', 'Healthcare'].map((sector) => (
                <div key={sector} className="bg-gray-800 rounded-lg p-2 px-3">
                  <span className="text-gray-300 text-sm">{sector}</span>
                </div>
              ))}
            </div>
          </div>

          {/* Market Stats */}
          <div className="bg-gray-900 rounded-xl p-4">
            <h3 className="text-lg font-semibold text-white mb-4">📈 Market Overview</h3>
            <p className="text-gray-400 text-sm mb-3">
              View detailed market indices and analysis in our trading section.
            </p>
            <Link
              to="/paper/trading"
              className="block text-center bg-purple-600 hover:bg-purple-700 text-white text-sm py-2 rounded-lg transition-colors"
            >
              Go to Trading
            </Link>
          </div>

          {/* Start Trading */}
          <div className="bg-gradient-to-br from-purple-900 to-blue-900 rounded-xl p-4">
            <h3 className="text-lg font-semibold text-white mb-2">🚀 Start Trading</h3>
            <p className="text-sm text-gray-300 mb-3">
              Practice with ${(250000).toLocaleString()} in paper trading funds
            </p>
            <Link
              to="/paper/trading"
              className="block text-center bg-white/20 hover:bg-white/30 text-white text-sm py-2 rounded-lg transition-colors"
            >
              Open Trading Platform
            </Link>
          </div>
        </div>
      </div>
    </div>
  );
};

export default DiscoverPage;
