import React, { useState } from 'react';
import { Link } from 'react-router-dom';
import {
  WealthAdvisoryChat,
  ProfessionalRolesGuide,
  SuccessionPlanner,
  TeamCoordinator,
} from '../components/wealth';
import { ServiceTier } from '../services/wealthAdvisoryApi';

type ActiveTool = 'overview' | 'chat' | 'roles' | 'succession' | 'team';

const WealthPage: React.FC = () => {
  const [activeTool, setActiveTool] = useState<ActiveTool>('overview');
  // In a real app, this would come from user profile
  const [userTier] = useState<ServiceTier>('growth');

  const wealthProducts = [
    {
      name: 'Portfolio',
      description: 'View and manage your investments',
      benefit: 'Real-time tracking',
      path: '/portfolio',
      icon: '📊',
      category: 'Account Management',
    },
    {
      name: 'Transfers',
      description: 'Move money in and out of your account',
      benefit: 'Instant transfers',
      path: '/transfers',
      icon: '💸',
      category: 'Account Management',
    },
    {
      name: 'Statements',
      description: 'Access your account statements and tax documents',
      benefit: 'Digital records',
      path: '/statements',
      icon: '📄',
      category: 'Account Management',
    },
    {
      name: 'High-Yield Savings',
      description: 'Earn competitive interest on your cash',
      apy: '4.50%',
      path: '/savings',
      icon: '💰',
      category: 'Savings & Growth',
    },
    {
      name: 'Elson Card',
      description: 'Spend your portfolio gains instantly',
      benefit: 'No fees',
      path: '/card',
      icon: '💳',
      category: 'Spending',
    },
    {
      name: 'Insurance',
      description: 'Protect what matters most',
      benefit: 'Comprehensive coverage',
      path: '/insurance',
      icon: '🛡️',
      category: 'Protection',
    },
    {
      name: 'Retirement',
      description: 'Tax-advantaged investing for your future',
      benefit: 'IRA & 401(k)',
      path: '/retirement',
      icon: '🏖️',
      category: 'Retirement',
    },
  ];

  const advisoryTools = [
    {
      id: 'chat' as ActiveTool,
      name: 'AI Wealth Advisor',
      description: 'Chat with our AI about any wealth management question',
      icon: '🤖',
      color: 'from-purple-600 to-purple-800',
    },
    {
      id: 'roles' as ActiveTool,
      name: 'Professional Guide',
      description: 'Explore 70+ wealth management professional roles',
      icon: '👥',
      color: 'from-blue-600 to-blue-800',
    },
    {
      id: 'succession' as ActiveTool,
      name: 'Succession Planner',
      description: 'Plan your business transition with the Dream Team',
      icon: '🔄',
      color: 'from-green-600 to-green-800',
    },
    {
      id: 'team' as ActiveTool,
      name: 'Team Coordinator',
      description: 'Build your optimal advisory team',
      icon: '🤝',
      color: 'from-orange-600 to-orange-800',
    },
  ];

  const categories = Array.from(new Set(wealthProducts.map((p) => p.category)));

  const renderOverview = () => (
    <>
      {/* AI Advisory Tools */}
      <div className="mb-8">
        <h2 className="text-xl font-semibold text-white mb-4">
          AI Wealth Advisory
        </h2>
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
          {advisoryTools.map((tool) => (
            <button
              key={tool.id}
              onClick={() => setActiveTool(tool.id)}
              className={`bg-gradient-to-br ${tool.color} rounded-xl p-6 text-left hover:scale-105 transition-transform`}
            >
              <span className="text-4xl block mb-3">{tool.icon}</span>
              <h3 className="text-lg font-bold text-white mb-1">{tool.name}</h3>
              <p className="text-sm text-gray-200 opacity-90">
                {tool.description}
              </p>
            </button>
          ))}
        </div>
      </div>

      {/* Service Tier Info */}
      <div className="mb-8 p-4 bg-gray-900 rounded-xl border border-purple-700">
        <div className="flex items-center justify-between">
          <div>
            <h3 className="text-lg font-semibold text-white">
              Your Service Tier: <span className="text-purple-400 capitalize">{userTier}</span>
            </h3>
            <p className="text-sm text-gray-400">
              Access to CFP, CFA, and CPA-level advisory based on your portfolio value
            </p>
          </div>
          <Link
            to="/settings/tier"
            className="px-4 py-2 bg-purple-600 hover:bg-purple-700 text-white text-sm rounded-lg transition-colors"
          >
            View Benefits
          </Link>
        </div>
      </div>

      {/* Traditional Products */}
      {categories.map((category) => (
        <div key={category} className="mb-8">
          <h2 className="text-xl font-semibold text-white mb-4">{category}</h2>
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
            {wealthProducts
              .filter((p) => p.category === category)
              .map((product) => (
                <Link
                  key={product.path}
                  to={product.path}
                  className="bg-gray-900 rounded-xl p-6 hover:bg-gray-800 transition-colors"
                >
                  <div className="flex items-start mb-4">
                    <span className="text-4xl mr-4">{product.icon}</span>
                    <div>
                      <h3 className="text-lg font-bold text-white mb-1">
                        {product.name}
                      </h3>
                      <p className="text-gray-400 text-sm">
                        {product.description}
                      </p>
                    </div>
                  </div>
                  <div className="mt-4 flex items-center justify-between">
                    <div>
                      {product.apy && (
                        <div className="text-2xl font-bold text-green-400">
                          {product.apy} APY
                        </div>
                      )}
                      {product.benefit && (
                        <div className="text-sm font-medium text-purple-400">
                          {product.benefit}
                        </div>
                      )}
                    </div>
                    <svg
                      className="h-6 w-6 text-gray-400"
                      fill="none"
                      stroke="currentColor"
                      viewBox="0 0 24 24"
                    >
                      <path
                        strokeLinecap="round"
                        strokeLinejoin="round"
                        strokeWidth="2"
                        d="M9 5l7 7-7 7"
                      />
                    </svg>
                  </div>
                </Link>
              ))}
          </div>
        </div>
      ))}
    </>
  );

  const renderActiveTool = () => {
    switch (activeTool) {
      case 'chat':
        return (
          <div className="h-[700px]">
            <WealthAdvisoryChat userTier={userTier} />
          </div>
        );
      case 'roles':
        return <ProfessionalRolesGuide />;
      case 'succession':
        return <SuccessionPlanner />;
      case 'team':
        return <TeamCoordinator />;
      default:
        return renderOverview();
    }
  };

  return (
    <div className="bg-gray-800 min-h-screen p-6">
      <div className="mb-8">
        <div className="flex items-center justify-between">
          <div>
            <h1 className="text-3xl font-bold text-white mb-2">
              Wealth & Savings
            </h1>
            <p className="text-gray-400">
              {activeTool === 'overview'
                ? 'Manage your portfolio, grow your savings, and build wealth with our comprehensive financial tools'
                : 'Powered by Elson Financial AI - 70+ Professional Roles'}
            </p>
          </div>
          {activeTool !== 'overview' && (
            <button
              onClick={() => setActiveTool('overview')}
              className="px-4 py-2 bg-gray-700 hover:bg-gray-600 text-white rounded-lg transition-colors flex items-center"
            >
              <svg
                className="w-4 h-4 mr-2"
                fill="none"
                stroke="currentColor"
                viewBox="0 0 24 24"
              >
                <path
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  strokeWidth="2"
                  d="M15 19l-7-7 7-7"
                />
              </svg>
              Back to Overview
            </button>
          )}
        </div>

        {/* Tool Tabs when not on overview */}
        {activeTool !== 'overview' && (
          <div className="flex space-x-2 mt-4">
            {advisoryTools.map((tool) => (
              <button
                key={tool.id}
                onClick={() => setActiveTool(tool.id)}
                className={`px-4 py-2 rounded-lg text-sm font-medium transition-colors flex items-center ${
                  activeTool === tool.id
                    ? 'bg-purple-600 text-white'
                    : 'bg-gray-700 text-gray-300 hover:bg-gray-600'
                }`}
              >
                <span className="mr-2">{tool.icon}</span>
                {tool.name}
              </button>
            ))}
          </div>
        )}
      </div>

      {renderActiveTool()}
    </div>
  );
};

export default WealthPage;
