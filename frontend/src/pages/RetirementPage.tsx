import React, { useState } from 'react';

interface RetirementAccount {
  id: string;
  type: 'Traditional IRA' | 'Roth IRA' | '401(k) Rollover';
  balance: number;
  contributions: number;
  earnings: number;
  taxStatus: string;
}

interface Contribution {
  id: string;
  date: string;
  amount: number;
  type: string;
}

const RetirementPage: React.FC = () => {
  const [selectedAccount, setSelectedAccount] = useState<string>('traditional');
  const [contributionAmount, setContributionAmount] = useState<string>('');
  const [retirementAge, setRetirementAge] = useState<string>('65');
  const [monthlyContribution, setMonthlyContribution] = useState<string>('500');

  const currentAge = 35;
  const totalBalance = 125450.75;
  const ytdContributions = 6500;
  const ytdEarnings = 8450.50;

  const accounts: RetirementAccount[] = [
    {
      id: '1',
      type: 'Traditional IRA',
      balance: 75450.25,
      contributions: 52000,
      earnings: 23450.25,
      taxStatus: 'Tax-Deferred',
    },
    {
      id: '2',
      type: 'Roth IRA',
      balance: 50000.50,
      contributions: 40000,
      earnings: 10000.50,
      taxStatus: 'Tax-Free',
    },
  ];

  const recentContributions: Contribution[] = [
    { id: '1', date: '2024-03-01', amount: 500, type: 'Monthly Auto' },
    { id: '2', date: '2024-02-01', amount: 500, type: 'Monthly Auto' },
    { id: '3', date: '2024-01-15', amount: 2000, type: 'One-Time' },
    { id: '4', date: '2024-01-01', amount: 500, type: 'Monthly Auto' },
    { id: '5', date: '2023-12-01', amount: 500, type: 'Monthly Auto' },
  ];

  const contributionLimits = {
    traditionalIRA: 7000,
    rothIRA: 7000,
    combined: 7000,
    catchUp: 1000, // Age 50+
  };

  const calculateProjection = () => {
    const currentAge = 35;
    const targetAge = parseInt(retirementAge) || 65;
    const years = targetAge - currentAge;
    const monthly = parseFloat(monthlyContribution) || 500;
    const annualReturn = 0.07; // 7% average return

    let balance = totalBalance;
    for (let year = 0; year < years; year++) {
      balance = balance * (1 + annualReturn) + (monthly * 12);
    }

    return Math.round(balance);
  };

  const projectedBalance = calculateProjection();

  const handleContribute = () => {
    alert(`Contributing $${contributionAmount} to retirement account`);
    setContributionAmount('');
  };

  return (
    <div className="bg-gray-800 min-h-screen p-6">
      <div className="mb-8">
        <h1 className="text-3xl font-bold text-white mb-2">Retirement Accounts</h1>
        <p className="text-gray-400">
          Tax-advantaged investing for your future with Traditional IRA, Roth IRA, and 401(k) rollover options
        </p>
      </div>

      {/* Account Overview */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4 mb-6">
        <div className="bg-gradient-to-br from-green-900 to-green-800 rounded-xl p-4">
          <div className="text-green-300 text-sm mb-1">Total Balance</div>
          <div className="text-3xl font-bold text-white">${totalBalance.toLocaleString()}</div>
          <div className="text-green-200 text-xs mt-1">All accounts</div>
        </div>
        <div className="bg-gradient-to-br from-blue-900 to-blue-800 rounded-xl p-4">
          <div className="text-blue-300 text-sm mb-1">YTD Contributions</div>
          <div className="text-3xl font-bold text-white">${ytdContributions.toLocaleString()}</div>
          <div className="text-blue-200 text-xs mt-1">${contributionLimits.combined - ytdContributions} remaining</div>
        </div>
        <div className="bg-gradient-to-br from-purple-900 to-purple-800 rounded-xl p-4">
          <div className="text-purple-300 text-sm mb-1">YTD Earnings</div>
          <div className="text-3xl font-bold text-white">${ytdEarnings.toLocaleString()}</div>
          <div className="text-purple-200 text-xs mt-1">+{((ytdEarnings / (totalBalance - ytdEarnings)) * 100).toFixed(2)}% return</div>
        </div>
        <div className="bg-gradient-to-br from-yellow-900 to-yellow-800 rounded-xl p-4">
          <div className="text-yellow-300 text-sm mb-1">At Age {retirementAge}</div>
          <div className="text-3xl font-bold text-white">${(projectedBalance / 1000).toFixed(0)}K</div>
          <div className="text-yellow-200 text-xs mt-1">Projected balance</div>
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Main Content */}
        <div className="lg:col-span-2 space-y-6">
          {/* Make a Contribution */}
          <div className="bg-gray-900 rounded-xl p-6">
            <h2 className="text-xl font-semibold text-white mb-4">💰 Make a Contribution</h2>
            <div className="space-y-4">
              <div>
                <label className="block text-sm font-medium text-gray-400 mb-2">
                  Select Account
                </label>
                <select className="w-full bg-gray-800 text-white px-4 py-3 rounded-lg border border-gray-700 focus:border-purple-500 focus:outline-none">
                  <option value="traditional">Traditional IRA - $75,450.25</option>
                  <option value="roth">Roth IRA - $50,000.50</option>
                </select>
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-400 mb-2">
                  Contribution Amount
                </label>
                <div className="relative">
                  <span className="absolute left-4 top-1/2 transform -translate-y-1/2 text-gray-400 text-lg">$</span>
                  <input
                    type="number"
                    value={contributionAmount}
                    onChange={(e) => setContributionAmount(e.target.value)}
                    placeholder="0.00"
                    className="w-full bg-gray-800 text-white pl-10 pr-4 py-3 rounded-lg border border-gray-700 focus:border-purple-500 focus:outline-none text-lg"
                  />
                </div>
                <p className="text-xs text-gray-500 mt-1">
                  ${contributionLimits.combined - ytdContributions} remaining for {new Date().getFullYear()}
                </p>
              </div>
              <button
                onClick={handleContribute}
                disabled={!contributionAmount}
                className={`w-full py-3 rounded-lg font-medium transition-colors ${
                  contributionAmount
                    ? 'bg-green-600 hover:bg-green-700 text-white'
                    : 'bg-gray-700 text-gray-500 cursor-not-allowed'
                }`}
              >
                Contribute Now
              </button>
            </div>
          </div>

          {/* Retirement Accounts */}
          <div className="bg-gray-900 rounded-xl p-6">
            <h2 className="text-xl font-semibold text-white mb-4">🏦 Your Accounts</h2>
            <div className="space-y-4">
              {accounts.map((account) => (
                <div key={account.id} className="bg-gray-800 rounded-lg p-4">
                  <div className="flex items-start justify-between mb-3">
                    <div>
                      <h3 className="text-lg font-semibold text-white">{account.type}</h3>
                      <p className="text-sm text-gray-400">{account.taxStatus}</p>
                    </div>
                    <div className="text-right">
                      <div className="text-2xl font-bold text-white">${account.balance.toLocaleString()}</div>
                    </div>
                  </div>
                  <div className="grid grid-cols-2 gap-4">
                    <div className="bg-gray-900 rounded-lg p-3">
                      <div className="text-xs text-gray-400 mb-1">Contributions</div>
                      <div className="text-lg font-semibold text-blue-400">${account.contributions.toLocaleString()}</div>
                    </div>
                    <div className="bg-gray-900 rounded-lg p-3">
                      <div className="text-xs text-gray-400 mb-1">Earnings</div>
                      <div className="text-lg font-semibold text-green-400">${account.earnings.toLocaleString()}</div>
                    </div>
                  </div>
                  <div className="mt-3 flex space-x-2">
                    <button className="flex-1 bg-purple-600 hover:bg-purple-700 text-white py-2 rounded-lg text-sm font-medium transition-colors">
                      View Holdings
                    </button>
                    <button className="flex-1 bg-gray-700 hover:bg-gray-600 text-white py-2 rounded-lg text-sm font-medium transition-colors">
                      Manage
                    </button>
                  </div>
                </div>
              ))}

              {/* Add Account CTA */}
              <div className="bg-gradient-to-r from-purple-900/50 to-blue-900/50 rounded-lg p-4 border border-purple-600/30">
                <div className="flex items-center justify-between">
                  <div>
                    <h4 className="text-white font-medium mb-1">401(k) Rollover</h4>
                    <p className="text-sm text-gray-400">Transfer your old 401(k) to Elson</p>
                  </div>
                  <button className="bg-purple-600 hover:bg-purple-700 text-white px-4 py-2 rounded-lg text-sm font-medium transition-colors">
                    Start Rollover
                  </button>
                </div>
              </div>
            </div>
          </div>

          {/* Recent Contributions */}
          <div className="bg-gray-900 rounded-xl overflow-hidden">
            <div className="p-4 border-b border-gray-700">
              <h2 className="text-xl font-semibold text-white">📊 Recent Contributions</h2>
            </div>
            <div className="divide-y divide-gray-700">
              {recentContributions.map((contribution) => (
                <div key={contribution.id} className="p-4 hover:bg-gray-800 transition-colors">
                  <div className="flex items-center justify-between">
                    <div>
                      <div className="text-white font-medium">Contribution</div>
                      <div className="text-sm text-gray-400">{new Date(contribution.date).toLocaleDateString()}</div>
                      <div className="text-xs text-purple-400">{contribution.type}</div>
                    </div>
                    <div className="text-right">
                      <div className="text-lg font-semibold text-green-400">+${contribution.amount.toFixed(2)}</div>
                    </div>
                  </div>
                </div>
              ))}
            </div>
          </div>
        </div>

        {/* Sidebar */}
        <div className="space-y-6">
          {/* Retirement Projection */}
          <div className="bg-gradient-to-br from-blue-900 to-indigo-900 rounded-xl p-4">
            <h3 className="text-lg font-semibold text-white mb-4">📈 Retirement Calculator</h3>
            <div className="space-y-4">
              <div>
                <label className="block text-sm font-medium text-blue-200 mb-2">Retirement Age</label>
                <input
                  type="number"
                  value={retirementAge}
                  onChange={(e) => setRetirementAge(e.target.value)}
                  className="w-full bg-white/10 backdrop-blur text-white px-4 py-2 rounded-lg border border-blue-500/30 focus:border-blue-500 focus:outline-none"
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-blue-200 mb-2">Monthly Contribution</label>
                <div className="relative">
                  <span className="absolute left-3 top-1/2 transform -translate-y-1/2 text-blue-200">$</span>
                  <input
                    type="number"
                    value={monthlyContribution}
                    onChange={(e) => setMonthlyContribution(e.target.value)}
                    className="w-full bg-white/10 backdrop-blur text-white pl-8 pr-4 py-2 rounded-lg border border-blue-500/30 focus:border-blue-500 focus:outline-none"
                  />
                </div>
              </div>

              <div className="bg-white/10 backdrop-blur rounded-lg p-4 border border-blue-500/30">
                <div className="text-blue-200 text-sm mb-1">Projected at Age {retirementAge}</div>
                <div className="text-3xl font-bold text-white mb-2">${(projectedBalance / 1000000).toFixed(2)}M</div>
                <div className="text-xs text-blue-200">
                  Based on 7% annual return
                </div>
              </div>

              <div className="space-y-2 text-sm">
                <div className="flex justify-between text-blue-200">
                  <span>Years to retirement:</span>
                  <span className="font-semibold">{parseInt(retirementAge) - currentAge}</span>
                </div>
                <div className="flex justify-between text-blue-200">
                  <span>Total contributions:</span>
                  <span className="font-semibold">${((parseInt(retirementAge) - currentAge) * parseFloat(monthlyContribution) * 12).toLocaleString()}</span>
                </div>
                <div className="flex justify-between text-green-300">
                  <span>Est. earnings:</span>
                  <span className="font-semibold">${(projectedBalance - totalBalance - ((parseInt(retirementAge) - currentAge) * parseFloat(monthlyContribution) * 12)).toLocaleString()}</span>
                </div>
              </div>
            </div>
          </div>

          {/* Contribution Limits */}
          <div className="bg-gray-900 rounded-xl p-4">
            <h3 className="text-lg font-semibold text-white mb-3">📋 {new Date().getFullYear()} Limits</h3>
            <div className="space-y-3">
              <div className="bg-gray-800 rounded-lg p-3">
                <div className="flex items-center justify-between mb-1">
                  <span className="text-gray-300 text-sm">IRA Contribution</span>
                  <span className="text-white font-semibold">${contributionLimits.traditionalIRA.toLocaleString()}</span>
                </div>
                <div className="w-full bg-gray-700 rounded-full h-2">
                  <div
                    className="bg-blue-500 rounded-full h-2"
                    style={{ width: `${(ytdContributions / contributionLimits.combined) * 100}%` }}
                  />
                </div>
                <div className="text-xs text-gray-500 mt-1">
                  ${ytdContributions} contributed
                </div>
              </div>
              <div className="bg-gray-800 rounded-lg p-3">
                <div className="flex items-center justify-between">
                  <span className="text-gray-300 text-sm">Catch-up (Age 50+)</span>
                  <span className="text-white font-semibold">+${contributionLimits.catchUp.toLocaleString()}</span>
                </div>
              </div>
            </div>
          </div>

          {/* Account Types */}
          <div className="bg-gray-900 rounded-xl p-4">
            <h3 className="text-lg font-semibold text-white mb-3">💡 Account Types</h3>
            <div className="space-y-3 text-sm">
              <div className="bg-gray-800 rounded-lg p-3">
                <div className="font-medium text-white mb-1">Traditional IRA</div>
                <p className="text-xs text-gray-400">Tax-deductible contributions, taxed at withdrawal</p>
              </div>
              <div className="bg-gray-800 rounded-lg p-3">
                <div className="font-medium text-white mb-1">Roth IRA</div>
                <p className="text-xs text-gray-400">After-tax contributions, tax-free withdrawals</p>
              </div>
              <div className="bg-gray-800 rounded-lg p-3">
                <div className="font-medium text-white mb-1">401(k) Rollover</div>
                <p className="text-xs text-gray-400">Transfer old employer plans to IRA</p>
              </div>
            </div>
          </div>

          {/* Benefits */}
          <div className="bg-gradient-to-br from-purple-900 to-blue-900 rounded-xl p-4">
            <h3 className="text-lg font-semibold text-white mb-3">✨ Benefits</h3>
            <div className="space-y-2 text-sm text-gray-200">
              <div className="flex items-start space-x-2">
                <span>✓</span>
                <p>Tax-advantaged growth</p>
              </div>
              <div className="flex items-start space-x-2">
                <span>✓</span>
                <p>No account minimums or fees</p>
              </div>
              <div className="flex items-start space-x-2">
                <span>✓</span>
                <p>Auto-invest with recurring contributions</p>
              </div>
              <div className="flex items-start space-x-2">
                <span>✓</span>
                <p>Free portfolio reviews</p>
              </div>
              <div className="flex items-start space-x-2">
                <span>✓</span>
                <p>Access to target-date funds</p>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default RetirementPage;
