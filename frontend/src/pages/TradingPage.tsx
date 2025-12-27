import React, { useState, useEffect } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { useTradingContext } from '../contexts/TradingContext';
import { useGetQuoteQuery, useGetHistoricalDataQuery } from '../services/marketDataApi';
import {
  useGetAISignalQuery,
  useGetRiskAssessmentQuery,
  useGetCompanyInfoQuery,
  useGetNewsQuery
} from '../services/aiTradingApi';
import { TradingSidebar } from '../components/trading/TradingSidebar';
import { StockHeader } from '../components/trading/StockHeader';
import { StockChart } from '../components/charts/StockChart';
import OrderForm from '../components/trading/OrderForm';
import { AITradingAssistant } from '../components/trading/AITradingAssistant';
import { CompanyInfo } from '../components/trading/CompanyInfo';
import { LiveMarketData } from '../components/trading/LiveMarketData';
import { LivePortfolioUpdates, CompactPortfolioUpdates } from '../components/trading/LivePortfolioUpdates';
import { LiveOrderUpdates } from '../components/trading/LiveOrderUpdates';
import { TradingModeStatusAlert, RiskLimitWarning } from '../components/trading/TradingSafeguards';
import { LoadingSpinner } from '../components/common/LoadingSpinner';

const TradingPage: React.FC = () => {
  const { symbol: urlSymbol } = useParams<{ symbol: string }>();
  const navigate = useNavigate();
  const { mode, dailyLimits } = useTradingContext();

  // Default symbol if none provided in URL
  const [currentSymbol, setCurrentSymbol] = useState(urlSymbol || 'TSLA');
  const [chartTimeframe, setChartTimeframe] = useState<'1D' | '1W' | '1M' | '3M' | '1Y' | '5Y'>('1M');

  // Market data queries
  const {
    data: quoteData,
    error: quoteError,
    isLoading: isQuoteLoading,
    refetch: refetchQuote
  } = useGetQuoteQuery(currentSymbol, {
    pollingInterval: 5000, // Refresh every 5 seconds
    skip: !currentSymbol,
  });

  // AI Trading queries
  const { data: aiSignal } = useGetAISignalQuery(
    { symbol: currentSymbol, mode },
    { skip: !currentSymbol, pollingInterval: 60000 } // Refresh every minute
  );

  const { data: riskAssessmentData } = useGetRiskAssessmentQuery(
    { symbol: currentSymbol, mode },
    { skip: !currentSymbol, pollingInterval: 300000 } // Refresh every 5 minutes
  );

  const { data: companyInfo } = useGetCompanyInfoQuery(currentSymbol, {
    skip: !currentSymbol,
  });

  const { data: newsData } = useGetNewsQuery(
    { symbol: currentSymbol, limit: 5 },
    { skip: !currentSymbol, pollingInterval: 300000 } // Refresh every 5 minutes
  );

  // Map frontend timeframe to backend period
  const timeframeToPeriod = (timeframe: string) => {
    switch (timeframe) {
      case '1D': return '1d';
      case '1W': return '5d';
      case '1M': return '1mo';
      case '3M': return '3mo';
      case '1Y': return '1y';
      case '5Y': return '5y';
      default: return '1mo';
    }
  };

  const {
    data: historicalData,
    isLoading: isHistoryLoading,
  } = useGetHistoricalDataQuery(
    { symbol: currentSymbol, period: timeframeToPeriod(chartTimeframe) },
    { skip: !currentSymbol }
  );

  // Effect to handle URL symbol changes
  useEffect(() => {
    if (urlSymbol && urlSymbol !== currentSymbol) {
      setCurrentSymbol(urlSymbol.toUpperCase());
    }
  }, [urlSymbol, currentSymbol]);

  // Transform historical data for chart
  const chartData = React.useMemo(() => {
    if (!historicalData?.data) {
      return null;
    }

    return {
      labels: historicalData.data.map(point =>
        new Date(point.timestamp).toLocaleDateString()
      ),
      prices: historicalData.data.map(point => point.close)
    };
  }, [historicalData]);

  // Transform AI signal data for AITradingAssistant component
  const aiAnalysis = aiSignal ? {
    signal: aiSignal.signal,
    confidence: aiSignal.confidence,
    description: aiSignal.reasons?.join(' ') || 'AI analysis in progress...'
  } : {
    signal: 'HOLD' as const,
    confidence: 50,
    description: 'Loading AI analysis...'
  };

  const aiStrategy = {
    title: 'AI Trading Strategy',
    description: aiSignal?.reasons?.[0] || 'Strategy analysis pending...',
    enabled: true
  };

  const riskAssessment = riskAssessmentData ? {
    score: riskAssessmentData.risk_score,
    level: (riskAssessmentData.risk_level === 'VERY_HIGH' ? 'HIGH' : riskAssessmentData.risk_level) as 'LOW' | 'MEDIUM' | 'HIGH',
    description: riskAssessmentData.recommendations?.[0] || 'Risk analysis in progress...',
    recommendation: riskAssessmentData.recommendations?.join('. ') || ''
  } : {
    score: 50,
    level: 'MEDIUM' as const,
    description: 'Loading risk assessment...',
    recommendation: ''
  };

  // Transform company info for CompanyInfo component
  const companyData = companyInfo ? {
    name: companyInfo.name,
    symbol: companyInfo.symbol,
    description: companyInfo.description,
    ceo: companyInfo.ceo || 'N/A',
    founded: companyInfo.founded || 'N/A',
    headquarters: companyInfo.headquarters || 'N/A',
    employees: companyInfo.employees?.toString() || 'N/A',
    website: `https://www.${companyInfo.symbol.toLowerCase()}.com`, // Fallback
    industry: companyInfo.industry
  } : {
    name: currentSymbol,
    symbol: currentSymbol,
    description: 'Loading company information...',
    ceo: 'Loading...',
    founded: 'Loading...',
    headquarters: 'Loading...',
    employees: 'Loading...',
    website: '#',
    industry: 'Loading...'
  };

  // Transform news data for CompanyInfo component
  const formattedNewsData = newsData?.map(item => ({
    id: item.url,
    title: item.title,
    source: item.source,
    publishedAt: item.published_at,
    url: item.url
  })) || [];

  // Event Handlers
  const handleSymbolSearch = (query: string) => {
    console.log('Symbol search:', query);
    // This will be implemented with the search API
  };

  const handleSymbolSelect = (symbol: string) => {
    const upperSymbol = symbol.toUpperCase();
    setCurrentSymbol(upperSymbol);
    // Update URL to reflect new symbol
    navigate(`/${mode}/trading/${upperSymbol}`, { replace: true });
  };

  const handleAssetTypeChange = (type: string) => {
    console.log('Asset type changed:', type);
  };

  const handleAddToWatchlist = () => {
    console.log('Added to watchlist:', currentSymbol);
    // TODO: Implement watchlist API
  };

  const handleShare = () => {
    const url = `${window.location.origin}/${mode}/trading/${currentSymbol}`;
    if (navigator.share) {
      navigator.share({
        title: `${currentSymbol} Stock Analysis`,
        url: url
      });
    } else {
      navigator.clipboard.writeText(url);
      alert('Link copied to clipboard!');
    }
  };

  const handleApplyStrategy = () => {
    console.log('Apply AI strategy for:', currentSymbol);
    // TODO: Implement AI strategy application
  };

  const handleUpdateStrategy = () => {
    console.log('Update AI strategy configuration');
    // TODO: Implement strategy update
  };

  const handleTimeframeChange = (timeframe: string) => {
    const validTimeframes: Array<'1D' | '1W' | '1M' | '3M' | '1Y' | '5Y'> = ['1D', '1W', '1M', '3M', '1Y', '5Y'];
    if (validTimeframes.includes(timeframe as any)) {
      setChartTimeframe(timeframe as '1D' | '1W' | '1M' | '3M' | '1Y' | '5Y');
    }
  };

  // Error and loading states
  if (isQuoteLoading && !quoteData) {
    return (
      <div className="bg-gray-800 min-h-screen flex items-center justify-center">
        <LoadingSpinner />
      </div>
    );
  }

  if (quoteError) {
    return (
      <div className="bg-gray-800 min-h-screen flex items-center justify-center">
        <div className="text-center">
          <h2 className="text-red-400 text-xl mb-4">Error loading market data</h2>
          <p className="text-gray-300 mb-4">Unable to load data for {currentSymbol}</p>
          <button 
            onClick={() => refetchQuote()}
            className="bg-purple-600 hover:bg-purple-700 px-4 py-2 rounded text-white"
          >
            Retry
          </button>
        </div>
      </div>
    );
  }

  return (
    <div className="bg-gray-800 min-h-screen flex">
      {/* Trading Mode Status Alert */}
      <TradingModeStatusAlert />
      
      {/* Trading Sidebar */}
      <TradingSidebar 
        onSymbolSearch={handleSymbolSearch}
        onAssetTypeChange={handleAssetTypeChange}
      />
      
      {/* Main Content */}
      <div className="flex-1 p-6">
        {/* Live Portfolio Summary */}
        <div className="mb-6">
          <CompactPortfolioUpdates className="max-w-xs" />
        </div>
        
        {/* Risk Warnings */}
        <div className="space-y-4 mb-6">
          <RiskLimitWarning
            currentValue={dailyLimits.dailyOrderLimit - dailyLimits.ordersRemaining}
            limit={dailyLimits.dailyOrderLimit}
            type="orders"
          />
          <RiskLimitWarning
            currentValue={dailyLimits.dailyLossLimit - dailyLimits.lossRemaining}
            limit={dailyLimits.dailyLossLimit}
            type="loss"
          />
        </div>
        
        {/* Live Market Data with WebSocket */}
        <div className="mb-6">
          <LiveMarketData 
            symbol={currentSymbol}
            onPriceUpdate={(price, change, changePercent) => {
              // Update any dependent components with real-time price
              console.log('Live price update:', { price, change, changePercent });
            }}
            showConnectionStatus={true}
          />
        </div>

        {/* Stock Header with Real Data */}
        {quoteData && (
          <StockHeader
            symbol={quoteData.symbol}
            companyName={companyInfo?.name || `${quoteData.symbol} Inc.`}
            exchange="NASDAQ"
            sector={companyInfo?.sector || "N/A"}
            currentPrice={quoteData.price}
            priceChange={quoteData.change || 0}
            priceChangePercent={quoteData.change_percent || 0}
            afterHoursPrice={undefined}
            afterHoursChange={undefined}
            afterHoursChangePercent={undefined}
            marketCap={quoteData.market_cap || "N/A"}
            peRatio={quoteData.pe_ratio || 0}
            weekRange52={{
              low: quoteData.week_52_low || 0,
              high: quoteData.week_52_high || 0
            }}
            dividendYield={quoteData.dividend_yield || "0.00%"}
            onAddToWatchlist={handleAddToWatchlist}
            onShare={handleShare}
          />
        )}
        
        {/* Main Trading Interface */}
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6 mt-6">
          {/* Stock Chart */}
          <div className="lg:col-span-2">
            {isHistoryLoading ? (
              <div className="bg-gray-900 rounded-xl p-6 h-96 flex items-center justify-center">
                <LoadingSpinner />
              </div>
            ) : chartData ? (
              <StockChart 
                data={chartData}
                symbol={currentSymbol}
                timeframe={chartTimeframe}
                onTimeframeChange={handleTimeframeChange}
              />
            ) : (
              <div className="bg-gray-900 rounded-xl p-6 h-96 flex items-center justify-center">
                <div className="text-center text-gray-400">
                  <p>Chart data unavailable</p>
                  <p className="text-sm mt-2">Historical data not found for {currentSymbol}</p>
                </div>
              </div>
            )}
          </div>
          
          {/* Order Form */}
          <div>
            <OrderForm 
              symbol={currentSymbol}
              currentPrice={quoteData?.price || 0}
              availableBalance={25000} // TODO: Get from user account data
            />
          </div>
        </div>
        
        {/* Bottom Section - Live Updates and AI Assistant */}
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6 mt-6">
          {/* Live Portfolio and Order Updates */}
          <div className="space-y-6">
            <LivePortfolioUpdates 
              showRecentOrders={true}
              showPositions={true}
              maxOrdersToShow={3}
              maxPositionsToShow={3}
            />
          </div>
          
          {/* AI Trading Assistant */}
          <div>
            <AITradingAssistant 
              symbol={currentSymbol}
              analysis={aiAnalysis}
              strategy={aiStrategy}
              riskAssessment={riskAssessment}
              onApplyStrategy={handleApplyStrategy}
              onUpdateStrategy={handleUpdateStrategy}
            />
          </div>
          
          {/* Company Info */}
          <div>
            <CompanyInfo
              company={companyData}
              news={formattedNewsData}
            />
          </div>
        </div>

        {/* Live Order Updates Panel */}
        <div className="mt-6">
          <LiveOrderUpdates 
            maxOrdersToShow={5}
            showFilters={true}
            onOrderClick={(orderId) => {
              console.log('Order clicked:', orderId);
              // TODO: Navigate to order details or show modal
            }}
          />
        </div>
      </div>
    </div>
  );
};

export default TradingPage;