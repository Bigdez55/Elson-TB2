import React, { useState, useEffect } from 'react';
import { useParams } from 'react-router-dom';
import { TradingSidebar } from '../components/trading/TradingSidebar';
import { StockHeader } from '../components/trading/StockHeader';
import { StockChart } from '../components/charts/StockChart';
import OrderForm from '../components/trading/OrderForm';
import { AITradingAssistant } from '../components/trading/AITradingAssistant';
import { CompanyInfo } from '../components/trading/CompanyInfo';
import { Badge } from '../components/common/Badge';

interface StockData {
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
  marketCap: string;
  peRatio: number;
  weekRange52: { low: number; high: number };
  dividendYield: string;
}

const TradingPage: React.FC = () => {
  const { symbol: urlSymbol } = useParams<{ symbol: string }>();
  const [currentSymbol, setCurrentSymbol] = useState(urlSymbol || 'TSLA');
  const [paperTradingEnabled, setPaperTradingEnabled] = useState(true);
  const [loading, setLoading] = useState(false);
  
  // Mock stock data - in real app this would come from an API
  const [stockData, setStockData] = useState<StockData>({
    symbol: 'TSLA',
    companyName: 'Tesla, Inc.',
    exchange: 'NASDAQ',
    sector: 'Consumer Cyclical',
    currentPrice: 248.50,
    priceChange: 18.75,
    priceChangePercent: 8.16,
    afterHoursPrice: 250.25,
    afterHoursChange: 1.75,
    afterHoursChangePercent: 0.70,
    marketCap: '$788.5B',
    peRatio: 61.2,
    weekRange52: { low: 138.80, high: 271.00 },
    dividendYield: '0.00%'
  });
  
  // Mock chart data
  const [chartData] = useState({
    labels: ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec'],
    prices: [180, 165, 190, 220, 185, 205, 240, 225, 248, 235, 250, 248]
  });
  
  // Mock AI analysis
  const [aiAnalysis] = useState({
    signal: 'BUY' as const,
    confidence: 87,
    description: 'Strong technical momentum combined with positive earnings outlook suggests continued upward movement.'
  });
  
  // Mock AI strategy
  const [aiStrategy] = useState({
    title: 'Momentum Growth Strategy',
    description: 'Automated buying on dips with stop-loss protection and profit taking at key resistance levels.',
    enabled: true
  });
  
  // Mock risk assessment
  const [riskAssessment] = useState({
    score: 72,
    level: 'MEDIUM' as const,
    description: 'Moderate volatility expected due to market conditions and earnings season.',
    recommendation: 'Consider position sizing and stop-loss levels'
  });
  
  // Mock company data
  const [companyData] = useState({
    name: 'Tesla, Inc.',
    symbol: 'TSLA',
    description: 'Tesla designs, develops, manufactures, leases, and sells electric vehicles, and energy generation and storage systems in the United States, China, and internationally.',
    ceo: 'Elon Musk',
    founded: '2003',
    headquarters: 'Austin, Texas',
    employees: '127,855',
    website: 'https://tesla.com',
    industry: 'Auto Manufacturers'
  });
  
  // Mock news data
  const [newsData] = useState([
    {
      id: '1',
      title: 'Tesla Reports Strong Q4 Earnings, Beats Wall Street Expectations',
      source: 'Reuters',
      publishedAt: '2024-01-25T10:30:00Z',
      url: 'https://reuters.com/tesla-earnings'
    },
    {
      id: '2', 
      title: 'New Tesla Model Y Production Facility Opens in Mexico',
      source: 'Bloomberg',
      publishedAt: '2024-01-24T14:15:00Z',
      url: 'https://bloomberg.com/tesla-mexico'
    },
    {
      id: '3',
      title: 'Tesla Stock Upgraded by Morgan Stanley on AI Potential',
      source: 'CNBC',
      publishedAt: '2024-01-23T09:45:00Z',
      url: 'https://cnbc.com/tesla-upgrade'
    }
  ]);

  const handleSymbolSearch = (query: string) => {
    console.log('Symbol search:', query);
    // In real app, this would trigger API search
  };

  const handlePaperTradingChange = (enabled: boolean) => {
    setPaperTradingEnabled(enabled);
  };

  const handleAssetTypeChange = (type: string) => {
    console.log('Asset type changed:', type);
  };

  const handleAddToWatchlist = () => {
    console.log('Added to watchlist:', currentSymbol);
  };

  const handleShare = () => {
    console.log('Share stock:', currentSymbol);
  };

  const handleApplyStrategy = () => {
    console.log('Apply AI strategy for:', currentSymbol);
  };

  const handleUpdateStrategy = () => {
    console.log('Update AI strategy configuration');
  };

  const handleTimeframeChange = (timeframe: string) => {
    console.log('Timeframe changed:', timeframe);
    // In real app, this would update chart data
  };

  return (
    <div className="bg-gray-800 min-h-screen flex">
      {/* Trading Sidebar */}
      <TradingSidebar 
        onSymbolSearch={handleSymbolSearch}
        onPaperTradingChange={handlePaperTradingChange}
        onAssetTypeChange={handleAssetTypeChange}
      />
      
      {/* Main Content */}
      <div className="flex-1 p-6">
        {/* Paper Trading Banner */}
        {paperTradingEnabled && (
          <div className="bg-yellow-900 bg-opacity-30 border border-yellow-700 rounded-lg p-4 mb-6">
            <div className="flex items-center justify-between">
              <div className="flex items-center">
                <svg className="h-5 w-5 text-yellow-400 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
                </svg>
                <span className="text-yellow-300 font-medium">Paper Trading Mode Active</span>
                <Badge variant="warning" size="sm" className="ml-2">Practice</Badge>
              </div>
              <button 
                onClick={() => setPaperTradingEnabled(false)}
                className="text-yellow-400 hover:text-yellow-300 text-sm transition-colors"
              >
                Switch to Live Trading
              </button>
            </div>
            <p className="text-yellow-200 text-sm mt-1">
              You're trading with virtual money. No real transactions will be executed.
            </p>
          </div>
        )}
        
        {/* Stock Header */}
        <StockHeader 
          symbol={stockData.symbol}
          companyName={stockData.companyName}
          exchange={stockData.exchange}
          sector={stockData.sector}
          currentPrice={stockData.currentPrice}
          priceChange={stockData.priceChange}
          priceChangePercent={stockData.priceChangePercent}
          afterHoursPrice={stockData.afterHoursPrice}
          afterHoursChange={stockData.afterHoursChange}
          afterHoursChangePercent={stockData.afterHoursChangePercent}
          marketCap={stockData.marketCap}
          peRatio={stockData.peRatio}
          weekRange52={stockData.weekRange52}
          dividendYield={stockData.dividendYield}
          onAddToWatchlist={handleAddToWatchlist}
          onShare={handleShare}
        />
        
        {/* Main Trading Interface */}
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6 mt-6">
          {/* Stock Chart - Full Width on Mobile, 2 Columns on Desktop */}
          <div className="lg:col-span-2">
            <StockChart 
              data={chartData}
              symbol={stockData.symbol}
              timeframe="1M"
              onTimeframeChange={handleTimeframeChange}
            />
          </div>
          
          {/* Order Form */}
          <div>
            <OrderForm 
              symbol={stockData.symbol}
              currentPrice={stockData.currentPrice}
              availableBalance={25000}
            />
          </div>
        </div>
        
        {/* Bottom Section - AI Assistant and Company Info */}
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6 mt-6">
          {/* AI Trading Assistant */}
          <div>
            <AITradingAssistant 
              symbol={stockData.symbol}
              analysis={aiAnalysis}
              strategy={aiStrategy}
              riskAssessment={riskAssessment}
              onApplyStrategy={handleApplyStrategy}
              onUpdateStrategy={handleUpdateStrategy}
            />
          </div>
          
          {/* Company Info */}
          <CompanyInfo 
            company={companyData}
            news={newsData}
          />
        </div>
      </div>
    </div>
  );
};

export default TradingPage;