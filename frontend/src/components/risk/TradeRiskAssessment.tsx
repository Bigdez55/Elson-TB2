import React, { useState, useEffect } from 'react';
import { useTradingContext } from '../../contexts/TradingContext';
import { 
  useAssessTradeRiskMutation,
  useGetSymbolRiskScoreQuery,
  TradeRiskRequest,
  TradeRiskResponse 
} from '../../services/riskManagementApi';
import { LoadingSpinner } from '../common/LoadingSpinner';

interface TradeRiskAssessmentProps {
  symbol: string;
  tradeType: 'BUY' | 'SELL';
  quantity: number;
  price?: number;
  onRiskAssessment?: (assessment: TradeRiskResponse | null) => void;
  className?: string;
}

export const TradeRiskAssessment: React.FC<TradeRiskAssessmentProps> = ({
  symbol,
  tradeType,
  quantity,
  price,
  onRiskAssessment,
  className = '',
}) => {
  const { mode } = useTradingContext();
  const [assessment, setAssessment] = useState<TradeRiskResponse | null>(null);
  const [showDetails, setShowDetails] = useState(false);

  // API calls
  const [assessTradeRisk, { isLoading: isAssessing }] = useAssessTradeRiskMutation();
  
  const {
    data: symbolRisk,
    isLoading: isSymbolRiskLoading,
  } = useGetSymbolRiskScoreQuery(symbol, {
    skip: !symbol,
  });

  // Assess trade risk when parameters change
  useEffect(() => {
    if (symbol && quantity > 0) {
      const assessRisk = async () => {
        try {
          const request: TradeRiskRequest = {
            symbol: symbol.toUpperCase(),
            trade_type: tradeType,
            quantity,
            price,
          };

          const result = await assessTradeRisk(request).unwrap();
          setAssessment(result);
          onRiskAssessment?.(result);
        } catch (error) {
          console.error('Risk assessment failed:', error);
          setAssessment(null);
          onRiskAssessment?.(null);
        }
      };

      // Debounce the assessment
      const timeoutId = setTimeout(assessRisk, 500);
      return () => clearTimeout(timeoutId);
    } else {
      setAssessment(null);
      onRiskAssessment?.(null);
    }
  }, [symbol, tradeType, quantity, price, assessTradeRisk, onRiskAssessment]);

  const getRiskLevelColor = (level: string) => {
    switch (level.toLowerCase()) {
      case 'low': return 'text-green-400 bg-green-900';
      case 'medium': return 'text-yellow-400 bg-yellow-900';
      case 'high': return 'text-red-400 bg-red-900';
      default: return 'text-gray-400 bg-gray-900';
    }
  };

  const getCheckResultColor = (result: string) => {
    switch (result.toLowerCase()) {
      case 'approved': return 'text-green-400 bg-green-900';
      case 'warning': return 'text-yellow-400 bg-yellow-900';
      case 'rejected': return 'text-red-400 bg-red-900';
      default: return 'text-gray-400 bg-gray-900';
    }
  };

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

  if (!symbol || quantity <= 0) {
    return null;
  }

  if (isAssessing || isSymbolRiskLoading) {
    return (
      <div className={`bg-gray-900 rounded-lg p-4 ${className}`}>
        <div className="flex items-center space-x-3">
          <LoadingSpinner size="sm" />
          <span className="text-gray-400 text-sm">Assessing trade risk...</span>
        </div>
      </div>
    );
  }

  return (
    <div className={`bg-gray-900 rounded-lg p-4 space-y-4 ${className}`}>
      {/* Quick Risk Summary */}
      {assessment && (
        <div className="flex items-center justify-between">
          <div className="flex items-center space-x-3">
            <div className={`px-3 py-1 rounded-full text-sm font-medium bg-opacity-20 ${getRiskLevelColor(assessment.risk_level)}`}>
              {assessment.risk_level.toUpperCase()} RISK
            </div>
            <div className={`px-3 py-1 rounded-full text-sm font-medium bg-opacity-20 ${getCheckResultColor(assessment.check_result)}`}>
              {assessment.check_result.toUpperCase()}
            </div>
            {mode === 'live' && (
              <div className="px-2 py-1 rounded text-xs font-medium bg-red-900 text-red-300 bg-opacity-20">
                LIVE TRADE
              </div>
            )}
          </div>
          
          <button
            onClick={() => setShowDetails(!showDetails)}
            className="text-purple-400 hover:text-purple-300 text-sm transition-colors"
          >
            {showDetails ? 'Hide Details' : 'Show Details'}
          </button>
        </div>
      )}

      {/* Symbol Risk Score */}
      {symbolRisk && (
        <div className="bg-gray-800 rounded p-3">
          <div className="flex items-center justify-between mb-2">
            <span className="text-gray-400 text-sm">Symbol Risk Score</span>
            <span className={`font-medium ${
              symbolRisk.risk_score > 0.7 ? 'text-red-400' :
              symbolRisk.risk_score > 0.4 ? 'text-yellow-400' :
              'text-green-400'
            }`}>
              {(symbolRisk.risk_score * 100).toFixed(0)}/100
            </span>
          </div>
          <div className="text-xs text-gray-500 mb-2">{symbolRisk.recommendation}</div>
          <div className="w-full bg-gray-700 rounded-full h-2">
            <div 
              className={`h-2 rounded-full transition-all duration-300 ${
                symbolRisk.risk_score > 0.7 ? 'bg-red-500' :
                symbolRisk.risk_score > 0.4 ? 'bg-yellow-500' :
                'bg-green-500'
              }`}
              style={{ width: `${symbolRisk.risk_score * 100}%` }}
            />
          </div>
        </div>
      )}

      {/* Assessment Details */}
      {assessment && showDetails && (
        <div className="space-y-3">
          {/* Trade Impact Analysis */}
          <div className="bg-gray-800 rounded p-3">
            <h4 className="text-white font-medium mb-2">Impact Analysis</h4>
            <div className="grid grid-cols-2 gap-3 text-sm">
              <div>
                <span className="text-gray-400">Position Value:</span>
                <span className="text-white ml-2 font-medium">
                  {formatCurrency(assessment.impact_analysis.position_value)}
                </span>
              </div>
              <div>
                <span className="text-gray-400">Portfolio Impact:</span>
                <span className="text-white ml-2 font-medium">
                  {formatPercentage(assessment.impact_analysis.portfolio_impact_pct)}
                </span>
              </div>
              <div>
                <span className="text-gray-400">New Concentration:</span>
                <span className={`ml-2 font-medium ${
                  assessment.impact_analysis.concentration_after > 0.15 ? 'text-red-400' :
                  assessment.impact_analysis.concentration_after > 0.10 ? 'text-yellow-400' :
                  'text-green-400'
                }`}>
                  {formatPercentage(assessment.impact_analysis.concentration_after)}
                </span>
              </div>
              <div>
                <span className="text-gray-400">VaR Impact:</span>
                <span className="text-red-400 ml-2 font-medium">
                  {formatCurrency(assessment.impact_analysis.var_impact)}
                </span>
              </div>
            </div>
          </div>

          {/* Risk Score */}
          <div className="bg-gray-800 rounded p-3">
            <div className="flex items-center justify-between mb-2">
              <span className="text-gray-400 text-sm">Overall Risk Score</span>
              <span className={`text-lg font-bold ${
                assessment.risk_score > 0.7 ? 'text-red-400' :
                assessment.risk_score > 0.4 ? 'text-yellow-400' :
                'text-green-400'
              }`}>
                {(assessment.risk_score * 100).toFixed(0)}
              </span>
            </div>
            <div className="w-full bg-gray-700 rounded-full h-3">
              <div 
                className={`h-3 rounded-full transition-all duration-300 ${
                  assessment.risk_score > 0.7 ? 'bg-red-500' :
                  assessment.risk_score > 0.4 ? 'bg-yellow-500' :
                  'bg-green-500'
                }`}
                style={{ width: `${assessment.risk_score * 100}%` }}
              />
            </div>
          </div>

          {/* Violations */}
          {assessment.violations.length > 0 && (
            <div className="bg-red-900 bg-opacity-20 border border-red-700 rounded p-3">
              <h4 className="text-red-300 font-medium mb-2 flex items-center">
                <svg className="h-4 w-4 mr-1" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z" />
                </svg>
                Risk Violations
              </h4>
              <ul className="space-y-1">
                {assessment.violations.map((violation, index) => (
                  <li key={index} className="text-red-400 text-sm">
                    • {violation}
                  </li>
                ))}
              </ul>
            </div>
          )}

          {/* Warnings */}
          {assessment.warnings.length > 0 && (
            <div className="bg-yellow-900 bg-opacity-20 border border-yellow-700 rounded p-3">
              <h4 className="text-yellow-300 font-medium mb-2 flex items-center">
                <svg className="h-4 w-4 mr-1" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z" />
                </svg>
                Warnings
              </h4>
              <ul className="space-y-1">
                {assessment.warnings.map((warning, index) => (
                  <li key={index} className="text-yellow-400 text-sm">
                    • {warning}
                  </li>
                ))}
              </ul>
            </div>
          )}

          {/* Recommendations */}
          <div className="bg-blue-900 bg-opacity-20 border border-blue-700 rounded p-3">
            <h4 className="text-blue-300 font-medium mb-2 flex items-center">
              <svg className="h-4 w-4 mr-1" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
              </svg>
              Recommendation
            </h4>
            <p className="text-blue-200 text-sm">{assessment.recommended_action}</p>
            {assessment.max_allowed_quantity && assessment.max_allowed_quantity < quantity && (
              <p className="text-blue-300 text-sm mt-2">
                Maximum recommended quantity: {assessment.max_allowed_quantity.toLocaleString()}
              </p>
            )}
          </div>

          {/* Symbol Risk Factors */}
          {symbolRisk && symbolRisk.risk_factors.length > 0 && (
            <div className="bg-gray-800 rounded p-3">
              <h4 className="text-gray-300 font-medium mb-2">Symbol Risk Factors</h4>
              <ul className="space-y-1">
                {symbolRisk.risk_factors.map((factor, index) => (
                  <li key={index} className="text-gray-400 text-sm">
                    • {factor}
                  </li>
                ))}
              </ul>
              <div className="mt-2 text-xs text-gray-500">
                Sector: {symbolRisk.sector} • Beta: {symbolRisk.beta.toFixed(2)} • 
                Volatility: {formatPercentage(symbolRisk.volatility)}
              </div>
            </div>
          )}
        </div>
      )}
    </div>
  );
};

export default TradeRiskAssessment;