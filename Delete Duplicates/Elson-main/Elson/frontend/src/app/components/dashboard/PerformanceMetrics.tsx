import React from 'react';
import { useSelector } from 'react-redux';
import { formatCurrency, formatPercentage } from '../../utils/formatters';
import { LineChart, Line, XAxis, YAxis, Tooltip, ResponsiveContainer as RechartsResponsiveContainer } from 'recharts';
import { useTheme, useMediaQuery } from '@mui/material';
import ResponsiveContainer from '../common/ResponsiveContainer';

interface MetricCardProps {
  title: string;
  value: string | number;
  change: number;
  icon: string;
}

const MetricCard: React.FC<MetricCardProps> = ({ title, value, change, icon }) => {
  const theme = useTheme();
  const isMobile = useMediaQuery(theme.breakpoints.down('sm'));
  const isTablet = useMediaQuery(theme.breakpoints.between('sm', 'md'));
  
  return (
    <div className="bg-gray-700 rounded-lg p-4 transition-all hover:bg-gray-600">
      <div className="flex justify-between items-start">
        <div>
          <p className="text-gray-400 text-sm">{title}</p>
          <h3 className={`${isMobile ? 'text-xl' : isTablet ? 'text-xl' : 'text-2xl'} font-semibold mt-1`}>{value}</h3>
        </div>
        <div className={`p-2 rounded ${icon} ${isMobile ? 'text-lg' : 'text-xl'}`} />
      </div>
      <div className="mt-2">
        <span className={`${isMobile ? 'text-xs' : 'text-sm'} ${change >= 0 ? 'text-green-500' : 'text-red-500'}`}>
          {change >= 0 ? '↑' : '↓'} {formatPercentage(Math.abs(change))}
        </span>
        <span className={`${isMobile ? 'text-xs' : 'text-sm'} text-gray-400 ml-1`}>vs last period</span>
      </div>
    </div>
  );
};

const PerformanceMetrics: React.FC = () => {
  const theme = useTheme();
  const isMobile = useMediaQuery(theme.breakpoints.down('sm'));
  const isTablet = useMediaQuery(theme.breakpoints.between('sm', 'md'));
  
  const {
    totalValue,
    totalProfitLoss,
    profitLossChange,
    winRate,
    winRateChange,
    performanceHistory,
    loading,
    error
  } = useSelector((state: any) => state.trading.performance);

  if (loading) {
    return (
      <div className={`bg-gray-800 rounded-lg ${isMobile ? 'p-4' : 'p-6'}`}>
        <div className="animate-pulse">
          <div className={`h-${isMobile ? '6' : '8'} bg-gray-700 rounded w-1/4 ${isMobile ? 'mb-4' : 'mb-6'}`}></div>
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
            {[...Array(4)].map((_, i) => (
              <div key={i} className={`h-${isMobile ? '24' : '32'} bg-gray-700 rounded`}></div>
            ))}
          </div>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className={`bg-gray-800 rounded-lg ${isMobile ? 'p-4' : 'p-6'}`}>
        <div className="text-red-500 text-sm">Error loading performance metrics: {error}</div>
      </div>
    );
  }

  return (
    <div className={`bg-gray-800 rounded-lg ${isMobile ? 'p-4' : 'p-6'} transition-all hover:shadow-lg`}>
      <h2 className={`${isMobile ? 'text-lg' : 'text-xl'} font-semibold ${isMobile ? 'mb-4' : 'mb-6'}`}>
        Performance Metrics
      </h2>
      
      <ResponsiveContainer
        mobileClasses="grid grid-cols-1 gap-3"
        desktopClasses="grid grid-cols-2 gap-4"
        breakpoint="sm"
        className="mb-6 lg:grid-cols-4"
      >
        <MetricCard
          title="Portfolio Value"
          value={formatCurrency(totalValue)}
          change={profitLossChange}
          icon="fas fa-wallet"
        />
        <MetricCard
          title="Total P/L"
          value={formatCurrency(totalProfitLoss)}
          change={profitLossChange}
          icon="fas fa-chart-line"
        />
        <MetricCard
          title="Win Rate"
          value={formatPercentage(winRate)}
          change={winRateChange}
          icon="fas fa-trophy"
        />
        <MetricCard
          title="ROI"
          value={formatPercentage(totalProfitLoss / totalValue * 100)}
          change={profitLossChange}
          icon="fas fa-percentage"
        />
      </ResponsiveContainer>

      <div className={`bg-gray-700 rounded-lg ${isMobile ? 'p-3' : isTablet ? 'p-3.5' : 'p-4'} transition-all hover:bg-gray-600`}>
        <h3 className={`${isMobile ? 'text-base' : 'text-lg'} font-medium ${isMobile ? 'mb-3' : 'mb-4'}`}>
          Performance History
        </h3>
        <ResponsiveContainer
          mobileClasses="h-48"
          desktopClasses="h-56"
          breakpoint="sm"
          className="lg:h-64"
        >
          <RechartsResponsiveContainer width="100%" height="100%">
            <LineChart data={performanceHistory}>
              <XAxis
                dataKey="date"
                stroke="#9CA3AF"
                fontSize={isMobile ? 10 : isTablet ? 11 : 12}
                tickLine={false}
                tick={{ fontSize: isMobile ? 10 : isTablet ? 11 : 12 }}
                tickCount={isMobile ? 4 : isTablet ? 5 : undefined}
              />
              <YAxis
                stroke="#9CA3AF"
                fontSize={isMobile ? 10 : isTablet ? 11 : 12}
                tickLine={false}
                tickFormatter={(value) => isMobile || isTablet ? formatCurrency(value, true) : formatCurrency(value)}
                width={isMobile ? 50 : isTablet ? 55 : 60}
              />
              <Tooltip
                contentStyle={{
                  backgroundColor: '#1F2937',
                  border: 'none',
                  borderRadius: '0.5rem',
                  fontSize: isMobile ? '0.75rem' : undefined
                }}
                itemStyle={{ color: '#E5E7EB' }}
                formatter={(value: number) => [formatCurrency(value), 'Value']}
              />
              <Line
                type="monotone"
                dataKey="value"
                stroke="#60A5FA"
                strokeWidth={isMobile ? 1.5 : isTablet ? 1.75 : 2}
                dot={false}
              />
            </LineChart>
          </RechartsResponsiveContainer>
        </ResponsiveContainer>
      </div>
    </div>
  );
};

export default PerformanceMetrics;