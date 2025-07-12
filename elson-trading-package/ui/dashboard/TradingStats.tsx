import React, { useState } from 'react';
import { useSelector } from 'react-redux';
import { PieChart, Pie, Cell, ResponsiveContainer as RechartsResponsiveContainer, Tooltip } from 'recharts';
import { formatCurrency, formatPercentage } from '../../utils/formatters';
import Select from '../common/Select';
import { useTheme, useMediaQuery } from '@mui/material';
import ResponsiveContainer from '../common/ResponsiveContainer';

interface StatCardProps {
  title: string;
  value: string | number;
  subtitle: string;
  trend?: 'up' | 'down' | 'neutral';
}

const StatCard: React.FC<StatCardProps> = ({ title, value, subtitle, trend }) => {
  const theme = useTheme();
  const isMobile = useMediaQuery(theme.breakpoints.down('sm'));
  const trendColor = trend === 'up' ? 'text-green-500' : trend === 'down' ? 'text-red-500' : 'text-gray-400';
  const trendIcon = trend === 'up' ? '↑' : trend === 'down' ? '↓' : '→';

  return (
    <div className="bg-gray-700 rounded-lg p-4 transition-all hover:bg-gray-600">
      <h4 className="text-gray-400 text-sm">{title}</h4>
      <div className="flex items-baseline mt-1">
        <h3 className={`${isMobile ? 'text-xl' : isTablet ? 'text-xl' : 'text-2xl'} font-semibold`}>{value}</h3>
        {trend && (
          <span className={`ml-2 ${trendColor}`}>
            {trendIcon}
          </span>
        )}
      </div>
      <p className={`${isMobile ? 'text-xs' : 'text-sm'} text-gray-400 mt-1`}>{subtitle}</p>
    </div>
  );
};

const TradingStats: React.FC = () => {
  const theme = useTheme();
  const isMobile = useMediaQuery(theme.breakpoints.down('sm'));
  const isTablet = useMediaQuery(theme.breakpoints.between('sm', 'md'));
  const [timeframe, setTimeframe] = useState('7d');
  const {
    totalTrades,
    winningTrades,
    losingTrades,
    averageWin,
    averageLoss,
    largestWin,
    largestLoss,
    profitFactor,
    assetAllocation,
    loading,
    error
  } = useSelector((state: any) => state.trading.stats);

  const COLORS = ['#60A5FA', '#34D399', '#F87171', '#FBBF24', '#A78BFA'];

  const winRate = (winningTrades / totalTrades) * 100;

  return (
    <div className={`bg-gray-800 rounded-lg ${isMobile ? 'p-4' : 'p-6'} transition-all hover:shadow-lg`}>
      <ResponsiveContainer
        mobileClasses="flex flex-col items-start gap-3"
        desktopClasses="flex flex-row justify-between items-center"
        className="mb-6"
      >
        <h2 className={`${isMobile ? 'text-lg' : 'text-xl'} font-semibold`}>Trading Statistics</h2>
        <Select
          value={timeframe}
          onChange={(value) => setTimeframe(value)}
          options={[
            { value: '24h', label: isMobile ? '24 Hrs' : 'Last 24 Hours' },
            { value: '7d', label: isMobile ? '7 Days' : 'Last 7 Days' },
            { value: '30d', label: isMobile ? '30 Days' : 'Last 30 Days' },
            { value: 'all', label: 'All Time' }
          ]}
          className={isMobile ? "w-full" : "w-40"}
        />
      </ResponsiveContainer>

      <ResponsiveContainer
        mobileClasses="grid grid-cols-1 gap-3" 
        desktopClasses="grid grid-cols-2 gap-4"
        breakpoint="sm"
        className="mb-6 lg:grid-cols-3"
      >
        <StatCard
          title="Total Trades"
          value={totalTrades}
          subtitle="Total number of trades executed"
          trend="neutral"
        />
        <StatCard
          title="Win Rate"
          value={formatPercentage(winRate)}
          subtitle={`${winningTrades} winning, ${losingTrades} losing trades`}
          trend={winRate >= 50 ? 'up' : 'down'}
        />
        <StatCard
          title="Profit Factor"
          value={profitFactor.toFixed(2)}
          subtitle="Gross profit / Gross loss"
          trend={profitFactor >= 1 ? 'up' : 'down'}
        />
        <StatCard
          title="Average Win"
          value={formatCurrency(averageWin)}
          subtitle={`Largest win: ${formatCurrency(largestWin)}`}
          trend="up"
        />
        <StatCard
          title="Average Loss"
          value={formatCurrency(Math.abs(averageLoss))}
          subtitle={`Largest loss: ${formatCurrency(Math.abs(largestLoss))}`}
          trend="down"
        />
        <StatCard
          title="Risk/Reward Ratio"
          value={(Math.abs(averageWin) / Math.abs(averageLoss)).toFixed(2)}
          subtitle="Average win / Average loss"
          trend="neutral"
        />
      </ResponsiveContainer>

      <div className={`bg-gray-700 rounded-lg ${isMobile ? 'p-3' : isTablet ? 'p-3.5' : 'p-4'} transition-all hover:bg-gray-600`}>
        <h3 className={`${isMobile ? 'text-base' : 'text-lg'} font-medium ${isMobile ? 'mb-3' : 'mb-4'}`}>
          Asset Allocation
        </h3>
        <ResponsiveContainer
          mobileClasses="grid grid-cols-1 gap-4"
          desktopClasses="grid grid-cols-1 gap-4 lg:grid-cols-2"
        >
          <ResponsiveContainer
            mobileClasses="h-52"
            desktopClasses="h-56"
            breakpoint="sm"
            className="lg:h-64"
          >
            <RechartsResponsiveContainer width="100%" height="100%">
              <PieChart>
                <Pie
                  data={assetAllocation}
                  dataKey="percentage"
                  nameKey="symbol"
                  cx="50%"
                  cy="50%"
                  outerRadius={isMobile ? 60 : isTablet ? 70 : 80}
                  label={isMobile ? undefined : (entry: any) => `${entry.symbol} (${formatPercentage(entry.percentage)})`}
                >
                  {assetAllocation.map((_: any, index: number) => (
                    <Cell key={`cell-${index}`} fill={COLORS[index % COLORS.length]} />
                  ))}
                </Pie>
                <Tooltip
                  formatter={(value: number) => formatPercentage(value)}
                  contentStyle={{
                    backgroundColor: '#1F2937',
                    border: 'none',
                    borderRadius: '0.5rem',
                    fontSize: isMobile ? '0.75rem' : undefined
                  }}
                />
              </PieChart>
            </RechartsResponsiveContainer>
          </ResponsiveContainer>
          <div className={`space-y-${isMobile ? '1.5' : '2'}`}>
            {assetAllocation.map((asset: any, index: number) => (
              <div key={asset.symbol} className="flex items-center justify-between">
                <div className="flex items-center">
                  <div
                    className={`${isMobile ? 'w-2 h-2' : 'w-3 h-3'} rounded-full mr-2`}
                    style={{ backgroundColor: COLORS[index % COLORS.length] }}
                  />
                  <span className={isMobile ? 'text-sm' : ''}>{asset.symbol}</span>
                </div>
                <div className="text-right">
                  <div className={isMobile ? 'text-sm' : ''}>{formatCurrency(asset.value)}</div>
                  <div className={`${isMobile ? 'text-xs' : 'text-sm'} text-gray-400`}>
                    {formatPercentage(asset.percentage)}
                  </div>
                </div>
              </div>
            ))}
          </div>
        </ResponsiveContainer>
      </div>
    </div>
  );
};

export default TradingStats;