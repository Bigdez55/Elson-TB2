import React, { useState } from 'react';
import OrderForm from './OrderForm';
import Portfolio from './Portfolio';
import LiveQuoteDisplay from './LiveQuoteDisplay';
import TradeHistory from './TradeHistory';
import Watchlist from './Watchlist';

const TradingDashboard: React.FC = () => {
  const [selectedSymbol, setSelectedSymbol] = useState('AAPL');
  const [currentPrice, setCurrentPrice] = useState(150.25);
  const [watchlistSymbols] = useState(['AAPL', 'MSFT', 'GOOGL', 'TSLA', 'NVDA']);

  const handleSymbolSelect = (symbol: string) => {
    setSelectedSymbol(symbol);
    // In a real app, you'd fetch the current price for this symbol
    setCurrentPrice(Math.random() * 200 + 50);
  };

  const handleQuoteUpdate = (quotes: any) => {
    // Update current price when live quotes change
    if (quotes[selectedSymbol]) {
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
            <OrderForm 
              symbol={selectedSymbol}
              currentPrice={currentPrice}
              availableBalance={10000}
            />
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
              <button 
                className="bg-blue-600 text-white py-2 px-4 rounded hover:bg-blue-700 transition-colors"
                onClick={() => setSelectedSymbol('AAPL')}
              >
                Trade AAPL
              </button>
              <button 
                className="bg-green-600 text-white py-2 px-4 rounded hover:bg-green-700 transition-colors"
                onClick={() => setSelectedSymbol('TSLA')}
              >
                Trade TSLA
              </button>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default TradingDashboard;