import React from 'react';
import { Link } from 'react-router-dom';

const WealthPage: React.FC = () => {
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

  const categories = Array.from(new Set(wealthProducts.map(p => p.category)));

  return (
    <div className="bg-gray-800 min-h-screen p-6">
      <div className="mb-8">
        <h1 className="text-3xl font-bold text-white mb-2">Wealth & Savings</h1>
        <p className="text-gray-400">
          Manage your portfolio, grow your savings, and build wealth with our comprehensive financial tools
        </p>
      </div>

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
                      <h3 className="text-lg font-bold text-white mb-1">{product.name}</h3>
                      <p className="text-gray-400 text-sm">{product.description}</p>
                    </div>
                  </div>
                  <div className="mt-4 flex items-center justify-between">
                    <div>
                      {product.apy && (
                        <div className="text-2xl font-bold text-green-400">{product.apy} APY</div>
                      )}
                      {product.benefit && (
                        <div className="text-sm font-medium text-purple-400">{product.benefit}</div>
                      )}
                    </div>
                    <svg className="h-6 w-6 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M9 5l7 7-7 7" />
                    </svg>
                  </div>
                </Link>
              ))}
          </div>
        </div>
      ))}
    </div>
  );
};

export default WealthPage;
