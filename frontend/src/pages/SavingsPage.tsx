import React, { useState } from 'react';

interface InterestTransaction {
  id: string;
  date: string;
  amount: number;
  balance: number;
  apy: number;
}

const SavingsPage: React.FC = () => {
  const [depositAmount, setDepositAmount] = useState<string>('');
  const [selectedGoal, setSelectedGoal] = useState<string>('');

  const currentBalance = 12500.50;
  const currentAPY = 4.50;
  const monthlyInterest = 46.88;
  const yearlyProjection = 562.50;

  const interestHistory: InterestTransaction[] = [
    { id: '1', date: '2024-03-01', amount: 46.88, balance: 12500.50, apy: 4.50 },
    { id: '2', date: '2024-02-01', amount: 45.50, balance: 12453.62, apy: 4.50 },
    { id: '3', date: '2024-01-01', amount: 44.12, balance: 12408.12, apy: 4.50 },
    { id: '4', date: '2023-12-01', amount: 43.80, balance: 12364.00, apy: 4.50 },
    { id: '5', date: '2023-11-01', amount: 42.45, balance: 12320.20, apy: 4.50 },
  ];

  const savingsGoals = [
    { id: '1', name: 'Emergency Fund', target: 20000, current: 12500, icon: '🚨' },
    { id: '2', name: 'Vacation', target: 5000, current: 2800, icon: '✈️' },
    { id: '3', name: 'Down Payment', target: 50000, current: 15000, icon: '🏠' },
  ];

  const handleDeposit = () => {
    alert(`Depositing $${depositAmount} to savings`);
    setDepositAmount('');
  };

  const projectedBalance = (months: number) => {
    const monthlyRate = currentAPY / 100 / 12;
    let balance = currentBalance;
    for (let i = 0; i < months; i++) {
      balance += balance * monthlyRate;
    }
    return balance;
  };

  return (
    <div className="bg-gray-800 min-h-screen p-6">
      <div className="mb-8">
        <h1 className="text-3xl font-bold text-white mb-2">High-Yield Savings</h1>
        <p className="text-gray-400">
          Earn {currentAPY}% APY on your cash with FDIC insurance up to $250,000
        </p>
      </div>

      {/* Account Overview */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4 mb-6">
        <div className="bg-gradient-to-br from-green-900 to-green-800 rounded-xl p-4">
          <div className="text-green-300 text-sm mb-1">Current Balance</div>
          <div className="text-3xl font-bold text-white">${currentBalance.toLocaleString()}</div>
          <div className="text-green-200 text-xs mt-1">FDIC Insured</div>
        </div>
        <div className="bg-gradient-to-br from-blue-900 to-blue-800 rounded-xl p-4">
          <div className="text-blue-300 text-sm mb-1">Current APY</div>
          <div className="text-3xl font-bold text-white">{currentAPY}%</div>
          <div className="text-blue-200 text-xs mt-1">Industry-leading rate</div>
        </div>
        <div className="bg-gradient-to-br from-purple-900 to-purple-800 rounded-xl p-4">
          <div className="text-purple-300 text-sm mb-1">This Month's Interest</div>
          <div className="text-3xl font-bold text-white">${monthlyInterest.toFixed(2)}</div>
          <div className="text-purple-200 text-xs mt-1">Paid {new Date().toLocaleDateString('en-US', { month: 'short', day: 'numeric' })}</div>
        </div>
        <div className="bg-gradient-to-br from-yellow-900 to-yellow-800 rounded-xl p-4">
          <div className="text-yellow-300 text-sm mb-1">Yearly Projection</div>
          <div className="text-3xl font-bold text-white">${yearlyProjection.toFixed(2)}</div>
          <div className="text-yellow-200 text-xs mt-1">Estimated earnings</div>
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Main Content */}
        <div className="lg:col-span-2 space-y-6">
          {/* Deposit Section */}
          <div className="bg-gray-900 rounded-xl p-6">
            <h2 className="text-xl font-semibold text-white mb-4">💰 Add Funds</h2>
            <div className="space-y-4">
              <div>
                <label className="block text-sm font-medium text-gray-400 mb-2">
                  Amount to Deposit
                </label>
                <div className="relative">
                  <span className="absolute left-4 top-1/2 transform -translate-y-1/2 text-gray-400 text-lg">$</span>
                  <input
                    type="number"
                    value={depositAmount}
                    onChange={(e) => setDepositAmount(e.target.value)}
                    placeholder="0.00"
                    className="w-full bg-gray-800 text-white pl-10 pr-4 py-3 rounded-lg border border-gray-700 focus:border-green-500 focus:outline-none text-lg"
                  />
                </div>
              </div>
              <button
                onClick={handleDeposit}
                disabled={!depositAmount}
                className={`w-full py-3 rounded-lg font-medium transition-colors ${
                  depositAmount
                    ? 'bg-green-600 hover:bg-green-700 text-white'
                    : 'bg-gray-700 text-gray-500 cursor-not-allowed'
                }`}
              >
                Deposit Funds
              </button>
            </div>
          </div>

          {/* Interest History */}
          <div className="bg-gray-900 rounded-xl overflow-hidden">
            <div className="p-4 border-b border-gray-700">
              <h2 className="text-xl font-semibold text-white">📊 Interest History</h2>
            </div>
            <div className="divide-y divide-gray-700">
              {interestHistory.map((transaction) => (
                <div key={transaction.id} className="p-4 hover:bg-gray-800 transition-colors">
                  <div className="flex items-center justify-between">
                    <div>
                      <div className="text-white font-medium">Interest Payment</div>
                      <div className="text-sm text-gray-400">{new Date(transaction.date).toLocaleDateString()}</div>
                      <div className="text-xs text-gray-500">{transaction.apy}% APY</div>
                    </div>
                    <div className="text-right">
                      <div className="text-lg font-semibold text-green-400">+${transaction.amount.toFixed(2)}</div>
                      <div className="text-sm text-gray-400">Balance: ${transaction.balance.toLocaleString()}</div>
                    </div>
                  </div>
                </div>
              ))}
            </div>
          </div>

          {/* Growth Projections */}
          <div className="bg-gray-900 rounded-xl p-6">
            <h2 className="text-xl font-semibold text-white mb-4">📈 Growth Projections</h2>
            <div className="space-y-3">
              <div className="flex items-center justify-between bg-gray-800 p-3 rounded-lg">
                <span className="text-gray-300">3 Months</span>
                <span className="text-white font-semibold">${projectedBalance(3).toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 2 })}</span>
              </div>
              <div className="flex items-center justify-between bg-gray-800 p-3 rounded-lg">
                <span className="text-gray-300">6 Months</span>
                <span className="text-white font-semibold">${projectedBalance(6).toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 2 })}</span>
              </div>
              <div className="flex items-center justify-between bg-gray-800 p-3 rounded-lg">
                <span className="text-gray-300">1 Year</span>
                <span className="text-white font-semibold">${projectedBalance(12).toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 2 })}</span>
              </div>
              <div className="flex items-center justify-between bg-gradient-to-r from-green-900/50 to-blue-900/50 p-3 rounded-lg border border-green-600/30">
                <span className="text-green-300 font-medium">5 Years</span>
                <span className="text-green-400 font-bold text-lg">${projectedBalance(60).toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 2 })}</span>
              </div>
            </div>
            <p className="text-xs text-gray-500 mt-3">
              * Projections assume {currentAPY}% APY and no additional deposits or withdrawals
            </p>
          </div>
        </div>

        {/* Sidebar */}
        <div className="space-y-6">
          {/* Savings Goals */}
          <div className="bg-gray-900 rounded-xl p-4">
            <h3 className="text-lg font-semibold text-white mb-4">🎯 Savings Goals</h3>
            <div className="space-y-4">
              {savingsGoals.map((goal) => {
                const progress = (goal.current / goal.target) * 100;
                return (
                  <div key={goal.id} className="bg-gray-800 rounded-lg p-3">
                    <div className="flex items-center justify-between mb-2">
                      <div className="flex items-center space-x-2">
                        <span className="text-2xl">{goal.icon}</span>
                        <span className="text-white font-medium">{goal.name}</span>
                      </div>
                    </div>
                    <div className="space-y-1">
                      <div className="flex justify-between text-sm">
                        <span className="text-gray-400">${goal.current.toLocaleString()}</span>
                        <span className="text-gray-400">${goal.target.toLocaleString()}</span>
                      </div>
                      <div className="w-full bg-gray-700 rounded-full h-2">
                        <div
                          className="bg-green-500 rounded-full h-2 transition-all"
                          style={{ width: `${Math.min(100, progress)}%` }}
                        />
                      </div>
                      <div className="text-xs text-gray-500">{progress.toFixed(0)}% complete</div>
                    </div>
                  </div>
                );
              })}
              <button className="w-full bg-gray-800 hover:bg-gray-700 text-white px-4 py-2 rounded-lg text-sm font-medium transition-colors">
                + Add New Goal
              </button>
            </div>
          </div>

          {/* Benefits */}
          <div className="bg-gradient-to-br from-green-900 to-blue-900 rounded-xl p-4">
            <h3 className="text-lg font-semibold text-white mb-3">✨ Benefits</h3>
            <div className="space-y-2 text-sm text-gray-200">
              <div className="flex items-start space-x-2">
                <span>✓</span>
                <p>Industry-leading {currentAPY}% APY</p>
              </div>
              <div className="flex items-start space-x-2">
                <span>✓</span>
                <p>FDIC insured up to $250,000</p>
              </div>
              <div className="flex items-start space-x-2">
                <span>✓</span>
                <p>No minimum balance required</p>
              </div>
              <div className="flex items-start space-x-2">
                <span>✓</span>
                <p>No monthly maintenance fees</p>
              </div>
              <div className="flex items-start space-x-2">
                <span>✓</span>
                <p>Interest paid monthly</p>
              </div>
              <div className="flex items-start space-x-2">
                <span>✓</span>
                <p>Instant transfers to trading account</p>
              </div>
            </div>
          </div>

          {/* Rate Comparison */}
          <div className="bg-gray-900 rounded-xl p-4">
            <h3 className="text-lg font-semibold text-white mb-3">📊 Rate Comparison</h3>
            <div className="space-y-3">
              <div className="bg-green-900/30 border border-green-600/50 rounded-lg p-3">
                <div className="flex items-center justify-between">
                  <span className="text-green-300 font-medium">Elson Savings</span>
                  <span className="text-green-400 font-bold">{currentAPY}%</span>
                </div>
              </div>
              <div className="bg-gray-800 rounded-lg p-3">
                <div className="flex items-center justify-between">
                  <span className="text-gray-400">National Average</span>
                  <span className="text-gray-400">0.46%</span>
                </div>
              </div>
              <div className="bg-gray-800 rounded-lg p-3">
                <div className="flex items-center justify-between">
                  <span className="text-gray-400">Traditional Banks</span>
                  <span className="text-gray-400">0.01%</span>
                </div>
              </div>
            </div>
            <p className="text-xs text-gray-500 mt-3">
              Earn up to 450x more than traditional banks
            </p>
          </div>
        </div>
      </div>
    </div>
  );
};

export default SavingsPage;
