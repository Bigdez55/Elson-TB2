import React, { useState, useEffect, useCallback } from 'react';
import { Card } from '../common/Card';
import { Button } from '../common/Button';
import { LoadingSpinner } from '../common/LoadingSpinner';
import { advancedTradingAPI, AdvancedTradingSignal } from '../../services/advancedTradingAPI';
import { logger } from '../../utils/logger';

interface TradingSignalsPanelProps {
  portfolioId: number;
  onError: (error: string) => void;
}

const TradingSignalsPanel: React.FC<TradingSignalsPanelProps> = ({ portfolioId, onError }) => {
  const [signals, setSignals] = useState<AdvancedTradingSignal[]>([]);
  const [loading, setLoading] = useState(false);
  const [autoExecute, setAutoExecute] = useState(false);
  const [executing, setExecuting] = useState(false);

  const generateSignals = useCallback(async () => {
    setLoading(true);
    onError('');
    
    try {
      const newSignals = await advancedTradingAPI.generateSignals({
        portfolio_id: portfolioId,
      });
      setSignals(newSignals);
    } catch (err: any) {
      onError(err.response?.data?.detail || 'Failed to generate trading signals');
    } finally {
      setLoading(false);
    }
  }, [portfolioId, onError]);

  const executeSignals = async () => {
    setExecuting(true);
    onError('');
    
    try {
      const result = await advancedTradingAPI.executeTrades({
        portfolio_id: portfolioId,
        auto_execute: autoExecute,
      });
      
      if (result.executed_trades?.length > 0) {
        onError(''); // Clear any previous errors
        // You might want to show a success message instead
        logger.info(`Executed ${result.executed_trades.length} trades`);
      }
    } catch (err: any) {
      onError(err.response?.data?.detail || 'Failed to execute trades');
    } finally {
      setExecuting(false);
    }
  };

  useEffect(() => {
    generateSignals();
  }, [generateSignals]);

  const getSignalColor = (action: string) => {
    switch (action.toLowerCase()) {
      case 'buy':
        return 'text-green-600 bg-green-100';
      case 'sell':
        return 'text-red-600 bg-red-100';
      default:
        return 'text-gray-600 bg-gray-100';
    }
  };

  const getConfidenceColor = (confidence: number) => {
    if (confidence >= 0.8) return 'text-green-600';
    if (confidence >= 0.6) return 'text-yellow-600';
    return 'text-red-600';
  };

  return (
    <Card>
      <div className="flex justify-between items-center mb-4">
        <h3 className="text-lg font-semibold">Trading Signals</h3>
        <div className="flex space-x-2">
          <Button
            onClick={generateSignals}
            disabled={loading}
            size="sm"
            variant="outline"
          >
            {loading ? <LoadingSpinner size="sm" /> : 'Refresh'}
          </Button>
        </div>
      </div>

      {signals.length === 0 && !loading ? (
        <div className="text-center py-8 text-gray-500">
          <p>No trading signals available.</p>
          <p className="text-sm">Click refresh to generate new signals.</p>
        </div>
      ) : (
        <div className="space-y-3 max-h-96 overflow-y-auto">
          {signals.map((signal, index) => (
            <div key={index} className="border border-gray-200 rounded-lg p-3">
              <div className="flex justify-between items-start mb-2">
                <div className="flex items-center space-x-2">
                  <span className="font-medium">{signal.symbol}</span>
                  <span className={`px-2 py-1 rounded-full text-xs font-medium ${getSignalColor(signal.action)}`}>
                    {signal.action.toUpperCase()}
                  </span>
                </div>
                <span className="text-sm text-gray-600">
                  ${signal.price.toFixed(2)}
                </span>
              </div>

              <div className="grid grid-cols-2 gap-4 text-sm">
                <div>
                  <span className="text-gray-600">Confidence:</span>
                  <span className={`ml-1 font-medium ${getConfidenceColor(signal.confidence)}`}>
                    {(signal.confidence * 100).toFixed(1)}%
                  </span>
                </div>
                {signal.ai_confidence && (
                  <div>
                    <span className="text-gray-600">AI Confidence:</span>
                    <span className={`ml-1 font-medium ${getConfidenceColor(signal.ai_confidence)}`}>
                      {(signal.ai_confidence * 100).toFixed(1)}%
                    </span>
                  </div>
                )}
              </div>

              <p className="text-sm text-gray-600 mt-2">{signal.reason}</p>

              {(signal.stop_loss || signal.take_profit) && (
                <div className="flex space-x-4 text-xs text-gray-500 mt-2">
                  {signal.stop_loss && (
                    <span>Stop Loss: ${signal.stop_loss.toFixed(2)}</span>
                  )}
                  {signal.take_profit && (
                    <span>Take Profit: ${signal.take_profit.toFixed(2)}</span>
                  )}
                </div>
              )}
            </div>
          ))}
        </div>
      )}

      {signals.length > 0 && (
        <div className="mt-4 pt-4 border-t border-gray-200">
          <div className="flex items-center justify-between">
            <label className="flex items-center">
              <input
                type="checkbox"
                checked={autoExecute}
                onChange={(e) => setAutoExecute(e.target.checked)}
                className="mr-2"
              />
              <span className="text-sm">Auto-execute trades</span>
            </label>
            
            <Button
              onClick={executeSignals}
              disabled={executing}
              className="bg-blue-600 hover:bg-blue-700"
            >
              {executing ? <LoadingSpinner size="sm" /> : 'Execute Trades'}
            </Button>
          </div>
        </div>
      )}
    </Card>
  );
};

export default TradingSignalsPanel;