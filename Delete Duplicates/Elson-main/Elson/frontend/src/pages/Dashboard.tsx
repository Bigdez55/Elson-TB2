import React, { useState, useEffect, Suspense, lazy } from 'react';
import { useSelector } from 'react-redux';
import { useTrading } from '../app/hooks/useTrading';
import { useWebSocket } from '../app/hooks/useWebSocket';
import Chart from 'chart.js/auto';
import Loading from '../app/components/common/Loading';
import { useTheme, useMediaQuery } from '@mui/material';

// Import the mobile dashboard lazily for better performance
const MobileDashboard = lazy(() => import('../app/components/dashboard/MobileDashboard'));

// Import necessary components
import PerformanceMetrics from '../app/components/dashboard/PerformanceMetrics';
import AlertsPanel from '../app/components/dashboard/AlertsPanel';
import RiskAnalysisPanel from '../app/components/dashboard/RiskAnalysisPanel';

export default function Dashboard() {
  const [portfolioChartInstance, setPortfolioChartInstance] = useState<Chart | null>(null);
  const [assetAllocationChartInstance, setAssetAllocationChartInstance] = useState<Chart | null>(null);
  const theme = useTheme();
  const isMobile = useMediaQuery(theme.breakpoints.down('sm'));
  const isTablet = useMediaQuery(theme.breakpoints.between('sm', 'md'));

  const { portfolio, isLoading, error } = useTrading();
  useWebSocket(['market', 'trades', 'alerts']);
  
  // Check if we should render the mobile version of the dashboard
  if (isMobile) {
    return (
      <Suspense fallback={<Loading />}>
        <MobileDashboard />
      </Suspense>
    );
  }

  const { user } = useSelector((state: any) => state.user);
  const { isPremium, isFamily } = useSelector((state: any) => state.subscription);

  useEffect(() => {
    if (isLoading) return;
    
    // Portfolio Performance Chart
    const initPortfolioChart = () => {
      const portfolioCtx = document.getElementById('portfolioChart') as HTMLCanvasElement;
      if (!portfolioCtx) return;

      // Destroy existing chart if it exists
      if (portfolioChartInstance) {
        portfolioChartInstance.destroy();
      }

      const newPortfolioChart = new Chart(portfolioCtx, {
        type: 'line',
        data: {
          labels: ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun'],
          datasets: [
            {
              label: 'Portfolio Value',
              data: [32400, 33100, 32800, 33500, 34100, 34300, 34567],
              backgroundColor: 'rgba(139, 92, 246, 0.1)',
              borderColor: 'rgba(139, 92, 246, 1)',
              borderWidth: 2,
              pointBackgroundColor: 'rgba(139, 92, 246, 1)',
              pointBorderColor: '#fff',
              pointRadius: 4,
              pointHoverRadius: 6,
              tension: 0.3,
              fill: true
            },
            {
              label: 'S&P 500',
              data: [32400, 32600, 32900, 33000, 33400, 33600, 33900],
              borderColor: 'rgba(156, 163, 175, 0.7)',
              borderWidth: 2,
              pointBackgroundColor: 'rgba(156, 163, 175, 0.7)',
              pointBorderColor: '#fff',
              pointRadius: 0,
              pointHoverRadius: 4,
              tension: 0.3,
              borderDash: [5, 5],
              fill: false
            }
          ]
        },
        options: {
          responsive: true,
          maintainAspectRatio: false,
          plugins: {
            legend: {
              display: true,
              position: 'top',
              labels: {
                color: '#e2e8f0',
                font: {
                  size: 12
                },
                boxWidth: 12
              }
            },
            tooltip: {
              mode: 'index',
              intersect: false,
              backgroundColor: 'rgba(17, 24, 39, 0.9)',
              titleColor: '#fff',
              bodyColor: '#fff',
              borderColor: 'rgba(139, 92, 246, 0.5)',
              borderWidth: 1,
              padding: isMobile ? 6 : isTablet ? 8 : 10,
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
                  size: isMobile ? 10 : isTablet ? 11 : 12
                },
                maxRotation: isMobile ? 45 : isTablet ? 30 : 0,
                autoSkip: isMobile || isTablet
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
                  size: isMobile ? 10 : isTablet ? 11 : 12
                },
                callback: function(value) {
                  if (isMobile || isTablet) {
                    // Simplified format for mobile and tablet
                    return '$' + (value as number / 1000).toFixed(0) + 'k';
                  }
                  return '$' + value.toString().replace(/\B(?=(\d{3})+(?!\d))/g, ",");
                }
              },
              beginAtZero: false
            }
          }
        }
      });
      
      setPortfolioChartInstance(newPortfolioChart);
    };

    // Asset Allocation Chart
    const initAssetAllocationChart = () => {
      const allocationCtx = document.getElementById('assetAllocationChart') as HTMLCanvasElement;
      if (!allocationCtx) return;

      // Destroy existing chart if it exists
      if (assetAllocationChartInstance) {
        assetAllocationChartInstance.destroy();
      }

      const newAllocationChart = new Chart(allocationCtx, {
        type: 'doughnut',
        data: {
          labels: ['Tech Stocks', 'Index ETFs', 'Clean Energy', 'Cryptocurrency', 'High-Yield Savings'],
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
          cutout: '70%',
          plugins: {
            legend: {
              display: false
            },
            tooltip: {
              backgroundColor: 'rgba(17, 24, 39, 0.9)',
              titleColor: '#fff',
              bodyColor: '#fff',
              padding: isMobile ? 6 : isTablet ? 8 : 10,
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
  }, [isLoading, portfolioChartInstance, assetAllocationChartInstance]);

  // Create skeleton for dashboard data
  const dashboardSkeleton = (
    <div className="space-y-6">
      {/* Portfolio Summary Cards Skeleton */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4 mb-8">
        {[1, 2, 3, 4].map((i) => (
          <div key={i} className="bg-gray-900 rounded-xl p-6 shadow-md">
            <div className="flex items-center justify-between mb-4">
              <div className="h-4 bg-gray-700 rounded w-1/3 animate-pulse"></div>
              <div className="h-4 bg-gray-700 rounded-full w-16 animate-pulse"></div>
            </div>
            <div className="h-8 bg-gray-700 rounded w-2/3 mb-2 animate-pulse"></div>
            <div className="h-4 bg-gray-700 rounded w-1/2 animate-pulse"></div>
          </div>
        ))}
      </div>
      
      {/* Chart Skeleton */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6 mb-8">
        <div className="bg-gray-900 rounded-xl p-6 shadow-md lg:col-span-2">
          <div className="flex justify-between items-center mb-6">
            <div className="h-5 bg-gray-700 rounded w-40 animate-pulse"></div>
            <div className="flex space-x-2">
              {[1, 2, 3, 4, 5].map((i) => (
                <div key={i} className="h-6 bg-gray-700 rounded w-8 animate-pulse"></div>
              ))}
            </div>
          </div>
          <div className="h-[300px] bg-gray-800 rounded-lg animate-pulse"></div>
        </div>
        
        <div className="bg-gray-900 rounded-xl p-6 shadow-md">
          <div className="flex justify-between items-center mb-4">
            <div className="h-5 bg-gray-700 rounded w-32 animate-pulse"></div>
            <div className="h-5 bg-gray-700 rounded w-8 animate-pulse"></div>
          </div>
          <div className="h-[240px] bg-gray-800 rounded-lg mb-4 animate-pulse"></div>
          <div className="space-y-2">
            {[1, 2, 3, 4, 5].map((i) => (
              <div key={i} className="flex justify-between">
                <div className="h-4 bg-gray-700 rounded w-1/3 animate-pulse"></div>
                <div className="h-4 bg-gray-700 rounded w-10 animate-pulse"></div>
              </div>
            ))}
          </div>
        </div>
      </div>
    </div>
  );
  
  // Import LoadingState and ErrorDisplay
  const LoadingState = React.lazy(() => import('../app/components/common/LoadingState'));
  const ErrorDisplay = React.lazy(() => import('../app/components/common/ErrorDisplay'));
  
  // Mock portfolio data
  const portfolioCards = [
    { title: 'Total Portfolio', value: '$34,567.89', change: '+$1,432.51 (4.3%)', trend: 'up', badge: '+12.5% YTD' },
    { title: 'AI Managed', value: '$21,250.42', change: '+$980.32 (4.8%)', trend: 'up', badge: '+18.3% YTD' },
    { title: 'High-Yield Savings', value: '$5,250.00', change: '$21.88 interest this month', trend: 'neutral', badge: '5.00% APY' },
    { title: 'Round-Ups', value: '$12.75', change: 'Pending this week', trend: 'neutral', badge: '$248 this year' }
  ];

  const wealthCards = [
    { title: 'Retirement', value: '$8,067.43', change: '+$1,250 (15.5%) YTD', trend: 'up', badge: 'Roth IRA' },
    { title: 'Elson Card', value: '$145.32', change: 'Rewards earned this month', trend: 'neutral', badge: 'Stock-Back®' },
    { title: 'Crypto', value: '$3,724.51', change: '+$425.21 (12.9%) today', trend: 'up', badge: '4 Assets' },
    { title: 'Tax Savings', value: '$347.92', change: 'Est. tax savings YTD', trend: 'up', badge: 'Harvesting' }
  ];

  const assets = [
    { symbol: 'AAPL', name: 'Apple Inc.', shares: '10.5 shares', value: '$1,947.25', change: '+$32.55 (1.7%)', color: 'blue' },
    { symbol: 'TSLA', name: 'Tesla, Inc.', shares: '8.2 shares', value: '$2,378.00', change: '+$189.42 (8.6%)', color: 'green' },
    { symbol: 'VOO', name: 'Vanguard S&P 500 ETF', shares: '15.3 shares', value: '$6,427.32', change: '+$107.10 (1.7%)', color: 'purple' },
    { symbol: 'BTC', name: 'Bitcoin', shares: '0.058 BTC', value: '$2,324.18', change: '+$212.50 (10.1%)', color: 'yellow' },
    { 
      symbol: <svg className="h-5 w-5" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke="currentColor">
        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M17 9V7a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2m2 4h10a2 2 0 002-2v-6a2 2 0 00-2-2H9a2 2 0 00-2 2v6a2 2 0 002 2zm7-5a2 2 0 11-4 0 2 2 0 014 0z" />
      </svg>, 
      name: 'High-Yield Savings', 
      shares: '5.00% APY', 
      value: '$5,250.00', 
      change: '+$21.88 this month', 
      color: 'pink' 
    }
  ];

  const aiInsights = [
    {
      title: 'Tax Loss Harvesting',
      subtitle: 'AI Tax Optimization',
      description: 'Potential tax savings of $125 identified. Consider selling MSFT position and buying similar asset.',
      icon: <svg className="h-4 w-4 text-green-300" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M9 12l2 2 4-4m5.618-4.016A11.955 11.955 0 0112 2.944a11.955 11.955 0 01-8.618 3.04A12.02 12.02 0 003 9c0 5.591 3.824 10.29 9 11.622 5.176-1.332 9-6.03 9-11.622 0-1.042-.133-2.052-.382-3.016z" />
            </svg>,
      iconBg: 'bg-green-900',
      primaryAction: 'Apply Strategy',
      secondaryAction: 'Dismiss'
    },
    {
      title: 'Retirement Planning',
      subtitle: 'Financial Coaching',
      description: 'You\'re on track to meet 85% of retirement goals. Increase monthly contribution by $75 to reach target.',
      icon: <svg className="h-4 w-4 text-blue-300" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M8 7V3m8 4V3m-9 8h10M5 21h14a2 2 0 002-2V7a2 2 0 00-2-2H5a2 2 0 00-2 2v12a2 2 0 002 2z" />
            </svg>,
      iconBg: 'bg-blue-900',
      primaryAction: 'Adjust Contribution',
      secondaryAction: 'Later'
    },
    {
      title: 'Stock-Back® Rewards',
      subtitle: 'Elson Card',
      description: 'You\'ve earned $42.18 in Stock-Back® rewards this week. Link more merchants for higher returns.',
      icon: <svg className="h-4 w-4 text-purple-300" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M3 10h18M7 15h1m4 0h1m-7 4h12a3 3 0 003-3V8a3 3 0 00-3-3H6a3 3 0 00-3 3v8a3 3 0 003 3z" />
            </svg>,
      iconBg: 'bg-purple-900',
      primaryAction: 'Manage Rewards',
      secondaryAction: 'Dismiss'
    }
  ];

  // Adjust chart options for mobile responsiveness
  useEffect(() => {
    const handleResize = () => {
      // Re-initialize charts when window size changes
      if (!isLoading) {
        initPortfolioChart();
        initAssetAllocationChart();
      }
    };
    
    // Define chart initialization functions in the scope where we can access window size
    const initPortfolioChart = () => {
      const portfolioCtx = document.getElementById('portfolioChart') as HTMLCanvasElement;
      if (!portfolioCtx) return;

      // Destroy existing chart if it exists
      if (portfolioChartInstance) {
        portfolioChartInstance.destroy();
      }

      const newPortfolioChart = new Chart(portfolioCtx, {
        type: 'line',
        data: {
          labels: ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun'],
          datasets: [
            {
              label: 'Portfolio Value',
              data: [32400, 33100, 32800, 33500, 34100, 34300, 34567],
              backgroundColor: 'rgba(139, 92, 246, 0.1)',
              borderColor: 'rgba(139, 92, 246, 1)',
              borderWidth: 2,
              pointBackgroundColor: 'rgba(139, 92, 246, 1)',
              pointBorderColor: '#fff',
              pointRadius: isMobile ? 2 : 4,
              pointHoverRadius: isMobile ? 4 : 6,
              tension: 0.3,
              fill: true
            },
            {
              label: 'S&P 500',
              data: [32400, 32600, 32900, 33000, 33400, 33600, 33900],
              borderColor: 'rgba(156, 163, 175, 0.7)',
              borderWidth: 2,
              pointBackgroundColor: 'rgba(156, 163, 175, 0.7)',
              pointBorderColor: '#fff',
              pointRadius: 0,
              pointHoverRadius: isMobile ? 2 : isTablet ? 3 : 4,
              tension: 0.3,
              borderDash: [5, 5],
              fill: false
            }
          ]
        },
        options: {
          responsive: true,
          maintainAspectRatio: false,
          plugins: {
            legend: {
              display: !isMobile,
          position: isTablet ? 'bottom' : 'top',
              position: 'top',
              labels: {
                color: '#e2e8f0',
                font: {
                  size: 12
                },
                boxWidth: 12
              }
            },
            tooltip: {
              mode: 'index',
              intersect: false,
              backgroundColor: 'rgba(17, 24, 39, 0.9)',
              titleColor: '#fff',
              bodyColor: '#fff',
              borderColor: 'rgba(139, 92, 246, 0.5)',
              borderWidth: 1,
              padding: isMobile ? 6 : 10,
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
                  size: isMobile ? 10 : 12
                },
                maxRotation: isMobile ? 45 : 0,
                autoSkip: isMobile
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
                  size: isMobile ? 10 : 12
                },
                callback: function(value) {
                  if (isMobile || isTablet) {
                    // Simplified format for mobile and tablet
                    return '$' + (value as number / 1000).toFixed(0) + 'k';
                  }
                  return '$' + value.toString().replace(/\B(?=(\d{3})+(?!\d))/g, ",");
                }
              },
              beginAtZero: false
            }
          }
        }
      });
      
      setPortfolioChartInstance(newPortfolioChart);
    };

    const initAssetAllocationChart = () => {
      const allocationCtx = document.getElementById('assetAllocationChart') as HTMLCanvasElement;
      if (!allocationCtx) return;

      // Destroy existing chart if it exists
      if (assetAllocationChartInstance) {
        assetAllocationChartInstance.destroy();
      }

      const newAllocationChart = new Chart(allocationCtx, {
        type: 'doughnut',
        data: {
          labels: ['Tech Stocks', 'Index ETFs', 'Clean Energy', 'Cryptocurrency', 'High-Yield Savings'],
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
          cutout: isMobile ? '60%' : isTablet ? '65%' : '70%',
          plugins: {
            legend: {
              display: false
            },
            tooltip: {
              backgroundColor: 'rgba(17, 24, 39, 0.9)',
              titleColor: '#fff',
              bodyColor: '#fff',
              padding: isMobile ? 6 : 10,
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

    // Add event listener for window resize
    window.addEventListener('resize', handleResize);
    
    // Initial setup
    handleResize();
    
    // Cleanup
    return () => {
      window.removeEventListener('resize', handleResize);
      if (portfolioChartInstance) {
        portfolioChartInstance.destroy();
      }
      if (assetAllocationChartInstance) {
        assetAllocationChartInstance.destroy();
      }
    };
  }, [isLoading, portfolioChartInstance, assetAllocationChartInstance]);

  return (
    <React.Suspense fallback={<Loading />}>
      <LoadingState 
        isLoading={isLoading} 
        error={error} 
        skeleton={dashboardSkeleton}
        onRetry={() => window.location.reload()}
      >
        <div className="main-content flex-1 bg-gray-800 min-h-screen p-4 sm:p-6 md:p-8">
          {/* Welcome Section */}
          <div className="flex flex-col sm:flex-row sm:justify-between sm:items-center gap-4 mb-6 sm:mb-8 transition-all">
            <div>
              <h1 className="text-xl sm:text-2xl font-bold text-white">Welcome back, {user?.username || 'Alex'}</h1>
              <p className="text-gray-400 text-sm sm:text-base">Here's what's happening with your investments today</p>
            </div>
            <div className="flex flex-row gap-3">
              <button className="bg-purple-700 hover:bg-purple-600 text-white px-3 sm:px-4 py-2 rounded-lg flex items-center text-sm sm:text-base flex-1 sm:flex-auto justify-center sm:justify-start transition-colors">
                <svg className="h-4 w-4 sm:h-5 sm:w-5 mr-1 sm:mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M12 6v6m0 0v6m0-6h6m-6 0H6"></path>
                </svg>
                Deposit
              </button>
              <button className="bg-gray-700 hover:bg-gray-600 text-white px-3 sm:px-4 py-2 rounded-lg flex items-center text-sm sm:text-base flex-1 sm:flex-auto justify-center sm:justify-start transition-colors">
                <svg className="h-4 w-4 sm:h-5 sm:w-5 mr-1 sm:mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M8 7h12m0 0l-4-4m4 4l-4 4m0 6H4m0 0l4 4m-4-4l4-4"></path>
                </svg>
                Withdraw
              </button>
            </div>
          </div>

          {/* Portfolio Summary Cards - Mobile Optimized with scrollable view */}
          <div className="mb-6 sm:mb-8 transition-all">
            <h3 className="text-lg font-semibold text-white mb-3 px-1">Portfolio Summary</h3>
            <div className="flex sm:grid sm:grid-cols-2 md:grid-cols-4 gap-3 sm:gap-4 overflow-x-auto sm:overflow-visible pb-4 sm:pb-0 -mx-4 sm:mx-0 px-4 sm:px-0">
              {portfolioCards.map((card, index) => (
                <div key={index} className="bg-gray-900 rounded-xl p-4 sm:p-6 shadow-md flex-shrink-0 w-72 sm:w-auto transition-all hover:shadow-lg hover:bg-gray-800">
                  <div className="flex items-center justify-between mb-3 sm:mb-4">
                    <h3 className="text-base sm:text-lg font-semibold text-white">{card.title}</h3>
                    <span className={`${card.title === 'High-Yield Savings' ? 'bg-green-900 text-green-300' : 'bg-purple-900 text-purple-300'} text-xs px-2 py-1 rounded-full whitespace-nowrap`}>
                      {card.badge}
                    </span>
                  </div>
                  <p className="text-xl sm:text-3xl font-bold text-white mb-2">{card.value}</p>
                  <div className={`flex items-center ${card.trend === 'up' ? 'text-green-400' : 'text-blue-400'} text-sm`}>
                    {card.trend === 'up' && (
                      <svg className="h-4 w-4 sm:h-5 sm:w-5 mr-1" fill="none" stroke="currentColor" viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M5 10l7-7m0 0l7 7m-7-7v18"></path>
                      </svg>
                    )}
                    <span>{card.change}</span>
                  </div>
                </div>
              ))}
            </div>
          </div>

          {/* Wealth Feature Cards - Mobile Optimized with scrollable view */}
          <div className="mb-6 sm:mb-8 transition-all">
            <h3 className="text-lg font-semibold text-white mb-3 px-1">Wealth Features</h3>
            <div className="flex sm:grid sm:grid-cols-2 md:grid-cols-4 gap-3 sm:gap-4 overflow-x-auto sm:overflow-visible pb-4 sm:pb-0 -mx-4 sm:mx-0 px-4 sm:px-0">
              {wealthCards.map((card, index) => (
                <div key={index} className="bg-gray-900 rounded-xl p-4 sm:p-6 shadow-md flex-shrink-0 w-72 sm:w-auto transition-all hover:shadow-lg hover:bg-gray-800">
                  <div className="flex items-center justify-between mb-3 sm:mb-4">
                    <h3 className="text-base sm:text-lg font-semibold text-white">{card.title}</h3>
                    <span className={`
                      ${card.title === 'Retirement' ? 'bg-blue-900 text-blue-300' : ''}
                      ${card.title === 'Elson Card' ? 'bg-purple-900 text-purple-300' : ''}
                      ${card.title === 'Crypto' ? 'bg-yellow-900 text-yellow-300' : ''}
                      ${card.title === 'Tax Savings' ? 'bg-green-900 text-green-300' : ''}
                      text-xs px-2 py-1 rounded-full whitespace-nowrap
                    `}>
                      {card.badge}
                    </span>
                  </div>
                  <p className="text-xl sm:text-3xl font-bold text-white mb-2">{card.value}</p>
                  <div className={`flex items-center ${card.trend === 'up' ? 'text-green-400' : 'text-blue-400'} text-sm`}>
                    {card.trend === 'up' && (
                      <svg className="h-4 w-4 sm:h-5 sm:w-5 mr-1" fill="none" stroke="currentColor" viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M5 10l7-7m0 0l7 7m-7-7v18"></path>
                      </svg>
                    )}
                    <span>{card.change}</span>
                  </div>
                </div>
              ))}
            </div>
          </div>

          {/* Portfolio Performance & Asset Allocation */}
          <div className="grid grid-cols-1 lg:grid-cols-3 gap-4 sm:gap-6 mb-6 sm:mb-8">
            <div className="bg-gray-900 rounded-xl p-4 sm:p-6 shadow-md lg:col-span-2 order-1 transition-all hover:shadow-lg">
              <div className="flex flex-col sm:flex-row sm:justify-between sm:items-center mb-4 sm:mb-6 gap-3">
                <h3 className="text-base sm:text-lg font-semibold text-white">Portfolio Performance</h3>
                <div className="flex flex-wrap gap-2">
                  <button className="bg-purple-800 text-purple-200 px-3 py-1 rounded-lg text-xs sm:text-sm transition-colors">1W</button>
                  <button className="bg-gray-800 text-gray-300 px-3 py-1 rounded-lg text-xs sm:text-sm hover:bg-purple-800 hover:text-purple-200 transition-colors">1M</button>
                  <button className="bg-gray-800 text-gray-300 px-3 py-1 rounded-lg text-xs sm:text-sm hover:bg-purple-800 hover:text-purple-200 transition-colors">3M</button>
                  <button className="bg-gray-800 text-gray-300 px-3 py-1 rounded-lg text-xs sm:text-sm hover:bg-purple-800 hover:text-purple-200 transition-colors">1Y</button>
                  <button className="bg-gray-800 text-gray-300 px-3 py-1 rounded-lg text-xs sm:text-sm hover:bg-purple-800 hover:text-purple-200 transition-colors">All</button>
                </div>
              </div>
              <div className="chart-container h-[250px] sm:h-[300px] w-full">
                <canvas id="portfolioChart"></canvas>
              </div>
            </div>
            
            <div className="bg-gray-900 rounded-xl p-4 sm:p-6 shadow-md order-2 transition-all hover:shadow-lg">
              <div className="flex justify-between items-center mb-3 sm:mb-4">
                <h3 className="text-base sm:text-lg font-semibold text-white">Asset Allocation</h3>
                <button className="text-purple-400 hover:text-purple-300 text-sm">
                  <svg className="h-5 w-5" fill="none" stroke="currentColor" viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M4 6h16M4 12h16M4 18h16"></path>
                  </svg>
                </button>
              </div>
              <div className="chart-container h-[180px] sm:h-[240px]">
                <canvas id="assetAllocationChart"></canvas>
              </div>
              <div className="grid grid-cols-2 sm:grid-cols-1 md:grid-cols-2 lg:grid-cols-1 gap-2 mt-3 sm:mt-4 text-xs sm:text-sm">
                <div className="flex items-center justify-between">
                  <div className="flex items-center">
                    <div className="w-2 h-2 sm:w-3 sm:h-3 rounded-full bg-purple-500 mr-1 sm:mr-2"></div>
                    <span className="text-gray-300">Tech Stocks</span>
                  </div>
                  <span className="text-gray-300">35%</span>
                </div>
                <div className="flex items-center justify-between">
                  <div className="flex items-center">
                    <div className="w-2 h-2 sm:w-3 sm:h-3 rounded-full bg-blue-500 mr-1 sm:mr-2"></div>
                    <span className="text-gray-300">Index ETFs</span>
                  </div>
                  <span className="text-gray-300">25%</span>
                </div>
                <div className="flex items-center justify-between">
                  <div className="flex items-center">
                    <div className="w-2 h-2 sm:w-3 sm:h-3 rounded-full bg-green-500 mr-1 sm:mr-2"></div>
                    <span className="text-gray-300">Clean Energy</span>
                  </div>
                  <span className="text-gray-300">10%</span>
                </div>
                <div className="flex items-center justify-between">
                  <div className="flex items-center">
                    <div className="w-2 h-2 sm:w-3 sm:h-3 rounded-full bg-yellow-500 mr-1 sm:mr-2"></div>
                    <span className="text-gray-300">Crypto</span>
                  </div>
                  <span className="text-gray-300">15%</span>
                </div>
                <div className="flex items-center justify-between">
                  <div className="flex items-center">
                    <div className="w-2 h-2 sm:w-3 sm:h-3 rounded-full bg-pink-500 mr-1 sm:mr-2"></div>
                    <span className="text-gray-300">Savings</span>
                  </div>
                  <span className="text-gray-300">15%</span>
                </div>
              </div>
            </div>
          </div>

          {/* Your Assets & AI Insights */}
          <div className="grid grid-cols-1 lg:grid-cols-5 gap-4 sm:gap-6">
            {/* Your Assets */}
            <div className="bg-gray-900 rounded-xl p-4 sm:p-6 shadow-md lg:col-span-3 order-2 lg:order-1 transition-all hover:shadow-lg">
              <div className="flex justify-between items-center mb-4 sm:mb-6">
                <h3 className="text-base sm:text-lg font-semibold text-white">Your Assets</h3>
                <button className="text-purple-400 hover:text-purple-300 text-xs sm:text-sm flex items-center transition-colors">
                  View All
                  <svg className="h-3 w-3 sm:h-4 sm:w-4 ml-1" fill="none" stroke="currentColor" viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M9 5l7 7-7 7"></path>
                  </svg>
                </button>
              </div>
              
              <div className="divide-y divide-gray-800">
                {assets.map((asset, index) => (
                  <div key={index} className="asset-item flex items-center py-3 sm:py-4 px-2 rounded-lg transition-all hover:bg-gray-800 cursor-pointer">
                    <div className={`flex-shrink-0 h-8 w-8 sm:h-10 sm:w-10 rounded-full bg-${asset.color}-900 flex items-center justify-center text-${asset.color}-300 font-bold`}>
                      {typeof asset.symbol === 'string' ? asset.symbol : asset.symbol}
                    </div>
                    <div className="ml-3 sm:ml-4 flex-1 min-w-0">
                      <h4 className="text-white font-medium text-sm sm:text-base truncate">{asset.name}</h4>
                      <p className="text-gray-400 text-xs sm:text-sm">{asset.shares}</p>
                    </div>
                    <div className="text-right ml-2">
                      <p className="text-white font-medium text-sm sm:text-base">{asset.value}</p>
                      <p className={`${asset.change.includes('+') ? 'text-green-400' : 'text-blue-400'} text-xs sm:text-sm`}>{asset.change}</p>
                    </div>
                  </div>
                ))}
              </div>
            </div>
            
            {/* AI Insights */}
            <div className="bg-gray-900 rounded-xl p-4 sm:p-6 shadow-md lg:col-span-2 order-1 lg:order-2 mb-4 lg:mb-0 transition-all hover:shadow-lg">
              <div className="flex justify-between items-center mb-4 sm:mb-6">
                <h3 className="text-base sm:text-lg font-semibold text-white">AI Insights</h3>
                <div className="px-2 py-1 bg-purple-900 bg-opacity-60 rounded-full text-xs text-purple-200 whitespace-nowrap">
                  Updated 5 min ago
                </div>
              </div>
              
              <div className="space-y-4 sm:space-y-6">
                {aiInsights.map((insight, index) => (
                  <div key={index} className="bg-gray-800 p-3 sm:p-4 rounded-lg hover:bg-gray-700 transition-colors">
                    <div className="flex items-center mb-2 sm:mb-3">
                      <div className={`h-6 w-6 sm:h-8 sm:w-8 rounded-full ${insight.iconBg} flex items-center justify-center`}>
                        {insight.icon}
                      </div>
                      <div className="ml-2 sm:ml-3">
                        <h4 className="text-white font-medium text-sm sm:text-base">{insight.title}</h4>
                        <p className="text-gray-400 text-xs">{insight.subtitle}</p>
                      </div>
                    </div>
                    <p className="text-gray-300 text-xs sm:text-sm">{insight.description}</p>
                    <div className="mt-2 sm:mt-3 flex justify-end space-x-2">
                      <button className="text-gray-400 text-xs hover:text-gray-300 transition-colors py-1 px-2">{insight.secondaryAction}</button>
                      <button className="text-purple-400 text-xs hover:text-purple-300 transition-colors py-1 px-2">{insight.primaryAction}</button>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          </div>
        </div>
      </LoadingState>
    </React.Suspense>
  );
}