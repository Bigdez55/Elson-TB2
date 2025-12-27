import React, { useState, useEffect } from 'react';
import { Badge } from '../common/Badge';
import {
  useGetAutoTradingStatusQuery,
  useStartAutoTradingMutation,
  useStopAutoTradingMutation,
  useGetAvailableStrategiesQuery,
  useGetStrategyCategoriesQuery,
  useAddStrategyMutation,
  useRemoveStrategyMutation,
  type AvailableStrategy,
} from '../../services/autoTradingApi';

interface AutoTradingSettingsProps {
  portfolioId: number;
  className?: string;
}

export const AutoTradingSettings: React.FC<AutoTradingSettingsProps> = ({
  portfolioId,
  className = '',
}) => {
  const [selectedStrategies, setSelectedStrategies] = useState<string[]>([]);
  const [selectedSymbols, setSelectedSymbols] = useState<string[]>(['AAPL', 'GOOGL', 'MSFT']);
  const [symbolInput, setSymbolInput] = useState('');
  const [categoryFilter, setCategoryFilter] = useState<string>('');

  // API hooks
  const { data: statusData, isLoading: statusLoading } = useGetAutoTradingStatusQuery(undefined, {
    pollingInterval: 10000, // Poll every 10s
  });
  const { data: categories } = useGetStrategyCategoriesQuery();
  const { data: strategies, isLoading: strategiesLoading } = useGetAvailableStrategiesQuery({
    category: categoryFilter || undefined,
  });

  const [startAutoTrading, { isLoading: isStarting }] = useStartAutoTradingMutation();
  const [stopAutoTrading, { isLoading: isStopping }] = useStopAutoTradingMutation();
  const [addStrategy] = useAddStrategyMutation();
  const [removeStrategy] = useRemoveStrategyMutation();

  const isActive = statusData?.is_active || false;
  const activeStrategies = statusData?.active_strategies || {};

  const handleToggleStrategy = (strategyName: string) => {
    setSelectedStrategies((prev) =>
      prev.includes(strategyName)
        ? prev.filter((s) => s !== strategyName)
        : [...prev, strategyName]
    );
  };

  const handleAddSymbol = () => {
    const symbol = symbolInput.trim().toUpperCase();
    if (symbol && !selectedSymbols.includes(symbol)) {
      setSelectedSymbols([...selectedSymbols, symbol]);
      setSymbolInput('');
    }
  };

  const handleRemoveSymbol = (symbol: string) => {
    setSelectedSymbols(selectedSymbols.filter((s) => s !== symbol));
  };

  const handleStartAutoTrading = async () => {
    if (selectedStrategies.length === 0) {
      alert('Please select at least one strategy');
      return;
    }
    if (selectedSymbols.length === 0) {
      alert('Please add at least one symbol');
      return;
    }

    try {
      await startAutoTrading({
        portfolio_id: portfolioId,
        strategy_names: selectedStrategies,
        symbols: selectedSymbols,
      }).unwrap();
    } catch (error: any) {
      alert(error?.data?.detail || 'Failed to start auto-trading');
    }
  };

  const handleStopAutoTrading = async () => {
    try {
      await stopAutoTrading().unwrap();
    } catch (error: any) {
      alert(error?.data?.detail || 'Failed to stop auto-trading');
    }
  };

  const getRiskBadgeVariant = (riskLevel: string) => {
    switch (riskLevel.toLowerCase()) {
      case 'low':
        return 'success';
      case 'medium':
        return 'warning';
      case 'high':
        return 'error';
      default:
        return 'neutral';
    }
  };

  const getCategoryBadgeVariant = (category: string) => {
    const categoryMap: Record<string, any> = {
      technical: 'info',
      momentum: 'premium',
      mean_reversion: 'warning',
      arbitrage: 'success',
      breakout: 'error',
      grid: 'neutral',
      execution: 'info',
    };
    return categoryMap[category] || 'neutral';
  };

  return (
    <div className={`bg-gray-900 rounded-xl p-6 ${className}`}>
      {/* Header with Master Toggle */}
      <div className="flex items-center justify-between mb-6">
        <div>
          <h2 className="text-xl font-bold text-white">Automated Trading</h2>
          <p className="text-gray-400 text-sm mt-1">
            AI-powered strategies trading automatically 24/7
          </p>
        </div>
        <div className="flex items-center gap-4">
          {isActive && (
            <div className="flex items-center gap-2">
              <div className="w-2 h-2 rounded-full bg-green-400 animate-pulse" />
              <span className="text-green-400 text-sm font-medium">Active</span>
            </div>
          )}
          <button
            onClick={isActive ? handleStopAutoTrading : handleStartAutoTrading}
            disabled={isStarting || isStopping || (!isActive && selectedStrategies.length === 0)}
            className={`px-6 py-2 rounded-lg font-medium transition-colors ${
              isActive
                ? 'bg-red-600 hover:bg-red-700 text-white'
                : 'bg-purple-600 hover:bg-purple-700 text-white disabled:bg-gray-700 disabled:text-gray-400'
            }`}
          >
            {isStarting || isStopping
              ? 'Processing...'
              : isActive
              ? 'Stop Auto-Trading'
              : 'Start Auto-Trading'}
          </button>
        </div>
      </div>

      {/* Active Strategies Overview */}
      {isActive && Object.keys(activeStrategies).length > 0 && (
        <div className="bg-gray-800 rounded-lg p-4 mb-6">
          <h3 className="text-white font-medium mb-3">Active Strategies</h3>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
            {Object.entries(activeStrategies).map(([key, strategy]) => (
              <div key={key} className="bg-gray-700 rounded-lg p-3">
                <div className="flex items-center justify-between mb-2">
                  <span className="text-white font-medium text-sm">{strategy.name}</span>
                  <Badge variant="success" size="sm">
                    {strategy.symbol}
                  </Badge>
                </div>
                <div className="grid grid-cols-2 gap-2 text-xs">
                  <div>
                    <span className="text-gray-400">Trades:</span>
                    <span className="text-white ml-1">
                      {strategy.performance.total_trades}
                    </span>
                  </div>
                  <div>
                    <span className="text-gray-400">Win Rate:</span>
                    <span className="text-white ml-1">
                      {(strategy.performance.win_rate * 100).toFixed(1)}%
                    </span>
                  </div>
                  <div>
                    <span className="text-gray-400">Return:</span>
                    <span
                      className={`ml-1 ${
                        strategy.performance.total_return >= 0
                          ? 'text-green-400'
                          : 'text-red-400'
                      }`}
                    >
                      {strategy.performance.total_return >= 0 ? '+' : ''}
                      {strategy.performance.total_return.toFixed(2)}%
                    </span>
                  </div>
                  <div>
                    <span className="text-gray-400">Sharpe:</span>
                    <span className="text-white ml-1">
                      {strategy.performance.sharpe_ratio.toFixed(2)}
                    </span>
                  </div>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Configuration Section (Only when stopped) */}
      {!isActive && (
        <>
          {/* Symbol Selection */}
          <div className="mb-6">
            <label className="block text-white font-medium mb-3">Trading Symbols</label>
            <div className="flex gap-2 mb-3">
              <input
                type="text"
                value={symbolInput}
                onChange={(e) => setSymbolInput(e.target.value.toUpperCase())}
                onKeyPress={(e) => e.key === 'Enter' && handleAddSymbol()}
                placeholder="Enter symbol (e.g., AAPL)"
                className="flex-1 bg-gray-800 border border-gray-700 rounded-lg px-4 py-2 text-white placeholder-gray-400 focus:outline-none focus:border-purple-500"
              />
              <button
                onClick={handleAddSymbol}
                className="px-6 py-2 bg-gray-700 hover:bg-gray-600 text-white rounded-lg transition-colors"
              >
                Add
              </button>
            </div>
            <div className="flex flex-wrap gap-2">
              {selectedSymbols.map((symbol) => (
                <div
                  key={symbol}
                  className="bg-gray-800 border border-gray-700 rounded-lg px-3 py-1 flex items-center gap-2"
                >
                  <span className="text-white text-sm">{symbol}</span>
                  <button
                    onClick={() => handleRemoveSymbol(symbol)}
                    className="text-gray-400 hover:text-red-400 transition-colors"
                  >
                    <svg
                      className="h-4 w-4"
                      fill="none"
                      stroke="currentColor"
                      viewBox="0 0 24 24"
                    >
                      <path
                        strokeLinecap="round"
                        strokeLinejoin="round"
                        strokeWidth="2"
                        d="M6 18L18 6M6 6l12 12"
                      />
                    </svg>
                  </button>
                </div>
              ))}
            </div>
          </div>

          {/* Strategy Selection */}
          <div>
            <div className="flex items-center justify-between mb-3">
              <label className="block text-white font-medium">Select Strategies</label>
              <select
                value={categoryFilter}
                onChange={(e) => setCategoryFilter(e.target.value)}
                className="bg-gray-800 border border-gray-700 rounded-lg px-3 py-1 text-white text-sm focus:outline-none focus:border-purple-500"
              >
                <option value="">All Categories</option>
                {categories?.map((cat) => (
                  <option key={cat} value={cat}>
                    {cat.replace('_', ' ').toUpperCase()}
                  </option>
                ))}
              </select>
            </div>

            {strategiesLoading ? (
              <div className="text-center py-8 text-gray-400">Loading strategies...</div>
            ) : (
              <div className="grid grid-cols-1 md:grid-cols-2 gap-3 max-h-96 overflow-y-auto">
                {strategies?.map((strategy) => (
                  <div
                    key={strategy.name}
                    onClick={() => handleToggleStrategy(strategy.name)}
                    className={`bg-gray-800 border-2 rounded-lg p-4 cursor-pointer transition-all ${
                      selectedStrategies.includes(strategy.name)
                        ? 'border-purple-500 bg-purple-900/20'
                        : 'border-gray-700 hover:border-gray-600'
                    }`}
                  >
                    <div className="flex items-start justify-between mb-2">
                      <div className="flex-1">
                        <h4 className="text-white font-medium text-sm mb-1">
                          {strategy.name.replace('_', ' ').toUpperCase()}
                        </h4>
                        <p className="text-gray-400 text-xs leading-relaxed">
                          {strategy.description}
                        </p>
                      </div>
                      {selectedStrategies.includes(strategy.name) && (
                        <svg
                          className="h-5 w-5 text-purple-400 flex-shrink-0 ml-2"
                          fill="currentColor"
                          viewBox="0 0 20 20"
                        >
                          <path
                            fillRule="evenodd"
                            d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-9.293a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z"
                            clipRule="evenodd"
                          />
                        </svg>
                      )}
                    </div>
                    <div className="flex gap-2 mt-3">
                      <Badge variant={getCategoryBadgeVariant(strategy.category)} size="sm">
                        {strategy.category.replace('_', ' ')}
                      </Badge>
                      <Badge variant={getRiskBadgeVariant(strategy.risk_level)} size="sm">
                        {strategy.risk_level} risk
                      </Badge>
                    </div>
                  </div>
                ))}
              </div>
            )}
          </div>

          {/* Summary */}
          {selectedStrategies.length > 0 && (
            <div className="mt-6 bg-gray-800 rounded-lg p-4">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-white font-medium">Ready to Start</p>
                  <p className="text-gray-400 text-sm">
                    {selectedStrategies.length} {selectedStrategies.length === 1 ? 'strategy' : 'strategies'} on{' '}
                    {selectedSymbols.length} {selectedSymbols.length === 1 ? 'symbol' : 'symbols'}
                  </p>
                </div>
                <div className="text-right">
                  <p className="text-purple-400 font-medium text-lg">
                    {selectedStrategies.length * selectedSymbols.length}
                  </p>
                  <p className="text-gray-400 text-xs">Total Combinations</p>
                </div>
              </div>
            </div>
          )}
        </>
      )}
    </div>
  );
};
