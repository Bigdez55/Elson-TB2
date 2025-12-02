import React, { useState, useEffect, useRef, useCallback } from 'react';
import { useSelector, useDispatch } from 'react-redux';
import { RootState, AppDispatch } from '../store/store';
import { 
  fetchPortfolioSummary, 
  fetchPerformance, 
  refreshPortfolioData 
} from '../store/slices/portfolioSlice';
import Chart from 'chart.js/auto';
import { TrendingUp, TrendingDown, RefreshCw, PieChart as PieChartIcon } from 'lucide-react';

const PortfolioPage: React.FC = () => {
  const dispatch = useDispatch<AppDispatch>();
  const { portfolio, holdings, performance, isLoading, error } = useSelector((state: RootState) => state.portfolio);
  
  const [activeTab, setActiveTab] = useState('overview');
  const [refreshing, setRefreshing] = useState(false);
  const performanceChartRef = useRef<HTMLCanvasElement>(null);
  const allocationChartRef = useRef<HTMLCanvasElement>(null);
  const chartInstancesRef = useRef<{ performance?: Chart; allocation?: Chart }>({});
  
  // Fetch data on component mount
  useEffect(() => {
    dispatch(fetchPortfolioSummary());
    dispatch(fetchPerformance());
  }, [dispatch]);
  
  const initializeCharts = useCallback(() => {
    // Performance Chart
    if (performanceChartRef.current && performance) {
      if (chartInstancesRef.current.performance) {
        chartInstancesRef.current.performance.destroy();
      }
      
      const ctx = performanceChartRef.current.getContext('2d');
      if (ctx) {
        chartInstancesRef.current.performance = new Chart(ctx, {
          type: 'line',
          data: {
            labels: performance.dates || ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun'],
            datasets: [
              {
                label: 'Portfolio Value',
                data: performance.values || [18500, 19200, 18900, 20100, 22000, 23400],
                backgroundColor: 'rgba(59, 130, 246, 0.1)',
                borderColor: 'rgba(59, 130, 246, 1)',
                borderWidth: 2,
                fill: true,
                tension: 0.4
              },
              {
                label: 'S&P 500',
                data: performance.benchmark || [18500, 18700, 19100, 19800, 20400, 21000],
                borderColor: 'rgba(156, 163, 175, 0.7)',
                borderWidth: 2,
                borderDash: [5, 5],
                fill: false,
                tension: 0.4
              }
            ]
          },
          options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
              legend: {
                position: 'top',
                labels: {
                  usePointStyle: true,
                  padding: 20
                }
              },
              tooltip: {
                mode: 'index',
                intersect: false,
                backgroundColor: 'rgba(17, 24, 39, 0.9)',
                titleColor: '#fff',
                bodyColor: '#fff',
                borderColor: 'rgba(59, 130, 246, 1)',
                borderWidth: 1,
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
                  display: false
                },
                ticks: {
                  color: '#6b7280'
                }
              },
              y: {
                grid: {
                  color: 'rgba(229, 231, 235, 0.5)'
                },
                ticks: {
                  color: '#6b7280',
                  callback: function(value) {
                    return '$' + (value as number / 1000).toFixed(0) + 'k';
                  }
                }
              }
            }
          }
        });
      }
    }
    
    // Asset Allocation Chart
    if (allocationChartRef.current && holdings.length > 0) {
      if (chartInstancesRef.current.allocation) {
        chartInstancesRef.current.allocation.destroy();
      }
      
      const ctx = allocationChartRef.current.getContext('2d');
      if (ctx) {
        const colors = [
          '#3b82f6', // blue
          '#ef4444', // red
          '#10b981', // green
          '#f59e0b', // amber
          '#8b5cf6', // violet
          '#ec4899', // pink
          '#06b6d4', // cyan
          '#84cc16', // lime
        ];
        
        chartInstancesRef.current.allocation = new Chart(ctx, {
          type: 'doughnut',
          data: {
            labels: holdings.map(h => h.symbol),
            datasets: [{
              data: holdings.map(h => h.current_allocation_percentage || h.market_value),
              backgroundColor: colors.slice(0, holdings.length),
              borderWidth: 2,
              borderColor: '#ffffff',
              hoverOffset: 8
            }]
          },
          options: {
            responsive: true,
            maintainAspectRatio: false,
            cutout: '60%',
            plugins: {
              legend: {
                position: 'right',
                labels: {
                  usePointStyle: true,
                  padding: 15,
                  generateLabels: function(chart) {
                    const data = chart.data;
                    if (data.labels?.length && data.datasets.length) {
                      return data.labels.map((label, i) => {
                        const value = data.datasets[0].data[i] as number;
                        return {
                          text: `${label} (${value > 1 ? value.toFixed(1) + '%' : '$' + value.toLocaleString()})`,
                          fillStyle: (data.datasets[0].backgroundColor as string[])?.[i] as string,
                          strokeStyle: (data.datasets[0].backgroundColor as string[])?.[i] as string,
                          lineWidth: 0,
                          pointStyle: 'circle'
                        };
                      });
                    }
                    return [];
                  }
                }
              },
              tooltip: {
                backgroundColor: 'rgba(17, 24, 39, 0.9)',
                titleColor: '#fff',
                bodyColor: '#fff',
                borderColor: 'rgba(59, 130, 246, 1)',
                borderWidth: 1,
                callbacks: {
                  label: function(context) {
                    const holding = holdings[context.dataIndex];
                    const allocation = context.parsed || 0;
                    return [
                      `${context.label}: ${allocation > 1 ? allocation.toFixed(1) + '%' : '$' + allocation.toLocaleString()}`,
                      `Market Value: $${holding.market_value.toLocaleString()}`,
                      `P&L: ${holding.unrealized_gain_loss >= 0 ? '+' : ''}$${holding.unrealized_gain_loss.toLocaleString()}`
                    ];
                  }
                }
              }
            }
          }
        });
      }
    }
  }, [performance, holdings]);
  
  // Initialize charts when data is available
  useEffect(() => {
    if (performance || holdings.length > 0) {
      initializeCharts();
    }
    
    // Capture current instances for cleanup
    const currentInstances = chartInstancesRef.current;
    
    return () => {
      // Cleanup charts on unmount
      Object.values(currentInstances).forEach(chart => {
        if (chart) chart.destroy();
      });
    };
  }, [initializeCharts, holdings.length, performance]);
  
  const handleRefresh = async () => {
    setRefreshing(true);
    try {
      await Promise.all([
        dispatch(fetchPortfolioSummary()),
        dispatch(refreshPortfolioData()),
        dispatch(fetchPerformance())
      ]);
    } finally {
      setRefreshing(false);
    }
  };
  
  // Calculate total P&L
  const totalUnrealizedPL = holdings.reduce((sum, holding) => sum + holding.unrealized_gain_loss, 0);
  const totalUnrealizedPLPercent = holdings.length > 0 
    ? holdings.reduce((sum, holding) => sum + holding.unrealized_gain_loss_percentage, 0) / holdings.length
    : 0;
  
  // Get best and worst performers
  const bestPerformer = holdings.reduce((best, current) => 
    current.unrealized_gain_loss_percentage > best.unrealized_gain_loss_percentage ? current : best
  , holdings[0] || null);
  
  const worstPerformer = holdings.reduce((worst, current) => 
    current.unrealized_gain_loss_percentage < worst.unrealized_gain_loss_percentage ? current : worst
  , holdings[0] || null);
  
  if (isLoading && !portfolio) {
    return (
      <div className="flex items-center justify-center min-h-96">
        <div className="animate-spin rounded-full h-32 w-32 border-b-2 border-blue-600"></div>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex justify-between items-center">
        <h1 className="text-3xl font-bold text-gray-900">Portfolio Dashboard</h1>
        <button
          onClick={handleRefresh}
          disabled={refreshing}
          className="inline-flex items-center px-4 py-2 border border-transparent text-sm font-medium rounded-md text-white bg-blue-600 hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed transition-colors duration-200"
        >
          <RefreshCw className={`h-4 w-4 mr-2 ${refreshing ? 'animate-spin' : ''}`} />
          {refreshing ? 'Refreshing...' : 'Refresh'}
        </button>
      </div>

      {error && (
        <div className="bg-red-50 border border-red-200 rounded-lg p-4">
          <div className="flex">
            <div className="flex-shrink-0">
              <svg className="h-5 w-5 text-red-400" viewBox="0 0 20 20" fill="currentColor">
                <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zM8.707 7.293a1 1 0 00-1.414 1.414L8.586 10l-1.293 1.293a1 1 0 101.414 1.414L10 11.414l1.293 1.293a1 1 0 001.414-1.414L11.414 10l1.293-1.293a1 1 0 00-1.414-1.414L10 8.586 8.707 7.293z" clipRule="evenodd" />
              </svg>
            </div>
            <div className="ml-3">
              <p className="text-sm text-red-800">{error}</p>
            </div>
          </div>
        </div>
      )}

      {/* Portfolio Summary */}
      <div className="bg-gradient-to-r from-blue-600 to-blue-700 rounded-lg shadow-lg p-6 text-white">
        <div className="flex justify-between items-start mb-6">
          <div>
            <h2 className="text-xl font-bold mb-1">Portfolio Overview</h2>
            <p className="text-blue-100 text-sm">Real-time portfolio performance</p>
          </div>
          <div className="text-right">
            <p className="text-3xl font-bold">${portfolio?.total_value?.toLocaleString() || '0.00'}</p>
            <div className="flex items-center justify-end mt-1">
              {(portfolio?.total_return || 0) >= 0 ? (
                <TrendingUp className="h-4 w-4 mr-1" />
              ) : (
                <TrendingDown className="h-4 w-4 mr-1" />
              )}
              <span className="text-sm">
                {(portfolio?.total_return || 0) >= 0 ? '+' : ''}${portfolio?.total_return?.toLocaleString() || '0.00'} 
                ({(portfolio?.total_return_percentage || 0).toFixed(2)}%)
              </span>
            </div>
          </div>
        </div>
        
        <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
          <div className="bg-blue-500 bg-opacity-30 rounded-lg p-4">
            <p className="text-blue-100 text-sm mb-1">Cash Balance</p>
            <p className="text-xl font-bold">${portfolio?.cash_balance?.toLocaleString() || '0.00'}</p>
          </div>
          <div className="bg-blue-500 bg-opacity-30 rounded-lg p-4">
            <p className="text-blue-100 text-sm mb-1">Invested Amount</p>
            <p className="text-xl font-bold">${portfolio?.invested_amount?.toLocaleString() || '0.00'}</p>
          </div>
          <div className="bg-blue-500 bg-opacity-30 rounded-lg p-4">
            <p className="text-blue-100 text-sm mb-1">Today's P&L</p>
            <p className={`text-xl font-bold ${totalUnrealizedPL >= 0 ? 'text-green-300' : 'text-red-300'}`}>
              {totalUnrealizedPL >= 0 ? '+' : ''}${totalUnrealizedPL.toLocaleString()}
            </p>
            <p className="text-sm text-blue-100">({totalUnrealizedPLPercent.toFixed(2)}%)</p>
          </div>
          <div className="bg-blue-500 bg-opacity-30 rounded-lg p-4">
            <p className="text-blue-100 text-sm mb-1">Total Positions</p>
            <p className="text-xl font-bold">{holdings.length}</p>
          </div>
        </div>
      </div>

      {/* Performance Highlights */}
      {holdings.length > 0 && (
        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
          <div className="bg-white rounded-lg shadow-lg p-6">
            <h3 className="text-lg font-semibold text-gray-900 mb-4 flex items-center">
              <TrendingUp className="h-5 w-5 mr-2 text-green-600" />
              Best Performer
            </h3>
            {bestPerformer && (
              <div className="flex justify-between items-center p-4 bg-green-50 rounded-lg">
                <div>
                  <p className="font-bold text-gray-900">{bestPerformer.symbol}</p>
                  <p className="text-sm text-gray-600">${bestPerformer.market_value.toLocaleString()}</p>
                </div>
                <div className="text-right">
                  <p className="font-bold text-green-600">
                    +${bestPerformer.unrealized_gain_loss.toLocaleString()}
                  </p>
                  <p className="text-sm text-green-600">
                    +{bestPerformer.unrealized_gain_loss_percentage.toFixed(2)}%
                  </p>
                </div>
              </div>
            )}
          </div>

          <div className="bg-white rounded-lg shadow-lg p-6">
            <h3 className="text-lg font-semibold text-gray-900 mb-4 flex items-center">
              <TrendingDown className="h-5 w-5 mr-2 text-red-600" />
              Worst Performer
            </h3>
            {worstPerformer && (
              <div className="flex justify-between items-center p-4 bg-red-50 rounded-lg">
                <div>
                  <p className="font-bold text-gray-900">{worstPerformer.symbol}</p>
                  <p className="text-sm text-gray-600">${worstPerformer.market_value.toLocaleString()}</p>
                </div>
                <div className="text-right">
                  <p className="font-bold text-red-600">
                    ${worstPerformer.unrealized_gain_loss.toLocaleString()}
                  </p>
                  <p className="text-sm text-red-600">
                    {worstPerformer.unrealized_gain_loss_percentage.toFixed(2)}%
                  </p>
                </div>
              </div>
            )}
          </div>
        </div>
      )}

      {/* Tab Navigation */}
      <div className="bg-white rounded-lg shadow-lg">
        <div className="border-b border-gray-200">
          <nav className="-mb-px flex space-x-8 px-6">
            {[
              { id: 'overview', name: 'Overview', icon: PieChartIcon },
              { id: 'holdings', name: 'Holdings', icon: TrendingUp },
              { id: 'performance', name: 'Performance', icon: TrendingUp }
            ].map((tab) => (
              <button
                key={tab.id}
                onClick={() => setActiveTab(tab.id)}
                className={`${
                  activeTab === tab.id
                    ? 'border-blue-500 text-blue-600'
                    : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
                } whitespace-nowrap py-4 px-1 border-b-2 font-medium text-sm flex items-center transition-colors duration-200`}
              >
                <tab.icon className="h-4 w-4 mr-2" />
                {tab.name}
              </button>
            ))}
          </nav>
        </div>

        <div className="p-6">
          {/* Overview Tab */}
          {activeTab === 'overview' && (
            <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
              {/* Asset Allocation Chart */}
              <div>
                <h3 className="text-lg font-semibold text-gray-900 mb-4">Asset Allocation</h3>
                {holdings.length > 0 ? (
                  <div className="h-80">
                    <canvas ref={allocationChartRef}></canvas>
                  </div>
                ) : (
                  <div className="h-80 bg-gray-50 rounded-lg flex items-center justify-center">
                    <div className="text-center">
                      <PieChartIcon className="h-12 w-12 text-gray-300 mx-auto mb-4" />
                      <p className="text-gray-500">No holdings to display</p>
                      <p className="text-sm text-gray-400">Start trading to see your allocation</p>
                    </div>
                  </div>
                )}
              </div>

              {/* Performance Chart */}
              <div>
                <h3 className="text-lg font-semibold text-gray-900 mb-4">Performance Chart</h3>
                <div className="h-80">
                  <canvas ref={performanceChartRef}></canvas>
                </div>
              </div>
            </div>
          )}

          {/* Holdings Tab */}
          {activeTab === 'holdings' && (
            <div>
              <h3 className="text-lg font-semibold text-gray-900 mb-4">Your Holdings</h3>
              {holdings.length > 0 ? (
                <div className="overflow-x-auto">
                  <table className="min-w-full divide-y divide-gray-200">
                    <thead className="bg-gray-50">
                      <tr>
                        <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Symbol</th>
                        <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Quantity</th>
                        <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Avg Cost</th>
                        <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Current Price</th>
                        <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Market Value</th>
                        <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">P&L</th>
                        <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">P&L %</th>
                      </tr>
                    </thead>
                    <tbody className="bg-white divide-y divide-gray-200">
                      {holdings.map((holding) => (
                        <tr key={holding.id} className="hover:bg-gray-50">
                          <td className="px-6 py-4 whitespace-nowrap">
                            <div className="text-sm font-medium text-gray-900">{holding.symbol}</div>
                            <div className="text-sm text-gray-500">{holding.asset_type}</div>
                          </td>
                          <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                            {holding.quantity.toLocaleString()}
                          </td>
                          <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                            ${holding.average_cost.toFixed(2)}
                          </td>
                          <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                            ${holding.current_price.toFixed(2)}
                          </td>
                          <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                            ${holding.market_value.toLocaleString()}
                          </td>
                          <td className={`px-6 py-4 whitespace-nowrap text-sm font-medium ${
                            holding.unrealized_gain_loss >= 0 ? 'text-green-600' : 'text-red-600'
                          }`}>
                            {holding.unrealized_gain_loss >= 0 ? '+' : ''}${holding.unrealized_gain_loss.toLocaleString()}
                          </td>
                          <td className={`px-6 py-4 whitespace-nowrap text-sm font-medium ${
                            holding.unrealized_gain_loss_percentage >= 0 ? 'text-green-600' : 'text-red-600'
                          }`}>
                            {holding.unrealized_gain_loss_percentage >= 0 ? '+' : ''}{holding.unrealized_gain_loss_percentage.toFixed(2)}%
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              ) : (
                <div className="text-center py-12">
                  <TrendingUp className="h-12 w-12 text-gray-300 mx-auto mb-4" />
                  <p className="text-gray-500 text-lg">No holdings found</p>
                  <p className="text-sm text-gray-400 mb-6">Start trading to build your portfolio</p>
                  <button className="inline-flex items-center px-4 py-2 border border-transparent text-sm font-medium rounded-md text-white bg-blue-600 hover:bg-blue-700">
                    Start Trading
                  </button>
                </div>
              )}
            </div>
          )}

          {/* Performance Tab */}
          {activeTab === 'performance' && (
            <div>
              <h3 className="text-lg font-semibold text-gray-900 mb-4">Portfolio Performance</h3>
              <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
                <div className="lg:col-span-2">
                  <div className="h-96">
                    <canvas ref={performanceChartRef}></canvas>
                  </div>
                </div>
                <div className="space-y-4">
                  <div className="bg-gray-50 rounded-lg p-4">
                    <h4 className="text-sm font-medium text-gray-900 mb-2">Performance Metrics</h4>
                    <div className="space-y-2">
                      <div className="flex justify-between">
                        <span className="text-sm text-gray-600">Total Return:</span>
                        <span className={`text-sm font-medium ${
                          (portfolio?.total_return || 0) >= 0 ? 'text-green-600' : 'text-red-600'
                        }`}>
                          {(portfolio?.total_return || 0) >= 0 ? '+' : ''}${portfolio?.total_return?.toLocaleString() || '0.00'}
                        </span>
                      </div>
                      <div className="flex justify-between">
                        <span className="text-sm text-gray-600">Total Return %:</span>
                        <span className={`text-sm font-medium ${
                          (portfolio?.total_return_percentage || 0) >= 0 ? 'text-green-600' : 'text-red-600'
                        }`}>
                          {(portfolio?.total_return_percentage || 0).toFixed(2)}%
                        </span>
                      </div>
                      <div className="flex justify-between">
                        <span className="text-sm text-gray-600">Unrealized P&L:</span>
                        <span className={`text-sm font-medium ${
                          totalUnrealizedPL >= 0 ? 'text-green-600' : 'text-red-600'
                        }`}>
                          {totalUnrealizedPL >= 0 ? '+' : ''}${totalUnrealizedPL.toLocaleString()}
                        </span>
                      </div>
                    </div>
                  </div>
                  
                  {performance?.risk_metrics && (
                    <div className="bg-gray-50 rounded-lg p-4">
                      <h4 className="text-sm font-medium text-gray-900 mb-2">Risk Metrics</h4>
                      <div className="space-y-2">
                        <div className="flex justify-between">
                          <span className="text-sm text-gray-600">Volatility:</span>
                          <span className="text-sm font-medium">{performance.risk_metrics.volatility?.toFixed(2)}%</span>
                        </div>
                        <div className="flex justify-between">
                          <span className="text-sm text-gray-600">Sharpe Ratio:</span>
                          <span className="text-sm font-medium">{performance.risk_metrics.sharpe_ratio?.toFixed(2)}</span>
                        </div>
                        <div className="flex justify-between">
                          <span className="text-sm text-gray-600">Max Drawdown:</span>
                          <span className="text-sm font-medium text-red-600">{performance.risk_metrics.max_drawdown?.toFixed(2)}%</span>
                        </div>
                      </div>
                    </div>
                  )}
                </div>
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
};

export default PortfolioPage;