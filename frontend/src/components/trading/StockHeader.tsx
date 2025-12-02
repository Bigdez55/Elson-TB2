import React from 'react';
import { Badge } from '../common/Badge';

interface StockHeaderProps {
  symbol: string;
  companyName: string;
  exchange: string;
  sector: string;
  currentPrice: number;
  priceChange: number;
  priceChangePercent: number;
  afterHoursPrice?: number;
  afterHoursChange?: number;
  afterHoursChangePercent?: number;
  marketCap?: string;
  peRatio?: number;
  weekRange52?: { low: number; high: number };
  dividendYield?: string;
  onAddToWatchlist?: () => void;
  onShare?: () => void;
}

export const StockHeader: React.FC<StockHeaderProps> = ({
  symbol,
  companyName,
  exchange,
  sector,
  currentPrice,
  priceChange,
  priceChangePercent,
  afterHoursPrice,
  afterHoursChange,
  afterHoursChangePercent,
  marketCap = "N/A",
  peRatio,
  weekRange52,
  dividendYield = "N/A",
  onAddToWatchlist,
  onShare,
}) => {
  const isPositiveChange = priceChange >= 0;
  const isAfterHoursPositive = afterHoursChange ? afterHoursChange >= 0 : false;

  const getSymbolIcon = (symbol: string) => {
    // You can customize this to return different icons for different symbols
    const symbolColors = {
      'TSLA': 'bg-green-900 text-green-300',
      'AAPL': 'bg-blue-900 text-blue-300',
      'MSFT': 'bg-purple-900 text-purple-300',
      'NVDA': 'bg-yellow-900 text-yellow-300',
    };
    
    return symbolColors[symbol as keyof typeof symbolColors] || 'bg-gray-900 text-gray-300';
  };

  return (
    <div className="space-y-6">
      {/* Stock Info Header */}
      <div className="flex justify-between items-start">
        <div>
          <div className="flex items-center">
            <div className={`h-10 w-10 rounded-md flex items-center justify-center font-bold text-sm mr-3 ${getSymbolIcon(symbol)}`}>
              {symbol}
            </div>
            <div>
              <h1 className="text-2xl font-bold text-white">{companyName}</h1>
              <p className="text-gray-400">{exchange}: {symbol} • {sector}</p>
            </div>
          </div>
        </div>
        <div className="flex space-x-3">
          <button 
            onClick={onAddToWatchlist}
            className="bg-gray-700 hover:bg-gray-600 text-white px-3 py-2 rounded-lg flex items-center transition-colors"
          >
            <svg className="h-4 w-4 mr-1" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M4.318 6.318a4.5 4.5 0 000 6.364L12 20.364l7.682-7.682a4.5 4.5 0 00-6.364-6.364L12 7.636l-1.318-1.318a4.5 4.5 0 00-6.364 0z" />
            </svg>
            Add to Watchlist
          </button>
          <button 
            onClick={onShare}
            className="bg-gray-700 hover:bg-gray-600 text-white px-3 py-2 rounded-lg flex items-center transition-colors"
          >
            <svg className="h-4 w-4 mr-1" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M8.684 13.342C8.886 12.938 9 12.482 9 12c0-.482-.114-.938-.316-1.342m0 2.684a3 3 0 110-2.684m0 2.684l6.632 3.316m-6.632-6l6.632-3.316m0 0a3 3 0 105.367-2.684 3 3 0 00-5.367 2.684zm0 9.316a3 3 0 105.368 2.684 3 3 0 00-5.368-2.684z" />
            </svg>
            Share
          </button>
        </div>
      </div>

      {/* Stock Price & Stats */}
      <div className="grid grid-cols-1 lg:grid-cols-4 gap-6">
        <div className="bg-gray-900 rounded-xl p-6 lg:col-span-2">
          <div className="flex justify-between items-center">
            <div>
              <h2 className="text-3xl font-bold text-white">${currentPrice.toFixed(2)}</h2>
              <div className="flex items-center">
                <span className={`font-medium mr-2 ${isPositiveChange ? 'text-green-400' : 'text-red-400'}`}>
                  {isPositiveChange ? '+' : ''}${priceChange.toFixed(2)} ({priceChangePercent.toFixed(2)}%)
                </span>
                <span className="text-gray-400 text-sm">Today</span>
              </div>
            </div>
            {afterHoursPrice && (
              <div className="text-right">
                <div className={`font-medium ${isAfterHoursPositive ? 'text-green-400' : 'text-red-400'}`}>
                  <span className="text-sm">After Hours:</span> ${afterHoursPrice.toFixed(2)}
                </div>
                {afterHoursChange && afterHoursChangePercent && (
                  <div className="text-gray-400 text-sm">
                    {isAfterHoursPositive ? '+' : ''}${afterHoursChange.toFixed(2)} ({afterHoursChangePercent.toFixed(2)}%)
                  </div>
                )}
              </div>
            )}
          </div>
        </div>

        <div className="bg-gray-900 rounded-xl p-4">
          <h3 className="text-gray-400 text-sm mb-1">Market Cap</h3>
          <p className="text-white font-medium">{marketCap}</p>
          <div className="mt-2">
            <h3 className="text-gray-400 text-sm mb-1">P/E Ratio</h3>
            <p className="text-white font-medium">{peRatio ? peRatio.toFixed(2) : 'N/A'}</p>
          </div>
        </div>

        <div className="bg-gray-900 rounded-xl p-4">
          <h3 className="text-gray-400 text-sm mb-1">52 Week Range</h3>
          <p className="text-white font-medium">
            {weekRange52 ? `$${weekRange52.low.toFixed(2)} - $${weekRange52.high.toFixed(2)}` : 'N/A'}
          </p>
          <div className="mt-2">
            <h3 className="text-gray-400 text-sm mb-1">Dividend Yield</h3>
            <p className="text-white font-medium">{dividendYield}</p>
          </div>
        </div>
      </div>
    </div>
  );
};