import React from 'react';
import { CircuitBreaker } from '../../services/riskManagementApi';

interface CircuitBreakerStatusProps {
  breakers: CircuitBreaker[];
  className?: string;
}

export const CircuitBreakerStatus: React.FC<CircuitBreakerStatusProps> = ({ 
  breakers, 
  className = '' 
}) => {
  const getStatusColor = (isTriggered: boolean) => {
    return isTriggered 
      ? 'bg-red-900 text-red-300 border-red-700' 
      : 'bg-green-900 text-green-300 border-green-700';
  };

  const getStatusIcon = (isTriggered: boolean) => {
    if (isTriggered) {
      return (
        <svg className="h-5 w-5 text-red-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z" />
        </svg>
      );
    }
    
    return (
      <svg className="h-5 w-5 text-green-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" />
      </svg>
    );
  };

  const formatValue = (value: number, breakerType: string) => {
    if (breakerType.includes('loss') || breakerType.includes('value')) {
      return `$${value.toLocaleString()}`;
    }
    if (breakerType.includes('percent') || breakerType.includes('pct')) {
      return `${(value * 100).toFixed(2)}%`;
    }
    return value.toLocaleString();
  };

  const formatTime = (timeString: string | undefined) => {
    if (!timeString) return 'N/A';
    
    try {
      const date = new Date(timeString);
      return date.toLocaleString();
    } catch {
      return 'Invalid Date';
    }
  };

  const getProgressPercentage = (current: number, threshold: number) => {
    return Math.min((current / threshold) * 100, 100);
  };

  const getProgressColor = (percentage: number) => {
    if (percentage >= 100) return 'bg-red-500';
    if (percentage >= 80) return 'bg-red-400';
    if (percentage >= 60) return 'bg-yellow-400';
    return 'bg-green-500';
  };

  const triggeredBreakers = breakers.filter(b => b.is_triggered);
  const activeBreakers = breakers.filter(b => !b.is_triggered);

  return (
    <div className={`space-y-6 ${className}`}>
      {/* Summary Cards */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        <div className="bg-gray-800 rounded-lg p-4">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-gray-400 text-sm">Total Breakers</p>
              <p className="text-2xl font-bold text-white">{breakers.length}</p>
            </div>
            <svg className="h-8 w-8 text-blue-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M9 12l2 2 4-4m5.618-4.016A11.955 11.955 0 0112 2.944a11.955 11.955 0 01-8.618 3.04A12.02 12.02 0 003 9c0 5.591 3.824 10.29 9 11.622 5.176-1.332 9-6.03 9-11.622 0-1.042-.133-2.052-.382-3.016z" />
            </svg>
          </div>
        </div>

        <div className="bg-gray-800 rounded-lg p-4">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-gray-400 text-sm">Triggered</p>
              <p className="text-2xl font-bold text-red-400">{triggeredBreakers.length}</p>
            </div>
            <svg className="h-8 w-8 text-red-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z" />
            </svg>
          </div>
        </div>

        <div className="bg-gray-800 rounded-lg p-4">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-gray-400 text-sm">Active</p>
              <p className="text-2xl font-bold text-green-400">{activeBreakers.length}</p>
            </div>
            <svg className="h-8 w-8 text-green-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" />
            </svg>
          </div>
        </div>
      </div>

      {/* Triggered Breakers Alert */}
      {triggeredBreakers.length > 0 && (
        <div className="bg-red-900 bg-opacity-30 border border-red-700 rounded-lg p-4">
          <div className="flex items-center mb-3">
            <svg className="h-6 w-6 text-red-400 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z" />
            </svg>
            <h3 className="text-red-300 font-bold text-lg">Circuit Breakers Triggered</h3>
          </div>
          <p className="text-red-400 text-sm mb-4">
            {triggeredBreakers.length} circuit breaker{triggeredBreakers.length > 1 ? 's have' : ' has'} been triggered. 
            Trading may be restricted until conditions improve.
          </p>
          <div className="space-y-2">
            {triggeredBreakers.map((breaker, index) => (
              <div key={index} className="bg-red-800 bg-opacity-50 rounded p-3">
                <div className="flex justify-between items-start">
                  <div>
                    <p className="text-red-200 font-medium">{breaker.breaker_type}</p>
                    <p className="text-red-300 text-sm">{breaker.description}</p>
                    <p className="text-red-400 text-xs mt-1">
                      Triggered: {formatTime(breaker.triggered_at)}
                    </p>
                  </div>
                  <div className="text-right">
                    <p className="text-red-200 text-sm">
                      {formatValue(breaker.current_value, breaker.breaker_type)} / {formatValue(breaker.threshold_value, breaker.breaker_type)}
                    </p>
                    {breaker.reset_time && (
                      <p className="text-red-400 text-xs">
                        Reset: {formatTime(breaker.reset_time)}
                      </p>
                    )}
                  </div>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* All Circuit Breakers */}
      <div className="bg-gray-800 rounded-lg overflow-hidden">
        <div className="p-6 border-b border-gray-700">
          <h3 className="text-lg font-medium text-white">Circuit Breaker Status</h3>
          <p className="text-gray-400 text-sm mt-1">
            Real-time monitoring of risk management circuit breakers
          </p>
        </div>

        <div className="divide-y divide-gray-700">
          {breakers.map((breaker, index) => {
            const progressPercentage = getProgressPercentage(breaker.current_value, breaker.threshold_value);
            
            return (
              <div key={index} className="p-6">
                <div className="flex items-start justify-between mb-4">
                  <div className="flex items-start space-x-3">
                    {getStatusIcon(breaker.is_triggered)}
                    <div>
                      <h4 className="text-white font-medium capitalize">
                        {breaker.breaker_type.replace(/_/g, ' ')}
                      </h4>
                      <p className="text-gray-400 text-sm mt-1">
                        {breaker.description}
                      </p>
                    </div>
                  </div>
                  
                  <div className={`px-3 py-1 rounded-full text-sm font-medium border ${getStatusColor(breaker.is_triggered)}`}>
                    {breaker.is_triggered ? 'TRIGGERED' : 'ACTIVE'}
                  </div>
                </div>

                {/* Progress Bar */}
                <div className="mb-4">
                  <div className="flex justify-between items-center mb-2">
                    <span className="text-gray-400 text-sm">Current Usage</span>
                    <span className="text-white text-sm font-medium">
                      {formatValue(breaker.current_value, breaker.breaker_type)} / {formatValue(breaker.threshold_value, breaker.breaker_type)}
                    </span>
                  </div>
                  <div className="w-full bg-gray-700 rounded-full h-3">
                    <div 
                      className={`h-3 rounded-full transition-all duration-300 ${getProgressColor(progressPercentage)}`}
                      style={{ width: `${progressPercentage}%` }}
                    />
                  </div>
                  <div className="flex justify-between items-center mt-1">
                    <span className="text-gray-500 text-xs">0%</span>
                    <span className="text-gray-500 text-xs">{progressPercentage.toFixed(1)}%</span>
                    <span className="text-gray-500 text-xs">100%</span>
                  </div>
                </div>

                {/* Timestamps */}
                <div className="flex justify-between items-center text-xs text-gray-500">
                  <div>
                    {breaker.triggered_at && (
                      <span>Last Triggered: {formatTime(breaker.triggered_at)}</span>
                    )}
                  </div>
                  <div>
                    {breaker.reset_time && (
                      <span>Reset Time: {formatTime(breaker.reset_time)}</span>
                    )}
                  </div>
                </div>
              </div>
            );
          })}
        </div>
      </div>

      {breakers.length === 0 && (
        <div className="bg-gray-800 rounded-lg p-8 text-center">
          <svg className="h-12 w-12 text-gray-400 mx-auto mb-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M9 12l2 2 4-4m5.618-4.016A11.955 11.955 0 0112 2.944a11.955 11.955 0 01-8.618 3.04A12.02 12.02 0 003 9c0 5.591 3.824 10.29 9 11.622 5.176-1.332 9-6.03 9-11.622 0-1.042-.133-2.052-.382-3.016z" />
          </svg>
          <h3 className="text-gray-400 text-lg font-medium mb-2">No Circuit Breakers Configured</h3>
          <p className="text-gray-500">Risk management circuit breakers have not been set up for this account.</p>
        </div>
      )}
    </div>
  );
};

export default CircuitBreakerStatus;