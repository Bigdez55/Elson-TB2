import React, { useState, useEffect, useCallback } from 'react';
import { useSelector } from 'react-redux';
import { RootState } from '../../store/store';
import { useAccessibility } from '../../hooks/useAccessibility';
import { useTradingContext } from '../../contexts/TradingContext';
import { useGetBatchDataQuery } from '../../services/tradingApi';
import Chart from 'chart.js/auto';
import LoadingSpinner from '../common/LoadingSpinner';
import { Link } from 'react-router-dom';

/**
 * Mobile-optimized Portfolio component
 * Designed for small screens with touch-friendly interface and simplified UI
 */
export default function MobilePortfolio() {
  const [performanceChartInstance, setPerformanceChartInstance] = useState<Chart | null>(null);
  const [allocationChartInstance, setAllocationChartInstance] = useState<Chart | null>(null);
  const [activeTab, setActiveTab] = useState('holdings');

  // Accessibility context for user preferences
  const { prefersReducedMotion, announce } = useAccessibility();

  // Get trading mode and real data
  const { mode } = useTradingContext();
  const { data: batchData, isLoading, error } = useGetBatchDataQuery({ mode });

  const portfolio = batchData?.portfolio;
  const positions = batchData?.positions || [];
  const recentOrders = batchData?.recent_orders || [];

  // Initialize charts with real data
  useEffect(() => {
    if (isLoading || !portfolio) return;

    // Performance Chart - Simplified for mobile
    const initPerformanceChart = () => {
      const ctx = document.getElementById('mobilePerformanceChart') as HTMLCanvasElement;
      if (!ctx) return;

      // Destroy existing chart if it exists
      if (performanceChartInstance) {
        performanceChartInstance.destroy();
      }

      // Use actual portfolio value for chart
      const currentValue = portfolio.total_value || 0;
      const labels = ['Now'];
      const data = [currentValue];

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
              pointRadius: 4,
              tension: 0.3,
              fill: true
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
              display: false,
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
                  return `Portfolio: $${value.toLocaleString()}`;
                }
              }
            }
          },
          scales: {
            x: {
              grid: { display: false },
              ticks: { color: '#9CA3AF', font: { size: 10 } }
            },
            y: {
              grid: { color: 'rgba(75, 85, 99, 0.3)' },
              ticks: {
                color: '#9CA3AF',
                font: { size: 10 },
                callback: function(value) {
                  return '$' + (Number(value) / 1000).toFixed(0) + 'K';
                }
              }
            }
          }
        }
      });
      setPerformanceChartInstance(newChart);
    };

    // Allocation Chart
    const initAllocationChart = () => {
      const ctx = document.getElementById('mobileAllocationChart') as HTMLCanvasElement;
      if (!ctx) return;

      if (allocationChartInstance) {
        allocationChartInstance.destroy();
      }

      // Calculate allocation from positions
      const totalValue = positions.reduce((sum, pos) => sum + pos.market_value, 0);
      const labels = positions.slice(0, 5).map(p => p.symbol);
      const data = positions.slice(0, 5).map(p => totalValue > 0 ? (p.market_value / totalValue) * 100 : 0);

      if (positions.length > 5) {
        const otherValue = positions.slice(5).reduce((sum, p) => sum + p.market_value, 0);
        labels.push('Other');
        data.push(totalValue > 0 ? (otherValue / totalValue) * 100 : 0);
      }

      const colors = [
        'rgba(139, 92, 246, 0.8)',
        'rgba(59, 130, 246, 0.8)',
        'rgba(16, 185, 129, 0.8)',
        'rgba(245, 158, 11, 0.8)',
        'rgba(236, 72, 153, 0.8)',
        'rgba(156, 163, 175, 0.8)'
      ];

      const newChart = new Chart(ctx, {
        type: 'doughnut',
        data: {
          labels: labels,
          datasets: [{
            data: data,
            backgroundColor: colors.slice(0, labels.length),
            borderWidth: 0,
          }]
        },
        options: {
          responsive: true,
          maintainAspectRatio: false,
          cutout: '65%',
          animation: {
            duration: prefersReducedMotion ? 0 : 600,
          },
          plugins: {
            legend: {
              display: true,
              position: 'bottom',
              labels: { color: '#9CA3AF', font: { size: 10 }, boxWidth: 12 }
            },
            tooltip: {
              backgroundColor: 'rgba(17, 24, 39, 0.9)',
              callbacks: {
                label: function(context) {
                  return `${context.label}: ${context.parsed.toFixed(1)}%`;
                }
              }
            }
          }
        }
      });
      setAllocationChartInstance(newChart);
    };

    initPerformanceChart();
    initAllocationChart();

    return () => {
      if (performanceChartInstance) performanceChartInstance.destroy();
      if (allocationChartInstance) allocationChartInstance.destroy();
    };
  }, [isLoading, portfolio, positions, performanceChartInstance, allocationChartInstance, prefersReducedMotion]);

  const handleTabChange = (tab: string) => {
    setActiveTab(tab);
    announce(`${tab} tab selected`, false);
  };

  if (isLoading) {
    return (
      <div className="flex items-center justify-center min-h-[70vh]">
        <LoadingSpinner size="large" color="text-purple-600" text="Loading portfolio..." />
      </div>
    );
  }

  if (error) {
    return (
      <div className="p-4 text-center">
        <div className="bg-red-900/30 rounded-xl p-6">
          <p className="text-red-400">Failed to load portfolio data</p>
          <button
            onClick={() => window.location.reload()}
            className="mt-4 bg-purple-600 text-white px-4 py-2 rounded-lg"
          >
            Retry
          </button>
        </div>
      </div>
    );
  }

  const totalValue = portfolio?.total_value || 0;
  const dayPnl = portfolio?.day_pnl || 0;
  const dayPnlPercent = portfolio?.day_pnl_percent || 0;
  const totalPnl = portfolio?.total_pnl || 0;
  const totalPnlPercent = portfolio?.total_pnl_percent || 0;

  return (
    <div className="mobile-portfolio pb-16 prevent-pull-refresh">
      {/* Portfolio Summary */}
      <div className="bg-gray-900 p-4 mb-4 rounded-xl">
        <h1 className="text-xl font-bold text-white mb-1">My Portfolio</h1>
        <div className="flex items-baseline justify-between">
          <span className="text-2xl font-bold text-white">
            ${totalValue.toLocaleString('en-US', { minimumFractionDigits: 2, maximumFractionDigits: 2 })}
          </span>
          <span className={`text-sm ${dayPnl >= 0 ? 'text-green-400' : 'text-red-400'}`}>
            {dayPnl >= 0 ? '+' : ''}${dayPnl.toFixed(2)} ({dayPnlPercent.toFixed(2)}%) today
          </span>
        </div>
        <div className="flex mt-6 gap-2 justify-between">
          <div className="flex-1 bg-gray-800 p-3 rounded-lg">
            <p className="text-gray-400 text-xs mb-1">Total Return</p>
            <p className={`text-lg font-bold ${totalPnlPercent >= 0 ? 'text-green-400' : 'text-red-400'}`}>
              {totalPnlPercent >= 0 ? '+' : ''}{totalPnlPercent.toFixed(1)}%
            </p>
            <p className="text-gray-400 text-xs">
              {totalPnl >= 0 ? '+' : ''}${Math.abs(totalPnl).toFixed(2)}
            </p>
          </div>
          <div className="flex-1 bg-gray-800 p-3 rounded-lg">
            <p className="text-gray-400 text-xs mb-1">Positions</p>
            <p className="text-purple-400 text-lg font-bold">{positions.length}</p>
            <p className="text-gray-400 text-xs">Holdings</p>
          </div>
          <div className="flex-1 bg-gray-800 p-3 rounded-lg">
            <p className="text-gray-400 text-xs mb-1">Mode</p>
            <p className="text-purple-400 text-lg font-bold capitalize">{mode}</p>
            <p className="text-gray-400 text-xs">Trading</p>
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
            </div>

            {positions.length === 0 ? (
              <div className="text-center py-8">
                <p className="text-gray-400 mb-4">No positions yet</p>
                <Link
                  to={`/${mode}/trading`}
                  className="bg-purple-600 text-white px-4 py-2 rounded-lg inline-block"
                >
                  Start Trading
                </Link>
              </div>
            ) : (
              <div className="max-h-[400px] overflow-y-auto hide-scrollbar">
                {positions.map((position) => (
                  <div key={position.id} className="py-3 border-b border-gray-800 last:border-b-0">
                    <div className="flex justify-between items-start mb-1">
                      <div>
                        <div className="flex items-center">
                          <span className="text-white font-medium">{position.symbol}</span>
                        </div>
                        <p className="text-xs text-gray-400">{position.quantity.toFixed(4)} shares</p>
                      </div>
                      <div className="text-right">
                        <p className="text-white font-medium">${position.market_value.toFixed(2)}</p>
                        <p className={`text-xs ${position.unrealized_pnl >= 0 ? 'text-green-400' : 'text-red-400'}`}>
                          {position.unrealized_pnl >= 0 ? '+' : ''}${position.unrealized_pnl.toFixed(2)} ({position.unrealized_pnl_percent.toFixed(2)}%)
                        </p>
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            )}
          </div>
        )}

        {/* Tab content - Activity */}
        {activeTab === 'activity' && (
          <div className="p-4" role="tabpanel" aria-label="Activity tab">
            <h3 className="text-base font-semibold text-white mb-3">Recent Activity</h3>

            {recentOrders.length === 0 ? (
              <div className="text-center py-8">
                <p className="text-gray-400">No recent activity</p>
              </div>
            ) : (
              <div className="max-h-[400px] overflow-y-auto hide-scrollbar">
                {recentOrders.slice(0, 10).map((order) => (
                  <div key={order.id} className="py-3 border-b border-gray-800 last:border-b-0">
                    <div className="flex justify-between items-start">
                      <div>
                        <span className={`text-xs px-2 py-1 rounded ${order.trade_type === 'BUY' ? 'bg-green-900/50 text-green-400' : 'bg-red-900/50 text-red-400'}`}>
                          {order.trade_type}
                        </span>
                        <span className="text-white font-medium ml-2">{order.symbol}</span>
                        <p className="text-xs text-gray-400 mt-1">{order.quantity} shares @ ${order.price?.toFixed(2) || 'Market'}</p>
                      </div>
                      <div className="text-right">
                        <p className={`text-xs px-2 py-1 rounded ${order.status === 'FILLED' ? 'bg-green-900/30 text-green-400' : 'bg-yellow-900/30 text-yellow-400'}`}>
                          {order.status}
                        </p>
                        <p className="text-xs text-gray-400 mt-1">{new Date(order.created_at).toLocaleDateString()}</p>
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            )}
          </div>
        )}

        {/* Tab content - Analysis */}
        {activeTab === 'analysis' && (
          <div className="p-4" role="tabpanel" aria-label="Analysis tab">
            <h3 className="text-base font-semibold text-white mb-3">Portfolio Analysis</h3>

            {positions.length === 0 ? (
              <div className="text-center py-8">
                <p className="text-gray-400">Add positions to see analysis</p>
              </div>
            ) : (
              <>
                {/* Allocation Chart */}
                <div className="bg-gray-800 p-4 rounded-lg mb-4">
                  <h4 className="text-sm font-medium text-gray-300 mb-3">Asset Allocation</h4>
                  <div className="h-48">
                    <canvas id="mobileAllocationChart"></canvas>
                  </div>
                </div>

                {/* Performance Chart */}
                <div className="bg-gray-800 p-4 rounded-lg">
                  <h4 className="text-sm font-medium text-gray-300 mb-3">Portfolio Value</h4>
                  <div className="h-40">
                    <canvas id="mobilePerformanceChart"></canvas>
                  </div>
                </div>
              </>
            )}
          </div>
        )}
      </div>
    </div>
  );
}
