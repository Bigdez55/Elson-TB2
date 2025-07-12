import React, { useState, useEffect, useCallback } from 'react';
import { Card } from '../common/Card';
import { Button } from '../common/Button';
import LoadingSpinner from '../LoadingSpinner';
import { advancedTradingAPI, AIModelStatus } from '../../services/advancedTradingAPI';

interface AIModelsStatusProps {
  onError: (error: string) => void;
}

const AIModelsStatus: React.FC<AIModelsStatusProps> = ({ onError }) => {
  const [modelStatus, setModelStatus] = useState<AIModelStatus | null>(null);
  const [loading, setLoading] = useState(true);
  const [retraining, setRetraining] = useState(false);

  const loadModelStatus = useCallback(async () => {
    try {
      const status = await advancedTradingAPI.getAIModelsStatus();
      setModelStatus(status);
    } catch (err: any) {
      onError(err.response?.data?.detail || 'Failed to load AI model status');
    } finally {
      setLoading(false);
    }
  }, [onError]);

  const retrainModels = async () => {
    if (!modelStatus) return;
    
    setRetraining(true);
    onError('');
    
    try {
      const symbols = Object.keys(modelStatus.models);
      await advancedTradingAPI.retrainAIModels(symbols);
      
      // Refresh status after a short delay to show retraining has started
      setTimeout(() => {
        loadModelStatus();
      }, 2000);
    } catch (err: any) {
      onError(err.response?.data?.detail || 'Failed to start model retraining');
    } finally {
      setRetraining(false);
    }
  };

  useEffect(() => {
    loadModelStatus();
    // Refresh every 60 seconds
    const interval = setInterval(loadModelStatus, 60000);
    return () => clearInterval(interval);
  }, [loadModelStatus]);

  if (loading) {
    return (
      <Card>
        <h3 className="text-lg font-semibold mb-4">AI Models Status</h3>
        <div className="flex justify-center py-8">
          <LoadingSpinner />
        </div>
      </Card>
    );
  }

  if (!modelStatus) {
    return (
      <Card>
        <h3 className="text-lg font-semibold mb-4">AI Models Status</h3>
        <div className="text-center py-8 text-gray-500">
          <p>No AI models found.</p>
          <p className="text-sm">Initialize the trading system to create AI models.</p>
        </div>
      </Card>
    );
  }

  const trainingPercentage = modelStatus.total_models > 0 
    ? (modelStatus.trained_models / modelStatus.total_models) * 100 
    : 0;

  return (
    <Card>
      <div className="flex justify-between items-center mb-4">
        <h3 className="text-lg font-semibold">AI Models Status</h3>
        <Button
          onClick={retrainModels}
          disabled={retraining}
          size="sm"
          variant="outline"
        >
          {retraining ? <LoadingSpinner size="small" /> : 'Retrain All'}
        </Button>
      </div>

      {/* Overview Stats */}
      <div className="grid grid-cols-2 gap-4 mb-4">
        <div className="text-center p-3 bg-blue-50 rounded-lg">
          <div className="text-2xl font-bold text-blue-600">{modelStatus.total_models}</div>
          <div className="text-sm text-blue-600">Total Models</div>
        </div>
        <div className="text-center p-3 bg-green-50 rounded-lg">
          <div className="text-2xl font-bold text-green-600">{modelStatus.trained_models}</div>
          <div className="text-sm text-green-600">Trained</div>
        </div>
      </div>

      {/* Training Progress Bar */}
      <div className="mb-4">
        <div className="flex justify-between text-sm text-gray-600 mb-1">
          <span>Training Progress</span>
          <span>{trainingPercentage.toFixed(0)}%</span>
        </div>
        <div className="w-full bg-gray-200 rounded-full h-2">
          <div 
            className="bg-blue-600 h-2 rounded-full transition-all duration-300"
            style={{ width: `${trainingPercentage}%` }}
          ></div>
        </div>
      </div>

      {/* Individual Model Status */}
      <div className="space-y-2 max-h-64 overflow-y-auto">
        {Object.entries(modelStatus.models).map(([symbol, model]) => (
          <div key={symbol} className="flex items-center justify-between p-2 border border-gray-200 rounded">
            <div className="flex items-center space-x-3">
              <span className="font-medium">{symbol}</span>
              <span className={`px-2 py-1 rounded-full text-xs font-medium ${
                model.is_trained 
                  ? 'bg-green-100 text-green-800' 
                  : 'bg-yellow-100 text-yellow-800'
              }`}>
                {model.is_trained ? 'Trained' : 'Training'}
              </span>
            </div>
            
            <div className="text-right text-sm">
              {model.is_trained && model.last_prediction !== undefined && (
                <div className="text-gray-600">
                  Prediction: {(model.last_prediction * 100).toFixed(1)}%
                </div>
              )}
              {model.prediction_confidence && (
                <div className="text-gray-500 text-xs">
                  Confidence: {(model.prediction_confidence * 100).toFixed(1)}%
                </div>
              )}
            </div>
          </div>
        ))}
      </div>

      {/* Training Summary */}
      {modelStatus.trained_models > 0 && (
        <div className="mt-4 pt-4 border-t border-gray-200">
          <h4 className="font-medium text-sm text-gray-700 mb-2">Training Summary</h4>
          <div className="text-xs text-gray-600">
            <p>• Quantum-inspired machine learning algorithms</p>
            <p>• Real-time feature engineering from market data</p>
            <p>• Continuous learning and adaptation</p>
          </div>
        </div>
      )}
    </Card>
  );
};

export default AIModelsStatus;