import React from 'react';
import { Link } from 'react-router-dom';

const SavingsPage: React.FC = () => {
  return (
    <div className="bg-gray-800 min-h-screen p-6">
      {/* Header */}
      <div className="mb-8">
        <h1 className="text-2xl font-bold text-white">High-Yield Savings</h1>
        <p className="text-gray-400">Earn competitive interest on your cash</p>
      </div>

      {/* Coming Soon Banner */}
      <div className="max-w-2xl mx-auto">
        <div className="bg-gradient-to-r from-green-900/40 to-teal-900/40 rounded-2xl p-8 border border-green-500/30 text-center">
          <div className="w-20 h-20 bg-green-600/30 rounded-full flex items-center justify-center mx-auto mb-6">
            <svg className="w-10 h-10 text-green-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M17 9V7a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2m2 4h10a2 2 0 002-2v-6a2 2 0 00-2-2H9a2 2 0 00-2 2v6a2 2 0 002 2zm7-5a2 2 0 11-4 0 2 2 0 014 0z" />
            </svg>
          </div>

          <h2 className="text-2xl font-bold text-white mb-3">High-Yield Savings Coming Soon</h2>
          <p className="text-gray-300 mb-6 max-w-md mx-auto">
            Earn competitive interest on your cash with our upcoming high-yield savings account.
            FDIC insured up to $250,000 with no minimum balance requirements.
          </p>

          <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mb-8">
            <div className="bg-gray-800/50 rounded-lg p-4">
              <div className="text-green-400 text-2xl mb-2">💰</div>
              <h3 className="text-white font-medium mb-1">Competitive APY</h3>
              <p className="text-gray-400 text-sm">Earn more than traditional savings accounts</p>
            </div>
            <div className="bg-gray-800/50 rounded-lg p-4">
              <div className="text-green-400 text-2xl mb-2">🔒</div>
              <h3 className="text-white font-medium mb-1">FDIC Insured</h3>
              <p className="text-gray-400 text-sm">Protected up to $250,000 per depositor</p>
            </div>
            <div className="bg-gray-800/50 rounded-lg p-4">
              <div className="text-green-400 text-2xl mb-2">🎯</div>
              <h3 className="text-white font-medium mb-1">Savings Goals</h3>
              <p className="text-gray-400 text-sm">Set and track progress towards your goals</p>
            </div>
          </div>

          <div className="bg-gray-800/50 rounded-lg p-4 mb-6 text-left">
            <h4 className="text-white font-medium mb-2">What You'll Get</h4>
            <ul className="text-gray-300 text-sm space-y-2">
              <li className="flex items-start gap-2">
                <span className="text-green-400 mt-1">•</span>
                <span>No minimum balance requirements</span>
              </li>
              <li className="flex items-start gap-2">
                <span className="text-green-400 mt-1">•</span>
                <span>Interest paid monthly</span>
              </li>
              <li className="flex items-start gap-2">
                <span className="text-green-400 mt-1">•</span>
                <span>Unlimited withdrawals</span>
              </li>
              <li className="flex items-start gap-2">
                <span className="text-green-400 mt-1">•</span>
                <span>Create multiple savings buckets</span>
              </li>
            </ul>
          </div>

          <div className="flex flex-col sm:flex-row gap-4 justify-center">
            <button className="bg-green-600 hover:bg-green-700 text-white px-6 py-3 rounded-lg font-medium transition-colors">
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

        {/* Current Option */}
        <div className="mt-8 bg-gray-900 rounded-xl p-6">
          <h3 className="text-lg font-semibold text-white mb-4">Currently Available</h3>
          <div className="bg-gradient-to-r from-purple-900/30 to-blue-900/30 rounded-lg p-4 border border-purple-500/20">
            <div className="flex items-center gap-4">
              <div className="h-12 w-12 rounded-full bg-purple-600/30 flex items-center justify-center">
                <span className="text-2xl">📈</span>
              </div>
              <div className="flex-1">
                <h4 className="text-white font-medium">Paper Trading</h4>
                <p className="text-gray-400 text-sm">Practice investing with $250,000 in virtual funds</p>
              </div>
              <Link
                to="/paper/trading"
                className="bg-purple-600 hover:bg-purple-700 text-white px-4 py-2 rounded-lg text-sm transition-colors"
              >
                Start Now
              </Link>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default SavingsPage;
