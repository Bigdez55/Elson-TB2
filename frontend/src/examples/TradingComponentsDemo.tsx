import React, { useState } from 'react';
import {
  OrderForm,
  Portfolio,
  LiveQuoteDisplay,
  TradeHistory,
  Watchlist,
  TradingDashboard
} from '../components/trading';

/**
 * Demo component showing how to use the integrated trading UI components
 * This demonstrates the key features for personal trading use cases
 */
const TradingComponentsDemo: React.FC = () => {
  const [selectedSymbol, setSelectedSymbol] = useState('AAPL');
  const [currentPrice, setCurrentPrice] = useState(150.25);

  return (
    <div className="min-h-screen bg-gray-900 p-4">
      <div className="max-w-6xl mx-auto">
        <h1 className="text-3xl font-bold text-white mb-8">
          Personal Trading UI Components Demo
        </h1>
        
        <div className="space-y-8">
          {/* Complete Trading Dashboard */}
          <section>
            <h2 className="text-2xl font-semibold text-white mb-4">Complete Trading Dashboard</h2>
            <TradingDashboard />
          </section>

          {/* Individual Component Examples */}
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
            
            {/* Order Form Example */}
            <section>
              <h3 className="text-xl font-semibold text-white mb-4">Order Form Component</h3>
              <OrderForm 
                symbol={selectedSymbol}
                currentPrice={currentPrice}
                availableBalance={5000}
              />
            </section>

            {/* Live Quotes Example */}
            <section>
              <h3 className="text-xl font-semibold text-white mb-4">Live Quote Display</h3>
              <LiveQuoteDisplay 
                symbols={['AAPL', 'MSFT', 'GOOGL']}
                onQuoteUpdate={(quotes) => {
                  if (quotes[selectedSymbol]) {
                    setCurrentPrice(quotes[selectedSymbol].price);
                  }
                }}
              />
            </section>

            {/* Portfolio Example */}
            <section>
              <h3 className="text-xl font-semibold text-white mb-4">Portfolio Component</h3>
              <Portfolio />
            </section>

            {/* Watchlist Example */}
            <section>
              <h3 className="text-xl font-semibold text-white mb-4">Watchlist Component</h3>
              <Watchlist 
                onSymbolSelect={(symbol) => {
                  setSelectedSymbol(symbol);
                  setCurrentPrice(Math.random() * 200 + 50);
                }}
              />
            </section>
          </div>

          {/* Trade History Example */}
          <section>
            <h3 className="text-xl font-semibold text-white mb-4">Trade History Component</h3>
            <TradeHistory />
          </section>

          {/* Usage Instructions */}
          <section className="bg-gray-800 rounded-lg p-6">
            <h3 className="text-xl font-semibold text-white mb-4">Usage Instructions</h3>
            <div className="text-gray-300 space-y-3">
              <p><strong>OrderForm:</strong> Place buy/sell orders with market, limit, stop, and stop-limit order types</p>
              <p><strong>Portfolio:</strong> View your current holdings with real-time values and profit/loss calculations</p>
              <p><strong>LiveQuoteDisplay:</strong> Monitor real-time price updates for selected symbols</p>
              <p><strong>TradeHistory:</strong> Review past trades with filtering and pagination</p>
              <p><strong>Watchlist:</strong> Track symbols of interest and quickly select them for trading</p>
              <p><strong>TradingDashboard:</strong> Complete trading interface combining all components</p>
            </div>
          </section>

          {/* Features */}
          <section className="bg-gray-800 rounded-lg p-6">
            <h3 className="text-xl font-semibold text-white mb-4">Key Features</h3>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4 text-gray-300">
              <ul className="space-y-2">
                <li>✅ Professional dark theme design</li>
                <li>✅ Real-time market data simulation</li>
                <li>✅ Form validation and error handling</li>
                <li>✅ Responsive mobile-friendly layout</li>
                <li>✅ TypeScript support with proper types</li>
              </ul>
              <ul className="space-y-2">
                <li>✅ Loading states and error boundaries</li>
                <li>✅ Mock data for development/testing</li>
                <li>✅ Modular component architecture</li>
                <li>✅ Easy integration with Redux/state management</li>
                <li>✅ Accessibility considerations</li>
              </ul>
            </div>
          </section>
        </div>
      </div>
    </div>
  );
};

export default TradingComponentsDemo;