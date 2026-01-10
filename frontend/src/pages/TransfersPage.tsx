import React from 'react';
import { Link } from 'react-router-dom';

const TransfersPage: React.FC = () => {
  return (
    <div className="bg-gray-800 min-h-screen p-6">
      {/* Header */}
      <div className="mb-8">
        <h1 className="text-2xl font-bold text-white">Transfers</h1>
        <p className="text-gray-400">Move money in and out of your Elson account</p>
      </div>

      {/* Coming Soon Banner */}
      <div className="max-w-2xl mx-auto">
        <div className="bg-gradient-to-r from-green-900/40 to-blue-900/40 rounded-2xl p-8 border border-green-500/30 text-center">
          <div className="w-20 h-20 bg-green-600/30 rounded-full flex items-center justify-center mx-auto mb-6">
            <svg className="w-10 h-10 text-green-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M8 7h12m0 0l-4-4m4 4l-4 4m0 6H4m0 0l4 4m-4-4l4-4" />
            </svg>
          </div>

          <h2 className="text-2xl font-bold text-white mb-3">Bank Transfers Coming Soon</h2>
          <p className="text-gray-300 mb-6 max-w-md mx-auto">
            We're working on secure bank linking and instant transfers.
            Soon you'll be able to easily move funds between your bank and Elson account.
          </p>

          <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mb-8">
            <div className="bg-gray-800/50 rounded-lg p-4">
              <div className="text-green-400 text-2xl mb-2">🏦</div>
              <h3 className="text-white font-medium mb-1">Link Bank Accounts</h3>
              <p className="text-gray-400 text-sm">Securely connect your checking and savings accounts</p>
            </div>
            <div className="bg-gray-800/50 rounded-lg p-4">
              <div className="text-green-400 text-2xl mb-2">⚡</div>
              <h3 className="text-white font-medium mb-1">Instant Transfers</h3>
              <p className="text-gray-400 text-sm">Move money instantly or via standard ACH</p>
            </div>
            <div className="bg-gray-800/50 rounded-lg p-4">
              <div className="text-green-400 text-2xl mb-2">🔒</div>
              <h3 className="text-white font-medium mb-1">Bank-Level Security</h3>
              <p className="text-gray-400 text-sm">256-bit encryption and FDIC insurance</p>
            </div>
          </div>

          <div className="bg-gray-800/50 rounded-lg p-4 mb-6 text-left">
            <h4 className="text-white font-medium mb-2">Current Status</h4>
            <p className="text-gray-300 text-sm">
              You're using <span className="text-green-400 font-medium">Paper Trading</span> with ${(250000).toLocaleString()} in virtual funds.
              Paper trading lets you practice buying and selling stocks without risking real money.
            </p>
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

        {/* Info Section */}
        <div className="mt-8 grid grid-cols-1 md:grid-cols-2 gap-6">
          <div className="bg-gray-900 rounded-xl p-6">
            <h3 className="text-lg font-semibold text-white mb-4">About Paper Trading</h3>
            <ul className="space-y-3 text-gray-300 text-sm">
              <li className="flex items-start gap-2">
                <span className="text-green-400 mt-1">✓</span>
                <span>Start with $250,000 in virtual funds</span>
              </li>
              <li className="flex items-start gap-2">
                <span className="text-green-400 mt-1">✓</span>
                <span>Practice with real market data</span>
              </li>
              <li className="flex items-start gap-2">
                <span className="text-green-400 mt-1">✓</span>
                <span>Learn trading strategies risk-free</span>
              </li>
              <li className="flex items-start gap-2">
                <span className="text-green-400 mt-1">✓</span>
                <span>Track your performance over time</span>
              </li>
            </ul>
          </div>

          <div className="bg-gray-900 rounded-xl p-6">
            <h3 className="text-lg font-semibold text-white mb-4">What's Coming</h3>
            <ul className="space-y-3 text-gray-300 text-sm">
              <li className="flex items-start gap-2">
                <span className="text-purple-400 mt-1">◦</span>
                <span>Link checking and savings accounts</span>
              </li>
              <li className="flex items-start gap-2">
                <span className="text-purple-400 mt-1">◦</span>
                <span>Instant and ACH transfers</span>
              </li>
              <li className="flex items-start gap-2">
                <span className="text-purple-400 mt-1">◦</span>
                <span>Recurring deposit schedules</span>
              </li>
              <li className="flex items-start gap-2">
                <span className="text-purple-400 mt-1">◦</span>
                <span>Transfer history and tracking</span>
              </li>
            </ul>
          </div>
        </div>
      </div>
    </div>
  );
};

export default TransfersPage;
