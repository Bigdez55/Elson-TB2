import React, { useState, useEffect, useCallback } from 'react';
import { Card } from '../common/Card';
import { LoadingSpinner } from '../common/LoadingSpinner';
import { advancedTradingAPI, PositionMonitoring } from '../../services/advancedTradingAPI';

interface PositionMonitoringPanelProps {
  portfolioId: number;
  onError: (error: string) => void;
}

const PositionMonitoringPanel: React.FC<PositionMonitoringPanelProps> = ({ portfolioId, onError }) => {
  const [monitoring, setMonitoring] = useState<PositionMonitoring | null>(null);
  const [loading, setLoading] = useState(true);

  const loadMonitoringData = useCallback(async () => {
    try {
      const data = await advancedTradingAPI.monitorPositions(portfolioId);
      setMonitoring(data);
    } catch (err: any) {
      onError(err.response?.data?.detail || 'Failed to load position monitoring data');
    } finally {
      setLoading(false);
    }
  }, [portfolioId, onError]);

  useEffect(() => {
    loadMonitoringData();
    // Refresh every 30 seconds
    const interval = setInterval(loadMonitoringData, 30000);
    return () => clearInterval(interval);
  }, [loadMonitoringData]);

  if (loading) {
    return (
      <Card>
        <h3 className="text-lg font-semibold mb-4">Position Monitoring</h3>
        <div className="flex justify-center py-8">
          <LoadingSpinner />
        </div>
      </Card>
    );
  }

  if (!monitoring) {
    return (
      <Card>
        <h3 className="text-lg font-semibold mb-4">Position Monitoring</h3>
        <div className="text-center py-8 text-gray-500">
          <p>No monitoring data available.</p>
        </div>
      </Card>
    );
  }

  const getAlertColor = (severity: string) => {
    switch (severity.toLowerCase()) {
      case 'high':
        return 'bg-red-100 border-red-300 text-red-800';
      case 'medium':
        return 'bg-yellow-100 border-yellow-300 text-yellow-800';
      case 'low':
        return 'bg-blue-100 border-blue-300 text-blue-800';
      default:
        return 'bg-gray-100 border-gray-300 text-gray-800';
    }
  };

  const formatCurrency = (value: number) => {
    return new Intl.NumberFormat('en-US', {
      style: 'currency',
      currency: 'USD',
    }).format(value);
  };

  const formatPercentage = (value: number) => {
    return `${(value * 100).toFixed(2)}%`;
  };

  return (
    <Card>
      <div className="flex justify-between items-center mb-4">
        <h3 className="text-lg font-semibold">Position Monitoring</h3>
        <div className="text-xs text-gray-500">
          Last updated: {new Date().toLocaleTimeString()}
        </div>
      </div>

      {/* Portfolio Overview */}
      <div className="grid grid-cols-3 gap-4 mb-6">
        <div className="text-center p-3 bg-blue-50 rounded-lg">
          <div className="text-lg font-bold text-blue-600">{monitoring.total_positions}</div>
          <div className="text-sm text-blue-600">Positions</div>
        </div>
        <div className="text-center p-3 bg-green-50 rounded-lg">
          <div className="text-lg font-bold text-green-600">
            {formatCurrency(monitoring.total_value)}
          </div>
          <div className="text-sm text-green-600">Total Value</div>
        </div>
        <div className={`text-center p-3 rounded-lg ${
          monitoring.unrealized_pnl >= 0 
            ? 'bg-green-50' 
            : 'bg-red-50'
        }`}>
          <div className={`text-lg font-bold ${
            monitoring.unrealized_pnl >= 0 
              ? 'text-green-600' 
              : 'text-red-600'
          }`}>
            {formatCurrency(monitoring.unrealized_pnl)}
          </div>
          <div className={`text-sm ${
            monitoring.unrealized_pnl >= 0 
              ? 'text-green-600' 
              : 'text-red-600'
          }`}>
            Unrealized P&L
          </div>
        </div>
      </div>

      {/* Risk Metrics */}
      {monitoring.risk_metrics && (
        <div className="mb-6">
          <h4 className="font-medium mb-3">Risk Metrics</h4>
          <div className="grid grid-cols-2 gap-4 text-sm">
            {monitoring.risk_metrics.daily_drawdown && (
              <div className="flex justify-between">
                <span className="text-gray-600">Daily Drawdown:</span>
                <span className="font-medium">
                  {formatPercentage(monitoring.risk_metrics.daily_drawdown)}
                </span>
              </div>
            )}
            {monitoring.risk_metrics.daily_trades !== undefined && (
              <div className="flex justify-between">
                <span className="text-gray-600">Daily Trades:</span>
                <span className="font-medium">{monitoring.risk_metrics.daily_trades}</span>
              </div>
            )}
            {monitoring.risk_metrics.portfolio_value && (
              <div className="flex justify-between">
                <span className="text-gray-600">Portfolio Value:</span>
                <span className="font-medium">
                  {formatCurrency(monitoring.risk_metrics.portfolio_value)}
                </span>
              </div>
            )}
            {monitoring.risk_metrics.risk_profile && (
              <div className="flex justify-between">
                <span className="text-gray-600">Risk Profile:</span>
                <span className="font-medium capitalize">
                  {monitoring.risk_metrics.risk_profile}
                </span>
              </div>
            )}
          </div>
        </div>
      )}

      {/* Alerts */}
      {monitoring.alerts && monitoring.alerts.length > 0 && (
        <div className="mb-4">
          <h4 className="font-medium mb-3">Risk Alerts</h4>
          <div className="space-y-2 max-h-32 overflow-y-auto">
            {monitoring.alerts.map((alert, index) => (
              <div
                key={index}
                className={`p-3 rounded-lg border ${getAlertColor(alert.severity)}`}
              >
                <div className="flex justify-between items-start">
                  <div className="flex-1">
                    <div className="font-medium text-sm">{alert.type.replace('_', ' ').toUpperCase()}</div>
                    <div className="text-sm mt-1">{alert.message}</div>
                  </div>
                  <span className="text-xs font-medium px-2 py-1 rounded-full bg-white bg-opacity-50">
                    {alert.severity.toUpperCase()}
                  </span>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* No Alerts Message */}
      {(!monitoring.alerts || monitoring.alerts.length === 0) && (
        <div className="bg-green-50 p-3 rounded-lg border border-green-200">
          <div className="flex items-center space-x-2">
            <div className="w-2 h-2 bg-green-500 rounded-full"></div>
            <span className="text-sm text-green-700 font-medium">All systems normal</span>
          </div>
          <p className="text-xs text-green-600 mt-1">
            No risk alerts detected. Portfolio is operating within safe parameters.
          </p>
        </div>
      )}
    </Card>
  );
};

export default PositionMonitoringPanel;