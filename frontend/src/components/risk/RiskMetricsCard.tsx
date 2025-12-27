import React from 'react';
import { RiskMetricsResponse } from '../../services/riskManagementApi';

interface RiskMetricsCardProps {
  metrics: RiskMetricsResponse;
  className?: string;
}

export const RiskMetricsCard: React.FC<RiskMetricsCardProps> = ({ 
  metrics, 
  className = '' 
}) => {
  // Calculate risk level based on multiple factors
  const getRiskLevel = () => {
    const varPercentage = (metrics.daily_var / metrics.portfolio_value) * 100;
    const concentrationRisk = metrics.concentration_risk * 100;
    
    if (varPercentage > 3 || concentrationRisk > 70) return { level: 'High', color: 'text-red-400 bg-red-900' };
    if (varPercentage > 2 || concentrationRisk > 50) return { level: 'Medium', color: 'text-yellow-400 bg-yellow-900' };
    return { level: 'Low', color: 'text-green-400 bg-green-900' };
  };

  const riskLevel = getRiskLevel();
  const varPercentage = (metrics.daily_var / metrics.portfolio_value) * 100;

  const formatCurrency = (amount: number) => {
    return new Intl.NumberFormat('en-US', {
      style: 'currency',
      currency: 'USD',
      minimumFractionDigits: 0,
      maximumFractionDigits: 0,
    }).format(amount);
  };

  const formatPercentage = (value: number) => {
    return `${(value * 100).toFixed(2)}%`;
  };

  const getProgressBarColor = (percentage: number) => {
    if (percentage > 70) return 'bg-red-500';
    if (percentage > 50) return 'bg-yellow-500';
    return 'bg-green-500';
  };

  return (
    <div className={`bg-gray-800 rounded-lg p-6 ${className}`}>
      <div className="flex items-center justify-between mb-6">
        <h3 className="text-lg font-medium text-white">Portfolio Risk Metrics</h3>
        <div className={`px-3 py-1 rounded-full text-sm font-medium ${riskLevel.color} bg-opacity-20`}>
          {riskLevel.level} Risk
        </div>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
        {/* Portfolio Value */}
        <div className="bg-gray-900 rounded-lg p-4">
          <div className="flex items-center justify-between mb-2">
            <h4 className="text-gray-400 text-sm font-medium">Portfolio Value</h4>
            <svg className="h-5 w-5 text-blue-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M12 8c-1.657 0-3 .895-3 2s1.343 2 3 2 3 .895 3 2-1.343 2-3 2m0-8c1.11 0 2.08.402 2.599 1M12 8V7m0 1v8m0 0v1m0-1c-1.11 0-2.08-.402-2.599-1M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
            </svg>
          </div>
          <p className="text-white text-xl font-bold">{formatCurrency(metrics.portfolio_value)}</p>
          <p className="text-gray-500 text-sm">Cash: {formatPercentage(metrics.cash_percentage)}</p>
        </div>

        {/* Daily VaR */}
        <div className="bg-gray-900 rounded-lg p-4">
          <div className="flex items-center justify-between mb-2">
            <h4 className="text-gray-400 text-sm font-medium">Daily VaR (95%)</h4>
            <svg className="h-5 w-5 text-red-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M13 17h8m0 0V9m0 8l-8-8-4 4-6-6" />
            </svg>
          </div>
          <p className="text-red-400 text-xl font-bold">{formatCurrency(metrics.daily_var)}</p>
          <p className="text-gray-500 text-sm">{varPercentage.toFixed(2)}% of portfolio</p>
        </div>

        {/* Beta */}
        <div className="bg-gray-900 rounded-lg p-4">
          <div className="flex items-center justify-between mb-2">
            <h4 className="text-gray-400 text-sm font-medium">Portfolio Beta</h4>
            <svg className="h-5 w-5 text-purple-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z" />
            </svg>
          </div>
          <p className="text-purple-400 text-xl font-bold">{metrics.portfolio_beta.toFixed(2)}</p>
          <p className="text-gray-500 text-sm">
            {metrics.portfolio_beta > 1 ? 'More volatile than market' : 
             metrics.portfolio_beta < 1 ? 'Less volatile than market' : 'Market volatility'}
          </p>
        </div>

        {/* Sharpe Ratio */}
        <div className="bg-gray-900 rounded-lg p-4">
          <div className="flex items-center justify-between mb-2">
            <h4 className="text-gray-400 text-sm font-medium">Sharpe Ratio</h4>
            <svg className="h-5 w-5 text-green-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M13 7h8m0 0v8m0-8l-8 8-4-4-6 6" />
            </svg>
          </div>
          <p className={`text-xl font-bold ${
            metrics.sharpe_ratio > 1.5 ? 'text-green-400' :
            metrics.sharpe_ratio > 1 ? 'text-yellow-400' : 'text-red-400'
          }`}>
            {metrics.sharpe_ratio.toFixed(2)}
          </p>
          <p className="text-gray-500 text-sm">Risk-adjusted returns</p>
        </div>

        {/* Volatility */}
        <div className="bg-gray-900 rounded-lg p-4">
          <div className="flex items-center justify-between mb-2">
            <h4 className="text-gray-400 text-sm font-medium">Volatility</h4>
            <svg className="h-5 w-5 text-orange-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z" />
            </svg>
          </div>
          <p className="text-orange-400 text-xl font-bold">{formatPercentage(metrics.volatility)}</p>
          <p className="text-gray-500 text-sm">Annualized volatility</p>
        </div>

        {/* Max Drawdown */}
        <div className="bg-gray-900 rounded-lg p-4">
          <div className="flex items-center justify-between mb-2">
            <h4 className="text-gray-400 text-sm font-medium">Max Drawdown</h4>
            <svg className="h-5 w-5 text-red-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M19 14l-7 7m0 0l-7-7m7 7V3" />
            </svg>
          </div>
          <p className="text-red-400 text-xl font-bold">{formatPercentage(Math.abs(metrics.max_drawdown))}</p>
          <p className="text-gray-500 text-sm">Historical peak-to-trough</p>
        </div>
      </div>

      {/* Concentration Risk Analysis */}
      <div className="mt-6 bg-gray-900 rounded-lg p-4">
        <h4 className="text-white font-medium mb-4">Concentration Analysis</h4>
        <div className="space-y-4">
          {/* Overall Concentration */}
          <div>
            <div className="flex justify-between items-center mb-2">
              <span className="text-gray-400 text-sm">Overall Concentration</span>
              <span className="text-white font-medium">{formatPercentage(metrics.concentration_risk)}</span>
            </div>
            <div className="w-full bg-gray-700 rounded-full h-2">
              <div 
                className={`h-2 rounded-full transition-all duration-300 ${getProgressBarColor(metrics.concentration_risk * 100)}`}
                style={{ width: `${Math.min(metrics.concentration_risk * 100, 100)}%` }}
              />
            </div>
          </div>

          {/* Largest Position */}
          <div>
            <div className="flex justify-between items-center mb-2">
              <span className="text-gray-400 text-sm">Largest Position</span>
              <span className="text-white font-medium">{formatPercentage(metrics.largest_position_pct)}</span>
            </div>
            <div className="w-full bg-gray-700 rounded-full h-2">
              <div 
                className={`h-2 rounded-full transition-all duration-300 ${getProgressBarColor(metrics.largest_position_pct * 100)}`}
                style={{ width: `${Math.min(metrics.largest_position_pct * 100, 100)}%` }}
              />
            </div>
          </div>

          {/* Leverage */}
          <div>
            <div className="flex justify-between items-center mb-2">
              <span className="text-gray-400 text-sm">Leverage Ratio</span>
              <span className="text-white font-medium">{metrics.leverage_ratio.toFixed(2)}x</span>
            </div>
            <div className="w-full bg-gray-700 rounded-full h-2">
              <div 
                className={`h-2 rounded-full transition-all duration-300 ${
                  metrics.leverage_ratio > 2 ? 'bg-red-500' :
                  metrics.leverage_ratio > 1.5 ? 'bg-yellow-500' : 'bg-green-500'
                }`}
                style={{ width: `${Math.min(metrics.leverage_ratio * 50, 100)}%` }}
              />
            </div>
          </div>
        </div>
      </div>

      {/* Sector Concentration */}
      {Object.keys(metrics.sector_concentration).length > 0 && (
        <div className="mt-6 bg-gray-900 rounded-lg p-4">
          <h4 className="text-white font-medium mb-4">Sector Allocation</h4>
          <div className="space-y-3">
            {Object.entries(metrics.sector_concentration)
              .sort(([, a], [, b]) => b - a)
              .slice(0, 5) // Show top 5 sectors
              .map(([sector, percentage]) => (
                <div key={sector}>
                  <div className="flex justify-between items-center mb-1">
                    <span className="text-gray-400 text-sm capitalize">{sector}</span>
                    <span className="text-white font-medium">{formatPercentage(percentage)}</span>
                  </div>
                  <div className="w-full bg-gray-700 rounded-full h-2">
                    <div 
                      className={`h-2 rounded-full transition-all duration-300 ${getProgressBarColor(percentage * 100)}`}
                      style={{ width: `${Math.min(percentage * 100, 100)}%` }}
                    />
                  </div>
                </div>
              ))}
          </div>
        </div>
      )}
    </div>
  );
};

export default RiskMetricsCard;