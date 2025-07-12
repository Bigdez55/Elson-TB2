import React from 'react';
import { useSelector } from 'react-redux';
import { RootState } from '../store/store';
import { Link } from 'react-router-dom';

const DashboardPage: React.FC = () => {
  const { user } = useSelector((state: RootState) => state.auth);
  const { portfolio } = useSelector((state: RootState) => state.portfolio);

  return (
    <div className="space-y-6">
      <div className="flex justify-between items-center">
        <h1 className="text-3xl font-bold text-gray-900">Dashboard</h1>
        <div className="text-sm text-gray-600">
          Welcome back, {user?.full_name || user?.email}
        </div>
      </div>

      {/* Quick Stats */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
        <div className="bg-white shadow rounded-lg p-6">
          <h3 className="text-lg font-medium text-gray-900 mb-2">Portfolio Value</h3>
          <p className="text-3xl font-bold text-green-600">
            ${portfolio?.total_value?.toLocaleString() || '0.00'}
          </p>
        </div>
        
        <div className="bg-white shadow rounded-lg p-6">
          <h3 className="text-lg font-medium text-gray-900 mb-2">Cash Balance</h3>
          <p className="text-3xl font-bold text-blue-600">
            ${portfolio?.cash_balance?.toLocaleString() || '0.00'}
          </p>
        </div>
        
        <div className="bg-white shadow rounded-lg p-6">
          <h3 className="text-lg font-medium text-gray-900 mb-2">Total Return</h3>
          <p className={`text-3xl font-bold ${(portfolio?.total_return || 0) >= 0 ? 'text-green-600' : 'text-red-600'}`}>
            {portfolio?.total_return_percentage?.toFixed(2) || '0.00'}%
          </p>
        </div>
      </div>

      {/* Feature Cards */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        <Link 
          to="/trading"
          className="bg-white shadow rounded-lg p-6 hover:shadow-lg transition-shadow block"
        >
          <div className="flex items-center">
            <div className="text-3xl mr-4">💰</div>
            <div>
              <h3 className="text-lg font-medium text-gray-900">Manual Trading</h3>
              <p className="text-gray-600">Place buy and sell orders manually</p>
            </div>
          </div>
        </Link>

        <Link 
          to="/advanced-trading"
          className="bg-white shadow rounded-lg p-6 hover:shadow-lg transition-shadow block"
        >
          <div className="flex items-center">
            <div className="text-3xl mr-4">🤖</div>
            <div>
              <h3 className="text-lg font-medium text-gray-900">Advanced Trading</h3>
              <p className="text-gray-600">AI-powered strategies and risk management</p>
            </div>
          </div>
        </Link>

        <Link 
          to="/portfolio"
          className="bg-white shadow rounded-lg p-6 hover:shadow-lg transition-shadow block"
        >
          <div className="flex items-center">
            <div className="text-3xl mr-4">💼</div>
            <div>
              <h3 className="text-lg font-medium text-gray-900">Portfolio</h3>
              <p className="text-gray-600">View holdings and performance</p>
            </div>
          </div>
        </Link>

        <div className="bg-white shadow rounded-lg p-6">
          <div className="flex items-center">
            <div className="text-3xl mr-4">📈</div>
            <div>
              <h3 className="text-lg font-medium text-gray-900">Market Analysis</h3>
              <p className="text-gray-600">Coming soon...</p>
            </div>
          </div>
        </div>
      </div>

      {/* Advanced Trading Features Highlight */}
      <div className="bg-gradient-to-r from-blue-500 to-purple-600 rounded-lg p-6 text-white">
        <h3 className="text-xl font-bold mb-2">🚀 Advanced Trading Features Now Available!</h3>
        <p className="mb-4">
          Experience next-generation trading with AI-powered strategies, quantum-inspired machine learning, 
          and comprehensive risk management.
        </p>
        <Link 
          to="/advanced-trading"
          className="bg-white text-blue-600 px-4 py-2 rounded-md font-medium hover:bg-gray-100 transition-colors inline-block"
        >
          Get Started
        </Link>
      </div>
    </div>
  );
};

export default DashboardPage;