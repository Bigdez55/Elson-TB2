import React, { useState, useEffect, useCallback } from 'react';
import { Link } from 'react-router-dom';
import { Skeleton } from '../components/common/Skeleton';

interface Stock {
  symbol: string;
  name: string;
  price: number;
  change: number;
  changePercent: number;
  volume: number;
  sector: string;
}

// Large pool of popular stocks to cycle through
const ALL_STOCKS_INFO: Record<string, { name: string; sector: string; color: string }> = {
  // Technology
  'AAPL': { name: 'Apple', sector: 'Technology', color: 'from-gray-600 to-gray-800' },
  'MSFT': { name: 'Microsoft', sector: 'Technology', color: 'from-blue-500 to-blue-700' },
  'GOOGL': { name: 'Alphabet', sector: 'Technology', color: 'from-red-500 to-yellow-500' },
  'NVDA': { name: 'NVIDIA', sector: 'Technology', color: 'from-green-500 to-green-700' },
  'META': { name: 'Meta', sector: 'Technology', color: 'from-blue-400 to-blue-600' },
  'AVGO': { name: 'Broadcom', sector: 'Technology', color: 'from-red-600 to-red-800' },
  'ORCL': { name: 'Oracle', sector: 'Technology', color: 'from-red-500 to-red-700' },
  'CRM': { name: 'Salesforce', sector: 'Technology', color: 'from-blue-400 to-cyan-500' },
  'AMD': { name: 'AMD', sector: 'Technology', color: 'from-red-600 to-gray-800' },
  'INTC': { name: 'Intel', sector: 'Technology', color: 'from-blue-500 to-blue-700' },
  'CSCO': { name: 'Cisco', sector: 'Technology', color: 'from-blue-600 to-blue-800' },
  'IBM': { name: 'IBM', sector: 'Technology', color: 'from-blue-700 to-blue-900' },
  // Consumer
  'AMZN': { name: 'Amazon', sector: 'Consumer', color: 'from-orange-400 to-orange-600' },
  'WMT': { name: 'Walmart', sector: 'Consumer', color: 'from-blue-500 to-yellow-500' },
  'HD': { name: 'Home Depot', sector: 'Consumer', color: 'from-orange-500 to-orange-700' },
  'COST': { name: 'Costco', sector: 'Consumer', color: 'from-red-600 to-blue-600' },
  'NKE': { name: 'Nike', sector: 'Consumer', color: 'from-orange-500 to-red-500' },
  'MCD': { name: 'McDonald\'s', sector: 'Consumer', color: 'from-red-500 to-yellow-500' },
  'SBUX': { name: 'Starbucks', sector: 'Consumer', color: 'from-green-600 to-green-800' },
  'TGT': { name: 'Target', sector: 'Consumer', color: 'from-red-500 to-red-700' },
  // Finance
  'JPM': { name: 'JPMorgan', sector: 'Finance', color: 'from-blue-700 to-blue-900' },
  'BAC': { name: 'Bank of America', sector: 'Finance', color: 'from-red-600 to-blue-600' },
  'WFC': { name: 'Wells Fargo', sector: 'Finance', color: 'from-red-600 to-yellow-600' },
  'GS': { name: 'Goldman Sachs', sector: 'Finance', color: 'from-blue-600 to-blue-800' },
  'MS': { name: 'Morgan Stanley', sector: 'Finance', color: 'from-blue-500 to-blue-700' },
  'V': { name: 'Visa', sector: 'Finance', color: 'from-blue-600 to-yellow-500' },
  'MA': { name: 'Mastercard', sector: 'Finance', color: 'from-red-500 to-orange-500' },
  'AXP': { name: 'Amex', sector: 'Finance', color: 'from-blue-500 to-blue-700' },
  // Healthcare
  'JNJ': { name: 'J&J', sector: 'Healthcare', color: 'from-red-500 to-red-700' },
  'UNH': { name: 'UnitedHealth', sector: 'Healthcare', color: 'from-blue-500 to-blue-700' },
  'PFE': { name: 'Pfizer', sector: 'Healthcare', color: 'from-blue-400 to-blue-600' },
  'MRK': { name: 'Merck', sector: 'Healthcare', color: 'from-teal-500 to-teal-700' },
  'ABBV': { name: 'AbbVie', sector: 'Healthcare', color: 'from-blue-600 to-purple-600' },
  'LLY': { name: 'Eli Lilly', sector: 'Healthcare', color: 'from-red-500 to-red-700' },
  // Automotive & Industrial
  'TSLA': { name: 'Tesla', sector: 'Automotive', color: 'from-red-500 to-gray-800' },
  'F': { name: 'Ford', sector: 'Automotive', color: 'from-blue-600 to-blue-800' },
  'GM': { name: 'GM', sector: 'Automotive', color: 'from-blue-500 to-blue-700' },
  'CAT': { name: 'Caterpillar', sector: 'Industrial', color: 'from-yellow-500 to-yellow-700' },
  'BA': { name: 'Boeing', sector: 'Industrial', color: 'from-blue-600 to-blue-800' },
  'GE': { name: 'GE', sector: 'Industrial', color: 'from-blue-500 to-blue-700' },
  // Energy
  'XOM': { name: 'Exxon', sector: 'Energy', color: 'from-red-500 to-red-700' },
  'CVX': { name: 'Chevron', sector: 'Energy', color: 'from-blue-500 to-red-500' },
  // Entertainment & Communication
  'DIS': { name: 'Disney', sector: 'Entertainment', color: 'from-blue-500 to-blue-700' },
  'NFLX': { name: 'Netflix', sector: 'Entertainment', color: 'from-red-600 to-red-800' },
  'T': { name: 'AT&T', sector: 'Communication', color: 'from-blue-400 to-blue-600' },
  'VZ': { name: 'Verizon', sector: 'Communication', color: 'from-red-500 to-red-700' },
};

// Get random stocks from pool
const getRandomStocks = (count: number = 12): string[] => {
  const allSymbols = Object.keys(ALL_STOCKS_INFO);
  const shuffled = [...allSymbols].sort(() => Math.random() - 0.5);
  return shuffled.slice(0, count);
};

// Sector collections like Stash/Robinhood
const COLLECTIONS = [
  { id: 'tech', name: 'Tech Giants', emoji: '💻', description: 'Leading technology companies', symbols: ['AAPL', 'MSFT', 'GOOGL', 'META'] },
  { id: 'finance', name: 'Financial Power', emoji: '🏦', description: 'Major financial institutions', symbols: ['JPM', 'V', 'MA', 'GS'] },
  { id: 'health', name: 'Healthcare', emoji: '💊', description: 'Pharmaceutical & health leaders', symbols: ['JNJ', 'PFE', 'UNH', 'LLY'] },
  { id: 'consumer', name: 'Consumer Favorites', emoji: '🛒', description: 'Popular consumer brands', symbols: ['AMZN', 'NKE', 'SBUX', 'MCD'] },
];

const DiscoverPage: React.FC = () => {
  const [selectedCategory, setSelectedCategory] = useState<'all' | 'gainers' | 'losers'>('all');
  const [isLoading, setIsLoading] = useState(true);
  const [stocks, setStocks] = useState<Stock[]>([]);
  const [error, setError] = useState<string | null>(null);
  const [selectedSymbols] = useState<string[]>(() => getRandomStocks(12));

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

      if (!response.ok) throw new Error('Failed to fetch market data');

      const data = await response.json();
      const stockData: Stock[] = (data.quotes || []).map((quote: any) => {
        const info = ALL_STOCKS_INFO[quote.symbol] || { name: quote.symbol, sector: 'Unknown', color: 'from-gray-500 to-gray-700' };
        return {
          symbol: quote.symbol,
          name: info.name,
          price: quote.price || 0,
          change: quote.change || 0,
          changePercent: quote.change_percent || 0,
          volume: quote.volume || 0,
          sector: info.sector,
        };
      });

      setStocks(stockData);
      setError(null);
    } catch (err) {
      console.error('Error fetching market data:', err);
      setError('Unable to load market data');
    } finally {
      setIsLoading(false);
    }
  }, [selectedSymbols]);

  useEffect(() => {
    fetchMarketData();
    const interval = setInterval(fetchMarketData, 60000);
    return () => clearInterval(interval);
  }, [fetchMarketData]);

  const getFilteredStocks = () => {
    if (stocks.length === 0) return [];
    switch (selectedCategory) {
      case 'gainers': return [...stocks].filter(s => s.changePercent > 0).sort((a, b) => b.changePercent - a.changePercent);
      case 'losers': return [...stocks].filter(s => s.changePercent < 0).sort((a, b) => a.changePercent - b.changePercent);
      default: return stocks;
    }
  };

  const formatVolume = (num: number) => {
    if (num >= 1000000) return `${(num / 1000000).toFixed(1)}M`;
    if (num >= 1000) return `${(num / 1000).toFixed(1)}K`;
    return num.toString();
  };

  // Stock Card Component - Robinhood/Coinbase style
  const StockCard: React.FC<{ stock: Stock }> = ({ stock }) => {
    const info = ALL_STOCKS_INFO[stock.symbol] || { color: 'from-gray-500 to-gray-700' };
    const isPositive = stock.changePercent >= 0;

    return (
      <Link
        to={`/paper/trading/${stock.symbol}`}
        className="block bg-gray-800/50 hover:bg-gray-700/50 rounded-2xl p-4 transition-all duration-200 hover:scale-[1.02] hover:shadow-lg border border-gray-700/50"
      >
        <div className="flex items-center justify-between mb-3">
          <div className={`w-12 h-12 rounded-xl bg-gradient-to-br ${info.color} flex items-center justify-center shadow-lg`}>
            <span className="text-white font-bold text-sm">{stock.symbol.slice(0, 2)}</span>
          </div>
          <div className={`px-2.5 py-1 rounded-full text-xs font-semibold ${
            isPositive ? 'bg-green-500/20 text-green-400' : 'bg-red-500/20 text-red-400'
          }`}>
            {isPositive ? '+' : ''}{stock.changePercent.toFixed(2)}%
          </div>
        </div>
        <div className="mb-1">
          <h3 className="text-white font-semibold text-lg">{stock.symbol}</h3>
          <p className="text-gray-400 text-sm truncate">{stock.name}</p>
        </div>
        <div className="flex items-end justify-between mt-3">
          <span className="text-white text-xl font-bold">${stock.price.toFixed(2)}</span>
          <span className="text-gray-500 text-xs">Vol: {formatVolume(stock.volume)}</span>
        </div>
      </Link>
    );
  };

  // Collection Card - Stash style
  const CollectionCard: React.FC<{ collection: typeof COLLECTIONS[0] }> = ({ collection }) => (
    <div className="bg-gradient-to-br from-gray-800 to-gray-900 rounded-2xl p-5 border border-gray-700/50 hover:border-purple-500/50 transition-all cursor-pointer">
      <div className="flex items-center gap-3 mb-3">
        <span className="text-3xl">{collection.emoji}</span>
        <div>
          <h3 className="text-white font-semibold">{collection.name}</h3>
          <p className="text-gray-400 text-xs">{collection.description}</p>
        </div>
      </div>
      <div className="flex gap-2 flex-wrap">
        {collection.symbols.map(symbol => (
          <Link
            key={symbol}
            to={`/paper/trading/${symbol}`}
            className="bg-gray-700/50 hover:bg-purple-600/30 px-3 py-1.5 rounded-full text-xs text-gray-300 hover:text-white transition-colors"
          >
            {symbol}
          </Link>
        ))}
      </div>
    </div>
  );

  if (isLoading) {
    return (
      <div className="bg-gray-900 min-h-screen p-4 md:p-6">
        <div className="max-w-6xl mx-auto">
          <Skeleton variant="text" width="200px" height="32px" className="mb-2" />
          <Skeleton variant="text" width="300px" height="20px" className="mb-8" />
          <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-4 gap-4">
            {[...Array(8)].map((_, i) => (
              <div key={i} className="bg-gray-800/50 rounded-2xl p-4">
                <Skeleton variant="rectangular" width="48px" height="48px" className="rounded-xl mb-3" />
                <Skeleton variant="text" width="60%" height="20px" className="mb-1" />
                <Skeleton variant="text" width="80%" height="16px" className="mb-3" />
                <Skeleton variant="text" width="50%" height="24px" />
              </div>
            ))}
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="bg-gray-900 min-h-screen">
      {/* Hero Section */}
      <div className="bg-gradient-to-b from-purple-900/30 to-gray-900 px-4 md:px-6 pt-6 pb-8">
        <div className="max-w-6xl mx-auto">
          <h1 className="text-3xl md:text-4xl font-bold text-white mb-2">Discover</h1>
          <p className="text-gray-400">Find your next investment opportunity</p>
        </div>
      </div>

      <div className="max-w-6xl mx-auto px-4 md:px-6 -mt-2">
        {/* Quick Actions */}
        <div className="flex gap-3 mb-8 overflow-x-auto pb-2 scrollbar-hide">
          <Link to="/paper/trading" className="flex-shrink-0 bg-gradient-to-r from-purple-600 to-blue-600 hover:from-purple-500 hover:to-blue-500 text-white px-5 py-3 rounded-xl font-medium transition-all flex items-center gap-2 shadow-lg shadow-purple-500/20">
            <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M13 7h8m0 0v8m0-8l-8 8-4-4-6 6" />
            </svg>
            Start Trading
          </Link>
          <Link to="/paper/portfolio" className="flex-shrink-0 bg-gray-800 hover:bg-gray-700 text-white px-5 py-3 rounded-xl font-medium transition-all flex items-center gap-2 border border-gray-700">
            <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z" />
            </svg>
            Portfolio
          </Link>
        </div>

        {/* Collections Section - Like Stash */}
        <section className="mb-10">
          <h2 className="text-xl font-bold text-white mb-4 flex items-center gap-2">
            <span className="text-2xl">📦</span> Collections
          </h2>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            {COLLECTIONS.map(collection => (
              <CollectionCard key={collection.id} collection={collection} />
            ))}
          </div>
        </section>

        {/* Market Movers */}
        <section className="mb-10">
          <div className="flex items-center justify-between mb-4">
            <h2 className="text-xl font-bold text-white flex items-center gap-2">
              <span className="text-2xl">📈</span> Market Movers
            </h2>
            <div className="flex gap-1 bg-gray-800 p-1 rounded-xl">
              {[
                { key: 'all', label: 'All' },
                { key: 'gainers', label: 'Gainers' },
                { key: 'losers', label: 'Losers' },
              ].map(cat => (
                <button
                  key={cat.key}
                  onClick={() => setSelectedCategory(cat.key as any)}
                  className={`px-4 py-1.5 rounded-lg text-sm font-medium transition-all ${
                    selectedCategory === cat.key
                      ? 'bg-purple-600 text-white'
                      : 'text-gray-400 hover:text-white'
                  }`}
                >
                  {cat.label}
                </button>
              ))}
            </div>
          </div>

          {error ? (
            <div className="bg-gray-800/50 rounded-2xl p-8 text-center">
              <div className="w-16 h-16 bg-red-500/20 rounded-full flex items-center justify-center mx-auto mb-4">
                <svg className="w-8 h-8 text-red-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M12 8v4m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
                </svg>
              </div>
              <h3 className="text-white font-medium mb-2">Unable to Load Data</h3>
              <p className="text-gray-400 text-sm mb-4">{error}</p>
              <button
                onClick={() => { setIsLoading(true); fetchMarketData(); }}
                className="bg-purple-600 hover:bg-purple-700 text-white px-6 py-2 rounded-xl text-sm font-medium transition-colors"
              >
                Try Again
              </button>
            </div>
          ) : getFilteredStocks().length === 0 ? (
            <div className="bg-gray-800/50 rounded-2xl p-8 text-center">
              <span className="text-5xl mb-4 block">📊</span>
              <h3 className="text-white font-medium mb-2">No Stocks Found</h3>
              <p className="text-gray-400 text-sm">
                {selectedCategory === 'gainers' ? 'No gainers at the moment' :
                 selectedCategory === 'losers' ? 'No losers at the moment' : 'Loading...'}
              </p>
            </div>
          ) : (
            <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-4 gap-4">
              {getFilteredStocks().map(stock => (
                <StockCard key={stock.symbol} stock={stock} />
              ))}
            </div>
          )}
        </section>

        {/* Paper Trading Banner */}
        <section className="mb-10">
          <div className="bg-gradient-to-r from-purple-900/50 to-blue-900/50 rounded-2xl p-6 border border-purple-500/20">
            <div className="flex flex-col md:flex-row items-center justify-between gap-4">
              <div className="text-center md:text-left">
                <h3 className="text-xl font-bold text-white mb-1">Practice with Paper Trading</h3>
                <p className="text-gray-300">Start with $250,000 in virtual funds - no risk, real learning</p>
              </div>
              <Link
                to="/paper/trading"
                className="bg-white hover:bg-gray-100 text-purple-700 px-6 py-3 rounded-xl font-semibold transition-colors whitespace-nowrap"
              >
                Get Started Free
              </Link>
            </div>
          </div>
        </section>

        {/* Popular Stocks Horizontal Scroll - Coinbase style */}
        <section className="mb-10">
          <h2 className="text-xl font-bold text-white mb-4 flex items-center gap-2">
            <span className="text-2xl">🔥</span> Popular Today
          </h2>
          <div className="flex gap-3 overflow-x-auto pb-4 scrollbar-hide">
            {stocks.slice(0, 6).map(stock => {
              const info = ALL_STOCKS_INFO[stock.symbol] || { color: 'from-gray-500 to-gray-700' };
              return (
                <Link
                  key={stock.symbol}
                  to={`/paper/trading/${stock.symbol}`}
                  className="flex-shrink-0 w-40 bg-gray-800/50 hover:bg-gray-700/50 rounded-xl p-4 transition-all border border-gray-700/50"
                >
                  <div className={`w-10 h-10 rounded-lg bg-gradient-to-br ${info.color} flex items-center justify-center mb-2`}>
                    <span className="text-white font-bold text-xs">{stock.symbol.slice(0, 2)}</span>
                  </div>
                  <h4 className="text-white font-semibold text-sm">{stock.symbol}</h4>
                  <p className="text-gray-400 text-xs truncate mb-2">{stock.name}</p>
                  <div className="flex items-center justify-between">
                    <span className="text-white font-medium">${stock.price.toFixed(2)}</span>
                    <span className={`text-xs font-medium ${stock.changePercent >= 0 ? 'text-green-400' : 'text-red-400'}`}>
                      {stock.changePercent >= 0 ? '+' : ''}{stock.changePercent.toFixed(1)}%
                    </span>
                  </div>
                </Link>
              );
            })}
          </div>
        </section>
      </div>
    </div>
  );
};

export default DiscoverPage;
