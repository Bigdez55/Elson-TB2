import React from 'react';
import { Outlet, NavLink } from 'react-router-dom';

/**
 * Layout component for all analytics pages.
 * Provides a sidebar navigation and main content area for analytics.
 */
const AnalyticsLayout: React.FC = () => {
  const analyticsCategories = [
    { name: 'Overview', path: '/analytics' },
    { name: 'Trading', path: '/analytics/trading' },
    { name: 'Portfolio', path: '/analytics/portfolio' },
    { name: 'Performance', path: '/analytics/performance' },
    { name: 'Risk', path: '/analytics/risk' },
    { name: 'Market', path: '/analytics/market' },
    { name: 'Backtest', path: '/analytics/backtest' },
    { name: 'Strategy', path: '/analytics/strategy' },
    { name: 'Trading Bot', path: '/analytics/trading-bot' },
    { name: 'Trading Pair', path: '/analytics/trading-pair' },
    { name: 'Correlation', path: '/analytics/correlation' },
    { name: 'Model Performance', path: '/analytics/model-performance' },
    { name: 'Exchange', path: '/analytics/exchange' },
    { name: 'Event', path: '/analytics/event' },
    { name: 'Error', path: '/analytics/error' },
    { name: 'Data Import', path: '/analytics/data-import' },
    { name: 'Orderbook', path: '/analytics/orderbook' },
    { name: 'Reporting', path: '/analytics/reporting' },
    { name: 'Prediction', path: '/analytics/prediction' },
    { name: 'Tax', path: '/analytics/tax' }
  ];

  return (
    <div className="flex h-full">
      {/* Analytics sidebar */}
      <div className="w-64 bg-gray-800 h-full overflow-y-auto hidden md:block">
        <div className="p-4">
          <h2 className="text-xl font-bold text-white mb-4">Analytics</h2>
          <nav className="space-y-1">
            {analyticsCategories.map((category) => (
              <NavLink
                key={category.path}
                to={category.path}
                className={({ isActive }) =>
                  `flex items-center px-4 py-2 text-sm rounded-md transition-colors ${
                    isActive
                      ? 'bg-purple-600 text-white'
                      : 'text-gray-300 hover:bg-gray-700'
                  }`
                }
              >
                {category.name}
              </NavLink>
            ))}
          </nav>
        </div>
      </div>

      {/* Mobile dropdown for analytics (visible on small screens) */}
      <div className="md:hidden w-full bg-gray-800 p-4">
        <select 
          className="w-full bg-gray-700 text-white rounded py-2 px-3"
          onChange={(e) => {
            window.location.href = e.target.value;
          }}
          value={window.location.pathname}
        >
          {analyticsCategories.map((category) => (
            <option key={category.path} value={category.path}>
              {category.name}
            </option>
          ))}
        </select>
      </div>

      {/* Main content area */}
      <div className="flex-1 overflow-auto p-6">
        <Outlet />
      </div>
    </div>
  );
};

export default AnalyticsLayout;