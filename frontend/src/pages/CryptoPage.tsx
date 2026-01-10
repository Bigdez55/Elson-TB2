import React from 'react';
import { Link } from 'react-router-dom';

const CryptoPage: React.FC = () => {
  return (
    <div className="bg-gray-800 min-h-screen p-6">
      {/* Header */}
      <div className="mb-8">
        <h1 className="text-2xl font-bold text-white">Crypto Trading</h1>
        <p className="text-gray-400">Buy, sell, and track cryptocurrency</p>
      </div>

      {/* Coming Soon Banner */}
      <div className="max-w-2xl mx-auto">
        <div className="bg-gradient-to-r from-orange-900/40 to-yellow-900/40 rounded-2xl p-8 border border-orange-500/30 text-center">
          <div className="w-20 h-20 bg-orange-600/30 rounded-full flex items-center justify-center mx-auto mb-6">
            <span className="text-4xl">₿</span>
          </div>

          <h2 className="text-2xl font-bold text-white mb-3">Crypto Trading Coming Soon</h2>
          <p className="text-gray-300 mb-6 max-w-md mx-auto">
            Trade popular cryptocurrencies with competitive fees.
            Bitcoin, Ethereum, Solana, and more coming to Elson.
          </p>

          <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-8">
            <div className="bg-gray-800/50 rounded-lg p-3">
              <div className="text-2xl mb-1">₿</div>
              <h3 className="text-white font-medium text-sm">Bitcoin</h3>
            </div>
            <div className="bg-gray-800/50 rounded-lg p-3">
              <div className="text-2xl mb-1">Ξ</div>
              <h3 className="text-white font-medium text-sm">Ethereum</h3>
            </div>
            <div className="bg-gray-800/50 rounded-lg p-3">
              <div className="text-2xl mb-1">◎</div>
              <h3 className="text-white font-medium text-sm">Solana</h3>
            </div>
            <div className="bg-gray-800/50 rounded-lg p-3">
              <div className="text-2xl mb-1">+</div>
              <h3 className="text-white font-medium text-sm">More...</h3>
            </div>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mb-8">
            <div className="bg-gray-800/50 rounded-lg p-4">
              <div className="text-orange-400 text-2xl mb-2">🔄</div>
              <h3 className="text-white font-medium mb-1">Easy Trading</h3>
              <p className="text-gray-400 text-sm">Buy and sell crypto in seconds</p>
            </div>
            <div className="bg-gray-800/50 rounded-lg p-4">
              <div className="text-orange-400 text-2xl mb-2">📊</div>
              <h3 className="text-white font-medium mb-1">Live Prices</h3>
              <p className="text-gray-400 text-sm">Real-time market data</p>
            </div>
            <div className="bg-gray-800/50 rounded-lg p-4">
              <div className="text-orange-400 text-2xl mb-2">🔒</div>
              <h3 className="text-white font-medium mb-1">Secure Storage</h3>
              <p className="text-gray-400 text-sm">Industry-leading security</p>
            </div>
          </div>

          <div className="flex flex-col sm:flex-row gap-4 justify-center">
            <button className="bg-orange-600 hover:bg-orange-700 text-white px-6 py-3 rounded-lg font-medium transition-colors">
              Join the Waitlist
            </button>
            <Link
              to="/paper/trading"
              className="bg-gray-700 hover:bg-gray-600 text-white px-6 py-3 rounded-lg font-medium transition-colors"
            >
              Trade Stocks Instead
            </Link>
          </div>
        </div>

        {/* Current Option */}
        <div className="mt-8 bg-gray-900 rounded-xl p-6">
          <h3 className="text-lg font-semibold text-white mb-4">Trade Stocks Now</h3>
          <p className="text-gray-400 text-sm mb-4">
            While crypto trading is coming soon, you can start paper trading stocks today
            with $250,000 in virtual funds to practice your investment strategies.
          </p>
          <Link
            to="/paper/trading"
            className="inline-block bg-purple-600 hover:bg-purple-700 text-white px-6 py-3 rounded-lg font-medium transition-colors"
          >
            Start Paper Trading
          </Link>
        </div>
      </div>
    </div>
  );
};

export default CryptoPage;
