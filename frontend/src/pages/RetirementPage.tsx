import React from 'react';
import { Link } from 'react-router-dom';

const RetirementPage: React.FC = () => {
  return (
    <div className="bg-gray-800 min-h-screen p-6">
      {/* Header */}
      <div className="mb-8">
        <h1 className="text-2xl font-bold text-white">Retirement Accounts</h1>
        <p className="text-gray-400">Plan and grow your retirement savings</p>
      </div>

      {/* Coming Soon Banner */}
      <div className="max-w-2xl mx-auto">
        <div className="bg-gradient-to-r from-yellow-900/40 to-orange-900/40 rounded-2xl p-8 border border-yellow-500/30 text-center">
          <div className="w-20 h-20 bg-yellow-600/30 rounded-full flex items-center justify-center mx-auto mb-6">
            <svg className="w-10 h-10 text-yellow-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M12 8c-1.657 0-3 .895-3 2s1.343 2 3 2 3 .895 3 2-1.343 2-3 2m0-8c1.11 0 2.08.402 2.599 1M12 8V7m0 1v8m0 0v1m0-1c-1.11 0-2.08-.402-2.599-1M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
            </svg>
          </div>

          <h2 className="text-2xl font-bold text-white mb-3">Retirement Accounts Coming Soon</h2>
          <p className="text-gray-300 mb-6 max-w-md mx-auto">
            We're building powerful retirement planning tools to help you save for your future.
            Open and manage IRA accounts, track contributions, and plan your retirement.
          </p>

          <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mb-8">
            <div className="bg-gray-800/50 rounded-lg p-4">
              <div className="text-yellow-400 text-2xl mb-2">📈</div>
              <h3 className="text-white font-medium mb-1">Traditional IRA</h3>
              <p className="text-gray-400 text-sm">Tax-deferred growth with deductible contributions</p>
            </div>
            <div className="bg-gray-800/50 rounded-lg p-4">
              <div className="text-yellow-400 text-2xl mb-2">💎</div>
              <h3 className="text-white font-medium mb-1">Roth IRA</h3>
              <p className="text-gray-400 text-sm">Tax-free growth and withdrawals in retirement</p>
            </div>
            <div className="bg-gray-800/50 rounded-lg p-4">
              <div className="text-yellow-400 text-2xl mb-2">🔄</div>
              <h3 className="text-white font-medium mb-1">401(k) Rollover</h3>
              <p className="text-gray-400 text-sm">Consolidate old employer retirement accounts</p>
            </div>
          </div>

          <div className="bg-gray-800/50 rounded-lg p-4 mb-6 text-left">
            <h4 className="text-white font-medium mb-2">What to Expect</h4>
            <ul className="text-gray-300 text-sm space-y-2">
              <li className="flex items-start gap-2">
                <span className="text-yellow-400 mt-1">•</span>
                <span>Open Traditional and Roth IRA accounts</span>
              </li>
              <li className="flex items-start gap-2">
                <span className="text-yellow-400 mt-1">•</span>
                <span>Automated contribution scheduling</span>
              </li>
              <li className="flex items-start gap-2">
                <span className="text-yellow-400 mt-1">•</span>
                <span>Retirement projection calculator</span>
              </li>
              <li className="flex items-start gap-2">
                <span className="text-yellow-400 mt-1">•</span>
                <span>Tax optimization recommendations</span>
              </li>
            </ul>
          </div>

          <div className="flex flex-col sm:flex-row gap-4 justify-center">
            <button className="bg-yellow-600 hover:bg-yellow-700 text-white px-6 py-3 rounded-lg font-medium transition-colors">
              Notify Me When Available
            </button>
            <Link
              to="/paper/trading"
              className="bg-gray-700 hover:bg-gray-600 text-white px-6 py-3 rounded-lg font-medium transition-colors"
            >
              Start Paper Trading
            </Link>
          </div>
        </div>

        {/* Learn About Retirement */}
        <div className="mt-8 bg-gray-900 rounded-xl p-6">
          <h3 className="text-lg font-semibold text-white mb-4">Learn About Retirement Accounts</h3>
          <div className="space-y-4">
            <div className="border-l-4 border-yellow-500 pl-4">
              <h4 className="text-white font-medium mb-1">Why Start Early?</h4>
              <p className="text-gray-400 text-sm">
                The power of compound interest means starting early can significantly increase your retirement savings.
                Even small monthly contributions can grow substantially over time.
              </p>
            </div>
            <div className="border-l-4 border-purple-500 pl-4">
              <h4 className="text-white font-medium mb-1">Traditional vs Roth</h4>
              <p className="text-gray-400 text-sm">
                Traditional IRAs offer tax deductions now with taxes due at withdrawal.
                Roth IRAs are funded with after-tax dollars but grow and are withdrawn tax-free.
              </p>
            </div>
            <div className="border-l-4 border-blue-500 pl-4">
              <h4 className="text-white font-medium mb-1">2024 Contribution Limits</h4>
              <p className="text-gray-400 text-sm">
                The IRA contribution limit is $7,000 per year ($8,000 if you're 50 or older).
                You can contribute to both Traditional and Roth IRAs, but the combined limit applies.
              </p>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default RetirementPage;
