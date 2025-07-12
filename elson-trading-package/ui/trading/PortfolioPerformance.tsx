import React, { useEffect, useState, useCallback } from 'react';
import { useSelector, useDispatch } from 'react-redux';
import { RootState } from '../../store/store';
import { fetchPortfolio, updatePerformance } from '../../store/slices/tradingSlice';
import { Card } from '../common/Card';
import { formatCurrency, formatPercent } from '../../utils/formatters';
import { useMarketWebSocket } from '../../hooks/useMarketWebSocket';

interface PerformanceMetric {
  label: string;
  value: number;
  change?: number;
  changePercent?: number;
  format: 'currency' | 'percent' | 'number';
  color?: 'green' | 'red' | 'neutral';
}

interface PortfolioPerformanceProps {
  timeframe?: '1D' | '1W' | '1M' | '3M' | '1Y' | 'ALL';
  showChart?: boolean;
}

export const PortfolioPerformance: React.FC<PortfolioPerformanceProps> = ({
  timeframe = '1D',
  showChart = true,
}) => {
  const dispatch = useDispatch();
  const { positions, portfolio, performance, loading } = useSelector((state: RootState) => state.trading);
  const [selectedTimeframe, setSelectedTimeframe] = useState(timeframe);
  const [chartData, setChartData] = useState<Array<{ time: string; value: number }>>([]);

  // Get symbols for real-time updates
  const symbols = positions.map(p => p.symbol);
  const { quotes, isConnected } = useMarketWebSocket(symbols);

  useEffect(() => {
    dispatch(fetchPortfolio() as any);
  }, [dispatch]);

  // Calculate real-time portfolio metrics
  const calculateMetrics = (): PerformanceMetric[] => {
    const totalValue = positions.reduce((sum, pos) => sum + pos.market_value, 0);
    const totalCost = positions.reduce((sum, pos) => sum + (pos.avg_cost * pos.quantity), 0);
    const totalPnL = positions.reduce((sum, pos) => sum + pos.unrealized_pnl, 0);
    const totalPnLPercent = totalCost > 0 ? (totalPnL / totalCost) * 100 : 0;

    const dayChange = performance.dailyPnL;
    const dayChangePercent = totalValue > 0 ? (dayChange / (totalValue - dayChange)) * 100 : 0;

    return [
      {
        label: 'Total Portfolio Value',
        value: totalValue + portfolio.balance,
        change: dayChange,
        changePercent: dayChangePercent,
        format: 'currency',
        color: dayChange >= 0 ? 'green' : 'red',
      },
      {
        label: 'Invested Amount',
        value: totalValue,
        format: 'currency',
        color: 'neutral',
      },
      {
        label: 'Cash Balance',
        value: portfolio.balance,
        format: 'currency',
        color: 'neutral',
      },
      {
        label: 'Buying Power',
        value: portfolio.buyingPower,
        format: 'currency',
        color: 'neutral',
      },
      {
        label: 'Total Return',
        value: totalPnL,
        changePercent: totalPnLPercent,
        format: 'currency',
        color: totalPnL >= 0 ? 'green' : 'red',
      },
      {
        label: 'Day P&L',
        value: performance.dailyPnL,
        changePercent: dayChangePercent,
        format: 'currency',
        color: performance.dailyPnL >= 0 ? 'green' : 'red',
      },
      {
        label: 'Win Rate',
        value: performance.winRate,
        format: 'percent',
        color: performance.winRate >= 50 ? 'green' : 'red',
      },
      {
        label: 'Day Trades Used',
        value: performance.dayTradeCount,
        format: 'number',
        color: performance.dayTradeCount >= 3 ? 'red' : 'neutral',
      },
    ];
  };

  const getAssetAllocation = () => {
    const totalValue = positions.reduce((sum, pos) => sum + pos.market_value, 0);
    
    if (totalValue === 0) return [];
    
    return positions
      .map(pos => ({
        symbol: pos.symbol,
        value: pos.market_value,
        percentage: (pos.market_value / totalValue) * 100,
        pnl: pos.unrealized_pnl,
        pnlPercent: pos.unrealized_pnl_percent,
      }))
      .sort((a, b) => b.value - a.value);
  };

  const formatValue = (value: number, format: PerformanceMetric['format']) => {
    switch (format) {
      case 'currency':
        return formatCurrency(value);
      case 'percent':
        return formatPercent(value);
      case 'number':
        return value.toLocaleString();
      default:
        return value.toString();
    }
  };

  const getColorClass = (color: PerformanceMetric['color']) => {
    switch (color) {
      case 'green':
        return 'text-green-600';
      case 'red':
        return 'text-red-600';
      default:
        return 'text-gray-900';
    }
  };

  const metrics = calculateMetrics();
  const allocation = getAssetAllocation();

  const timeframes = ['1D', '1W', '1M', '3M', '1Y', 'ALL'];

  return (
    <div className="space-y-6">
      {/* Performance Metrics Grid */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
        {metrics.map((metric, index) => (
          <Card key={index} className="p-4">
            <div className="space-y-1">
              <p className="text-sm text-gray-500">{metric.label}</p>
              <p className={`text-lg font-semibold ${getColorClass(metric.color)}`}>
                {formatValue(metric.value, metric.format)}
              </p>
              {(metric.change !== undefined || metric.changePercent !== undefined) && (
                <div className={`text-sm ${getColorClass(metric.color)}`}>
                  {metric.change !== undefined && (
                    <span>
                      {metric.change >= 0 ? '+' : ''}{formatCurrency(metric.change)}
                    </span>
                  )}
                  {metric.changePercent !== undefined && (
                    <span className="ml-1">
                      ({metric.changePercent >= 0 ? '+' : ''}{formatPercent(metric.changePercent)})
                    </span>
                  )}
                </div>
              )}
            </div>
          </Card>
        ))}
      </div>

      {/* Connection Status */}
      <Card className="p-4">
        <div className="flex items-center justify-between">
          <div className="flex items-center space-x-2">
            <div className={`w-2 h-2 rounded-full ${isConnected ? 'bg-green-500' : 'bg-red-500'}`}></div>
            <span className="text-sm text-gray-600">
              {isConnected ? 'Real-time data active' : 'Real-time data disconnected'}
            </span>
          </div>
          <div className="text-sm text-gray-500">
            Last updated: {new Date().toLocaleTimeString()}
          </div>
        </div>
      </Card>

      {/* Asset Allocation */}
      {allocation.length > 0 && (
        <Card className="p-6">
          <h3 className="text-lg font-medium mb-4">Asset Allocation</h3>
          <div className="space-y-3">
            {allocation.map((asset, index) => (
              <div key={asset.symbol} className="flex items-center justify-between">
                <div className="flex items-center space-x-3">
                  <div className="w-3 h-3 rounded-full" 
                       style={{ backgroundColor: `hsl(${(index * 360) / allocation.length}, 70%, 50%)` }}>
                  </div>
                  <span className="font-medium">{asset.symbol}</span>
                </div>
                
                <div className="flex items-center space-x-4">
                  <div className="text-right">
                    <div className="font-medium">{formatCurrency(asset.value)}</div>
                    <div className="text-sm text-gray-500">{formatPercent(asset.percentage)}</div>
                  </div>
                  
                  <div className={`text-right ${asset.pnl >= 0 ? 'text-green-600' : 'text-red-600'}`}>
                    <div className="text-sm font-medium">{formatCurrency(asset.pnl)}</div>
                    <div className="text-xs">{formatPercent(asset.pnlPercent)}</div>
                  </div>
                </div>
              </div>
            ))}
          </div>
        </Card>
      )}

      {/* Portfolio Composition Chart */}
      {allocation.length > 0 && (
        <Card className="p-6">
          <h3 className="text-lg font-medium mb-4">Portfolio Composition</h3>
          <div className="relative">
            <div className="h-4 bg-gray-200 rounded-full overflow-hidden flex">
              {allocation.map((asset, index) => (
                <div
                  key={asset.symbol}
                  className="h-full transition-all duration-300"
                  style={{
                    width: `${asset.percentage}%`,
                    backgroundColor: `hsl(${(index * 360) / allocation.length}, 70%, 50%)`,
                  }}
                  title={`${asset.symbol}: ${formatPercent(asset.percentage)}`}
                />
              ))}
            </div>
            
            {/* Legend */}
            <div className="mt-4 grid grid-cols-2 md:grid-cols-3 lg:grid-cols-4 gap-2">
              {allocation.map((asset, index) => (
                <div key={asset.symbol} className="flex items-center space-x-2 text-sm">
                  <div className="w-3 h-3 rounded-full" 
                       style={{ backgroundColor: `hsl(${(index * 360) / allocation.length}, 70%, 50%)` }}>
                  </div>
                  <span>{asset.symbol} ({formatPercent(asset.percentage)})</span>
                </div>
              ))}
            </div>
          </div>
        </Card>
      )}

      {/* Risk Metrics */}
      <Card className="p-6">
        <h3 className="text-lg font-medium mb-4">Risk Metrics</h3>
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
          <div>
            <p className="text-sm text-gray-500">Portfolio Beta</p>
            <p className="text-lg font-semibold">1.05</p>
          </div>
          <div>
            <p className="text-sm text-gray-500">Sharpe Ratio</p>
            <p className="text-lg font-semibold">0.85</p>
          </div>
          <div>
            <p className="text-sm text-gray-500">Max Drawdown</p>
            <p className="text-lg font-semibold text-red-600">-5.2%</p>
          </div>
          <div>
            <p className="text-sm text-gray-500">Volatility (30d)</p>
            <p className="text-lg font-semibold">12.3%</p>
          </div>
        </div>
      </Card>
    </div>
  );
};