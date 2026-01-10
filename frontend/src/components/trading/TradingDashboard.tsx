import React, { useState } from 'react';
import OrderForm from './OrderForm';
import Portfolio from './Portfolio';
import LiveQuoteDisplay from './LiveQuoteDisplay';
import TradeHistory from './TradeHistory';
import Watchlist from './Watchlist';
import { useTradingContext } from '../../contexts/TradingContext';
import { useGetPortfolioQuery } from '../../services/tradingApi';

const TradingDashboard: React.FC = () => {
  const { mode } = useTradingContext();
  const [selectedSymbol, setSelectedSymbol] = useState<string | null>(null);
  const [currentPrice, setCurrentPrice] = useState<number | null>(null);
  const [watchlistSymbols] = useState(['AAPL', 'MSFT', 'GOOGL', 'TSLA', 'NVDA']);

  // Fetch portfolio data to get available balance
  const { data: portfolioData } = useGetPortfolioQuery({ mode });
  const availableBalance = portfolioData?.cash_balance ?? 0;

  const handleSymbolSelect = (symbol: string) => {
    setSelectedSymbol(symbol);
    // Price will be updated via handleQuoteUpdate when LiveQuoteDisplay fetches the quote
  };

  const handleQuoteUpdate = (quotes: any) => {
    // Update current price when live quotes change
    if (selectedSymbol && quotes[selectedSymbol]) {
      setCurrentPrice(quotes[selectedSymbol].price);
    }
  };

  return (
    <div className="min-h-screen bg-gray-900 p-4">
      <div className="max-w-7xl mx-auto">
        <h1 className="text-3xl font-bold text-white mb-8">Personal Trading Dashboard</h1>
        
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          {/* Left Column - Portfolio & Order Form */}
          <div className="lg:col-span-1 space-y-6">
            {/* Portfolio Overview */}
            <Portfolio />
            
            {/* Order Form */}
            {selectedSymbol && currentPrice !== null ? (
              <OrderForm
                symbol={selectedSymbol}
                currentPrice={currentPrice}
                availableBalance={availableBalance}
              />
            ) : (
              <div className="bg-gray-800 rounded-lg p-6 text-center">
                <p className="text-gray-400">Select a symbol from the watchlist to place an order</p>
              </div>
            )}
          </div>

          {/* Middle Column - Live Quotes & Watchlist */}
          <div className="lg:col-span-1 space-y-6">
            {/* Live Market Data */}
            <LiveQuoteDisplay 
              symbols={watchlistSymbols}
              onQuoteUpdate={handleQuoteUpdate}
              className="h-80"
            />
            
            {/* Watchlist */}
            <Watchlist onSymbolSelect={handleSymbolSelect} />
          </div>

          {/* Right Column - Trade History */}
          <div className="lg:col-span-1">
            <TradeHistory />
          </div>
        </div>

        {/* Mobile-friendly layout for smaller screens */}
        <div className="lg:hidden mt-8">
          <div className="bg-gray-800 rounded-lg p-4">
            <h3 className="text-lg font-semibold text-white mb-4">Quick Actions</h3>
            <div className="grid grid-cols-2 gap-4">
              {watchlistSymbols.slice(0, 4).map((symbol) => (
                <button
                  key={symbol}
                  className={`py-2 px-4 rounded transition-colors ${
                    selectedSymbol === symbol
                      ? 'bg-purple-600 text-white'
                      : 'bg-gray-700 text-white hover:bg-gray-600'
                  }`}
                  onClick={() => handleSymbolSelect(symbol)}
                >
                  Trade {symbol}
                </button>
              ))}
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default TradingDashboard;