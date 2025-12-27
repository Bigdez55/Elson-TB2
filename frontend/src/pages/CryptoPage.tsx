import React, { useState } from 'react';
import { Link } from 'react-router-dom';

interface Crypto {
  symbol: string;
  name: string;
  price: number;
  change24h: number;
  changePercent24h: number;
  marketCap: number;
  volume24h: number;
  holdings?: number;
  icon: string;
}

interface Transaction {
  id: string;
  type: 'Buy' | 'Sell';
  crypto: string;
  amount: number;
  price: number;
  total: number;
  date: string;
}

const CryptoPage: React.FC = () => {
  const [selectedTab, setSelectedTab] = useState<'market' | 'portfolio' | 'trade'>('market');
  const [tradeType, setTradeType] = useState<'buy' | 'sell'>('buy');
  const [tradeCrypto, setTradeCrypto] = useState<string>('BTC');
  const [tradeAmount, setTradeAmount] = useState<string>('');

  const portfolio = {
    totalValue: 48750.25,
    dayChange: 2450.50,
    dayChangePercent: 5.3,
  };

  const cryptos: Crypto[] = [
    {
      symbol: 'BTC',
      name: 'Bitcoin',
      price: 67842.50,
      change24h: 2842.50,
      changePercent24h: 4.37,
      marketCap: 1328000000000,
      volume24h: 28500000000,
      holdings: 0.5,
      icon: '₿',
    },
    {
      symbol: 'ETH',
      name: 'Ethereum',
      price: 3542.80,
      change24h: 185.40,
      changePercent24h: 5.52,
      marketCap: 425000000000,
      volume24h: 15200000000,
      holdings: 5.2,
      icon: 'Ξ',
    },
    {
      symbol: 'BNB',
      name: 'BNB',
      price: 584.25,
      change24h: -12.40,
      changePercent24h: -2.08,
      marketCap: 87000000000,
      volume24h: 2100000000,
      icon: 'B',
    },
    {
      symbol: 'SOL',
      name: 'Solana',
      price: 142.85,
      change24h: 8.50,
      changePercent24h: 6.33,
      marketCap: 63000000000,
      volume24h: 3800000000,
      holdings: 25,
      icon: 'S',
    },
    {
      symbol: 'XRP',
      name: 'Ripple',
      price: 0.62,
      change24h: 0.03,
      changePercent24h: 5.08,
      marketCap: 33000000000,
      volume24h: 1900000000,
      icon: 'X',
    },
    {
      symbol: 'ADA',
      name: 'Cardano',
      price: 0.58,
      change24h: -0.02,
      changePercent24h: -3.33,
      marketCap: 20000000000,
      volume24h: 850000000,
      icon: 'A',
    },
  ];

  const myHoldings = cryptos.filter(c => c.holdings && c.holdings > 0);

  const recentTransactions: Transaction[] = [
    { id: '1', type: 'Buy', crypto: 'BTC', amount: 0.1, price: 67500, total: 6750, date: '2024-03-15T10:30:00' },
    { id: '2', type: 'Buy', crypto: 'ETH', amount: 2, price: 3500, total: 7000, date: '2024-03-14T15:20:00' },
    { id: '3', type: 'Sell', crypto: 'SOL', amount: 10, price: 140, total: 1400, date: '2024-03-13T09:15:00' },
    { id: '4', type: 'Buy', crypto: 'SOL', amount: 20, price: 135, total: 2700, date: '2024-03-10T14:45:00' },
  ];

  const formatNumber = (num: number) => {
    if (num >= 1000000000) return `$${(num / 1000000000).toFixed(2)}B`;
    if (num >= 1000000) return `$${(num / 1000000).toFixed(2)}M`;
    if (num >= 1000) return `$${(num / 1000).toFixed(2)}K`;
    return `$${num.toFixed(2)}`;
  };

  const handleTrade = () => {
    const crypto = cryptos.find(c => c.symbol === tradeCrypto);
    if (!crypto) return;

    const amount = parseFloat(tradeAmount);
    const total = amount * crypto.price;
    alert(`${tradeType === 'buy' ? 'Buying' : 'Selling'} ${amount} ${tradeCrypto} for ${formatNumber(total)}`);
    setTradeAmount('');
  };

  return (
    <div className="bg-gray-800 min-h-screen p-6">
      <div className="mb-8">
        <h1 className="text-3xl font-bold text-white mb-2">Crypto Trading</h1>
        <p className="text-gray-400">
          Trade Bitcoin, Ethereum, and 50+ cryptocurrencies 24/7 with real-time data
        </p>
      </div>

      {/* Portfolio Overview */}
      {myHoldings.length > 0 && (
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mb-6">
          <div className="bg-gradient-to-br from-purple-900 to-purple-800 rounded-xl p-4">
            <div className="text-purple-300 text-sm mb-1">Portfolio Value</div>
            <div className="text-3xl font-bold text-white">${portfolio.totalValue.toLocaleString()}</div>
            <div className={`text-xs mt-1 ${portfolio.dayChange >= 0 ? 'text-green-400' : 'text-red-400'}`}>
              {portfolio.dayChange >= 0 ? '+' : ''}${portfolio.dayChange.toFixed(2)} ({portfolio.dayChangePercent >= 0 ? '+' : ''}{portfolio.dayChangePercent.toFixed(2)}%) today
            </div>
          </div>
          <div className="bg-gradient-to-br from-blue-900 to-blue-800 rounded-xl p-4">
            <div className="text-blue-300 text-sm mb-1">Assets Owned</div>
            <div className="text-3xl font-bold text-white">{myHoldings.length}</div>
            <div className="text-blue-200 text-xs mt-1">Total cryptocurrencies</div>
          </div>
          <div className="bg-gradient-to-br from-green-900 to-green-800 rounded-xl p-4">
            <div className="text-green-300 text-sm mb-1">24h Trading Volume</div>
            <div className="text-3xl font-bold text-white">${(portfolio.totalValue * 0.15).toFixed(0)}</div>
            <div className="text-green-200 text-xs mt-1">Across all assets</div>
          </div>
        </div>
      )}

      {/* Tab Navigation */}
      <div className="mb-6">
        <div className="flex space-x-2 bg-gray-900 p-2 rounded-lg inline-flex">
          <button
            onClick={() => setSelectedTab('market')}
            className={`px-4 py-2 rounded-lg transition-colors ${
              selectedTab === 'market' ? 'bg-purple-600 text-white' : 'text-gray-400 hover:bg-gray-800'
            }`}
          >
            📊 Markets
          </button>
          <button
            onClick={() => setSelectedTab('portfolio')}
            className={`px-4 py-2 rounded-lg transition-colors ${
              selectedTab === 'portfolio' ? 'bg-purple-600 text-white' : 'text-gray-400 hover:bg-gray-800'
            }`}
          >
            💼 Portfolio
          </button>
          <button
            onClick={() => setSelectedTab('trade')}
            className={`px-4 py-2 rounded-lg transition-colors ${
              selectedTab === 'trade' ? 'bg-purple-600 text-white' : 'text-gray-400 hover:bg-gray-800'
            }`}
          >
            💱 Trade
          </button>
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Main Content */}
        <div className="lg:col-span-2">
          {selectedTab === 'market' && (
            <div className="bg-gray-900 rounded-xl overflow-hidden">
              <div className="p-4 border-b border-gray-700">
                <h2 className="text-xl font-semibold text-white">Cryptocurrency Markets</h2>
              </div>
              <div className="divide-y divide-gray-700">
                {cryptos.map((crypto) => (
                  <div key={crypto.symbol} className="p-4 hover:bg-gray-800 transition-colors cursor-pointer">
                    <div className="flex items-center justify-between">
                      <div className="flex items-center space-x-4 flex-1">
                        <div className="w-12 h-12 bg-gradient-to-br from-purple-500 to-blue-500 rounded-full flex items-center justify-center flex-shrink-0">
                          <span className="text-white text-2xl font-bold">{crypto.icon}</span>
                        </div>
                        <div className="flex-1">
                          <div className="flex items-center space-x-2">
                            <h3 className="text-white font-semibold">{crypto.symbol}</h3>
                            {crypto.holdings && (
                              <span className="text-xs bg-purple-900/50 text-purple-400 px-2 py-0.5 rounded">
                                {crypto.holdings} {crypto.symbol}
                              </span>
                            )}
                          </div>
                          <p className="text-sm text-gray-400">{crypto.name}</p>
                        </div>
                      </div>
                      <div className="text-right mr-6">
                        <div className="text-white font-semibold">${crypto.price.toLocaleString()}</div>
                        <div className={`text-sm font-medium ${crypto.change24h >= 0 ? 'text-green-400' : 'text-red-400'}`}>
                          {crypto.change24h >= 0 ? '+' : ''}{crypto.changePercent24h.toFixed(2)}%
                        </div>
                      </div>
                      <div className="text-right">
                        <div className="text-sm text-gray-400">MCap: {formatNumber(crypto.marketCap)}</div>
                        <div className="text-sm text-gray-400">Vol: {formatNumber(crypto.volume24h)}</div>
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          )}

          {selectedTab === 'portfolio' && (
            <div className="space-y-6">
              {/* Holdings */}
              <div className="bg-gray-900 rounded-xl overflow-hidden">
                <div className="p-4 border-b border-gray-700">
                  <h2 className="text-xl font-semibold text-white">Your Holdings</h2>
                </div>
                <div className="divide-y divide-gray-700">
                  {myHoldings.map((crypto) => {
                    const value = crypto.price * (crypto.holdings || 0);
                    const portfolioPercent = (value / portfolio.totalValue) * 100;
                    return (
                      <div key={crypto.symbol} className="p-4 hover:bg-gray-800 transition-colors">
                        <div className="flex items-center justify-between mb-2">
                          <div className="flex items-center space-x-4">
                            <div className="w-12 h-12 bg-gradient-to-br from-purple-500 to-blue-500 rounded-full flex items-center justify-center">
                              <span className="text-white text-2xl font-bold">{crypto.icon}</span>
                            </div>
                            <div>
                              <h3 className="text-white font-semibold">{crypto.symbol}</h3>
                              <p className="text-sm text-gray-400">{crypto.holdings} {crypto.symbol}</p>
                            </div>
                          </div>
                          <div className="text-right">
                            <div className="text-xl font-bold text-white">${value.toLocaleString()}</div>
                            <div className={`text-sm ${crypto.change24h >= 0 ? 'text-green-400' : 'text-red-400'}`}>
                              {crypto.change24h >= 0 ? '+' : ''}{crypto.changePercent24h.toFixed(2)}%
                            </div>
                          </div>
                        </div>
                        <div className="w-full bg-gray-700 rounded-full h-2">
                          <div
                            className="bg-purple-500 rounded-full h-2"
                            style={{ width: `${portfolioPercent}%` }}
                          />
                        </div>
                        <div className="text-xs text-gray-500 mt-1">{portfolioPercent.toFixed(1)}% of portfolio</div>
                      </div>
                    );
                  })}
                </div>
              </div>

              {/* Recent Transactions */}
              <div className="bg-gray-900 rounded-xl overflow-hidden">
                <div className="p-4 border-b border-gray-700">
                  <h2 className="text-xl font-semibold text-white">Recent Transactions</h2>
                </div>
                <div className="divide-y divide-gray-700">
                  {recentTransactions.map((tx) => (
                    <div key={tx.id} className="p-4 hover:bg-gray-800 transition-colors">
                      <div className="flex items-center justify-between">
                        <div>
                          <div className="flex items-center space-x-2">
                            <span className={`px-2 py-1 rounded text-xs font-medium ${
                              tx.type === 'Buy' ? 'bg-green-900/30 text-green-400' : 'bg-red-900/30 text-red-400'
                            }`}>
                              {tx.type}
                            </span>
                            <span className="text-white font-medium">{tx.crypto}</span>
                          </div>
                          <div className="text-sm text-gray-400 mt-1">
                            {tx.amount} {tx.crypto} @ ${tx.price.toLocaleString()}
                          </div>
                          <div className="text-xs text-gray-500">{new Date(tx.date).toLocaleString()}</div>
                        </div>
                        <div className="text-right">
                          <div className={`text-lg font-semibold ${tx.type === 'Buy' ? 'text-red-400' : 'text-green-400'}`}>
                            {tx.type === 'Buy' ? '-' : '+'}${tx.total.toLocaleString()}
                          </div>
                        </div>
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            </div>
          )}

          {selectedTab === 'trade' && (
            <div className="bg-gray-900 rounded-xl p-6">
              <h2 className="text-xl font-semibold text-white mb-6">Trade Cryptocurrency</h2>

              {/* Buy/Sell Toggle */}
              <div className="flex space-x-2 bg-gray-800 p-2 rounded-lg mb-6 inline-flex">
                <button
                  onClick={() => setTradeType('buy')}
                  className={`px-6 py-2 rounded-lg transition-colors ${
                    tradeType === 'buy' ? 'bg-green-600 text-white' : 'text-gray-400 hover:bg-gray-700'
                  }`}
                >
                  Buy
                </button>
                <button
                  onClick={() => setTradeType('sell')}
                  className={`px-6 py-2 rounded-lg transition-colors ${
                    tradeType === 'sell' ? 'bg-red-600 text-white' : 'text-gray-400 hover:bg-gray-700'
                  }`}
                >
                  Sell
                </button>
              </div>

              <div className="space-y-4">
                <div>
                  <label className="block text-sm font-medium text-gray-400 mb-2">
                    Select Cryptocurrency
                  </label>
                  <select
                    value={tradeCrypto}
                    onChange={(e) => setTradeCrypto(e.target.value)}
                    className="w-full bg-gray-800 text-white px-4 py-3 rounded-lg border border-gray-700 focus:border-purple-500 focus:outline-none"
                  >
                    {cryptos.map((crypto) => (
                      <option key={crypto.symbol} value={crypto.symbol}>
                        {crypto.name} ({crypto.symbol}) - ${crypto.price.toLocaleString()}
                      </option>
                    ))}
                  </select>
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-400 mb-2">
                    Amount ({tradeCrypto})
                  </label>
                  <input
                    type="number"
                    value={tradeAmount}
                    onChange={(e) => setTradeAmount(e.target.value)}
                    placeholder="0.00"
                    step="0.0001"
                    className="w-full bg-gray-800 text-white px-4 py-3 rounded-lg border border-gray-700 focus:border-purple-500 focus:outline-none text-lg"
                  />
                  {tradeAmount && (
                    <p className="text-sm text-gray-400 mt-2">
                      Total: {formatNumber(parseFloat(tradeAmount) * (cryptos.find(c => c.symbol === tradeCrypto)?.price || 0))}
                    </p>
                  )}
                </div>

                <button
                  onClick={handleTrade}
                  disabled={!tradeAmount}
                  className={`w-full py-3 rounded-lg font-medium transition-colors ${
                    tradeAmount
                      ? `${tradeType === 'buy' ? 'bg-green-600 hover:bg-green-700' : 'bg-red-600 hover:bg-red-700'} text-white`
                      : 'bg-gray-700 text-gray-500 cursor-not-allowed'
                  }`}
                >
                  {tradeType === 'buy' ? 'Buy' : 'Sell'} {tradeCrypto}
                </button>
              </div>

              {/* Price Chart Placeholder */}
              <div className="mt-6 bg-gray-800 rounded-lg p-6 text-center">
                <p className="text-gray-400 mb-2">Live Price Chart</p>
                <div className="h-64 flex items-center justify-center border-2 border-dashed border-gray-700 rounded-lg">
                  <span className="text-gray-500">Chart visualization would appear here</span>
                </div>
              </div>
            </div>
          )}
        </div>

        {/* Sidebar */}
        <div className="space-y-6">
          {/* Market Stats */}
          <div className="bg-gray-900 rounded-xl p-4">
            <h3 className="text-lg font-semibold text-white mb-4">📊 Market Stats</h3>
            <div className="space-y-3">
              <div className="bg-gray-800 rounded-lg p-3">
                <div className="text-sm text-gray-400">Global Market Cap</div>
                <div className="text-xl font-bold text-white">$2.45T</div>
                <div className="text-sm text-green-400">+3.2% (24h)</div>
              </div>
              <div className="bg-gray-800 rounded-lg p-3">
                <div className="text-sm text-gray-400">24h Volume</div>
                <div className="text-xl font-bold text-white">$95.8B</div>
                <div className="text-sm text-blue-400">Active trading</div>
              </div>
              <div className="bg-gray-800 rounded-lg p-3">
                <div className="text-sm text-gray-400">BTC Dominance</div>
                <div className="text-xl font-bold text-white">54.2%</div>
                <div className="text-sm text-gray-400">Market share</div>
              </div>
            </div>
          </div>

          {/* Trending */}
          <div className="bg-gray-900 rounded-xl p-4">
            <h3 className="text-lg font-semibold text-white mb-4">🔥 Trending</h3>
            <div className="space-y-2">
              {cryptos.slice(0, 5).sort((a, b) => b.changePercent24h - a.changePercent24h).map((crypto, index) => (
                <div key={crypto.symbol} className="bg-gray-800 rounded-lg p-3">
                  <div className="flex items-center justify-between">
                    <div className="flex items-center space-x-2">
                      <span className="text-gray-500 text-sm">#{index + 1}</span>
                      <span className="text-white font-medium">{crypto.symbol}</span>
                    </div>
                    <span className={`text-sm font-semibold ${crypto.changePercent24h >= 0 ? 'text-green-400' : 'text-red-400'}`}>
                      {crypto.changePercent24h >= 0 ? '+' : ''}{crypto.changePercent24h.toFixed(2)}%
                    </span>
                  </div>
                </div>
              ))}
            </div>
          </div>

          {/* Features */}
          <div className="bg-gradient-to-br from-purple-900 to-blue-900 rounded-xl p-4">
            <h3 className="text-lg font-semibold text-white mb-3">✨ Features</h3>
            <div className="space-y-2 text-sm text-gray-200">
              <div className="flex items-start space-x-2">
                <span>✓</span>
                <p>Trade 50+ cryptocurrencies</p>
              </div>
              <div className="flex items-start space-x-2">
                <span>✓</span>
                <p>Real-time price updates</p>
              </div>
              <div className="flex items-start space-x-2">
                <span>✓</span>
                <p>24/7 trading availability</p>
              </div>
              <div className="flex items-start space-x-2">
                <span>✓</span>
                <p>Secure cold storage</p>
              </div>
              <div className="flex items-start space-x-2">
                <span>✓</span>
                <p>Low trading fees (0.5%)</p>
              </div>
              <div className="flex items-start space-x-2">
                <span>✓</span>
                <p>Instant deposits & withdrawals</p>
              </div>
            </div>
          </div>

          {/* Learn More */}
          <div className="bg-gray-900 rounded-xl p-4">
            <h3 className="text-lg font-semibold text-white mb-3">📚 New to Crypto?</h3>
            <p className="text-sm text-gray-400 mb-4">
              Learn the basics of cryptocurrency trading
            </p>
            <Link
              to="/learn"
              className="block text-center bg-purple-600 hover:bg-purple-700 text-white py-2 rounded-lg font-medium transition-colors"
            >
              Start Learning
            </Link>
          </div>
        </div>
      </div>
    </div>
  );
};

export default CryptoPage;
