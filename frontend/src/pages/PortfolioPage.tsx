import React from 'react';
import { useSelector } from 'react-redux';
import { RootState } from '../store/store';

const PortfolioPage: React.FC = () => {
  const { portfolio } = useSelector((state: RootState) => state.portfolio);

  return (
    <div className="space-y-6">
      <div className="flex justify-between items-center">
        <h1 className="text-3xl font-bold text-gray-900">Portfolio</h1>
      </div>

      {/* Portfolio Summary */}
      <div className="bg-white shadow rounded-lg p-6">
        <h3 className="text-lg font-medium text-gray-900 mb-4">Portfolio Summary</h3>
        <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
          <div>
            <p className="text-sm text-gray-600">Total Value</p>
            <p className="text-2xl font-bold text-gray-900">
              ${portfolio?.total_value?.toLocaleString() || '0.00'}
            </p>
          </div>
          <div>
            <p className="text-sm text-gray-600">Cash Balance</p>
            <p className="text-2xl font-bold text-blue-600">
              ${portfolio?.cash_balance?.toLocaleString() || '0.00'}
            </p>
          </div>
          <div>
            <p className="text-sm text-gray-600">Invested Amount</p>
            <p className="text-2xl font-bold text-purple-600">
              ${portfolio?.invested_amount?.toLocaleString() || '0.00'}
            </p>
          </div>
          <div>
            <p className="text-sm text-gray-600">Total Return</p>
            <p className={`text-2xl font-bold ${(portfolio?.total_return || 0) >= 0 ? 'text-green-600' : 'text-red-600'}`}>
              {portfolio?.total_return_percentage?.toFixed(2) || '0.00'}%
            </p>
          </div>
        </div>
      </div>

      {/* Holdings */}
      <div className="bg-white shadow rounded-lg p-6">
        <h3 className="text-lg font-medium text-gray-900 mb-4">Holdings</h3>
        <div className="text-center py-8 text-gray-500">
          <p>No holdings found.</p>
          <p className="text-sm">Start trading to build your portfolio.</p>
        </div>
      </div>

      {/* Performance Chart Placeholder */}
      <div className="bg-white shadow rounded-lg p-6">
        <h3 className="text-lg font-medium text-gray-900 mb-4">Performance Chart</h3>
        <div className="bg-gray-100 h-64 rounded-lg flex items-center justify-center">
          <p className="text-gray-500">Performance chart will be displayed here</p>
        </div>
      </div>
    </div>
  );
};

export default PortfolioPage;