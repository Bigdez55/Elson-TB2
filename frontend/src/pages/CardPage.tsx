import React, { useState } from 'react';

interface Transaction {
  id: string;
  merchant: string;
  category: string;
  amount: number;
  date: string;
  status: 'Completed' | 'Pending';
  cashback: number;
}

const CardPage: React.FC = () => {
  const [selectedTab, setSelectedTab] = useState<'card' | 'transactions' | 'rewards'>('card');

  const cardBalance = 2450.75;
  const availableCredit = 7549.25;
  const totalCashback = 148.50;
  const monthlySpend = 1850.00;

  const transactions: Transaction[] = [
    { id: '1', merchant: 'Amazon', category: 'Shopping', amount: 156.42, date: '2024-03-15', status: 'Completed', cashback: 3.13 },
    { id: '2', merchant: 'Whole Foods', category: 'Groceries', amount: 87.23, date: '2024-03-14', status: 'Completed', cashback: 1.74 },
    { id: '3', merchant: 'Shell Gas Station', category: 'Gas', amount: 52.18, date: '2024-03-14', status: 'Completed', cashback: 1.04 },
    { id: '4', merchant: 'Starbucks', category: 'Dining', amount: 12.45, date: '2024-03-13', status: 'Completed', cashback: 0.25 },
    { id: '5', merchant: 'Netflix', category: 'Entertainment', amount: 15.99, date: '2024-03-12', status: 'Pending', cashback: 0.32 },
    { id: '6', merchant: 'Target', category: 'Shopping', amount: 248.90, date: '2024-03-11', status: 'Completed', cashback: 4.98 },
    { id: '7', merchant: 'Uber', category: 'Transportation', amount: 28.50, date: '2024-03-10', status: 'Completed', cashback: 0.57 },
  ];

  const spendingByCategory = [
    { category: 'Shopping', amount: 405.32, percentage: 21.9, color: 'bg-purple-500' },
    { category: 'Groceries', amount: 287.65, percentage: 15.6, color: 'bg-green-500' },
    { category: 'Dining', amount: 542.18, percentage: 29.3, color: 'bg-yellow-500' },
    { category: 'Gas', amount: 215.42, percentage: 11.6, color: 'bg-blue-500' },
    { category: 'Entertainment', amount: 198.50, percentage: 10.7, color: 'bg-pink-500' },
    { category: 'Other', amount: 200.93, percentage: 10.9, color: 'bg-gray-500' },
  ];

  const getCategoryIcon = (category: string) => {
    const icons: { [key: string]: string } = {
      'Shopping': '🛍️',
      'Groceries': '🛒',
      'Dining': '🍽️',
      'Gas': '⛽',
      'Entertainment': '🎬',
      'Transportation': '🚗',
      'Other': '📦',
    };
    return icons[category] || '💳';
  };

  return (
    <div className="bg-gray-800 min-h-screen p-6">
      <div className="mb-8">
        <h1 className="text-3xl font-bold text-white mb-2">Elson Card</h1>
        <p className="text-gray-400">
          Spend your portfolio gains instantly with 2% cashback on all purchases
        </p>
      </div>

      {/* Quick Stats */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4 mb-6">
        <div className="bg-gradient-to-br from-purple-900 to-purple-800 rounded-xl p-4">
          <div className="text-purple-300 text-sm mb-1">Card Balance</div>
          <div className="text-3xl font-bold text-white">${cardBalance.toLocaleString()}</div>
          <div className="text-purple-200 text-xs mt-1">Current balance</div>
        </div>
        <div className="bg-gradient-to-br from-blue-900 to-blue-800 rounded-xl p-4">
          <div className="text-blue-300 text-sm mb-1">Available Credit</div>
          <div className="text-3xl font-bold text-white">${availableCredit.toLocaleString()}</div>
          <div className="text-blue-200 text-xs mt-1">$10,000 limit</div>
        </div>
        <div className="bg-gradient-to-br from-green-900 to-green-800 rounded-xl p-4">
          <div className="text-green-300 text-sm mb-1">Total Cashback</div>
          <div className="text-3xl font-bold text-white">${totalCashback.toFixed(2)}</div>
          <div className="text-green-200 text-xs mt-1">All time</div>
        </div>
        <div className="bg-gradient-to-br from-yellow-900 to-yellow-800 rounded-xl p-4">
          <div className="text-yellow-300 text-sm mb-1">This Month</div>
          <div className="text-3xl font-bold text-white">${monthlySpend.toLocaleString()}</div>
          <div className="text-yellow-200 text-xs mt-1">Total spend</div>
        </div>
      </div>

      {/* Tab Navigation */}
      <div className="mb-6">
        <div className="flex space-x-2 bg-gray-900 p-2 rounded-lg inline-flex">
          <button
            onClick={() => setSelectedTab('card')}
            className={`px-4 py-2 rounded-lg transition-colors ${
              selectedTab === 'card' ? 'bg-purple-600 text-white' : 'text-gray-400 hover:bg-gray-800'
            }`}
          >
            💳 My Card
          </button>
          <button
            onClick={() => setSelectedTab('transactions')}
            className={`px-4 py-2 rounded-lg transition-colors ${
              selectedTab === 'transactions' ? 'bg-purple-600 text-white' : 'text-gray-400 hover:bg-gray-800'
            }`}
          >
            📋 Transactions
          </button>
          <button
            onClick={() => setSelectedTab('rewards')}
            className={`px-4 py-2 rounded-lg transition-colors ${
              selectedTab === 'rewards' ? 'bg-purple-600 text-white' : 'text-gray-400 hover:bg-gray-800'
            }`}
          >
            🎁 Rewards
          </button>
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Main Content */}
        <div className="lg:col-span-2">
          {selectedTab === 'card' && (
            <div className="space-y-6">
              {/* Virtual Card */}
              <div className="relative bg-gradient-to-br from-purple-600 via-purple-700 to-indigo-800 rounded-2xl p-8 shadow-2xl">
                <div className="absolute top-6 right-6 text-white text-2xl">💳</div>
                <div className="mb-12">
                  <div className="text-purple-200 text-sm mb-1">Elson Premium Card</div>
                  <div className="text-white text-xs">Virtual • Physical available</div>
                </div>
                <div className="mb-6">
                  <div className="text-white text-2xl font-mono tracking-wider mb-2">
                    **** **** **** 4892
                  </div>
                </div>
                <div className="flex items-end justify-between">
                  <div>
                    <div className="text-purple-200 text-xs mb-1">CARD HOLDER</div>
                    <div className="text-white font-semibold">JOHN DOE</div>
                  </div>
                  <div>
                    <div className="text-purple-200 text-xs mb-1">EXPIRES</div>
                    <div className="text-white font-semibold">12/27</div>
                  </div>
                  <div>
                    <div className="text-purple-200 text-xs mb-1">CVV</div>
                    <div className="text-white font-semibold">***</div>
                  </div>
                </div>
              </div>

              {/* Card Actions */}
              <div className="grid grid-cols-2 gap-4">
                <button className="bg-gray-900 hover:bg-gray-800 text-white py-4 rounded-xl font-medium transition-colors">
                  🔒 Lock Card
                </button>
                <button className="bg-gray-900 hover:bg-gray-800 text-white py-4 rounded-xl font-medium transition-colors">
                  🔄 Replace Card
                </button>
                <button className="bg-gray-900 hover:bg-gray-800 text-white py-4 rounded-xl font-medium transition-colors">
                  📍 View PIN
                </button>
                <button className="bg-purple-600 hover:bg-purple-700 text-white py-4 rounded-xl font-medium transition-colors">
                  📮 Order Physical Card
                </button>
              </div>

              {/* Card Details */}
              <div className="bg-gray-900 rounded-xl p-6">
                <h3 className="text-lg font-semibold text-white mb-4">Card Details</h3>
                <div className="space-y-3">
                  <div className="flex items-center justify-between py-2 border-b border-gray-800">
                    <span className="text-gray-400">Card Number</span>
                    <span className="text-white font-mono">**** **** **** 4892</span>
                  </div>
                  <div className="flex items-center justify-between py-2 border-b border-gray-800">
                    <span className="text-gray-400">Card Type</span>
                    <span className="text-white">Virtual Debit</span>
                  </div>
                  <div className="flex items-center justify-between py-2 border-b border-gray-800">
                    <span className="text-gray-400">Status</span>
                    <span className="text-green-400 font-medium">● Active</span>
                  </div>
                  <div className="flex items-center justify-between py-2 border-b border-gray-800">
                    <span className="text-gray-400">Daily Limit</span>
                    <span className="text-white">$5,000</span>
                  </div>
                  <div className="flex items-center justify-between py-2">
                    <span className="text-gray-400">ATM Withdrawals</span>
                    <span className="text-white">Free (Any ATM)</span>
                  </div>
                </div>
              </div>
            </div>
          )}

          {selectedTab === 'transactions' && (
            <div className="bg-gray-900 rounded-xl overflow-hidden">
              <div className="p-4 border-b border-gray-700">
                <h2 className="text-xl font-semibold text-white">Recent Transactions</h2>
              </div>
              <div className="divide-y divide-gray-700">
                {transactions.map((transaction) => (
                  <div key={transaction.id} className="p-4 hover:bg-gray-800 transition-colors">
                    <div className="flex items-center justify-between">
                      <div className="flex items-center space-x-4">
                        <div className="w-10 h-10 bg-gradient-to-br from-purple-500 to-blue-500 rounded-lg flex items-center justify-center">
                          <span className="text-xl">{getCategoryIcon(transaction.category)}</span>
                        </div>
                        <div>
                          <div className="text-white font-medium">{transaction.merchant}</div>
                          <div className="text-sm text-gray-400">{transaction.category}</div>
                          <div className="text-xs text-green-400">+${transaction.cashback.toFixed(2)} cashback</div>
                        </div>
                      </div>
                      <div className="text-right">
                        <div className="text-lg font-semibold text-white">-${transaction.amount.toFixed(2)}</div>
                        <div className="text-sm text-gray-400">{new Date(transaction.date).toLocaleDateString()}</div>
                        <span className={`inline-block text-xs px-2 py-1 rounded ${
                          transaction.status === 'Completed' ? 'bg-green-900/30 text-green-400' : 'bg-yellow-900/30 text-yellow-400'
                        }`}>
                          {transaction.status}
                        </span>
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          )}

          {selectedTab === 'rewards' && (
            <div className="space-y-6">
              {/* Cashback Summary */}
              <div className="bg-gradient-to-br from-green-900 to-emerald-900 rounded-xl p-6">
                <h3 className="text-2xl font-bold text-white mb-2">💰 ${totalCashback.toFixed(2)}</h3>
                <p className="text-green-200 mb-4">Total Cashback Earned</p>
                <div className="grid grid-cols-2 gap-4">
                  <div className="bg-white/10 backdrop-blur rounded-lg p-3">
                    <div className="text-green-200 text-sm">This Month</div>
                    <div className="text-white text-xl font-bold">$37.00</div>
                  </div>
                  <div className="bg-white/10 backdrop-blur rounded-lg p-3">
                    <div className="text-green-200 text-sm">Pending</div>
                    <div className="text-white text-xl font-bold">$12.50</div>
                  </div>
                </div>
              </div>

              {/* Cashback Tiers */}
              <div className="bg-gray-900 rounded-xl p-6">
                <h3 className="text-lg font-semibold text-white mb-4">💎 Cashback Rates</h3>
                <div className="space-y-3">
                  <div className="bg-gradient-to-r from-purple-900/50 to-purple-800/50 p-4 rounded-lg border border-purple-600/30">
                    <div className="flex items-center justify-between">
                      <div>
                        <div className="text-white font-medium">All Purchases</div>
                        <div className="text-sm text-gray-400">Standard rate</div>
                      </div>
                      <div className="text-2xl font-bold text-purple-400">2%</div>
                    </div>
                  </div>
                  <div className="bg-gray-800 p-4 rounded-lg">
                    <div className="flex items-center justify-between">
                      <div>
                        <div className="text-white font-medium">Trading Fees</div>
                        <div className="text-sm text-gray-400">On Elson platform</div>
                      </div>
                      <div className="text-2xl font-bold text-green-400">5%</div>
                    </div>
                  </div>
                  <div className="bg-gray-800 p-4 rounded-lg">
                    <div className="flex items-center justify-between">
                      <div>
                        <div className="text-white font-medium">Travel</div>
                        <div className="text-sm text-gray-400">Flights, hotels, car rentals</div>
                      </div>
                      <div className="text-2xl font-bold text-blue-400">3%</div>
                    </div>
                  </div>
                </div>
              </div>

              {/* Redeem Options */}
              <div className="bg-gray-900 rounded-xl p-6">
                <h3 className="text-lg font-semibold text-white mb-4">🎁 Redeem Rewards</h3>
                <div className="space-y-3">
                  <button className="w-full bg-purple-600 hover:bg-purple-700 text-white py-3 rounded-lg font-medium transition-colors">
                    Transfer to Trading Account
                  </button>
                  <button className="w-full bg-gray-800 hover:bg-gray-700 text-white py-3 rounded-lg font-medium transition-colors">
                    Apply to Card Balance
                  </button>
                  <button className="w-full bg-gray-800 hover:bg-gray-700 text-white py-3 rounded-lg font-medium transition-colors">
                    Donate to Charity
                  </button>
                </div>
              </div>
            </div>
          )}
        </div>

        {/* Sidebar */}
        <div className="space-y-6">
          {/* Spending Breakdown */}
          <div className="bg-gray-900 rounded-xl p-4">
            <h3 className="text-lg font-semibold text-white mb-4">📊 Spending by Category</h3>
            <div className="space-y-3">
              {spendingByCategory.map((item) => (
                <div key={item.category}>
                  <div className="flex items-center justify-between mb-1">
                    <div className="flex items-center space-x-2">
                      <span>{getCategoryIcon(item.category)}</span>
                      <span className="text-gray-300 text-sm">{item.category}</span>
                    </div>
                    <span className="text-white font-semibold">${item.amount.toFixed(2)}</span>
                  </div>
                  <div className="w-full bg-gray-700 rounded-full h-2">
                    <div
                      className={`${item.color} rounded-full h-2`}
                      style={{ width: `${item.percentage}%` }}
                    />
                  </div>
                  <div className="text-xs text-gray-500 mt-1">{item.percentage}% of total</div>
                </div>
              ))}
            </div>
          </div>

          {/* Benefits */}
          <div className="bg-gradient-to-br from-purple-900 to-blue-900 rounded-xl p-4">
            <h3 className="text-lg font-semibold text-white mb-3">✨ Card Benefits</h3>
            <div className="space-y-2 text-sm text-gray-200">
              <div className="flex items-start space-x-2">
                <span>✓</span>
                <p>2% cashback on all purchases</p>
              </div>
              <div className="flex items-start space-x-2">
                <span>✓</span>
                <p>No annual fee</p>
              </div>
              <div className="flex items-start space-x-2">
                <span>✓</span>
                <p>Free ATM withdrawals worldwide</p>
              </div>
              <div className="flex items-start space-x-2">
                <span>✓</span>
                <p>No foreign transaction fees</p>
              </div>
              <div className="flex items-start space-x-2">
                <span>✓</span>
                <p>Instant virtual card</p>
              </div>
              <div className="flex items-start space-x-2">
                <span>✓</span>
                <p>Purchase protection</p>
              </div>
            </div>
          </div>

          {/* Security */}
          <div className="bg-gray-900 rounded-xl p-4">
            <h3 className="text-lg font-semibold text-white mb-3">🔒 Security</h3>
            <div className="space-y-3">
              <div className="flex items-center justify-between">
                <span className="text-gray-300 text-sm">Card Lock</span>
                <label className="relative inline-flex items-center cursor-pointer">
                  <input type="checkbox" className="sr-only peer" />
                  <div className="w-11 h-6 bg-gray-700 peer-focus:outline-none rounded-full peer peer-checked:after:translate-x-full peer-checked:after:border-white after:content-[''] after:absolute after:top-[2px] after:left-[2px] after:bg-white after:border-gray-300 after:border after:rounded-full after:h-5 after:w-5 after:transition-all peer-checked:bg-purple-600"></div>
                </label>
              </div>
              <div className="flex items-center justify-between">
                <span className="text-gray-300 text-sm">Online Transactions</span>
                <label className="relative inline-flex items-center cursor-pointer">
                  <input type="checkbox" className="sr-only peer" defaultChecked />
                  <div className="w-11 h-6 bg-gray-700 peer-focus:outline-none rounded-full peer peer-checked:after:translate-x-full peer-checked:after:border-white after:content-[''] after:absolute after:top-[2px] after:left-[2px] after:bg-white after:border-gray-300 after:border after:rounded-full after:h-5 after:w-5 after:transition-all peer-checked:bg-purple-600"></div>
                </label>
              </div>
              <div className="flex items-center justify-between">
                <span className="text-gray-300 text-sm">ATM Withdrawals</span>
                <label className="relative inline-flex items-center cursor-pointer">
                  <input type="checkbox" className="sr-only peer" defaultChecked />
                  <div className="w-11 h-6 bg-gray-700 peer-focus:outline-none rounded-full peer peer-checked:after:translate-x-full peer-checked:after:border-white after:content-[''] after:absolute after:top-[2px] after:left-[2px] after:bg-white after:border-gray-300 after:border after:rounded-full after:h-5 after:w-5 after:transition-all peer-checked:bg-purple-600"></div>
                </label>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default CardPage;
