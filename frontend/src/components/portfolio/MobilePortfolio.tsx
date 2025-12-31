import React, { useState, useEffect } from 'react';
import { useSelector } from 'react-redux';
import { useAccessibility } from '../../hooks/useAccessibility';
import Chart from 'chart.js/auto';
import LoadingSpinner from '../common/LoadingSpinner';

/**
 * Mobile-optimized Portfolio component
 * Designed for small screens with touch-friendly interface and simplified UI
 */
export default function MobilePortfolio() {
  const [performanceChartInstance, setPerformanceChartInstance] = useState<Chart | null>(null);
  const [allocationChartInstance, setAllocationChartInstance] = useState<Chart | null>(null);
  const [activeTab, setActiveTab] = useState('holdings');
  const [isLoading, setIsLoading] = useState(false);
  
  // Accessibility context for user preferences
  const { isDarkMode, prefersReducedMotion, announce } = useAccessibility();
  
  // Redux state (mock data for now)
  const { user } = useSelector((state: any) => state.user);

  // Initialize charts
  useEffect(() => {
    if (isLoading) return;
    
    // Performance Chart - Simplified for mobile
    const initPerformanceChart = () => {
      const ctx = document.getElementById('mobilePerformanceChart') as HTMLCanvasElement;
      if (!ctx) return;

      // Destroy existing chart if it exists
      if (performanceChartInstance) {
        performanceChartInstance.destroy();
      }

      const labels = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec'];
      const data = [18500, 19200, 18900, 20100, 22000, 23400, 24200, 23800, 25600, 27200, 28100, 29500];
      const benchmarkData = [18500, 18700, 19100, 19800, 20400, 21000, 21700, 22400, 23100, 24200, 25300, 26500];

      const newChart = new Chart(ctx, {
        type: 'line',
        data: {
          labels: labels,
          datasets: [
            {
              label: 'Portfolio',
              data: data,
              backgroundColor: 'rgba(139, 92, 246, 0.1)',
              borderColor: 'rgba(139, 92, 246, 1)',
              borderWidth: 2,
              pointBackgroundColor: 'rgba(139, 92, 246, 1)',
              pointBorderColor: '#fff',
              pointRadius: 2, // Smaller points for mobile
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
              padding: 6,
              displayColors: false,
              callbacks: {
                label: function(context) {
                  const value = context.parsed.y ?? 0;
                  return `${context.dataset.label}: $${value.toLocaleString()}`;
                }
              }
            }
          },
          scales: {
            x: {
              grid: {
                display: false
              },
              border: {
                display: false
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
                color: 'rgba(75, 85, 99, 0.2)'
              },
              border: {
                display: false
              },
              ticks: {
                color: '#9ca3af',
                font: {
                  size: 10
                },
                callback: function(value) {
                  return '$' + (value as number / 1000).toFixed(0) + 'k';
                }
              }
            }
          }
        }
      });
      
      setPerformanceChartInstance(newChart);
    };

    // Asset Allocation Chart - Simplified for mobile
    const initAllocationChart = () => {
      const ctx = document.getElementById('mobileAllocationChart') as HTMLCanvasElement;
      if (!ctx) return;

      // Destroy existing chart if it exists
      if (allocationChartInstance) {
        allocationChartInstance.destroy();
      }

      const newChart = new Chart(ctx, {
        type: 'doughnut',
        data: {
          labels: ['US Stocks', 'Intl Stocks', 'Bonds', 'Crypto', 'Cash'],
          datasets: [{
            data: [55, 15, 15, 10, 5],
            backgroundColor: [
              'rgba(139, 92, 246, 0.8)',
              'rgba(59, 130, 246, 0.8)',
              'rgba(16, 185, 129, 0.8)',
              'rgba(234, 179, 8, 0.8)',
              'rgba(209, 213, 219, 0.8)'
            ],
            borderColor: [
              'rgba(139, 92, 246, 1)',
              'rgba(59, 130, 246, 1)',
              'rgba(16, 185, 129, 1)',
              'rgba(234, 179, 8, 1)',
              'rgba(209, 213, 219, 1)'
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
      
      setAllocationChartInstance(newChart);
    };

    // Initialize charts
    initPerformanceChart();
    initAllocationChart();

    // Cleanup
    return () => {
      if (performanceChartInstance) {
        performanceChartInstance.destroy();
      }
      if (allocationChartInstance) {
        allocationChartInstance.destroy();
      }
    };
  }, [isLoading, performanceChartInstance, allocationChartInstance, prefersReducedMotion]);

  // Handle tab changes and announce for screen readers
  const handleTabChange = (tab: string) => {
    setActiveTab(tab);
    announce(`${tab} tab selected`, false);
  };

  // Mock data for portfolio
  const portfolioHoldings = [
    { symbol: 'VTI', name: 'Vanguard Total Stock Market ETF', shares: '25.32', value: '$5,815.86', change: '+$78.24 (+1.36%)', allocation: '19.7%' },
    { symbol: 'AAPL', name: 'Apple Inc.', shares: '15.5', value: '$2,675.35', change: '+$42.65 (+1.62%)', allocation: '9.1%' },
    { symbol: 'MSFT', name: 'Microsoft Corporation', shares: '8.2', value: '$2,542.36', change: '+$28.70 (+1.14%)', allocation: '8.6%' },
    { symbol: 'VXUS', name: 'Vanguard Total International Stock ETF', shares: '45.8', value: '$2,505.37', change: '-$12.37 (-0.49%)', allocation: '8.5%' },
    { symbol: 'BND', name: 'Vanguard Total Bond Market ETF', shares: '32.7', value: '$2,356.77', change: '-$5.89 (-0.25%)', allocation: '8.0%' },
    { symbol: 'GOOG', name: 'Alphabet Inc.', shares: '1.8', value: '$2,256.60', change: '+$34.20 (+1.54%)', allocation: '7.7%' },
    { symbol: 'AMZN', name: 'Amazon.com Inc.', shares: '6.3', value: '$2,070.24', change: '+$25.83 (+1.26%)', allocation: '7.0%' },
    { symbol: 'BTC', name: 'Bitcoin', shares: '0.057', value: '$1,739.85', change: '+$102.91 (+6.29%)', allocation: '5.9%' },
  ];
  
  const activityItems = [
    { type: 'buy', symbol: 'VTI', name: 'Vanguard Total Stock Market ETF', date: 'Nov 15, 2023', amount: '3.42 shares', value: '$785.22', status: 'Completed' },
    { type: 'dividend', symbol: 'AAPL', name: 'Apple Inc.', date: 'Nov 12, 2023', amount: '$12.40', value: '$12.40', status: 'Paid' },
    { type: 'sell', symbol: 'GOOGL', name: 'Alphabet Inc. Class A', date: 'Nov 10, 2023', amount: '1.5 shares', value: '$250.35', status: 'Completed' },
    { type: 'buy', symbol: 'MSFT', name: 'Microsoft Corporation', date: 'Nov 5, 2023', amount: '2.1 shares', value: '$650.97', status: 'Completed' },
    { type: 'round-up', symbol: '', name: 'Round-Up Investment', date: 'Nov 3, 2023', amount: '$23.47', value: '$23.47', status: 'Invested in VTI' },
    { type: 'deposit', symbol: '', name: 'Recurring Deposit', date: 'Nov 1, 2023', amount: '$250.00', value: '$250.00', status: 'Completed' },
  ];

  // Loading indicator for mobile
  if (isLoading) {
    return (
      <div className="flex items-center justify-center min-h-[70vh]">
        <LoadingSpinner size="large" color="text-purple-600" text="Loading portfolio..." />
      </div>
    );
  }

  return (
    <div className="mobile-portfolio pb-16 prevent-pull-refresh">
      {/* Portfolio Summary */}
      <div className="bg-gray-900 p-4 mb-4 rounded-xl">
        <h1 className="text-xl font-bold text-white mb-1">My Portfolio</h1>
        <div className="flex items-baseline justify-between">
          <span className="text-2xl font-bold text-white">$29,482.53</span>
          <span className="text-green-400 text-sm">+$521.67 (1.8%) today</span>
        </div>
        <div className="flex mt-6 gap-2 justify-between">
          <div className="flex-1 bg-gray-800 p-3 rounded-lg">
            <p className="text-gray-400 text-xs mb-1">Total Return</p>
            <p className="text-green-400 text-lg font-bold">+18.9%</p>
            <p className="text-gray-400 text-xs">+$4,682.53</p>
          </div>
          <div className="flex-1 bg-gray-800 p-3 rounded-lg">
            <p className="text-gray-400 text-xs mb-1">YTD Return</p>
            <p className="text-green-400 text-lg font-bold">+12.3%</p>
            <p className="text-gray-400 text-xs">+$3,225.18</p>
          </div>
          <div className="flex-1 bg-gray-800 p-3 rounded-lg">
            <p className="text-gray-400 text-xs mb-1">Risk Level</p>
            <p className="text-purple-400 text-lg font-bold">Moderate</p>
            <p className="text-gray-400 text-xs">70/30 Mix</p>
          </div>
        </div>
      </div>

      {/* Tab navigation */}
      <div className="bg-gray-900 rounded-xl mb-4 overflow-hidden">
        <div className="flex border-b border-gray-800">
          <button 
            className={`flex-1 py-3 text-sm font-medium ${activeTab === 'holdings' ? 'text-purple-400 border-b-2 border-purple-400' : 'text-gray-400'}`}
            onClick={() => handleTabChange('holdings')}
            aria-selected={activeTab === 'holdings'}
            role="tab"
          >
            Holdings
          </button>
          <button 
            className={`flex-1 py-3 text-sm font-medium ${activeTab === 'activity' ? 'text-purple-400 border-b-2 border-purple-400' : 'text-gray-400'}`}
            onClick={() => handleTabChange('activity')}
            aria-selected={activeTab === 'activity'}
            role="tab"
          >
            Activity
          </button>
          <button 
            className={`flex-1 py-3 text-sm font-medium ${activeTab === 'analysis' ? 'text-purple-400 border-b-2 border-purple-400' : 'text-gray-400'}`}
            onClick={() => handleTabChange('analysis')}
            aria-selected={activeTab === 'analysis'}
            role="tab"
          >
            Analysis
          </button>
        </div>

        {/* Tab content - Holdings */}
        {activeTab === 'holdings' && (
          <div className="p-4" role="tabpanel" aria-label="Holdings tab">
            <div className="flex justify-between items-center mb-3">
              <h3 className="text-base font-semibold text-white">Your Holdings</h3>
              <div className="flex">
                <button className="text-xs text-gray-400 px-2 py-1 min-h-0 min-w-0">
                  <svg className="h-4 w-4" fill="none" stroke="currentColor" viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M3 4h13M3 8h9m-9 4h6m4 0l4-4m0 0l4 4m-4-4v12"></path>
                  </svg>
                </button>
                <button className="text-xs text-gray-400 px-2 py-1 min-h-0 min-w-0">
                  <svg className="h-4 w-4" fill="none" stroke="currentColor" viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M3 4a1 1 0 011-1h16a1 1 0 011 1v2.586a1 1 0 01-.293.707l-6.414 6.414a1 1 0 00-.293.707V17l-4 4v-6.586a1 1 0 00-.293-.707L3.293 7.293A1 1 0 013 6.586V4z"></path>
                  </svg>
                </button>
              </div>
            </div>
            
            <div className="max-h-[400px] overflow-y-auto hide-scrollbar">
              {portfolioHoldings.map((holding, index) => (
                <div key={index} className="py-3 border-b border-gray-800 last:border-b-0">
                  <div className="flex justify-between items-start mb-1">
                    <div>
                      <div className="flex items-center">
                        <span className="text-white font-medium">{holding.symbol}</span>
                        <span className="ml-2 text-xs text-gray-400">{holding.allocation}</span>
                      </div>
                      <p className="text-xs text-gray-400">{holding.name}</p>
                    </div>
                    <div className="text-right">
                      <p className="text-white font-medium">{holding.value}</p>
                      <p className={`text-xs ${holding.change.includes('+') ? 'text-green-400' : 'text-red-400'}`}>
                        {holding.change}
                      </p>
                    </div>
                  </div>
                  <div className="flex justify-between text-xs mt-2">
                    <span className="text-gray-400">{holding.shares} shares</span>
                    <div>
                      <button className="bg-gray-800 text-white px-2 py-1 rounded mr-1 min-h-0 min-w-0">Buy</button>
                      <button className="bg-gray-800 text-white px-2 py-1 rounded min-h-0 min-w-0">Sell</button>
                    </div>
                  </div>
                </div>
              ))}
            </div>
          </div>
        )}

        {/* Tab content - Activity */}
        {activeTab === 'activity' && (
          <div className="p-4" role="tabpanel" aria-label="Activity tab">
            <div className="flex justify-between items-center mb-3">
              <h3 className="text-base font-semibold text-white">Recent Activity</h3>
              <button className="text-xs text-purple-400">View All</button>
            </div>
            
            <div className="max-h-[400px] overflow-y-auto hide-scrollbar">
              {activityItems.map((activity, index) => (
                <div key={index} className="py-3 border-b border-gray-800 last:border-b-0">
                  <div className="flex justify-between items-start">
                    <div className="flex">
                      <div className={`w-8 h-8 rounded-full flex items-center justify-center mr-3 text-white
                        ${activity.type === 'buy' ? 'bg-green-800' : ''}
                        ${activity.type === 'sell' ? 'bg-red-800' : ''}
                        ${activity.type === 'dividend' ? 'bg-blue-800' : ''}
                        ${activity.type === 'round-up' ? 'bg-purple-800' : ''}
                        ${activity.type === 'deposit' ? 'bg-gray-800' : ''}
                      `}>
                        {activity.type === 'buy' && <svg className="h-4 w-4" fill="none" stroke="currentColor" viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M12 6v6m0 0v6m0-6h6m-6 0H6"></path></svg>}
                        {activity.type === 'sell' && <svg className="h-4 w-4" fill="none" stroke="currentColor" viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M18 12H6"></path></svg>}
                        {activity.type === 'dividend' && <svg className="h-4 w-4" fill="none" stroke="currentColor" viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M12 8c-1.657 0-3 .895-3 2s1.343 2 3 2 3 .895 3 2-1.343 2-3 2m0-8c1.11 0 2.08.402 2.599 1M12 8V7m0 1v8m0 0v1m0-1c-1.11 0-2.08-.402-2.599-1M21 12a9 9 0 11-18 0 9 9 0 0118 0z"></path></svg>}
                        {activity.type === 'round-up' && <svg className="h-4 w-4" fill="none" stroke="currentColor" viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M15 15l-2 5L9 9l11 4-5 2zm0 0l5 5M7.188 2.239l.777 2.897M5.136 7.965l-2.898-.777M13.95 4.05l-2.122 2.122m-5.657 5.656l-2.12 2.122"></path></svg>}
                        {activity.type === 'deposit' && <svg className="h-4 w-4" fill="none" stroke="currentColor" viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M8 7l4-4m0 0l4 4m-4-4v18"></path></svg>}
                      </div>
                      <div>
                        <p className="text-sm text-white">{activity.type.charAt(0).toUpperCase() + activity.type.slice(1)} {activity.symbol}</p>
                        <p className="text-xs text-gray-400">{activity.date}</p>
                      </div>
                    </div>
                    <div className="text-right">
                      <p className="text-white text-sm">{activity.value}</p>
                      <p className="text-xs text-gray-400">{activity.status}</p>
                    </div>
                  </div>
                </div>
              ))}
            </div>
          </div>
        )}

        {/* Tab content - Analysis */}
        {activeTab === 'analysis' && (
          <div className="p-4" role="tabpanel" aria-label="Analysis tab">
            {/* Performance Chart */}
            <div className="mb-6">
              <div className="flex justify-between items-center mb-3">
                <h3 className="text-base font-semibold text-white">Performance</h3>
                <div className="flex bg-gray-800 rounded-lg p-1">
                  <button className="text-xs bg-purple-800 text-white rounded px-2 py-1 min-h-0 min-w-0">YTD</button>
                  <button className="text-xs text-gray-400 px-2 py-1 min-h-0 min-w-0">1Y</button>
                  <button className="text-xs text-gray-400 px-2 py-1 min-h-0 min-w-0">All</button>
                </div>
              </div>
              <div className="chart-container h-[200px] w-full">
                <canvas id="mobilePerformanceChart"></canvas>
              </div>
              <div className="flex justify-between text-xs text-gray-400 mt-2">
                <div>Jan</div>
                <div>+$11,000 (+59.5%)</div>
              </div>
            </div>
            
            {/* Allocation Chart */}
            <div className="mb-6">
              <div className="flex justify-between items-center mb-3">
                <h3 className="text-base font-semibold text-white">Asset Allocation</h3>
                <button className="text-xs text-purple-400">Details</button>
              </div>
              <div className="flex">
                <div className="chart-container h-[150px] w-[150px]">
                  <canvas id="mobileAllocationChart"></canvas>
                </div>
                <div className="flex-1 grid grid-cols-1 gap-1 ml-2">
                  <div className="flex items-center justify-between">
                    <div className="flex items-center">
                      <div className="w-2 h-2 rounded-full bg-purple-500 mr-1"></div>
                      <span className="text-gray-300 text-xs">US Stocks</span>
                    </div>
                    <span className="text-gray-300 text-xs">55%</span>
                  </div>
                  <div className="flex items-center justify-between">
                    <div className="flex items-center">
                      <div className="w-2 h-2 rounded-full bg-blue-500 mr-1"></div>
                      <span className="text-gray-300 text-xs">Intl Stocks</span>
                    </div>
                    <span className="text-gray-300 text-xs">15%</span>
                  </div>
                  <div className="flex items-center justify-between">
                    <div className="flex items-center">
                      <div className="w-2 h-2 rounded-full bg-green-500 mr-1"></div>
                      <span className="text-gray-300 text-xs">Bonds</span>
                    </div>
                    <span className="text-gray-300 text-xs">15%</span>
                  </div>
                  <div className="flex items-center justify-between">
                    <div className="flex items-center">
                      <div className="w-2 h-2 rounded-full bg-yellow-500 mr-1"></div>
                      <span className="text-gray-300 text-xs">Crypto</span>
                    </div>
                    <span className="text-gray-300 text-xs">10%</span>
                  </div>
                  <div className="flex items-center justify-between">
                    <div className="flex items-center">
                      <div className="w-2 h-2 rounded-full bg-gray-400 mr-1"></div>
                      <span className="text-gray-300 text-xs">Cash</span>
                    </div>
                    <span className="text-gray-300 text-xs">5%</span>
                  </div>
                </div>
              </div>
            </div>
            
            {/* Diversification */}
            <div>
              <div className="flex justify-between items-center mb-3">
                <h3 className="text-base font-semibold text-white">Diversification</h3>
                <button className="text-xs text-purple-400">Improve</button>
              </div>
              
              <div className="bg-gray-800 p-3 rounded-lg mb-3">
                <div className="flex justify-between items-center mb-2">
                  <span className="text-sm text-white">Overall Score</span>
                  <span className="text-sm text-green-400">Good</span>
                </div>
                <div className="w-full bg-gray-700 h-2 rounded-full overflow-hidden">
                  <div className="bg-green-500 h-full rounded-full" style={{ width: '75%' }}></div>
                </div>
                <div className="flex justify-between text-xs text-gray-400 mt-1">
                  <span>Poor</span>
                  <span>Excellent</span>
                </div>
              </div>
              
              <div className="grid grid-cols-2 gap-3">
                <div className="bg-gray-800 p-3 rounded-lg">
                  <div className="flex justify-between items-center mb-1">
                    <span className="text-xs text-gray-400">Sector Exposure</span>
                    <span className="text-xs text-yellow-400">Fair</span>
                  </div>
                  <div className="w-full bg-gray-700 h-1 rounded-full overflow-hidden">
                    <div className="bg-yellow-500 h-full rounded-full" style={{ width: '60%' }}></div>
                  </div>
                </div>
                <div className="bg-gray-800 p-3 rounded-lg">
                  <div className="flex justify-between items-center mb-1">
                    <span className="text-xs text-gray-400">Geographic</span>
                    <span className="text-xs text-green-400">Good</span>
                  </div>
                  <div className="w-full bg-gray-700 h-1 rounded-full overflow-hidden">
                    <div className="bg-green-500 h-full rounded-full" style={{ width: '80%' }}></div>
                  </div>
                </div>
                <div className="bg-gray-800 p-3 rounded-lg">
                  <div className="flex justify-between items-center mb-1">
                    <span className="text-xs text-gray-400">Asset Class</span>
                    <span className="text-xs text-green-400">Great</span>
                  </div>
                  <div className="w-full bg-gray-700 h-1 rounded-full overflow-hidden">
                    <div className="bg-green-500 h-full rounded-full" style={{ width: '85%' }}></div>
                  </div>
                </div>
                <div className="bg-gray-800 p-3 rounded-lg">
                  <div className="flex justify-between items-center mb-1">
                    <span className="text-xs text-gray-400">Risk Level</span>
                    <span className="text-xs text-green-400">Perfect</span>
                  </div>
                  <div className="w-full bg-gray-700 h-1 rounded-full overflow-hidden">
                    <div className="bg-green-500 h-full rounded-full" style={{ width: '95%' }}></div>
                  </div>
                </div>
              </div>
            </div>
          </div>
        )}
      </div>

      {/* Quick Actions */}
      <div className="fixed bottom-0 left-0 right-0 bg-gray-900 border-t border-gray-800 px-4 py-3 z-10">
        <div className="flex justify-between">
          <button className="bg-purple-700 text-white px-4 py-2 rounded-lg text-sm flex-1 mr-2 active:bg-purple-800 transition-colors">
            Buy / Sell
          </button>
          <button className="bg-gray-800 text-white px-4 py-2 rounded-lg text-sm flex-1 active:bg-gray-700 transition-colors">
            Deposit
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