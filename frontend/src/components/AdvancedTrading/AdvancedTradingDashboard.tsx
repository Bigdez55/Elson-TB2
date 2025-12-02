import React, { useState, useEffect } from 'react';
import { Card } from '../common/Card';
import { Button } from '../common/Button';
import LoadingSpinner from '../LoadingSpinner';
import { advancedTradingAPI, PerformanceSummary, CircuitBreakerStatus } from '../../services/advancedTradingAPI';
import TradingSignalsPanel from './TradingSignalsPanel';
import AIModelsStatus from './AIModelsStatus';
import RiskManagementPanel from './RiskManagementPanel';
import PositionMonitoringPanel from './PositionMonitoringPanel';
import { logger } from '../../utils/logger';

interface AdvancedTradingDashboardProps {
  portfolioId: number;
}

const AdvancedTradingDashboard: React.FC<AdvancedTradingDashboardProps> = ({ portfolioId }) => {
  const [isInitialized, setIsInitialized] = useState(false);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [performanceSummary, setPerformanceSummary] = useState<PerformanceSummary | null>(null);
  const [circuitBreakerStatus, setCircuitBreakerStatus] = useState<CircuitBreakerStatus | null>(null);
  const [riskProfile, setRiskProfile] = useState<'conservative' | 'moderate' | 'aggressive'>('moderate');

  useEffect(() => {
    loadDashboardData();
    // Refresh data every 30 seconds
    const interval = setInterval(loadDashboardData, 30000);
    return () => clearInterval(interval);
  }, []);

  const loadDashboardData = async () => {
    try {
      const [performance, circuitBreaker] = await Promise.all([
        advancedTradingAPI.getPerformanceSummary(),
        advancedTradingAPI.getCircuitBreakerStatus(),
      ]);
      
      setPerformanceSummary(performance);
      setCircuitBreakerStatus(circuitBreaker);
      setIsInitialized(performance.active_strategies > 0);
    } catch (err) {
      logger.error('Error loading dashboard data:', err);
      setError('Failed to load dashboard data');
    }
  };

  const handleInitialize = async () => {
    setLoading(true);
    setError(null);
    
    try {
      // Use some default symbols for initialization
      const symbols = ['AAPL', 'GOOGL', 'MSFT', 'TSLA', 'NVDA'];
      
      await advancedTradingAPI.initialize({
        symbols,
        risk_profile: riskProfile,
        enable_ai_models: true,
      });
      
      setIsInitialized(true);
      await loadDashboardData();
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Failed to initialize trading system');
    } finally {
      setLoading(false);
    }
  };

  const handleRiskProfileChange = async (newProfile: 'conservative' | 'moderate' | 'aggressive') => {
    try {
      await advancedTradingAPI.updateRiskProfile(newProfile);
      setRiskProfile(newProfile);
      await loadDashboardData();
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Failed to update risk profile');
    }
  };

  if (!isInitialized) {
    return (
      <div className="max-w-4xl mx-auto p-6">
        <Card className="text-center">
          <h2 className="text-2xl font-bold mb-4">Advanced Trading System</h2>
          <p className="text-gray-600 mb-6">
            Initialize the advanced trading system with AI-powered strategies and risk management.
          </p>
          
          <div className="mb-4">
            <label className="block text-sm font-medium mb-2">Risk Profile</label>
            <select
              value={riskProfile}
              onChange={(e) => setRiskProfile(e.target.value as any)}
              className="w-48 p-2 border border-gray-300 rounded-md"
            >
              <option value="conservative">Conservative</option>
              <option value="moderate">Moderate</option>
              <option value="aggressive">Aggressive</option>
            </select>
          </div>

          {error && (
            <div className="mb-4 p-3 bg-red-100 border border-red-400 text-red-700 rounded">
              {error}
            </div>
          )}

          <Button
            onClick={handleInitialize}
            disabled={loading}
            className="bg-blue-600 hover:bg-blue-700"
          >
            {loading ? <LoadingSpinner /> : 'Initialize Trading System'}
          </Button>
        </Card>
      </div>
    );
  }

  return (
    <div className="max-w-7xl mx-auto p-6 space-y-6">
      <div className="flex justify-between items-center">
        <h1 className="text-3xl font-bold">Advanced Trading Dashboard</h1>
        
        {circuitBreakerStatus && (
          <div className={`px-3 py-1 rounded-full text-sm font-medium ${
            circuitBreakerStatus.trading_allowed 
              ? 'bg-green-100 text-green-800' 
              : 'bg-red-100 text-red-800'
          }`}>
            {circuitBreakerStatus.trading_allowed ? 'Trading Active' : 'Trading Halted'}
          </div>
        )}
      </div>

      {/* Performance Overview */}
      {performanceSummary && (
        <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
          <Card>
            <h3 className="text-sm font-medium text-gray-600">Active Strategies</h3>
            <p className="text-2xl font-bold">{performanceSummary.active_strategies}</p>
          </Card>
          <Card>
            <h3 className="text-sm font-medium text-gray-600">AI Models Trained</h3>
            <p className="text-2xl font-bold">{performanceSummary.trained_ai_models}</p>
          </Card>
          <Card>
            <h3 className="text-sm font-medium text-gray-600">Risk Profile</h3>
            <p className="text-2xl font-bold capitalize">{performanceSummary.risk_profile}</p>
          </Card>
          <Card>
            <h3 className="text-sm font-medium text-gray-600">Total Trades</h3>
            <p className="text-2xl font-bold">
              {performanceSummary.performance_metrics.total_trades || 0}
            </p>
          </Card>
        </div>
      )}

      {error && (
        <div className="p-4 bg-red-100 border border-red-400 text-red-700 rounded-md">
          {error}
        </div>
      )}

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Trading Signals Panel */}
        <TradingSignalsPanel 
          portfolioId={portfolioId}
          onError={setError}
        />

        {/* Position Monitoring */}
        <PositionMonitoringPanel 
          portfolioId={portfolioId}
          onError={setError}
        />
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* AI Models Status */}
        <AIModelsStatus onError={setError} />

        {/* Risk Management */}
        <RiskManagementPanel
          currentProfile={riskProfile}
          onProfileChange={handleRiskProfileChange}
          circuitBreakerStatus={circuitBreakerStatus}
          onError={setError}
        />
      </div>
    </div>
  );
};

export default AdvancedTradingDashboard;