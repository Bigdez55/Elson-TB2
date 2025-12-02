import React, { useState, useEffect } from 'react';
import { useSelector } from 'react-redux';
import { useTrading } from '../../hooks/useTrading';
import { useWebSocket } from '../../hooks/useWebSocket';
import { useAccessibility } from '../../hooks/useAccessibility';
import Chart from 'chart.js/auto';
import LoadingSpinner from '../common/LoadingSpinner';

/**
 * Mobile-optimized Dashboard component
 * Designed for small screens with touch-friendly interface and simplified UI
 */
export default function MobileDashboard() {
  const [portfolioChartInstance, setPortfolioChartInstance] = useState<Chart | null>(null);
  const [assetAllocationChartInstance, setAssetAllocationChartInstance] = useState<Chart | null>(null);
  const [activeTimeframe, setActiveTimeframe] = useState<string>('1W');

  // Accessibility context for user preferences
  const { isDarkMode, prefersReducedMotion } = useAccessibility();
  
  // Trading data and websocket connections
  const { portfolio, isLoading, error } = useTrading();
  useWebSocket(['market', 'trades', 'alerts']);

  // Redux state
  const { user } = useSelector((state: any) => state.user);
  const { isPremium, isFamily } = useSelector((state: any) => state.subscription);

  // Initialize and update charts
  useEffect(() => {
    if (isLoading) return;
    
    // Portfolio Performance Chart - Simplified for mobile
    const initPortfolioChart = () => {
      const portfolioCtx = document.getElementById('mobilePortfolioChart') as HTMLCanvasElement;
      if (!portfolioCtx) return;

      // Destroy existing chart if it exists
      if (portfolioChartInstance) {
        portfolioChartInstance.destroy();
      }

      // Simplified data for mobile view
      const chartLabels = ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun'];
      
      // Modify based on selected timeframe
      let portfolioData = [32400, 33100, 32800, 33500, 34100, 34300, 34567];
      let benchmarkData = [32400, 32600, 32900, 33000, 33400, 33600, 33900];
      
      if (activeTimeframe === '1M') {
        // Monthly data would have more points - simulated here
        portfolioData = [31200, 31800, 32400, 33100, 32800, 33500, 34100, 34300, 34567];
        benchmarkData = [31200, 31500, 32400, 32600, 32900, 33000, 33400, 33600, 33900];
      }

      const newPortfolioChart = new Chart(portfolioCtx, {
        type: 'line',
        data: {
          labels: chartLabels,
          datasets: [
            {
              label: 'Portfolio Value',
              data: portfolioData,
              backgroundColor: 'rgba(139, 92, 246, 0.1)',
              borderColor: 'rgba(139, 92, 246, 1)',
              borderWidth: 2,
              pointBackgroundColor: 'rgba(139, 92, 246, 1)',
              pointBorderColor: '#fff',
              pointRadius: 2, // Smaller points for mobile
              pointHoverRadius: 4,
              tension: 0.3,
              fill: true
            },
            {
              label: 'S&P 500',
              data: benchmarkData,
              borderColor: 'rgba(156, 163, 175, 0.7)',
              borderWidth: 2,
              pointBackgroundColor: 'rgba(156, 163, 175, 0.7)',
              pointBorderColor: '#fff',
              pointRadius: 0,
              pointHoverRadius: 2,
              tension: 0.3,
              borderDash: [5, 5],
              fill: false
            }
          ]
        },
        options: {
          responsive: true,
          maintainAspectRatio: false,
          animation: {
            duration: prefersReducedMotion ? 0 : 600,
          },
          plugins: {
            legend: {
              display: false, // Hide legend on mobile
            },
            tooltip: {
              mode: 'index',
              intersect: false,
              backgroundColor: 'rgba(17, 24, 39, 0.9)',
              titleColor: '#fff',
              bodyColor: '#fff',
              borderColor: 'rgba(139, 92, 246, 0.5)',
              borderWidth: 1,
              padding: 6,
              displayColors: false,
              callbacks: {
                label: function(context) {
                  return `${context.dataset.label}: $${context.parsed.y.toLocaleString()}`;
                }
              }
            }
          },
          scales: {
            x: {
              grid: {
                display: false,
                drawBorder: false
              },
              ticks: {
                color: '#9ca3af',
                font: {
                  size: 10
                },
                maxRotation: 45,
                autoSkip: true
              }
            },
            y: {
              grid: {
                color: 'rgba(75, 85, 99, 0.2)',
                drawBorder: false
              },
              ticks: {
                color: '#9ca3af',
                font: {
                  size: 10
                },
                callback: function(value) {
                  // Simplified format for mobile
                  return '$' + (value as number / 1000).toFixed(0) + 'k';
                }
              },
              beginAtZero: false
            }
          }
        }
      });
      
      setPortfolioChartInstance(newPortfolioChart);
    };

    // Asset Allocation Chart - Simplified for mobile
    const initAssetAllocationChart = () => {
      const allocationCtx = document.getElementById('mobileAssetAllocationChart') as HTMLCanvasElement;
      if (!allocationCtx) return;

      // Destroy existing chart if it exists
      if (assetAllocationChartInstance) {
        assetAllocationChartInstance.destroy();
      }

      const newAllocationChart = new Chart(allocationCtx, {
        type: 'doughnut',
        data: {
          labels: ['Tech', 'ETFs', 'Energy', 'Crypto', 'Savings'],
          datasets: [{
            data: [35, 25, 10, 15, 15],
            backgroundColor: [
              'rgba(168, 85, 247, 0.8)',
              'rgba(59, 130, 246, 0.8)',
              'rgba(16, 185, 129, 0.8)',
              'rgba(234, 179, 8, 0.8)',
              'rgba(236, 72, 153, 0.8)'
            ],
            borderColor: [
              'rgba(168, 85, 247, 1)',
              'rgba(59, 130, 246, 1)',
              'rgba(16, 185, 129, 1)',
              'rgba(234, 179, 8, 1)',
              'rgba(236, 72, 153, 1)'
            ],
            borderWidth: 1,
            hoverOffset: 5
          }]
        },
        options: {
          responsive: true,
          maintainAspectRatio: false,
          cutout: '60%',
          animation: {
            duration: prefersReducedMotion ? 0 : 600,
          },
          plugins: {
            legend: {
              display: false // Hide legend on mobile
            },
            tooltip: {
              backgroundColor: 'rgba(17, 24, 39, 0.9)',
              titleColor: '#fff',
              bodyColor: '#fff',
              padding: 6,
              callbacks: {
                label: function(context) {
                  return `${context.label}: ${context.parsed}%`;
                }
              }
            }
          }
        }
      });
      
      setAssetAllocationChartInstance(newAllocationChart);
    };

    // Initialize charts
    initPortfolioChart();
    initAssetAllocationChart();

    // Cleanup
    return () => {
      if (portfolioChartInstance) {
        portfolioChartInstance.destroy();
      }
      if (assetAllocationChartInstance) {
        assetAllocationChartInstance.destroy();
      }
    };
  }, [isLoading, portfolioChartInstance, assetAllocationChartInstance, activeTimeframe, prefersReducedMotion]);

  // Handle timeframe changes
  const handleTimeframeChange = (timeframe: string) => {
    setActiveTimeframe(timeframe);
  };

  // Mock portfolio data - Simplified for mobile
  const portfolioCards = [
    { title: 'Total Portfolio', value: '$34,567', change: '+4.3%', trend: 'up', badge: '+12% YTD' },
    { title: 'AI Managed', value: '$21,250', change: '+4.8%', trend: 'up', badge: '+18% YTD' },
    { title: 'High-Yield Savings', value: '$5,250', change: '$22/mo', trend: 'neutral', badge: '5% APY' },
    { title: 'Round-Ups', value: '$13', change: 'Pending', trend: 'neutral', badge: '$248/yr' }
  ];

  const assets = [
    { symbol: 'AAPL', name: 'Apple Inc.', shares: '10.5 shares', value: '$1,947', change: '+1.7%', color: 'blue' },
    { symbol: 'TSLA', name: 'Tesla, Inc.', shares: '8.2 shares', value: '$2,378', change: '+8.6%', color: 'green' },
    { symbol: 'VOO', name: 'Vanguard S&P 500 ETF', shares: '15.3 shares', value: '$6,427', change: '+1.7%', color: 'purple' },
    { symbol: 'BTC', name: 'Bitcoin', shares: '0.058 BTC', value: '$2,324', change: '+10.1%', color: 'yellow' },
    { 
      symbol: <svg className="h-4 w-4" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke="currentColor">
        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M17 9V7a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2m2 4h10a2 2 0 002-2v-6a2 2 0 00-2-2H9a2 2 0 00-2 2v6a2 2 0 002 2zm7-5a2 2 0 11-4 0 2 2 0 014 0z" />
      </svg>, 
      name: 'High-Yield Savings', 
      shares: '5.00% APY', 
      value: '$5,250', 
      change: '+$22/mo', 
      color: 'pink' 
    }
  ];

  const aiInsights = [
    {
      title: 'Tax Loss Harvesting',
      subtitle: 'AI Tax Optimization',
      description: 'Potential tax savings of $125 identified.',
      icon: <svg className="h-4 w-4 text-green-300" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M9 12l2 2 4-4m5.618-4.016A11.955 11.955 0 0112 2.944a11.955 11.955 0 01-8.618 3.04A12.02 12.02 0 003 9c0 5.591 3.824 10.29 9 11.622 5.176-1.332 9-6.03 9-11.622 0-1.042-.133-2.052-.382-3.016z" />
            </svg>,
      iconBg: 'bg-green-900',
      primaryAction: 'Apply',
      secondaryAction: 'Dismiss'
    },
    {
      title: 'Retirement Planning',
      subtitle: 'Financial Coaching',
      description: 'You\'re on track to meet 85% of retirement goals.',
      icon: <svg className="h-4 w-4 text-blue-300" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M8 7V3m8 4V3m-9 8h10M5 21h14a2 2 0 002-2V7a2 2 0 00-2-2H5a2 2 0 00-2 2v12a2 2 0 002 2z" />
            </svg>,
      iconBg: 'bg-blue-900',
      primaryAction: 'Adjust',
      secondaryAction: 'Later'
    }
  ];

  // Loading indicator for mobile
  if (isLoading) {
    return (
      <div className="flex items-center justify-center min-h-[70vh]">
        <LoadingSpinner size="large" color="text-purple-600" text="Loading dashboard..." />
      </div>
    );
  }

  // Error handling for mobile
  if (error) {
    return (
      <div className="p-4 bg-red-900 bg-opacity-20 rounded-lg text-center my-4">
        <p className="text-red-400 mb-2">Unable to load dashboard data</p>
        <button 
          className="px-4 py-2 bg-red-800 text-white rounded-lg text-sm"
          onClick={() => window.location.reload()}
        >
          Retry
        </button>
      </div>
    );
  }

  return (
    <div className="mobile-dashboard pb-16">
      {/* Welcome Section - Simplified for mobile */}
      <div className="bg-gray-900 p-4 mb-4 rounded-xl">
        <h1 className="text-xl font-bold text-white mb-1">Welcome, {user?.username || 'Alex'}</h1>
        <p className="text-gray-400 text-sm">Here's your financial snapshot</p>
        
        <div className="flex gap-2 mt-4">
          <button className="bg-purple-700 text-white px-3 py-2 rounded-lg flex items-center text-sm flex-1 justify-center transition-colors active:bg-purple-800">
            <svg className="h-4 w-4 mr-1" fill="none" stroke="currentColor" viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M12 6v6m0 0v6m0-6h6m-6 0H6"></path>
            </svg>
            Deposit
          </button>
          <button className="bg-gray-700 text-white px-3 py-2 rounded-lg flex items-center text-sm flex-1 justify-center transition-colors active:bg-gray-800">
            <svg className="h-4 w-4 mr-1" fill="none" stroke="currentColor" viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M8 7h12m0 0l-4-4m4 4l-4 4m0 6H4m0 0l4 4m-4-4l4-4"></path>
            </svg>
            Withdraw
          </button>
        </div>
      </div>

      {/* Portfolio Summary Cards - Horizontal scrolling for mobile */}
      <div className="mb-6">
        <h3 className="text-lg font-semibold text-white mb-3 px-1">Portfolio Summary</h3>
        <div className="flex overflow-x-auto pb-4 -mx-4 px-4 gap-3 hide-scrollbar">
          {portfolioCards.map((card, index) => (
            <div key={index} className="bg-gray-900 rounded-xl p-4 shadow-md flex-shrink-0 w-72 touch-pan-x">
              <div className="flex items-center justify-between mb-3">
                <h3 className="text-base font-semibold text-white">{card.title}</h3>
                <span className={`${card.title === 'High-Yield Savings' ? 'bg-green-900 text-green-300' : 'bg-purple-900 text-purple-300'} text-xs px-2 py-1 rounded-full whitespace-nowrap`}>
                  {card.badge}
                </span>
              </div>
              <p className="text-xl font-bold text-white mb-2">{card.value}</p>
              <div className={`flex items-center ${card.trend === 'up' ? 'text-green-400' : 'text-blue-400'} text-sm`}>
                {card.trend === 'up' && (
                  <svg className="h-4 w-4 mr-1" fill="none" stroke="currentColor" viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M5 10l7-7m0 0l7 7m-7-7v18"></path>
                  </svg>
                )}
                <span>{card.change}</span>
              </div>
            </div>
          ))}
        </div>
      </div>

      {/* Portfolio Performance - Mobile optimized */}
      <div className="bg-gray-900 rounded-xl p-4 shadow-md mb-6">
        <div className="flex flex-col mb-4">
          <h3 className="text-base font-semibold text-white mb-3">Portfolio Performance</h3>
          <div className="flex gap-2 overflow-x-auto pb-2 hide-scrollbar">
            <button 
              className={`${activeTimeframe === '1W' ? 'bg-purple-800 text-purple-200' : 'bg-gray-800 text-gray-300'} px-3 py-1 rounded-lg text-xs transition-colors min-w-[40px] min-h-[32px]`}
              onClick={() => handleTimeframeChange('1W')}
            >
              1W
            </button>
            <button 
              className={`${activeTimeframe === '1M' ? 'bg-purple-800 text-purple-200' : 'bg-gray-800 text-gray-300'} px-3 py-1 rounded-lg text-xs transition-colors min-w-[40px] min-h-[32px]`}
              onClick={() => handleTimeframeChange('1M')}
            >
              1M
            </button>
            <button 
              className={`${activeTimeframe === '3M' ? 'bg-purple-800 text-purple-200' : 'bg-gray-800 text-gray-300'} px-3 py-1 rounded-lg text-xs transition-colors min-w-[40px] min-h-[32px]`}
              onClick={() => handleTimeframeChange('3M')}
            >
              3M
            </button>
            <button 
              className={`${activeTimeframe === '1Y' ? 'bg-purple-800 text-purple-200' : 'bg-gray-800 text-gray-300'} px-3 py-1 rounded-lg text-xs transition-colors min-w-[40px] min-h-[32px]`}
              onClick={() => handleTimeframeChange('1Y')}
            >
              1Y
            </button>
            <button 
              className={`${activeTimeframe === 'All' ? 'bg-purple-800 text-purple-200' : 'bg-gray-800 text-gray-300'} px-3 py-1 rounded-lg text-xs transition-colors min-w-[40px] min-h-[32px]`}
              onClick={() => handleTimeframeChange('All')}
            >
              All
            </button>
          </div>
        </div>
        <div className="chart-container h-[220px] w-full">
          <canvas id="mobilePortfolioChart"></canvas>
        </div>
        <div className="flex justify-between text-xs text-gray-400 mt-2 px-2">
          <div>$32.4k</div>
          <div>$34.6k (+6.8%)</div>
        </div>
      </div>

      {/* Asset Allocation - Mobile optimized */}
      <div className="bg-gray-900 rounded-xl p-4 shadow-md mb-6">
        <div className="flex justify-between items-center mb-3">
          <h3 className="text-base font-semibold text-white">Asset Allocation</h3>
          <button className="text-purple-400 active:text-purple-300 text-sm p-2 -mr-2">
            <svg className="h-5 w-5" fill="none" stroke="currentColor" viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M4 6h16M4 12h16M4 18h16"></path>
            </svg>
          </button>
        </div>
        <div className="flex">
          <div className="chart-container h-[160px] w-[160px] mx-auto">
            <canvas id="mobileAssetAllocationChart"></canvas>
          </div>
          <div className="flex-1 grid grid-cols-1 gap-1 ml-2">
            <div className="flex items-center justify-between">
              <div className="flex items-center">
                <div className="w-2 h-2 rounded-full bg-purple-500 mr-1"></div>
                <span className="text-gray-300 text-xs">Tech</span>
              </div>
              <span className="text-gray-300 text-xs">35%</span>
            </div>
            <div className="flex items-center justify-between">
              <div className="flex items-center">
                <div className="w-2 h-2 rounded-full bg-blue-500 mr-1"></div>
                <span className="text-gray-300 text-xs">ETFs</span>
              </div>
              <span className="text-gray-300 text-xs">25%</span>
            </div>
            <div className="flex items-center justify-between">
              <div className="flex items-center">
                <div className="w-2 h-2 rounded-full bg-green-500 mr-1"></div>
                <span className="text-gray-300 text-xs">Energy</span>
              </div>
              <span className="text-gray-300 text-xs">10%</span>
            </div>
            <div className="flex items-center justify-between">
              <div className="flex items-center">
                <div className="w-2 h-2 rounded-full bg-yellow-500 mr-1"></div>
                <span className="text-gray-300 text-xs">Crypto</span>
              </div>
              <span className="text-gray-300 text-xs">15%</span>
            </div>
            <div className="flex items-center justify-between">
              <div className="flex items-center">
                <div className="w-2 h-2 rounded-full bg-pink-500 mr-1"></div>
                <span className="text-gray-300 text-xs">Savings</span>
              </div>
              <span className="text-gray-300 text-xs">15%</span>
            </div>
          </div>
        </div>
      </div>

      {/* Your Assets - Mobile optimized */}
      <div className="bg-gray-900 rounded-xl p-4 shadow-md mb-6">
        <div className="flex justify-between items-center mb-4">
          <h3 className="text-base font-semibold text-white">Your Assets</h3>
          <button className="text-purple-400 active:text-purple-300 text-xs flex items-center transition-colors">
            View All
            <svg className="h-3 w-3 ml-1" fill="none" stroke="currentColor" viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M9 5l7 7-7 7"></path>
            </svg>
          </button>
        </div>
        
        <div className="divide-y divide-gray-800">
          {assets.slice(0, 3).map((asset, index) => (
            <div key={index} className="asset-item flex items-center py-3 px-1 rounded-lg transition-all active:bg-gray-800">
              <div className={`flex-shrink-0 h-8 w-8 rounded-full bg-${asset.color}-900 flex items-center justify-center text-${asset.color}-300 font-bold`}>
                {typeof asset.symbol === 'string' ? asset.symbol : asset.symbol}
              </div>
              <div className="ml-3 flex-1 min-w-0">
                <h4 className="text-white font-medium text-sm truncate">{asset.name}</h4>
                <p className="text-gray-400 text-xs">{asset.shares}</p>
              </div>
              <div className="text-right ml-2">
                <p className="text-white font-medium text-sm">{asset.value}</p>
                <p className={`${asset.change.includes('+') ? 'text-green-400' : 'text-blue-400'} text-xs`}>{asset.change}</p>
              </div>
            </div>
          ))}
        </div>
        <button className="w-full mt-3 py-2 bg-gray-800 text-gray-300 rounded-lg text-sm active:bg-gray-700 transition-colors">
          View All Assets
        </button>
      </div>

      {/* AI Insights - Mobile optimized */}
      <div className="bg-gray-900 rounded-xl p-4 shadow-md mb-6">
        <div className="flex justify-between items-center mb-4">
          <h3 className="text-base font-semibold text-white">AI Insights</h3>
          <div className="px-2 py-1 bg-purple-900 bg-opacity-60 rounded-full text-xs text-purple-200 whitespace-nowrap">
            New
          </div>
        </div>
        
        <div className="space-y-4">
          {aiInsights.map((insight, index) => (
            <div key={index} className="bg-gray-800 p-3 rounded-lg active:bg-gray-700 transition-colors">
              <div className="flex items-center mb-2">
                <div className={`h-6 w-6 rounded-full ${insight.iconBg} flex items-center justify-center`}>
                  {insight.icon}
                </div>
                <div className="ml-2">
                  <h4 className="text-white font-medium text-sm">{insight.title}</h4>
                  <p className="text-gray-400 text-xs">{insight.subtitle}</p>
                </div>
              </div>
              <p className="text-gray-300 text-xs">{insight.description}</p>
              <div className="mt-2 flex justify-end space-x-2">
                <button className="text-gray-400 text-xs active:text-gray-300 transition-colors py-1 px-2 min-h-[32px]">{insight.secondaryAction}</button>
                <button className="text-purple-400 text-xs active:text-purple-300 transition-colors py-1 px-2 min-h-[32px]">{insight.primaryAction}</button>
              </div>
            </div>
          ))}
        </div>
      </div>

      {/* Quick Actions - Mobile only section */}
      <div className="fixed bottom-0 left-0 right-0 bg-gray-900 border-t border-gray-800 px-4 py-3 z-10">
        <div className="flex justify-between">
          <button className="flex flex-col items-center justify-center text-xs text-purple-400 active:text-purple-300 transition-colors w-1/4">
            <svg className="h-6 w-6 mb-1" fill="none" stroke="currentColor" viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z"></path>
            </svg>
            <span>Quick Buy</span>
          </button>
          <button className="flex flex-col items-center justify-center text-xs text-gray-400 active:text-gray-300 transition-colors w-1/4">
            <svg className="h-6 w-6 mb-1" fill="none" stroke="currentColor" viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M16 15v-1a4 4 0 00-4-4H8m0 0l3 3m-3-3l3-3m9 14V5a2 2 0 00-2-2H6a2 2 0 00-2 2v16l4-2 4 2 4-2 4 2z"></path>
            </svg>
            <span>Learn</span>
          </button>
          <button className="flex flex-col items-center justify-center text-xs text-gray-400 active:text-gray-300 transition-colors w-1/4">
            <svg className="h-6 w-6 mb-1" fill="none" stroke="currentColor" viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M12 8c-1.657 0-3 .895-3 2s1.343 2 3 2 3 .895 3 2-1.343 2-3 2m0-8c1.11 0 2.08.402 2.599 1M12 8V7m0 1v8m0 0v1m0-1c-1.11 0-2.08-.402-2.599-1M21 12a9 9 0 11-18 0 9 9 0 0118 0z"></path>
            </svg>
            <span>Round-Ups</span>
          </button>
          <button className="flex flex-col items-center justify-center text-xs text-gray-400 active:text-gray-300 transition-colors w-1/4">
            <svg className="h-6 w-6 mb-1" fill="none" stroke="currentColor" viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M17 20h5v-2a3 3 0 00-5.356-1.857M17 20H7m10 0v-2c0-.656-.126-1.283-.356-1.857M7 20H2v-2a3 3 0 015.356-1.857M7 20v-2c0-.656.126-1.283.356-1.857m0 0a5.002 5.002 0 019.288 0M15 7a3 3 0 11-6 0 3 3 0 016 0zm6 3a2 2 0 11-4 0 2 2 0 014 0zM7 10a2 2 0 11-4 0 2 2 0 014 0z"></path>
            </svg>
            <span>Family</span>
          </button>
        </div>
      </div>

      {/* Accessibility - Add skip to content link for screen readers */}
      <div className="sr-only">
        <a href="#main-content" className="skip-nav">Skip to main content</a>
      </div>
    </div>
  );
}