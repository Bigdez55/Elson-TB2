import React, { useState } from 'react';
import { useSelector } from 'react-redux';
import { RootState } from '../store/store';
import { Link } from 'react-router-dom';
import { StatsCard } from '../components/common/Card';
import { PortfolioChart } from '../components/charts/PortfolioChart';
import { AllocationChart } from '../components/charts/AllocationChart';

const DashboardPage: React.FC = () => {
  const { user } = useSelector((state: RootState) => state.auth);
  const { portfolio } = useSelector((state: RootState) => state.portfolio);
  const [timeframe, setTimeframe] = useState<'1D' | '1W' | '1M' | '3M' | '1Y' | 'All'>('1W');

  // Mock data - replace with real data from Redux store
  const portfolioData = {
    labels: ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun'],
    portfolio: [32400, 33100, 32800, 33500, 34100, 34300, 34567],
    benchmark: [32400, 32600, 32900, 33000, 33400, 33600, 33900],
  };

  const allocationData = {
    labels: ['Tech Stocks', 'Index ETFs', 'Clean Energy', 'Cryptocurrency', 'High-Yield Savings'],
    values: [35, 25, 10, 15, 15],
    colors: [
      'rgba(168, 85, 247, 1)',
      'rgba(59, 130, 246, 1)',
      'rgba(16, 185, 129, 1)',
      'rgba(234, 179, 8, 1)',
      'rgba(236, 72, 153, 1)',
    ],
  };

  const assets = [
    { symbol: 'AAPL', name: 'Apple Inc.', shares: '10.5 shares', value: '$1,947.25', change: '+$32.55 (1.7%)', positive: true, bgColor: 'bg-blue-900', textColor: 'text-blue-300' },
    { symbol: 'TSLA', name: 'Tesla, Inc.', shares: '8.2 shares', value: '$2,378.00', change: '+$189.42 (8.6%)', positive: true, bgColor: 'bg-green-900', textColor: 'text-green-300' },
    { symbol: 'VOO', name: 'Vanguard S&P 500 ETF', shares: '15.3 shares', value: '$6,427.32', change: '+$107.10 (1.7%)', positive: true, bgColor: 'bg-purple-900', textColor: 'text-purple-300' },
    { symbol: 'BTC', name: 'Bitcoin', shares: '0.058 BTC', value: '$2,324.18', change: '+$212.50 (10.1%)', positive: true, bgColor: 'bg-yellow-900', textColor: 'text-yellow-300' },
  ];

  return (
    <div className="bg-gray-800 min-h-screen p-6">
      {/* Welcome Section */}
      <div className="flex justify-between items-center mb-8">
        <div>
          <h1 className="text-2xl font-bold text-white">Welcome back, {user?.full_name?.split(' ')[0] || 'Alex'}</h1>
          <p className="text-gray-400">Here's what's happening with your investments today</p>
        </div>
        <div className="flex space-x-4">
          <button className="bg-purple-700 hover:bg-purple-600 text-white px-4 py-2 rounded-lg flex items-center transition-colors">
            <svg className="h-5 w-5 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M12 6v6m0 0v6m0-6h6m-6 0H6" />
            </svg>
            Deposit
          </button>
          <button className="bg-gray-700 hover:bg-gray-600 text-white px-4 py-2 rounded-lg flex items-center transition-colors">
            <svg className="h-5 w-5 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M8 7h12m0 0l-4-4m4 4l-4 4m0 6H4m0 0l4 4m-4-4l4-4" />
            </svg>
            Withdraw
          </button>
        </div>
      </div>

      {/* Portfolio Summary */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4 mb-8">
        <StatsCard
          title="Total Portfolio"
          value={portfolio?.total_value ? `$${portfolio.total_value.toLocaleString()}` : '$34,567.89'}
          badge={{ text: '+12.5% YTD', variant: 'premium' }}
          change={{ value: '$1,432.51 (4.3%) today', positive: true }}
        />
        <StatsCard
          title="AI Managed"
          value="$21,250.42"
          badge={{ text: '+18.3% YTD', variant: 'premium' }}
          change={{ value: '$980.32 (4.8%) today', positive: true }}
        />
        <StatsCard
          title="High-Yield Savings"
          value="$5,250.00"
          badge={{ text: '5.00% APY', variant: 'success' }}
          change={{ value: '$21.88 interest this month', positive: true }}
        />
        <StatsCard
          title="Round-Ups"
          value="$12.75"
          badge={{ text: '$248 this year', variant: 'premium' }}
          change={{ value: 'Pending this week', positive: true }}
        />
      </div>

      {/* New Wealth Features Row */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4 mb-8">
        <StatsCard
          title="Retirement"
          value="$8,067.43"
          badge={{ text: 'Roth IRA', variant: 'info' }}
          change={{ value: '+$1,250 (15.5%) YTD', positive: true }}
        />
        <StatsCard
          title="Elson Card"
          value="$145.32"
          badge={{ text: 'Stock-Back®', variant: 'premium' }}
          change={{ value: 'Rewards earned this month', positive: true }}
        />
        <StatsCard
          title="Crypto"
          value="$3,724.51"
          badge={{ text: '4 Assets', variant: 'warning' }}
          change={{ value: '+$425.21 (12.9%) today', positive: true }}
        />
        <StatsCard
          title="Tax Savings"
          value="$347.92"
          badge={{ text: 'Harvesting', variant: 'success' }}
          change={{ value: 'Est. tax savings YTD', positive: true }}
        />
      </div>

      {/* Portfolio Performance & Allocation */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6 mb-8">
        <PortfolioChart
          data={portfolioData}
          timeframe={timeframe}
          onTimeframeChange={setTimeframe}
          className="lg:col-span-2"
        />
        <AllocationChart data={allocationData} />
      </div>

      {/* Your Assets & AI Insights */}
      <div className="grid grid-cols-1 lg:grid-cols-5 gap-6">
        {/* Your Assets */}
        <div className="bg-gray-900 rounded-xl p-6 shadow-md lg:col-span-3">
          <div className="flex justify-between items-center mb-6">
            <h3 className="text-lg font-semibold text-white">Your Assets</h3>
            <Link to="/portfolio" className="text-purple-400 hover:text-purple-300 text-sm flex items-center transition-colors">
              View All
              <svg className="h-4 w-4 ml-1" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M9 5l7 7-7 7" />
              </svg>
            </Link>
          </div>
          <div className="divide-y divide-gray-800">
            {assets.map((asset, index) => (
              <div key={asset.symbol} className="flex items-center py-4 px-2 rounded-lg hover:bg-purple-900 hover:bg-opacity-10 transition-colors">
                <div className={`flex-shrink-0 h-10 w-10 rounded-full ${asset.bgColor} flex items-center justify-center ${asset.textColor} font-bold`}>
                  {asset.symbol === 'BTC' ? (
                    <svg className="h-5 w-5" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M17 9V7a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2m2 4h10a2 2 0 002-2v-6a2 2 0 00-2-2H9a2 2 0 00-2 2v6a2 2 0 002 2zm7-5a2 2 0 11-4 0 2 2 0 014 0z" />
                    </svg>
                  ) : asset.symbol}
                </div>
                <div className="ml-4 flex-1">
                  <h4 className="text-white font-medium">{asset.name}</h4>
                  <p className="text-gray-400 text-sm">{asset.shares}</p>
                </div>
                <div className="text-right">
                  <p className="text-white font-medium">{asset.value}</p>
                  <p className={`text-sm ${asset.positive ? 'text-green-400' : 'text-red-400'}`}>{asset.change}</p>
                </div>
              </div>
            ))}
          </div>
        </div>

        {/* AI Insights */}
        <div className="bg-gray-900 rounded-xl p-6 shadow-md lg:col-span-2">
          <div className="flex justify-between items-center mb-6">
            <h3 className="text-lg font-semibold text-white">AI Insights</h3>
            <div className="px-2 py-1 bg-purple-900 bg-opacity-60 rounded-full text-xs text-purple-200">
              Updated 5 min ago
            </div>
          </div>
          
          <div className="space-y-6">
            {/* Tax Loss Harvesting */}
            <div className="bg-gray-800 p-4 rounded-lg">
              <div className="flex items-center mb-3">
                <div className="h-8 w-8 rounded-full bg-green-900 flex items-center justify-center">
                  <svg className="h-4 w-4 text-green-300" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M9 12l2 2 4-4m5.618-4.016A11.955 11.955 0 0112 2.944a11.955 11.955 0 01-8.618 3.04A12.02 12.02 0 003 9c0 5.591 3.824 10.29 9 11.622 5.176-1.332 9-6.03 9-11.622 0-1.042-.133-2.052-.382-3.016z" />
                  </svg>
                </div>
                <div className="ml-3">
                  <h4 className="text-white font-medium">Tax Loss Harvesting</h4>
                  <p className="text-gray-400 text-xs">AI Tax Optimization</p>
                </div>
              </div>
              <p className="text-gray-300 text-sm mb-3">Potential tax savings of $125 identified. Consider selling MSFT position and buying similar asset.</p>
              <div className="flex justify-end space-x-2">
                <button className="text-gray-400 text-xs hover:text-gray-300 transition-colors">Dismiss</button>
                <button className="text-purple-400 text-xs hover:text-purple-300 transition-colors">Apply Strategy</button>
              </div>
            </div>
            
            {/* Retirement */}
            <div className="bg-gray-800 p-4 rounded-lg">
              <div className="flex items-center mb-3">
                <div className="h-8 w-8 rounded-full bg-blue-900 flex items-center justify-center">
                  <svg className="h-4 w-4 text-blue-300" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M8 7V3m8 4V3m-9 8h10M5 21h14a2 2 0 002-2V7a2 2 0 00-2-2H5a2 2 0 00-2 2v12a2 2 0 002 2z" />
                  </svg>
                </div>
                <div className="ml-3">
                  <h4 className="text-white font-medium">Retirement Planning</h4>
                  <p className="text-gray-400 text-xs">Financial Coaching</p>
                </div>
              </div>
              <p className="text-gray-300 text-sm mb-3">You're on track to meet 85% of retirement goals. Increase monthly contribution by $75 to reach target.</p>
              <div className="flex justify-end space-x-2">
                <button className="text-gray-400 text-xs hover:text-gray-300 transition-colors">Later</button>
                <button className="text-purple-400 text-xs hover:text-purple-300 transition-colors">Adjust Contribution</button>
              </div>
            </div>
            
            {/* Stock-Back Reward Insight */}
            <div className="bg-gray-800 p-4 rounded-lg">
              <div className="flex items-center mb-3">
                <div className="h-8 w-8 rounded-full bg-purple-900 flex items-center justify-center">
                  <svg className="h-4 w-4 text-purple-300" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M3 10h18M7 15h1m4 0h1m-7 4h12a3 3 0 003-3V8a3 3 0 00-3-3H6a3 3 0 00-3 3v8a3 3 0 003 3z" />
                  </svg>
                </div>
                <div className="ml-3">
                  <h4 className="text-white font-medium">Stock-Back® Rewards</h4>
                  <p className="text-gray-400 text-xs">Elson Card</p>
                </div>
              </div>
              <p className="text-gray-300 text-sm mb-3">You've earned $42.18 in Stock-Back® rewards this week. Link more merchants for higher returns.</p>
              <div className="flex justify-end space-x-2">
                <button className="text-gray-400 text-xs hover:text-gray-300 transition-colors">Dismiss</button>
                <button className="text-purple-400 text-xs hover:text-purple-300 transition-colors">Manage Rewards</button>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default DashboardPage;