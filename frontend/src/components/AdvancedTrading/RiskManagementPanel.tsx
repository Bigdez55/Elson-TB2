import React from 'react';
import { Card } from '../common/Card';
import { Button } from '../common/Button';
import { CircuitBreakerStatus, advancedTradingAPI } from '../../services/advancedTradingAPI';

interface RiskManagementPanelProps {
  currentProfile: 'conservative' | 'moderate' | 'aggressive';
  onProfileChange: (profile: 'conservative' | 'moderate' | 'aggressive') => void;
  circuitBreakerStatus: CircuitBreakerStatus | null;
  onError: (error: string) => void;
}

const RiskManagementPanel: React.FC<RiskManagementPanelProps> = ({
  currentProfile,
  onProfileChange,
  circuitBreakerStatus,
  onError,
}) => {
  const handleResetCircuitBreaker = async (breakerType: string) => {
    try {
      await advancedTradingAPI.resetCircuitBreaker(breakerType);
      // You might want to refresh the circuit breaker status here
    } catch (err: any) {
      onError(err.response?.data?.detail || 'Failed to reset circuit breaker');
    }
  };

  const getRiskProfileDescription = (profile: string) => {
    switch (profile) {
      case 'conservative':
        return 'Lower risk, smaller position sizes, stricter stop losses';
      case 'moderate':
        return 'Balanced risk-reward, moderate position sizes';
      case 'aggressive':
        return 'Higher risk tolerance, larger positions, wider stops';
      default:
        return '';
    }
  };

  const getRiskProfileColor = (profile: string) => {
    switch (profile) {
      case 'conservative':
        return 'text-green-600 bg-green-100';
      case 'moderate':
        return 'text-yellow-600 bg-yellow-100';
      case 'aggressive':
        return 'text-red-600 bg-red-100';
      default:
        return 'text-gray-600 bg-gray-100';
    }
  };

  return (
    <Card>
      <h3 className="text-lg font-semibold mb-4">Risk Management</h3>

      {/* Risk Profile Selection */}
      <div className="mb-6">
        <h4 className="font-medium mb-3">Risk Profile</h4>
        <div className="space-y-2">
          {(['conservative', 'moderate', 'aggressive'] as const).map((profile) => (
            <label key={profile} className="flex items-center cursor-pointer">
              <input
                type="radio"
                name="riskProfile"
                value={profile}
                checked={currentProfile === profile}
                onChange={() => onProfileChange(profile)}
                className="mr-3"
              />
              <div className="flex-1">
                <div className="flex items-center space-x-2">
                  <span className="font-medium capitalize">{profile}</span>
                  {currentProfile === profile && (
                    <span className={`px-2 py-1 rounded-full text-xs font-medium ${getRiskProfileColor(profile)}`}>
                      Active
                    </span>
                  )}
                </div>
                <p className="text-sm text-gray-600 mt-1">
                  {getRiskProfileDescription(profile)}
                </p>
              </div>
            </label>
          ))}
        </div>
      </div>

      {/* Circuit Breaker Status */}
      {circuitBreakerStatus && (
        <div className="border-t border-gray-200 pt-4">
          <h4 className="font-medium mb-3">Circuit Breaker Status</h4>
          
          <div className="mb-3">
            <div className="flex justify-between items-center">
              <span className="text-sm text-gray-600">Trading Status</span>
              <span className={`px-2 py-1 rounded-full text-xs font-medium ${
                circuitBreakerStatus.trading_allowed 
                  ? 'bg-green-100 text-green-800' 
                  : 'bg-red-100 text-red-800'
              }`}>
                {circuitBreakerStatus.trading_allowed ? 'Active' : 'Halted'}
              </span>
            </div>
          </div>

          <div className="mb-3">
            <div className="flex justify-between items-center">
              <span className="text-sm text-gray-600">Position Sizing</span>
              <span className="text-sm font-medium">
                {(circuitBreakerStatus.position_sizing_multiplier * 100).toFixed(0)}%
              </span>
            </div>
          </div>

          {/* Active Breakers */}
          {Object.keys(circuitBreakerStatus.active_breakers).length > 0 && (
            <div className="mb-4">
              <h5 className="text-sm font-medium mb-2">Active Breakers</h5>
              <div className="space-y-2">
                {Object.entries(circuitBreakerStatus.active_breakers).map(([key, breaker]: [string, any]) => (
                  <div key={key} className="flex justify-between items-center p-2 bg-red-50 rounded">
                    <div>
                      <div className="text-sm font-medium">{breaker.type}</div>
                      <div className="text-xs text-gray-600">{breaker.reason}</div>
                    </div>
                    <Button
                      onClick={() => handleResetCircuitBreaker(breaker.type)}
                      size="sm"
                      variant="outline"
                      className="text-xs"
                    >
                      Reset
                    </Button>
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* Safety Features */}
          <div className="bg-blue-50 p-3 rounded-lg">
            <h5 className="text-sm font-medium text-blue-800 mb-2">Safety Features Active</h5>
            <ul className="text-xs text-blue-700 space-y-1">
              <li>• Automatic position sizing based on volatility</li>
              <li>• Daily loss limits and drawdown protection</li>
              <li>• Real-time risk monitoring and alerts</li>
              <li>• Emergency trading halt capabilities</li>
            </ul>
          </div>
        </div>
      )}
    </Card>
  );
};

export default RiskManagementPanel;