import React, { useState } from 'react';
import { PositionRiskResponse } from '../../services/riskManagementApi';

interface PositionRiskTableProps {
  positions: PositionRiskResponse[];
  className?: string;
}

export const PositionRiskTable: React.FC<PositionRiskTableProps> = ({ 
  positions, 
  className = '' 
}) => {
  const [sortField, setSortField] = useState<keyof PositionRiskResponse>('risk_contribution');
  const [sortDirection, setSortDirection] = useState<'asc' | 'desc'>('desc');

  const handleSort = (field: keyof PositionRiskResponse) => {
    if (sortField === field) {
      setSortDirection(sortDirection === 'asc' ? 'desc' : 'asc');
    } else {
      setSortField(field);
      setSortDirection('desc');
    }
  };

  const sortedPositions = [...positions].sort((a, b) => {
    const aValue = a[sortField];
    const bValue = b[sortField];
    
    if (typeof aValue === 'number' && typeof bValue === 'number') {
      return sortDirection === 'asc' ? aValue - bValue : bValue - aValue;
    }
    
    if (typeof aValue === 'string' && typeof bValue === 'string') {
      return sortDirection === 'asc' 
        ? aValue.localeCompare(bValue)
        : bValue.localeCompare(aValue);
    }
    
    return 0;
  });

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

  const getRiskColor = (riskContribution: number) => {
    if (riskContribution > 0.15) return 'text-red-400 bg-red-900';
    if (riskContribution > 0.10) return 'text-yellow-400 bg-yellow-900';
    return 'text-green-400 bg-green-900';
  };

  const getSectorColor = (sector: string) => {
    const colors = {
      'Technology': 'bg-blue-900 text-blue-300',
      'Healthcare': 'bg-green-900 text-green-300',
      'Financial': 'bg-purple-900 text-purple-300',
      'Consumer': 'bg-orange-900 text-orange-300',
      'Industrial': 'bg-gray-700 text-gray-300',
      'Energy': 'bg-yellow-900 text-yellow-300',
      'Utilities': 'bg-cyan-900 text-cyan-300',
      'Materials': 'bg-pink-900 text-pink-300',
    };
    
    return colors[sector as keyof typeof colors] || 'bg-gray-700 text-gray-300';
  };

  const SortIcon: React.FC<{ field: keyof PositionRiskResponse }> = ({ field }) => {
    if (sortField !== field) {
      return (
        <svg className="h-4 w-4 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M8 9l4-4 4 4m0 6l-4 4-4-4" />
        </svg>
      );
    }
    
    if (sortDirection === 'asc') {
      return (
        <svg className="h-4 w-4 text-purple-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M5 15l7-7 7 7" />
        </svg>
      );
    } else {
      return (
        <svg className="h-4 w-4 text-purple-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M19 9l-7 7-7-7" />
        </svg>
      );
    }
  };

  if (positions.length === 0) {
    return (
      <div className={`bg-gray-800 rounded-lg p-6 ${className}`}>
        <div className="text-center py-8">
          <svg className="h-12 w-12 text-gray-400 mx-auto mb-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M16 8v8m-4-5v5m-4-2v2m-2 4h12a2 2 0 002-2V6a2 2 0 00-2-2H6a2 2 0 00-2 2v12a2 2 0 002 2z" />
          </svg>
          <h3 className="text-gray-400 text-lg mb-2">No Positions Found</h3>
          <p className="text-gray-500">Your portfolio doesn't have any positions to analyze.</p>
        </div>
      </div>
    );
  }

  return (
    <div className={`bg-gray-800 rounded-lg overflow-hidden ${className}`}>
      <div className="p-6 border-b border-gray-700">
        <h3 className="text-lg font-medium text-white">Position Risk Analysis</h3>
        <p className="text-gray-400 text-sm mt-1">
          Detailed risk metrics for each position in your portfolio
        </p>
      </div>

      <div className="overflow-x-auto">
        <table className="min-w-full divide-y divide-gray-700">
          <thead className="bg-gray-900">
            <tr>
              <th 
                scope="col" 
                className="px-6 py-3 text-left text-xs font-medium text-gray-400 uppercase tracking-wider cursor-pointer hover:bg-gray-800 transition-colors"
                onClick={() => handleSort('symbol')}
              >
                <div className="flex items-center space-x-1">
                  <span>Symbol</span>
                  <SortIcon field="symbol" />
                </div>
              </th>
              <th 
                scope="col" 
                className="px-6 py-3 text-left text-xs font-medium text-gray-400 uppercase tracking-wider cursor-pointer hover:bg-gray-800 transition-colors"
                onClick={() => handleSort('position_value')}
              >
                <div className="flex items-center space-x-1">
                  <span>Value</span>
                  <SortIcon field="position_value" />
                </div>
              </th>
              <th 
                scope="col" 
                className="px-6 py-3 text-left text-xs font-medium text-gray-400 uppercase tracking-wider cursor-pointer hover:bg-gray-800 transition-colors"
                onClick={() => handleSort('position_percentage')}
              >
                <div className="flex items-center space-x-1">
                  <span>% Portfolio</span>
                  <SortIcon field="position_percentage" />
                </div>
              </th>
              <th 
                scope="col" 
                className="px-6 py-3 text-left text-xs font-medium text-gray-400 uppercase tracking-wider cursor-pointer hover:bg-gray-800 transition-colors"
                onClick={() => handleSort('sector')}
              >
                <div className="flex items-center space-x-1">
                  <span>Sector</span>
                  <SortIcon field="sector" />
                </div>
              </th>
              <th 
                scope="col" 
                className="px-6 py-3 text-left text-xs font-medium text-gray-400 uppercase tracking-wider cursor-pointer hover:bg-gray-800 transition-colors"
                onClick={() => handleSort('daily_var')}
              >
                <div className="flex items-center space-x-1">
                  <span>Daily VaR</span>
                  <SortIcon field="daily_var" />
                </div>
              </th>
              <th 
                scope="col" 
                className="px-6 py-3 text-left text-xs font-medium text-gray-400 uppercase tracking-wider cursor-pointer hover:bg-gray-800 transition-colors"
                onClick={() => handleSort('beta')}
              >
                <div className="flex items-center space-x-1">
                  <span>Beta</span>
                  <SortIcon field="beta" />
                </div>
              </th>
              <th 
                scope="col" 
                className="px-6 py-3 text-left text-xs font-medium text-gray-400 uppercase tracking-wider cursor-pointer hover:bg-gray-800 transition-colors"
                onClick={() => handleSort('volatility')}
              >
                <div className="flex items-center space-x-1">
                  <span>Volatility</span>
                  <SortIcon field="volatility" />
                </div>
              </th>
              <th 
                scope="col" 
                className="px-6 py-3 text-left text-xs font-medium text-gray-400 uppercase tracking-wider cursor-pointer hover:bg-gray-800 transition-colors"
                onClick={() => handleSort('risk_contribution')}
              >
                <div className="flex items-center space-x-1">
                  <span>Risk Contrib</span>
                  <SortIcon field="risk_contribution" />
                </div>
              </th>
            </tr>
          </thead>
          <tbody className="bg-gray-800 divide-y divide-gray-700">
            {sortedPositions.map((position, index) => (
              <tr 
                key={position.symbol}
                className="hover:bg-gray-750 transition-colors"
              >
                <td className="px-6 py-4 whitespace-nowrap">
                  <div className="flex items-center">
                    <div className="text-sm font-medium text-white">
                      {position.symbol}
                    </div>
                  </div>
                </td>
                <td className="px-6 py-4 whitespace-nowrap">
                  <div className="text-sm text-white font-medium">
                    {formatCurrency(position.position_value)}
                  </div>
                </td>
                <td className="px-6 py-4 whitespace-nowrap">
                  <div className="text-sm text-white">
                    {formatPercentage(position.position_percentage)}
                  </div>
                  <div className="w-full bg-gray-700 rounded-full h-1 mt-1">
                    <div 
                      className="bg-purple-500 h-1 rounded-full transition-all duration-300"
                      style={{ width: `${Math.min(position.position_percentage * 100, 100)}%` }}
                    />
                  </div>
                </td>
                <td className="px-6 py-4 whitespace-nowrap">
                  <span className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium ${getSectorColor(position.sector)}`}>
                    {position.sector}
                  </span>
                </td>
                <td className="px-6 py-4 whitespace-nowrap">
                  <div className="text-sm text-red-400 font-medium">
                    {formatCurrency(position.daily_var)}
                  </div>
                </td>
                <td className="px-6 py-4 whitespace-nowrap">
                  <div className={`text-sm font-medium ${
                    position.beta > 1.2 ? 'text-red-400' :
                    position.beta > 0.8 ? 'text-yellow-400' :
                    'text-green-400'
                  }`}>
                    {position.beta.toFixed(2)}
                  </div>
                </td>
                <td className="px-6 py-4 whitespace-nowrap">
                  <div className={`text-sm font-medium ${
                    position.volatility > 0.3 ? 'text-red-400' :
                    position.volatility > 0.2 ? 'text-yellow-400' :
                    'text-green-400'
                  }`}>
                    {formatPercentage(position.volatility)}
                  </div>
                </td>
                <td className="px-6 py-4 whitespace-nowrap">
                  <span className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-opacity-20 ${getRiskColor(position.risk_contribution)}`}>
                    {formatPercentage(position.risk_contribution)}
                  </span>
                  <div className="w-full bg-gray-700 rounded-full h-1 mt-1">
                    <div 
                      className={`h-1 rounded-full transition-all duration-300 ${
                        position.risk_contribution > 0.15 ? 'bg-red-500' :
                        position.risk_contribution > 0.10 ? 'bg-yellow-500' :
                        'bg-green-500'
                      }`}
                      style={{ width: `${Math.min(position.risk_contribution * 100 * 5, 100)}%` }}
                    />
                  </div>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      {/* Summary Footer */}
      <div className="bg-gray-900 px-6 py-4 border-t border-gray-700">
        <div className="flex justify-between items-center text-sm">
          <span className="text-gray-400">
            Total Positions: {positions.length}
          </span>
          <span className="text-gray-400">
            Total Value: {formatCurrency(positions.reduce((sum, pos) => sum + pos.position_value, 0))}
          </span>
        </div>
      </div>
    </div>
  );
};

export default PositionRiskTable;