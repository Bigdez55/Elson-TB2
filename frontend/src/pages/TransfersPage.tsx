import React, { useState } from 'react';

interface LinkedAccount {
  id: string;
  bankName: string;
  accountType: 'Checking' | 'Savings';
  lastFour: string;
  isPrimary: boolean;
  status: 'Active' | 'Pending' | 'Inactive';
}

interface Transfer {
  id: string;
  type: 'Deposit' | 'Withdrawal';
  amount: number;
  account: string;
  status: 'Completed' | 'Pending' | 'Failed';
  date: string;
  transferMethod: 'ACH' | 'Wire' | 'Instant';
}

const TransfersPage: React.FC = () => {
  const [activeTab, setActiveTab] = useState<'deposit' | 'withdraw' | 'history'>('deposit');
  const [amount, setAmount] = useState<string>('');
  const [selectedAccount, setSelectedAccount] = useState<string>('');
  const [transferSpeed, setTransferSpeed] = useState<'standard' | 'instant'>('standard');

  const linkedAccounts: LinkedAccount[] = [
    { id: '1', bankName: 'Chase Bank', accountType: 'Checking', lastFour: '4521', isPrimary: true, status: 'Active' },
    { id: '2', bankName: 'Bank of America', accountType: 'Savings', lastFour: '7890', isPrimary: false, status: 'Active' },
    { id: '3', bankName: 'Wells Fargo', accountType: 'Checking', lastFour: '2341', isPrimary: false, status: 'Pending' },
  ];

  const transferHistory: Transfer[] = [
    { id: '1', type: 'Deposit', amount: 5000, account: 'Chase ****4521', status: 'Completed', date: '2024-03-01', transferMethod: 'ACH' },
    { id: '2', type: 'Withdrawal', amount: 1200, account: 'BofA ****7890', status: 'Completed', date: '2024-02-28', transferMethod: 'ACH' },
    { id: '3', type: 'Deposit', amount: 500, account: 'Chase ****4521', status: 'Pending', date: '2024-03-05', transferMethod: 'Instant' },
    { id: '4', type: 'Deposit', amount: 10000, account: 'Chase ****4521', status: 'Completed', date: '2024-02-15', transferMethod: 'Wire' },
    { id: '5', type: 'Withdrawal', amount: 2500, account: 'BofA ****7890', status: 'Completed', date: '2024-02-10', transferMethod: 'ACH' },
  ];

  const handleTransfer = () => {
    alert(`Transfer ${activeTab} of $${amount} initiated via ${transferSpeed} method`);
    setAmount('');
  };

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'Completed': return 'text-green-400 bg-green-900/30';
      case 'Pending': return 'text-yellow-400 bg-yellow-900/30';
      case 'Failed': return 'text-red-400 bg-red-900/30';
      default: return 'text-gray-400 bg-gray-900/30';
    }
  };

  return (
    <div className="bg-gray-800 min-h-screen p-6">
      <div className="mb-8">
        <h1 className="text-3xl font-bold text-white mb-2">Transfers</h1>
        <p className="text-gray-400">
          Move money in and out of your Elson account
        </p>
      </div>

      {/* Quick Stats */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mb-6">
        <div className="bg-gray-900 rounded-xl p-4">
          <div className="text-gray-400 text-sm">Available Balance</div>
          <div className="text-2xl font-bold text-white mt-1">$25,450.00</div>
          <div className="text-green-400 text-xs mt-1">+$500 this month</div>
        </div>
        <div className="bg-gray-900 rounded-xl p-4">
          <div className="text-gray-400 text-sm">Pending Transfers</div>
          <div className="text-2xl font-bold text-yellow-400 mt-1">$500.00</div>
          <div className="text-gray-400 text-xs mt-1">1 transfer pending</div>
        </div>
        <div className="bg-gray-900 rounded-xl p-4">
          <div className="text-gray-400 text-sm">Linked Accounts</div>
          <div className="text-2xl font-bold text-white mt-1">{linkedAccounts.filter(a => a.status === 'Active').length}</div>
          <div className="text-gray-400 text-xs mt-1">{linkedAccounts.length} total accounts</div>
        </div>
      </div>

      {/* Tab Navigation */}
      <div className="mb-6">
        <div className="flex space-x-2 bg-gray-900 p-2 rounded-lg inline-flex">
          <button
            onClick={() => setActiveTab('deposit')}
            className={`px-4 py-2 rounded-lg transition-colors ${
              activeTab === 'deposit' ? 'bg-green-600 text-white' : 'text-gray-400 hover:bg-gray-800'
            }`}
          >
            💵 Deposit
          </button>
          <button
            onClick={() => setActiveTab('withdraw')}
            className={`px-4 py-2 rounded-lg transition-colors ${
              activeTab === 'withdraw' ? 'bg-red-600 text-white' : 'text-gray-400 hover:bg-gray-800'
            }`}
          >
            💸 Withdraw
          </button>
          <button
            onClick={() => setActiveTab('history')}
            className={`px-4 py-2 rounded-lg transition-colors ${
              activeTab === 'history' ? 'bg-purple-600 text-white' : 'text-gray-400 hover:bg-gray-800'
            }`}
          >
            📜 History
          </button>
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Main Content */}
        <div className="lg:col-span-2">
          {(activeTab === 'deposit' || activeTab === 'withdraw') && (
            <div className="bg-gray-900 rounded-xl p-6">
              <h2 className="text-xl font-semibold text-white mb-6">
                {activeTab === 'deposit' ? '💵 Deposit Funds' : '💸 Withdraw Funds'}
              </h2>

              {/* Amount Input */}
              <div className="mb-6">
                <label className="block text-sm font-medium text-gray-400 mb-2">
                  Amount
                </label>
                <div className="relative">
                  <span className="absolute left-4 top-1/2 transform -translate-y-1/2 text-gray-400 text-lg">$</span>
                  <input
                    type="number"
                    value={amount}
                    onChange={(e) => setAmount(e.target.value)}
                    placeholder="0.00"
                    className="w-full bg-gray-800 text-white pl-10 pr-4 py-3 rounded-lg border border-gray-700 focus:border-purple-500 focus:outline-none text-lg"
                  />
                </div>
              </div>

              {/* Account Selection */}
              <div className="mb-6">
                <label className="block text-sm font-medium text-gray-400 mb-2">
                  {activeTab === 'deposit' ? 'From Account' : 'To Account'}
                </label>
                <select
                  value={selectedAccount}
                  onChange={(e) => setSelectedAccount(e.target.value)}
                  className="w-full bg-gray-800 text-white px-4 py-3 rounded-lg border border-gray-700 focus:border-purple-500 focus:outline-none"
                >
                  <option value="">Select an account</option>
                  {linkedAccounts.filter(a => a.status === 'Active').map((account) => (
                    <option key={account.id} value={account.id}>
                      {account.bankName} - {account.accountType} ****{account.lastFour}
                      {account.isPrimary && ' (Primary)'}
                    </option>
                  ))}
                </select>
              </div>

              {/* Transfer Speed */}
              <div className="mb-6">
                <label className="block text-sm font-medium text-gray-400 mb-3">
                  Transfer Speed
                </label>
                <div className="space-y-3">
                  <div
                    onClick={() => setTransferSpeed('standard')}
                    className={`p-4 rounded-lg border-2 cursor-pointer transition-colors ${
                      transferSpeed === 'standard'
                        ? 'border-purple-500 bg-purple-900/20'
                        : 'border-gray-700 hover:border-gray-600'
                    }`}
                  >
                    <div className="flex items-center justify-between">
                      <div>
                        <div className="text-white font-medium">Standard (ACH)</div>
                        <div className="text-sm text-gray-400">3-5 business days • Free</div>
                      </div>
                      <div className="text-green-400 font-semibold">$0.00</div>
                    </div>
                  </div>
                  <div
                    onClick={() => setTransferSpeed('instant')}
                    className={`p-4 rounded-lg border-2 cursor-pointer transition-colors ${
                      transferSpeed === 'instant'
                        ? 'border-purple-500 bg-purple-900/20'
                        : 'border-gray-700 hover:border-gray-600'
                    }`}
                  >
                    <div className="flex items-center justify-between">
                      <div>
                        <div className="text-white font-medium">⚡ Instant</div>
                        <div className="text-sm text-gray-400">Within minutes • 1.5% fee</div>
                      </div>
                      <div className="text-yellow-400 font-semibold">
                        ${amount ? ((parseFloat(amount) * 0.015).toFixed(2)) : '0.00'}
                      </div>
                    </div>
                  </div>
                </div>
              </div>

              {/* Submit Button */}
              <button
                onClick={handleTransfer}
                disabled={!amount || !selectedAccount}
                className={`w-full py-3 rounded-lg font-medium transition-colors ${
                  amount && selectedAccount
                    ? `${activeTab === 'deposit' ? 'bg-green-600 hover:bg-green-700' : 'bg-red-600 hover:bg-red-700'} text-white`
                    : 'bg-gray-700 text-gray-500 cursor-not-allowed'
                }`}
              >
                {activeTab === 'deposit' ? 'Deposit Funds' : 'Withdraw Funds'}
              </button>
            </div>
          )}

          {activeTab === 'history' && (
            <div className="bg-gray-900 rounded-xl overflow-hidden">
              <div className="p-4 border-b border-gray-700">
                <h2 className="text-xl font-semibold text-white">Transfer History</h2>
              </div>
              <div className="divide-y divide-gray-700">
                {transferHistory.map((transfer) => (
                  <div key={transfer.id} className="p-4 hover:bg-gray-800 transition-colors">
                    <div className="flex items-center justify-between">
                      <div className="flex items-center space-x-4">
                        <div className={`w-10 h-10 rounded-lg flex items-center justify-center ${
                          transfer.type === 'Deposit' ? 'bg-green-900/30' : 'bg-red-900/30'
                        }`}>
                          <span className="text-xl">{transfer.type === 'Deposit' ? '💵' : '💸'}</span>
                        </div>
                        <div>
                          <div className="text-white font-medium">{transfer.type}</div>
                          <div className="text-sm text-gray-400">{transfer.account}</div>
                          <div className="text-xs text-gray-500">{transfer.transferMethod}</div>
                        </div>
                      </div>
                      <div className="text-right">
                        <div className={`text-lg font-semibold ${
                          transfer.type === 'Deposit' ? 'text-green-400' : 'text-red-400'
                        }`}>
                          {transfer.type === 'Deposit' ? '+' : '-'}${transfer.amount.toLocaleString()}
                        </div>
                        <div className="text-sm text-gray-400">{new Date(transfer.date).toLocaleDateString()}</div>
                        <span className={`inline-block px-2 py-1 rounded text-xs font-medium ${getStatusColor(transfer.status)}`}>
                          {transfer.status}
                        </span>
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          )}
        </div>

        {/* Sidebar */}
        <div className="space-y-6">
          {/* Linked Accounts */}
          <div className="bg-gray-900 rounded-xl p-4">
            <div className="flex items-center justify-between mb-4">
              <h3 className="text-lg font-semibold text-white">🏦 Linked Accounts</h3>
              <button className="text-purple-400 text-sm hover:text-purple-300">+ Add</button>
            </div>
            <div className="space-y-3">
              {linkedAccounts.map((account) => (
                <div key={account.id} className="bg-gray-800 rounded-lg p-3">
                  <div className="flex items-start justify-between">
                    <div>
                      <div className="text-white font-medium">{account.bankName}</div>
                      <div className="text-sm text-gray-400">
                        {account.accountType} ••••{account.lastFour}
                      </div>
                      {account.isPrimary && (
                        <span className="text-xs text-purple-400">⭐ Primary</span>
                      )}
                    </div>
                    <span className={`text-xs px-2 py-1 rounded ${getStatusColor(account.status)}`}>
                      {account.status}
                    </span>
                  </div>
                </div>
              ))}
            </div>
          </div>

          {/* Security Info */}
          <div className="bg-gradient-to-br from-blue-900 to-indigo-900 rounded-xl p-4">
            <h3 className="text-lg font-semibold text-white mb-2">🔒 Secure Transfers</h3>
            <div className="text-sm text-gray-300 space-y-2">
              <div className="flex items-start space-x-2">
                <span>✓</span>
                <p>Bank-level encryption</p>
              </div>
              <div className="flex items-start space-x-2">
                <span>✓</span>
                <p>FDIC insured up to $250,000</p>
              </div>
              <div className="flex items-start space-x-2">
                <span>✓</span>
                <p>Two-factor authentication</p>
              </div>
            </div>
          </div>

          {/* Limits */}
          <div className="bg-gray-900 rounded-xl p-4">
            <h3 className="text-lg font-semibold text-white mb-3">📊 Transfer Limits</h3>
            <div className="space-y-3 text-sm">
              <div>
                <div className="flex justify-between text-gray-400 mb-1">
                  <span>Daily Limit</span>
                  <span>$15,000 / $25,000</span>
                </div>
                <div className="w-full bg-gray-700 rounded-full h-2">
                  <div className="bg-blue-500 rounded-full h-2" style={{ width: '60%' }} />
                </div>
              </div>
              <div>
                <div className="flex justify-between text-gray-400 mb-1">
                  <span>Monthly Limit</span>
                  <span>$50,000 / $100,000</span>
                </div>
                <div className="w-full bg-gray-700 rounded-full h-2">
                  <div className="bg-green-500 rounded-full h-2" style={{ width: '50%' }} />
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default TransfersPage;
