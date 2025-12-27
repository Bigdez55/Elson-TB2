import React from 'react';
import { RiskMetricsResponse, PositionRiskResponse } from '../../services/riskManagementApi';

interface RiskChartProps {
  metrics: RiskMetricsResponse;
  positionRisks: PositionRiskResponse[];
  className?: string;
}

export const RiskChart: React.FC<RiskChartProps> = ({ 
  metrics, 
  positionRisks, 
  className = '' 
}) => {
  // Calculate risk distribution
  const totalRiskContribution = positionRisks.reduce((sum, pos) => sum + pos.risk_contribution, 0);
  
  // Group positions by sector for sector risk analysis
  const sectorRiskMap = positionRisks.reduce((acc, pos) => {
    if (!acc[pos.sector]) {
      acc[pos.sector] = {
        positions: 0,
        totalValue: 0,
        totalRisk: 0,
        avgBeta: 0,
        avgVolatility: 0,
      };
    }
    
    acc[pos.sector].positions += 1;
    acc[pos.sector].totalValue += pos.position_value;
    acc[pos.sector].totalRisk += pos.risk_contribution;
    acc[pos.sector].avgBeta += pos.beta;
    acc[pos.sector].avgVolatility += pos.volatility;
    
    return acc;
  }, {} as Record<string, any>);

  // Calculate averages for sectors
  Object.keys(sectorRiskMap).forEach(sector => {
    const data = sectorRiskMap[sector];
    data.avgBeta /= data.positions;
    data.avgVolatility /= data.positions;
  });

  const formatPercentage = (value: number) => `${(value * 100).toFixed(1)}%`;
  const formatCurrency = (value: number) => `$${value.toLocaleString()}`;

  const getSectorColor = (index: number) => {
    const colors = [
      'bg-blue-500', 'bg-green-500', 'bg-purple-500', 'bg-orange-500',
      'bg-red-500', 'bg-yellow-500', 'bg-pink-500', 'bg-indigo-500',
      'bg-cyan-500', 'bg-gray-500'
    ];
    return colors[index % colors.length];
  };

  const getRiskLevel = (riskContribution: number) => {
    if (riskContribution > 0.15) return { level: 'High', color: 'text-red-400' };
    if (riskContribution > 0.08) return { level: 'Medium', color: 'text-yellow-400' };
    return { level: 'Low', color: 'text-green-400' };
  };

  return (
    <div className={`space-y-6 ${className}`}>
      {/* Portfolio Risk Overview */}
      <div className="bg-gray-800 rounded-lg p-6">
        <h3 className="text-lg font-medium text-white mb-6">Portfolio Risk Visualization</h3>
        
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
          {/* Risk Composition Pie Chart (Simplified) */}
          <div>
            <h4 className="text-white font-medium mb-4">Risk Contribution by Position</h4>
            <div className="space-y-3">
              {positionRisks
                .sort((a, b) => b.risk_contribution - a.risk_contribution)
                .slice(0, 8) // Show top 8 positions
                .map((position, index) => {
                  const percentage = (position.risk_contribution / totalRiskContribution) * 100;
                  const riskLevel = getRiskLevel(position.risk_contribution);
                  
                  return (
                    <div key={position.symbol} className="flex items-center justify-between">
                      <div className="flex items-center space-x-3">
                        <div className={`w-4 h-4 rounded ${getSectorColor(index)}`} />
                        <span className="text-white font-medium">{position.symbol}</span>
                        <span className={`text-xs px-2 py-1 rounded ${riskLevel.color} bg-opacity-20`}>
                          {riskLevel.level}
                        </span>
                      </div>
                      <div className="text-right">
                        <div className="text-white font-medium">{percentage.toFixed(1)}%</div>
                        <div className="text-gray-400 text-sm">{formatCurrency(position.position_value)}</div>
                      </div>
                    </div>
                  );
                })}
              {positionRisks.length > 8 && (
                <div className="flex items-center justify-between text-gray-400">
                  <span>+{positionRisks.length - 8} more positions</span>
                  <span>{(100 - positionRisks.slice(0, 8).reduce((sum, pos) => sum + (pos.risk_contribution / totalRiskContribution) * 100, 0)).toFixed(1)}%</span>
                </div>
              )}
            </div>
          </div>

          {/* Risk vs Return Scatter Plot (Simplified) */}
          <div>
            <h4 className="text-white font-medium mb-4">Risk vs Beta Analysis</h4>
            <div className="bg-gray-900 rounded-lg p-4 h-64 relative">
              {/* Axes */}
              <div className="absolute bottom-0 left-0 w-full h-full">
                {/* Y-axis label */}
                <div className="absolute left-2 top-2 text-gray-400 text-xs transform -rotate-90 origin-center">
                  Risk Contribution
                </div>
                
                {/* X-axis label */}
                <div className="absolute bottom-2 right-2 text-gray-400 text-xs">
                  Beta
                </div>

                {/* Grid lines */}
                <div className="absolute inset-4">
                  {/* Horizontal grid lines */}
                  {[0.25, 0.5, 0.75].map((y, i) => (
                    <div 
                      key={`h-${i}`}
                      className="absolute w-full border-t border-gray-700"
                      style={{ top: `${y * 100}%` }}
                    />
                  ))}
                  
                  {/* Vertical grid lines */}
                  {[0.25, 0.5, 0.75].map((x, i) => (
                    <div 
                      key={`v-${i}`}
                      className="absolute h-full border-l border-gray-700"
                      style={{ left: `${x * 100}%` }}
                    />
                  ))}

                  {/* Plot points */}
                  {positionRisks.slice(0, 12).map((position, index) => {
                    const x = Math.min(Math.max((position.beta - 0.5) / 2, 0), 1); // Normalize beta 0.5-2.5 to 0-1
                    const y = 1 - Math.min(position.risk_contribution / 0.2, 1); // Normalize risk to 0-1, flip for display
                    
                    return (
                      <div
                        key={position.symbol}
                        className={`absolute w-3 h-3 rounded-full ${getSectorColor(index)} transform -translate-x-1/2 -translate-y-1/2 cursor-pointer group`}
                        style={{ 
                          left: `${x * 100}%`, 
                          top: `${y * 100}%` 
                        }}
                        title={`${position.symbol}: Beta ${position.beta.toFixed(2)}, Risk ${formatPercentage(position.risk_contribution)}`}
                      >
                        <div className="hidden group-hover:block absolute bottom-4 left-1/2 transform -translate-x-1/2 bg-gray-800 text-white text-xs p-2 rounded shadow-lg whitespace-nowrap z-10">
                          <div className="font-medium">{position.symbol}</div>
                          <div>Beta: {position.beta.toFixed(2)}</div>
                          <div>Risk: {formatPercentage(position.risk_contribution)}</div>
                        </div>
                      </div>
                    );
                  })}
                </div>

                {/* Axis values */}
                <div className="absolute bottom-0 left-8 text-gray-400 text-xs">0.5</div>
                <div className="absolute bottom-0 right-8 text-gray-400 text-xs">2.5</div>
                <div className="absolute top-4 left-2 text-gray-400 text-xs">High</div>
                <div className="absolute bottom-4 left-2 text-gray-400 text-xs">Low</div>
              </div>
            </div>
          </div>
        </div>
      </div>

      {/* Sector Risk Analysis */}
      <div className="bg-gray-800 rounded-lg p-6">
        <h3 className="text-lg font-medium text-white mb-6">Sector Risk Analysis</h3>
        
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
          {Object.entries(sectorRiskMap)
            .sort(([, a], [, b]) => b.totalRisk - a.totalRisk)
            .map(([sector, data], index) => (
              <div key={sector} className="bg-gray-900 rounded-lg p-4">
                <div className="flex items-center justify-between mb-3">
                  <h4 className="text-white font-medium capitalize">{sector}</h4>
                  <div className={`w-3 h-3 rounded-full ${getSectorColor(index)}`} />
                </div>
                
                <div className="space-y-2 text-sm">
                  <div className="flex justify-between">
                    <span className="text-gray-400">Positions:</span>
                    <span className="text-white">{data.positions}</span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-gray-400">Value:</span>
                    <span className="text-white">{formatCurrency(data.totalValue)}</span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-gray-400">Risk Contrib:</span>
                    <span className={`${getRiskLevel(data.totalRisk).color}`}>
                      {formatPercentage(data.totalRisk)}
                    </span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-gray-400">Avg Beta:</span>
                    <span className="text-white">{data.avgBeta.toFixed(2)}</span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-gray-400">Avg Vol:</span>
                    <span className="text-white">{formatPercentage(data.avgVolatility)}</span>
                  </div>
                </div>

                {/* Risk bar */}
                <div className="mt-3">
                  <div className="w-full bg-gray-700 rounded-full h-2">
                    <div 
                      className={`h-2 rounded-full transition-all duration-300 ${
                        data.totalRisk > 0.3 ? 'bg-red-500' :
                        data.totalRisk > 0.15 ? 'bg-yellow-500' :
                        'bg-green-500'
                      }`}
                      style={{ 
                        width: `${Math.min((data.totalRisk / totalRiskContribution) * 100, 100)}%` 
                      }}
                    />
                  </div>
                </div>
              </div>
            ))}
        </div>
      </div>

      {/* Risk Metrics Summary */}
      <div className="bg-gray-800 rounded-lg p-6">
        <h3 className="text-lg font-medium text-white mb-6">Risk Profile Summary</h3>
        
        <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
          <div className="text-center">
            <div className="text-2xl font-bold text-white mb-1">
              {formatPercentage(metrics.concentration_risk)}
            </div>
            <div className="text-gray-400 text-sm">Concentration Risk</div>
            <div className={`text-xs mt-1 ${
              metrics.concentration_risk > 0.7 ? 'text-red-400' :
              metrics.concentration_risk > 0.5 ? 'text-yellow-400' :
              'text-green-400'
            }`}>
              {metrics.concentration_risk > 0.7 ? 'High' :
               metrics.concentration_risk > 0.5 ? 'Medium' : 'Low'}
            </div>
          </div>

          <div className="text-center">
            <div className="text-2xl font-bold text-white mb-1">
              {formatPercentage(metrics.largest_position_pct)}
            </div>
            <div className="text-gray-400 text-sm">Largest Position</div>
            <div className={`text-xs mt-1 ${
              metrics.largest_position_pct > 0.2 ? 'text-red-400' :
              metrics.largest_position_pct > 0.1 ? 'text-yellow-400' :
              'text-green-400'
            }`}>
              {metrics.largest_position_pct > 0.2 ? 'High' :
               metrics.largest_position_pct > 0.1 ? 'Medium' : 'Low'}
            </div>
          </div>

          <div className="text-center">
            <div className="text-2xl font-bold text-white mb-1">
              {Object.keys(metrics.sector_concentration).length}
            </div>
            <div className="text-gray-400 text-sm">Sectors</div>
            <div className={`text-xs mt-1 ${
              Object.keys(metrics.sector_concentration).length < 3 ? 'text-red-400' :
              Object.keys(metrics.sector_concentration).length < 5 ? 'text-yellow-400' :
              'text-green-400'
            }`}>
              {Object.keys(metrics.sector_concentration).length < 3 ? 'Low Diversity' :
               Object.keys(metrics.sector_concentration).length < 5 ? 'Medium Diversity' : 'Well Diversified'}
            </div>
          </div>

          <div className="text-center">
            <div className="text-2xl font-bold text-white mb-1">
              {metrics.leverage_ratio.toFixed(1)}x
            </div>
            <div className="text-gray-400 text-sm">Leverage</div>
            <div className={`text-xs mt-1 ${
              metrics.leverage_ratio > 2 ? 'text-red-400' :
              metrics.leverage_ratio > 1.5 ? 'text-yellow-400' :
              'text-green-400'
            }`}>
              {metrics.leverage_ratio > 2 ? 'High' :
               metrics.leverage_ratio > 1.5 ? 'Medium' : 'Conservative'}
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default RiskChart;