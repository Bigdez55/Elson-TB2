import React, { useState } from 'react';
import { useTradingContext } from '../../contexts/TradingContext';
import {
  useGetPortfolioRiskMetricsQuery,
  useGetPositionRiskAnalysisQuery,
  useGetCircuitBreakersQuery,
  useValidatePortfolioMutation,
} from '../../services/riskManagementApi';
import { LoadingSpinner } from '../common/LoadingSpinner';
import { RiskMetricsCard } from './RiskMetricsCard';
import { PositionRiskTable } from './PositionRiskTable';
import { CircuitBreakerStatus } from './CircuitBreakerStatus';
import { RiskChart } from './RiskChart';

interface RiskDashboardProps {
  className?: string;
}

export const RiskDashboard: React.FC<RiskDashboardProps> = ({ className = '' }) => {
  const { mode, isBlocked } = useTradingContext();
  const [activeTab, setActiveTab] = useState<'overview' | 'positions' | 'breakers' | 'analysis'>('overview');

  // API queries
  const {
    data: riskMetrics,
    error: metricsError,
    isLoading: isMetricsLoading,
    refetch: refetchMetrics,
  } = useGetPortfolioRiskMetricsQuery(undefined, {
    pollingInterval: 30000, // Refresh every 30 seconds
  });

  const {
    data: positionRisks,
    error: positionsError,
    isLoading: isPositionsLoading,
  } = useGetPositionRiskAnalysisQuery();

  const {
    data: circuitBreakers,
    error: breakersError,
    isLoading: isBreakersLoading,
  } = useGetCircuitBreakersQuery(undefined, {
    pollingInterval: 10000, // Refresh every 10 seconds
  });

  const [validatePortfolio, { isLoading: isValidating }] = useValidatePortfolioMutation();

  // Handle portfolio validation
  const handleValidatePortfolio = async () => {
    try {
      const result = await validatePortfolio().unwrap();
      console.log('Portfolio validation result:', result);
      // Refresh metrics after validation
      refetchMetrics();
    } catch (error) {
      console.error('Portfolio validation failed:', error);
    }
  };

  const tabs = [
    { id: 'overview', label: 'Overview', icon: 'M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z' },
    { id: 'positions', label: 'Position Risk', icon: 'M16 8v8m-4-5v5m-4-2v2m-2 4h12a2 2 0 002-2V6a2 2 0 00-2-2H6a2 2 0 00-2 2v12a2 2 0 002 2z' },
    { id: 'breakers', label: 'Circuit Breakers', icon: 'M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z' },
    { id: 'analysis', label: 'Analysis', icon: 'M13 7h8m0 0v8m0-8l-8 8-4-4-6 6' },
  ];

  if (isMetricsLoading && !riskMetrics) {
    return (
      <div className={`bg-gray-900 rounded-xl p-6 ${className}`}>
        <div className="flex items-center justify-center h-64">
          <LoadingSpinner />
        </div>
      </div>
    );
  }

  return (
    <div className={`bg-gray-900 rounded-xl p-6 ${className}`}>
      {/* Header */}
      <div className="flex items-center justify-between mb-6">
        <div>
          <h2 className="text-xl font-bold text-white mb-2">Risk Management Dashboard</h2>
          <div className="flex items-center space-x-4">
            <span className={`px-3 py-1 rounded-full text-sm font-medium ${
              mode === 'paper' 
                ? 'bg-yellow-900 text-yellow-300' 
                : 'bg-red-900 text-red-300'
            }`}>
              {mode.toUpperCase()} MODE
            </span>
            {isBlocked && (
              <span className="px-3 py-1 rounded-full text-sm font-medium bg-red-900 text-red-300">
                TRADING BLOCKED
              </span>
            )}
          </div>
        </div>
        
        <div className="flex space-x-3">
          <button
            onClick={() => refetchMetrics()}
            className="bg-gray-700 hover:bg-gray-600 text-white px-4 py-2 rounded-lg text-sm transition-colors"
            disabled={isMetricsLoading}
          >
            {isMetricsLoading ? 'Refreshing...' : 'Refresh'}
          </button>
          <button
            onClick={handleValidatePortfolio}
            className="bg-purple-600 hover:bg-purple-700 text-white px-4 py-2 rounded-lg text-sm transition-colors"
            disabled={isValidating}
          >
            {isValidating ? 'Validating...' : 'Validate Portfolio'}
          </button>
        </div>
      </div>

      {/* Error States */}
      {metricsError && (
        <div className="bg-red-900 bg-opacity-30 border border-red-700 rounded-lg p-4 mb-6">
          <div className="flex items-center">
            <span className="text-red-400 mr-2">⚠️</span>
            <div>
              <p className="text-red-300 font-medium">Failed to load risk metrics</p>
              <p className="text-red-400 text-sm">Unable to retrieve portfolio risk data</p>
            </div>
          </div>
        </div>
      )}

      {/* Navigation Tabs */}
      <div className="flex space-x-1 mb-6 bg-gray-800 rounded-lg p-1">
        {tabs.map((tab) => (
          <button
            key={tab.id}
            onClick={() => setActiveTab(tab.id as any)}
            className={`flex items-center space-x-2 px-4 py-2 rounded-lg transition-colors ${
              activeTab === tab.id
                ? 'bg-purple-600 text-white'
                : 'text-gray-400 hover:text-white hover:bg-gray-700'
            }`}
          >
            <svg className="h-4 w-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d={tab.icon} />
            </svg>
            <span className="text-sm font-medium">{tab.label}</span>
          </button>
        ))}
      </div>

      {/* Tab Content */}
      {activeTab === 'overview' && riskMetrics && (
        <div className="space-y-6">
          <RiskMetricsCard metrics={riskMetrics} />
          {riskMetrics && (
            <RiskChart 
              metrics={riskMetrics} 
              positionRisks={positionRisks || []}
            />
          )}
        </div>
      )}

      {activeTab === 'positions' && (
        <div>
          {isPositionsLoading ? (
            <div className="flex items-center justify-center h-32">
              <LoadingSpinner />
            </div>
          ) : positionsError ? (
            <div className="text-center text-red-400 py-8">
              Failed to load position risk data
            </div>
          ) : positionRisks ? (
            <PositionRiskTable positions={positionRisks} />
          ) : (
            <div className="text-center text-gray-400 py-8">
              No position data available
            </div>
          )}
        </div>
      )}

      {activeTab === 'breakers' && (
        <div>
          {isBreakersLoading ? (
            <div className="flex items-center justify-center h-32">
              <LoadingSpinner />
            </div>
          ) : breakersError ? (
            <div className="text-center text-red-400 py-8">
              Failed to load circuit breaker status
            </div>
          ) : circuitBreakers ? (
            <CircuitBreakerStatus breakers={circuitBreakers} />
          ) : (
            <div className="text-center text-gray-400 py-8">
              No circuit breaker data available
            </div>
          )}
        </div>
      )}

      {activeTab === 'analysis' && riskMetrics && (
        <div className="space-y-6">
          <div className="bg-gray-800 rounded-lg p-6">
            <h3 className="text-lg font-medium text-white mb-4">Risk Analysis Summary</h3>
            <div className="space-y-4">
              <div className="flex justify-between items-center">
                <span className="text-gray-400">Portfolio Value</span>
                <span className="text-white font-medium">
                  ${riskMetrics.portfolio_value.toLocaleString()}
                </span>
              </div>
              <div className="flex justify-between items-center">
                <span className="text-gray-400">Daily Value at Risk</span>
                <span className="text-red-400 font-medium">
                  ${riskMetrics.daily_var.toLocaleString()} 
                  <span className="text-sm ml-1">
                    ({((riskMetrics.daily_var / riskMetrics.portfolio_value) * 100).toFixed(2)}%)
                  </span>
                </span>
              </div>
              <div className="flex justify-between items-center">
                <span className="text-gray-400">Concentration Risk</span>
                <span className={`font-medium ${
                  riskMetrics.concentration_risk > 0.7 ? 'text-red-400' :
                  riskMetrics.concentration_risk > 0.5 ? 'text-yellow-400' :
                  'text-green-400'
                }`}>
                  {(riskMetrics.concentration_risk * 100).toFixed(1)}%
                </span>
              </div>
              <div className="flex justify-between items-center">
                <span className="text-gray-400">Sharpe Ratio</span>
                <span className={`font-medium ${
                  riskMetrics.sharpe_ratio > 1.5 ? 'text-green-400' :
                  riskMetrics.sharpe_ratio > 1 ? 'text-yellow-400' :
                  'text-red-400'
                }`}>
                  {riskMetrics.sharpe_ratio.toFixed(2)}
                </span>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default RiskDashboard;