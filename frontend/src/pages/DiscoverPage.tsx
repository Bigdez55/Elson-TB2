import React, { useState, useEffect, useCallback } from 'react';
import { Link } from 'react-router-dom';
import { Skeleton } from '../components/common/Skeleton';
import { RefreshCw, TrendingUp, TrendingDown, Flame, Zap, Building2, Heart, Car, Cpu } from 'lucide-react';

interface Stock {
  symbol: string;
  name: string;
  price: number;
  change: number;
  changePercent: number;
  volume: number;
  sector: string;
}

// Large pool of 60+ popular stocks organized by sector
const STOCK_UNIVERSE: Record<string, { name: string; sector: string }> = {
  // Technology (15)
  'AAPL': { name: 'Apple Inc', sector: 'Technology' },
  'MSFT': { name: 'Microsoft', sector: 'Technology' },
  'GOOGL': { name: 'Alphabet', sector: 'Technology' },
  'NVDA': { name: 'NVIDIA', sector: 'Technology' },
  'META': { name: 'Meta Platforms', sector: 'Technology' },
  'AVGO': { name: 'Broadcom', sector: 'Technology' },
  'ORCL': { name: 'Oracle', sector: 'Technology' },
  'CRM': { name: 'Salesforce', sector: 'Technology' },
  'AMD': { name: 'AMD', sector: 'Technology' },
  'INTC': { name: 'Intel', sector: 'Technology' },
  'CSCO': { name: 'Cisco', sector: 'Technology' },
  'IBM': { name: 'IBM', sector: 'Technology' },
  'ADBE': { name: 'Adobe', sector: 'Technology' },
  'NOW': { name: 'ServiceNow', sector: 'Technology' },
  'QCOM': { name: 'Qualcomm', sector: 'Technology' },
  // Consumer (12)
  'AMZN': { name: 'Amazon', sector: 'Consumer' },
  'WMT': { name: 'Walmart', sector: 'Consumer' },
  'HD': { name: 'Home Depot', sector: 'Consumer' },
  'COST': { name: 'Costco', sector: 'Consumer' },
  'NKE': { name: 'Nike', sector: 'Consumer' },
  'MCD': { name: 'McDonalds', sector: 'Consumer' },
  'SBUX': { name: 'Starbucks', sector: 'Consumer' },
  'TGT': { name: 'Target', sector: 'Consumer' },
  'LOW': { name: 'Lowes', sector: 'Consumer' },
  'TJX': { name: 'TJX Companies', sector: 'Consumer' },
  'BKNG': { name: 'Booking Holdings', sector: 'Consumer' },
  'CMG': { name: 'Chipotle', sector: 'Consumer' },
  // Finance (12)
  'JPM': { name: 'JPMorgan', sector: 'Finance' },
  'BAC': { name: 'Bank of America', sector: 'Finance' },
  'WFC': { name: 'Wells Fargo', sector: 'Finance' },
  'GS': { name: 'Goldman Sachs', sector: 'Finance' },
  'MS': { name: 'Morgan Stanley', sector: 'Finance' },
  'V': { name: 'Visa', sector: 'Finance' },
  'MA': { name: 'Mastercard', sector: 'Finance' },
  'AXP': { name: 'American Express', sector: 'Finance' },
  'BLK': { name: 'BlackRock', sector: 'Finance' },
  'C': { name: 'Citigroup', sector: 'Finance' },
  'SCHW': { name: 'Charles Schwab', sector: 'Finance' },
  'PYPL': { name: 'PayPal', sector: 'Finance' },
  // Healthcare (10)
  'JNJ': { name: 'Johnson & Johnson', sector: 'Healthcare' },
  'UNH': { name: 'UnitedHealth', sector: 'Healthcare' },
  'PFE': { name: 'Pfizer', sector: 'Healthcare' },
  'MRK': { name: 'Merck', sector: 'Healthcare' },
  'ABBV': { name: 'AbbVie', sector: 'Healthcare' },
  'LLY': { name: 'Eli Lilly', sector: 'Healthcare' },
  'TMO': { name: 'Thermo Fisher', sector: 'Healthcare' },
  'ABT': { name: 'Abbott Labs', sector: 'Healthcare' },
  'BMY': { name: 'Bristol-Myers', sector: 'Healthcare' },
  'AMGN': { name: 'Amgen', sector: 'Healthcare' },
  // Automotive & Industrial (8)
  'TSLA': { name: 'Tesla', sector: 'Automotive' },
  'F': { name: 'Ford', sector: 'Automotive' },
  'GM': { name: 'General Motors', sector: 'Automotive' },
  'CAT': { name: 'Caterpillar', sector: 'Industrial' },
  'BA': { name: 'Boeing', sector: 'Industrial' },
  'GE': { name: 'GE Aerospace', sector: 'Industrial' },
  'HON': { name: 'Honeywell', sector: 'Industrial' },
  'UPS': { name: 'UPS', sector: 'Industrial' },
  // Energy (6)
  'XOM': { name: 'Exxon Mobil', sector: 'Energy' },
  'CVX': { name: 'Chevron', sector: 'Energy' },
  'COP': { name: 'ConocoPhillips', sector: 'Energy' },
  'SLB': { name: 'Schlumberger', sector: 'Energy' },
  'EOG': { name: 'EOG Resources', sector: 'Energy' },
  'OXY': { name: 'Occidental', sector: 'Energy' },
  // Entertainment (6)
  'DIS': { name: 'Disney', sector: 'Entertainment' },
  'NFLX': { name: 'Netflix', sector: 'Entertainment' },
  'CMCSA': { name: 'Comcast', sector: 'Entertainment' },
  'T': { name: 'AT&T', sector: 'Communication' },
  'VZ': { name: 'Verizon', sector: 'Communication' },
  'TMUS': { name: 'T-Mobile', sector: 'Communication' },
};

// Get random selection from array
const getRandomSelection = <T,>(arr: T[], count: number): T[] => {
  const shuffled = [...arr].sort(() => Math.random() - 0.5);
  return shuffled.slice(0, count);
};

// Get stocks by sector
const getStocksBySector = (sector: string): string[] => {
  return Object.entries(STOCK_UNIVERSE)
    .filter(([_, info]) => info.sector === sector)
    .map(([symbol]) => symbol);
};

const DiscoverPage: React.FC = () => {
  const [stocks, setStocks] = useState<Stock[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [lastRefresh, setLastRefresh] = useState<Date>(new Date());
  const [activeFilter, setActiveFilter] = useState<'all' | 'gainers' | 'losers'>('all');
  const [refreshing, setRefreshing] = useState(false);

  // Generate random stock selections on each render/refresh
  const [selections, setSelections] = useState(() => ({
    trending: getRandomSelection(Object.keys(STOCK_UNIVERSE), 12),
    techGiants: getRandomSelection(getStocksBySector('Technology'), 6),
    finance: getRandomSelection(getStocksBySector('Finance'), 6),
    healthcare: getRandomSelection(getStocksBySector('Healthcare'), 5),
    consumer: getRandomSelection(getStocksBySector('Consumer'), 5),
  }));

  // Fetch market data from backend
  const fetchMarketData = useCallback(async (symbols: string[]) => {
    try {
      const token = localStorage.getItem('token');
      const baseUrl = process.env.REACT_APP_API_URL || '/api/v1';

      const response = await fetch(`${baseUrl}/market-data/quotes`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${token}`,
        },
        body: JSON.stringify(symbols),
      });

      if (!response.ok) {
        throw new Error('Failed to fetch market data');
      }

      const data = await response.json();
      return (data.quotes || []).map((quote: any) => {
        const info = STOCK_UNIVERSE[quote.symbol] || { name: quote.symbol, sector: 'Unknown' };
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
    } catch (err) {
      console.error('Error fetching market data:', err);
      throw err;
    }
  }, []);

  // Load all stocks
  const loadAllStocks = useCallback(async () => {
    setIsLoading(true);
    setError(null);
    try {
      // Combine all unique symbols
      const allSymbols = Array.from(new Set([
        ...selections.trending,
        ...selections.techGiants,
        ...selections.finance,
        ...selections.healthcare,
        ...selections.consumer,
      ]));

      const stockData = await fetchMarketData(allSymbols);
      setStocks(stockData);
      setLastRefresh(new Date());
    } catch (err) {
      setError('Unable to load market data. Please try again.');
    } finally {
      setIsLoading(false);
      setRefreshing(false);
    }
  }, [fetchMarketData, selections]);

  // Refresh with new random stocks
  const handleRefresh = () => {
    setRefreshing(true);
    // Generate new random selections
    setSelections({
      trending: getRandomSelection(Object.keys(STOCK_UNIVERSE), 12),
      techGiants: getRandomSelection(getStocksBySector('Technology'), 6),
      finance: getRandomSelection(getStocksBySector('Finance'), 6),
      healthcare: getRandomSelection(getStocksBySector('Healthcare'), 5),
      consumer: getRandomSelection(getStocksBySector('Consumer'), 5),
    });
  };

  // Load on mount and when selections change
  useEffect(() => {
    loadAllStocks();
  }, [loadAllStocks]);

  // Auto-refresh prices every 30 seconds
  useEffect(() => {
    const interval = setInterval(() => {
      if (!isLoading) {
        loadAllStocks();
      }
    }, 30000);
    return () => clearInterval(interval);
  }, [loadAllStocks, isLoading]);

  // Get stock by symbol
  const getStock = (symbol: string): Stock | undefined => stocks.find(s => s.symbol === symbol);

  // Get filtered stocks
  const getFilteredStocks = (symbols: string[]) => {
    const filtered = symbols.map(s => getStock(s)).filter(Boolean) as Stock[];
    if (activeFilter === 'gainers') return filtered.filter(s => s.changePercent > 0);
    if (activeFilter === 'losers') return filtered.filter(s => s.changePercent < 0);
    return filtered;
  };

  // Top movers
  const topGainers = [...stocks].filter(s => s.changePercent > 0).sort((a, b) => b.changePercent - a.changePercent).slice(0, 5);
  const topLosers = [...stocks].filter(s => s.changePercent < 0).sort((a, b) => a.changePercent - b.changePercent).slice(0, 5);

  // Stock card component
  const StockCard = ({ stock, size = 'normal' }: { stock: Stock; size?: 'small' | 'normal' | 'large' }) => {
    const isPositive = stock.changePercent >= 0;
    const sizeClasses = {
      small: 'p-3',
      normal: 'p-4',
      large: 'p-5',
    };

    return (
      <Link
        to={`/paper/trading/${stock.symbol}`}
        className={`block bg-gray-800 hover:bg-gray-750 rounded-xl transition-all hover:scale-[1.02] ${sizeClasses[size]}`}
      >
        <div className="flex items-center justify-between mb-2">
          <div className="flex items-center space-x-3">
            <div className={`w-10 h-10 rounded-lg flex items-center justify-center font-bold text-white text-sm
              ${stock.sector === 'Technology' ? 'bg-gradient-to-br from-blue-500 to-purple-600' :
                stock.sector === 'Finance' ? 'bg-gradient-to-br from-green-500 to-emerald-600' :
                stock.sector === 'Healthcare' ? 'bg-gradient-to-br from-pink-500 to-rose-600' :
                stock.sector === 'Consumer' ? 'bg-gradient-to-br from-orange-500 to-amber-600' :
                stock.sector === 'Automotive' ? 'bg-gradient-to-br from-red-500 to-rose-600' :
                'bg-gradient-to-br from-gray-500 to-gray-600'}`}
            >
              {stock.symbol.substring(0, 2)}
            </div>
            <div>
              <h3 className="text-white font-semibold">{stock.symbol}</h3>
              <p className="text-gray-400 text-xs truncate max-w-[100px]">{stock.name}</p>
            </div>
          </div>
          <div className={`flex items-center px-2 py-1 rounded-lg text-xs font-medium ${
            isPositive ? 'bg-green-900/50 text-green-400' : 'bg-red-900/50 text-red-400'
          }`}>
            {isPositive ? <TrendingUp className="w-3 h-3 mr-1" /> : <TrendingDown className="w-3 h-3 mr-1" />}
            {isPositive ? '+' : ''}{stock.changePercent.toFixed(2)}%
          </div>
        </div>
        <div className="flex items-end justify-between">
          <span className="text-white text-lg font-bold">${stock.price.toFixed(2)}</span>
          <span className={`text-sm ${isPositive ? 'text-green-400' : 'text-red-400'}`}>
            {isPositive ? '+' : ''}${stock.change.toFixed(2)}
          </span>
        </div>
      </Link>
    );
  };

  // Section header component
  const SectionHeader = ({ icon: Icon, title, subtitle }: { icon: any; title: string; subtitle?: string }) => (
    <div className="flex items-center space-x-3 mb-4">
      <div className="w-10 h-10 bg-purple-900/50 rounded-lg flex items-center justify-center">
        <Icon className="w-5 h-5 text-purple-400" />
      </div>
      <div>
        <h2 className="text-lg font-semibold text-white">{title}</h2>
        {subtitle && <p className="text-xs text-gray-400">{subtitle}</p>}
      </div>
    </div>
  );

  if (isLoading && stocks.length === 0) {
    return (
      <div className="bg-gray-900 min-h-screen p-4 md:p-6">
        <div className="max-w-7xl mx-auto">
          <div className="mb-6">
            <Skeleton variant="text" width="200px" height="32px" className="mb-2" />
            <Skeleton variant="text" width="300px" height="20px" />
          </div>
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-8">
            {[1, 2, 3, 4].map(i => (
              <Skeleton key={i} variant="rectangular" height="120px" className="rounded-xl" />
            ))}
          </div>
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
            {[1, 2, 3, 4, 5, 6].map(i => (
              <Skeleton key={i} variant="rectangular" height="100px" className="rounded-xl" />
            ))}
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="bg-gray-900 min-h-screen p-4 md:p-6">
      <div className="max-w-7xl mx-auto">
        {/* Header */}
        <div className="flex flex-col md:flex-row md:items-center md:justify-between mb-6">
          <div>
            <h1 className="text-2xl md:text-3xl font-bold text-white mb-1">Discover</h1>
            <p className="text-gray-400 text-sm">
              Live market data updated {lastRefresh.toLocaleTimeString()}
            </p>
          </div>
          <button
            onClick={handleRefresh}
            disabled={refreshing}
            className={`mt-4 md:mt-0 flex items-center space-x-2 px-4 py-2 rounded-lg transition-colors ${
              refreshing ? 'bg-gray-700 text-gray-400' : 'bg-purple-600 hover:bg-purple-700 text-white'
            }`}
          >
            <RefreshCw className={`w-4 h-4 ${refreshing ? 'animate-spin' : ''}`} />
            <span>{refreshing ? 'Refreshing...' : 'Show New Stocks'}</span>
          </button>
        </div>

        {error && (
          <div className="bg-red-900/30 border border-red-500/50 rounded-xl p-4 mb-6">
            <p className="text-red-400">{error}</p>
            <button
              onClick={handleRefresh}
              className="mt-2 text-sm text-red-300 hover:text-white"
            >
              Try again
            </button>
          </div>
        )}

        {/* Market Movers - Horizontal Scroll */}
        <div className="mb-8">
          <SectionHeader icon={Zap} title="Market Movers" subtitle="Today's biggest moves" />
          <div className="flex space-x-4 overflow-x-auto pb-4 -mx-4 px-4 scrollbar-hide">
            {[...topGainers, ...topLosers].map((stock) => (
              <div key={stock.symbol} className="flex-shrink-0 w-40">
                <StockCard stock={stock} size="small" />
              </div>
            ))}
          </div>
        </div>

        {/* Filter Tabs */}
        <div className="flex space-x-2 mb-6 overflow-x-auto pb-2">
          {[
            { key: 'all', label: 'All Stocks', icon: Flame },
            { key: 'gainers', label: 'Gainers', icon: TrendingUp },
            { key: 'losers', label: 'Losers', icon: TrendingDown },
          ].map(({ key, label, icon: Icon }) => (
            <button
              key={key}
              onClick={() => setActiveFilter(key as any)}
              className={`flex items-center space-x-2 px-4 py-2 rounded-lg whitespace-nowrap transition-colors ${
                activeFilter === key
                  ? 'bg-purple-600 text-white'
                  : 'bg-gray-800 text-gray-400 hover:bg-gray-700'
              }`}
            >
              <Icon className="w-4 h-4" />
              <span>{label}</span>
            </button>
          ))}
        </div>

        {/* Trending Section */}
        <div className="mb-8">
          <SectionHeader icon={Flame} title="Trending Now" subtitle="Popular stocks today" />
          <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-4 gap-4">
            {getFilteredStocks(selections.trending).slice(0, 8).map((stock) => (
              <StockCard key={stock.symbol} stock={stock} />
            ))}
          </div>
        </div>

        {/* Collections Grid */}
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-8 mb-8">
          {/* Tech Giants */}
          <div className="bg-gray-800/50 rounded-2xl p-5">
            <SectionHeader icon={Cpu} title="Tech Giants" subtitle="Leading technology companies" />
            <div className="grid grid-cols-2 gap-3">
              {getFilteredStocks(selections.techGiants).map((stock) => (
                <StockCard key={stock.symbol} stock={stock} size="small" />
              ))}
            </div>
          </div>

          {/* Finance */}
          <div className="bg-gray-800/50 rounded-2xl p-5">
            <SectionHeader icon={Building2} title="Finance" subtitle="Banks & financial services" />
            <div className="grid grid-cols-2 gap-3">
              {getFilteredStocks(selections.finance).map((stock) => (
                <StockCard key={stock.symbol} stock={stock} size="small" />
              ))}
            </div>
          </div>

          {/* Healthcare */}
          <div className="bg-gray-800/50 rounded-2xl p-5">
            <SectionHeader icon={Heart} title="Healthcare" subtitle="Pharma & medical" />
            <div className="grid grid-cols-2 gap-3">
              {getFilteredStocks(selections.healthcare).map((stock) => (
                <StockCard key={stock.symbol} stock={stock} size="small" />
              ))}
            </div>
          </div>

          {/* Consumer */}
          <div className="bg-gray-800/50 rounded-2xl p-5">
            <SectionHeader icon={Car} title="Consumer & Retail" subtitle="Consumer goods & services" />
            <div className="grid grid-cols-2 gap-3">
              {getFilteredStocks(selections.consumer).map((stock) => (
                <StockCard key={stock.symbol} stock={stock} size="small" />
              ))}
            </div>
          </div>
        </div>

        {/* Paper Trading CTA */}
        <div className="bg-gradient-to-r from-purple-900 to-blue-900 rounded-2xl p-6 text-center">
          <h3 className="text-xl font-bold text-white mb-2">Start Paper Trading</h3>
          <p className="text-gray-300 mb-4">
            Practice with $100,000 in virtual funds - no risk, real market data
          </p>
          <Link
            to="/paper/trading"
            className="inline-block bg-white text-purple-900 font-semibold px-6 py-3 rounded-lg hover:bg-gray-100 transition-colors"
          >
            Open Trading Platform
          </Link>
        </div>
      </div>
    </div>
  );
};

export default DiscoverPage;
