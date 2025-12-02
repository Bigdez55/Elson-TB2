import React from 'react';
import { Link } from 'react-router-dom';

/**
 * Main Analytics page that presents an overview of all analytics categories
 * and provides navigation to specific analytics views.
 * 
 * This is a consolidated version that uses the new consolidated analytics components.
 */
const Analytics: React.FC = () => {
  const analyticsCategories = [
    { 
      name: 'Trading Analytics', 
      path: '/analytics/consolidated/trading',
      description: 'View trading performance, win rates, and trade statistics',
      icon: '📈'
    },
    { 
      name: 'Portfolio Analytics', 
      path: '/analytics/consolidated/portfolio',
      description: 'Analyze portfolio composition, allocation, and performance',
      icon: '💼'
    },
    { 
      name: 'Model Analytics', 
      path: '/analytics/consolidated/model',
      description: 'Assess model performance, accuracy, and backtesting results',
      icon: '🧠'
    },
    { 
      name: 'Market Analytics', 
      path: '/analytics/consolidated/market',
      description: 'Monitor market conditions, trends, and correlations',
      icon: '🌐'
    }
  ];

  return (
    <div className="space-y-6">
      <div className="flex justify-between items-center">
        <h1 className="text-2xl font-bold">Analytics Dashboard</h1>
      </div>

      {/* Analytics overview stats */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        <div className="bg-gray-800 p-4 rounded-lg">
          <h3 className="text-gray-400 text-sm">Total Profit/Loss</h3>
          <p className="text-2xl font-bold mt-1 text-green-500">$12,438.65</p>
          <p className="text-sm text-gray-400">+18.72% this month</p>
        </div>
        <div className="bg-gray-800 p-4 rounded-lg">
          <h3 className="text-gray-400 text-sm">Portfolio Value</h3>
          <p className="text-2xl font-bold mt-1">$142,892.19</p>
          <p className="text-sm text-gray-400">+2.3% this week</p>
        </div>
        <div className="bg-gray-800 p-4 rounded-lg">
          <h3 className="text-gray-400 text-sm">Active Strategies</h3>
          <p className="text-2xl font-bold mt-1">8</p>
          <p className="text-sm text-gray-400">2 performing above benchmark</p>
        </div>
      </div>

      {/* Analytics Categories */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
        {analyticsCategories.map((category) => (
          <Link 
            key={category.path} 
            to={category.path}
            className="bg-gray-800 p-6 rounded-lg transition-transform hover:transform hover:scale-105"
          >
            <div className="flex items-center mb-3">
              <span className="text-2xl mr-3">{category.icon}</span>
              <h2 className="text-xl font-semibold">{category.name}</h2>
            </div>
            <p className="text-gray-400">{category.description}</p>
          </Link>
        ))}
      </div>

      {/* Feature Highlights */}
      <div className="bg-gray-800 p-6 rounded-lg">
        <h2 className="text-xl font-semibold mb-4">Key Performance Insights</h2>
        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
          <div className="border border-gray-700 rounded p-4">
            <h3 className="font-medium text-lg">Model Performance</h3>
            <div className="mt-2">
              <div className="flex justify-between text-sm mb-1">
                <span>Overall Accuracy</span>
                <span className="text-green-500">73.1%</span>
              </div>
              <div className="h-2 w-full bg-gray-700 rounded">
                <div className="h-2 bg-green-500 rounded" style={{ width: '73.1%' }}></div>
              </div>
            </div>
            <div className="mt-4">
              <div className="flex justify-between text-sm mb-1">
                <span>Win Rate (High Volatility)</span>
                <span className="text-green-500">74.8%</span>
              </div>
              <div className="h-2 w-full bg-gray-700 rounded">
                <div className="h-2 bg-green-500 rounded" style={{ width: '74.8%' }}></div>
              </div>
            </div>
            <div className="mt-2 text-right">
              <Link to="/analytics/consolidated/model" className="text-blue-400 hover:text-blue-300 text-sm">
                View Model Details →
              </Link>
            </div>
          </div>

          <div className="border border-gray-700 rounded p-4">
            <h3 className="font-medium text-lg">Portfolio Health</h3>
            <div className="mt-2">
              <div className="flex justify-between text-sm mb-1">
                <span>Diversification Score</span>
                <span className="text-green-500">87%</span>
              </div>
              <div className="h-2 w-full bg-gray-700 rounded">
                <div className="h-2 bg-green-500 rounded" style={{ width: '87%' }}></div>
              </div>
            </div>
            <div className="mt-4">
              <div className="flex justify-between text-sm mb-1">
                <span>Risk-Adjusted Return (Sharpe)</span>
                <span className="text-green-500">1.87</span>
              </div>
              <div className="h-2 w-full bg-gray-700 rounded">
                <div className="h-2 bg-green-500 rounded" style={{ width: '76%' }}></div>
              </div>
            </div>
            <div className="mt-2 text-right">
              <Link to="/analytics/consolidated/portfolio" className="text-blue-400 hover:text-blue-300 text-sm">
                View Portfolio Details →
              </Link>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default Analytics;