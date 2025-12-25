import React from 'react';
import { Badge } from '../common/Badge';

interface AIAnalysis {
  signal: 'BUY' | 'SELL' | 'HOLD';
  confidence: number;
  description: string;
}

interface AIStrategy {
  title: string;
  description: string;
  enabled: boolean;
}

interface RiskAssessment {
  score: number; // 0-100
  level: 'LOW' | 'MEDIUM' | 'HIGH';
  description: string;
  recommendation?: string;
}

interface AITradingAssistantProps {
  symbol: string;
  analysis: AIAnalysis;
  strategy: AIStrategy;
  riskAssessment: RiskAssessment;
  onApplyStrategy?: () => void;
  onUpdateStrategy?: () => void;
  className?: string;
}

export const AITradingAssistant: React.FC<AITradingAssistantProps> = ({
  symbol,
  analysis,
  strategy,
  riskAssessment,
  onApplyStrategy,
  onUpdateStrategy,
  className = '',
}) => {
  const getSignalColor = (signal: string) => {
    switch (signal) {
      case 'BUY': return 'bg-green-900 bg-opacity-30 text-green-400';
      case 'SELL': return 'bg-red-900 bg-opacity-30 text-red-400';
      case 'HOLD': return 'bg-yellow-900 bg-opacity-30 text-yellow-400';
      default: return 'bg-gray-900 bg-opacity-30 text-gray-400';
    }
  };

  const getConfidenceColor = (confidence: number) => {
    if (confidence >= 80) return 'bg-purple-900 bg-opacity-30 text-purple-300';
    if (confidence >= 60) return 'bg-blue-900 bg-opacity-30 text-blue-300';
    return 'bg-yellow-900 bg-opacity-30 text-yellow-300';
  };

  const getRiskColor = (level: string) => {
    switch (level) {
      case 'LOW': return 'from-green-500 to-yellow-500';
      case 'MEDIUM': return 'from-yellow-500 to-orange-500';
      case 'HIGH': return 'from-orange-500 to-red-500';
      default: return 'from-gray-500 to-gray-600';
    }
  };

  return (
    <div className={`bg-gray-900 rounded-xl p-6 ${className}`}>
      <div className="flex justify-between items-center mb-4">
        <h3 className="text-lg font-medium text-white">AI Trading Assistant</h3>
        <Badge variant="premium" size="sm">
          Premium
        </Badge>
      </div>
      
      <div className="space-y-4">
        {/* Quantum AI Analysis */}
        <div className="bg-gray-800 p-4 rounded-lg">
          <div className="flex items-center mb-2">
            <svg className="h-5 w-5 text-purple-400 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M9.663 17h4.673M12 3v1m6.364 1.636l-.707.707M21 12h-1M4 12H3m3.343-5.657l-.707-.707m2.828 9.9a5 5 0 117.072 0l-.548.547A3.374 3.374 0 0014 18.469V19a2 2 0 11-4 0v-.531c0-.895-.356-1.754-.988-2.386l-.548-.547z" />
            </svg>
            <span className="text-white font-medium">Quantum AI Analysis</span>
          </div>
          <p className="text-gray-300 text-sm mb-2">{analysis.description}</p>
          <div className="flex space-x-2">
            <div className={`px-2 py-1 rounded-md text-xs ${getSignalColor(analysis.signal)}`}>
              {analysis.signal} Signal
            </div>
            <div className={`px-2 py-1 rounded-md text-xs ${getConfidenceColor(analysis.confidence)}`}>
              {analysis.confidence}% Confidence
            </div>
          </div>
        </div>
        
        {/* Automated Strategy */}
        <div className="bg-gray-800 p-4 rounded-lg">
          <div className="flex items-center mb-2">
            <svg className="h-5 w-5 text-purple-400 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z" />
            </svg>
            <span className="text-white font-medium">Automated Strategy</span>
          </div>
          <p className="text-gray-300 text-sm mb-2">{strategy.description}</p>
          <button 
            onClick={onApplyStrategy}
            className="w-full bg-purple-600 hover:bg-purple-700 text-white rounded-lg p-2 text-sm transition-colors"
          >
            Apply AI Strategy
          </button>
        </div>
        
        {/* Risk Assessment */}
        <div className="bg-gray-800 p-4 rounded-lg">
          <div className="flex items-center mb-2">
            <svg className="h-5 w-5 text-purple-400 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
            </svg>
            <span className="text-white font-medium">Risk Assessment</span>
          </div>
          <div className="flex items-center mb-2">
            <div className="flex-1 h-2 bg-gray-700 rounded-full overflow-hidden">
              <div 
                className={`h-full bg-gradient-to-r ${getRiskColor(riskAssessment.level)}`} 
                style={{ width: `${riskAssessment.score}%` }}
              />
            </div>
            <span className="ml-2 text-gray-300 text-sm">{riskAssessment.score}/100</span>
          </div>
          <p className="text-gray-300 text-sm">{riskAssessment.description}</p>
          {riskAssessment.recommendation && (
            <p className="text-yellow-300 text-xs mt-1">
              <span className="font-medium">Recommendation:</span> {riskAssessment.recommendation}
            </p>
          )}
        </div>

        {/* Additional AI Features */}
        <div className="bg-gray-800 p-4 rounded-lg">
          <div className="flex items-center justify-between mb-2">
            <span className="text-white font-medium text-sm">AI Features</span>
            <button 
              onClick={onUpdateStrategy}
              className="text-purple-400 hover:text-purple-300 text-xs transition-colors"
            >
              Configure
            </button>
          </div>
          <div className="space-y-2">
            <div className="flex items-center justify-between text-xs">
              <span className="text-gray-300">Auto-rebalancing</span>
              <div className="w-2 h-2 rounded-full bg-green-400"></div>
            </div>
            <div className="flex items-center justify-between text-xs">
              <span className="text-gray-300">Stop-loss protection</span>
              <div className="w-2 h-2 rounded-full bg-green-400"></div>
            </div>
            <div className="flex items-center justify-between text-xs">
              <span className="text-gray-300">Market sentiment analysis</span>
              <div className="w-2 h-2 rounded-full bg-yellow-400"></div>
            </div>
            <div className="flex items-center justify-between text-xs">
              <span className="text-gray-300">Technical indicators</span>
              <div className="w-2 h-2 rounded-full bg-green-400"></div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};