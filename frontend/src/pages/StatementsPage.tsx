import React, { useState } from 'react';
import { EmptyState } from '../components/common/ErrorDisplay';

interface Document {
  id: string;
  type: 'Monthly Statement' | 'Trade Confirmation' | 'Tax Document';
  date: string;
  description: string;
  size: string;
  url: string;
  status: 'Available' | 'Processing';
}

const StatementsPage: React.FC = () => {
  const [selectedType, setSelectedType] = useState<string>('all');
  const [selectedYear, setSelectedYear] = useState<string>('2024');

  const documents: Document[] = [
    { id: '1', type: 'Monthly Statement', date: '2024-03-01', description: 'March 2024 Account Statement', size: '2.4 MB', url: '#', status: 'Available' },
    { id: '2', type: 'Monthly Statement', date: '2024-02-01', description: 'February 2024 Account Statement', size: '2.1 MB', url: '#', status: 'Available' },
    { id: '3', type: 'Tax Document', date: '2024-01-31', description: '2023 Form 1099-B', size: '1.8 MB', url: '#', status: 'Available' },
    { id: '4', type: 'Trade Confirmation', date: '2024-03-15', description: 'AAPL - Buy 100 shares at $175.50', size: '156 KB', url: '#', status: 'Available' },
    { id: '5', type: 'Trade Confirmation', date: '2024-03-14', description: 'TSLA - Sell 50 shares at $242.80', size: '142 KB', url: '#', status: 'Available' },
    { id: '6', type: 'Monthly Statement', date: '2024-01-01', description: 'January 2024 Account Statement', size: '1.9 MB', url: '#', status: 'Available' },
    { id: '7', type: 'Trade Confirmation', date: '2024-03-10', description: 'NVDA - Buy 25 shares at $880.00', size: '148 KB', url: '#', status: 'Available' },
    { id: '8', type: 'Tax Document', date: '2024-01-31', description: '2023 Form 1099-DIV', size: '892 KB', url: '#', status: 'Available' },
    { id: '9', type: 'Monthly Statement', date: '2023-12-01', description: 'December 2023 Account Statement', size: '2.3 MB', url: '#', status: 'Available' },
    { id: '10', type: 'Trade Confirmation', date: '2024-03-05', description: 'MSFT - Buy 30 shares at $420.50', size: '151 KB', url: '#', status: 'Available' },
  ];

  const filteredDocuments = documents.filter(doc => {
    const matchesType = selectedType === 'all' || doc.type === selectedType;
    const matchesYear = doc.date.startsWith(selectedYear);
    return matchesType && matchesYear;
  });

  const getDocumentIcon = (type: string) => {
    switch (type) {
      case 'Monthly Statement': return '📊';
      case 'Trade Confirmation': return '📋';
      case 'Tax Document': return '📄';
      default: return '📁';
    }
  };

  const documentsByType = {
    monthly: documents.filter(d => d.type === 'Monthly Statement').length,
    trades: documents.filter(d => d.type === 'Trade Confirmation').length,
    tax: documents.filter(d => d.type === 'Tax Document').length,
  };

  return (
    <div className="bg-gray-800 min-h-screen p-6">
      <div className="mb-8">
        <h1 className="text-3xl font-bold text-white mb-2">Statements & Documents</h1>
        <p className="text-gray-400">
          Access your account statements, trade confirmations, and tax documents
        </p>
      </div>

      {/* Quick Stats */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4 mb-6">
        <div className="bg-gray-900 rounded-xl p-4">
          <div className="text-gray-400 text-sm">Total Documents</div>
          <div className="text-2xl font-bold text-white mt-1">{documents.length}</div>
          <div className="text-purple-400 text-xs mt-1">All time</div>
        </div>
        <div className="bg-gray-900 rounded-xl p-4">
          <div className="text-gray-400 text-sm">Monthly Statements</div>
          <div className="text-2xl font-bold text-blue-400 mt-1">{documentsByType.monthly}</div>
          <div className="text-gray-400 text-xs mt-1">Account summaries</div>
        </div>
        <div className="bg-gray-900 rounded-xl p-4">
          <div className="text-gray-400 text-sm">Trade Confirmations</div>
          <div className="text-2xl font-bold text-green-400 mt-1">{documentsByType.trades}</div>
          <div className="text-gray-400 text-xs mt-1">Transaction records</div>
        </div>
        <div className="bg-gray-900 rounded-xl p-4">
          <div className="text-gray-400 text-sm">Tax Documents</div>
          <div className="text-2xl font-bold text-yellow-400 mt-1">{documentsByType.tax}</div>
          <div className="text-gray-400 text-xs mt-1">IRS forms</div>
        </div>
      </div>

      {/* Filters */}
      <div className="mb-6 flex flex-wrap gap-4">
        <div>
          <label className="block text-sm font-medium text-gray-400 mb-2">Document Type</label>
          <select
            value={selectedType}
            onChange={(e) => setSelectedType(e.target.value)}
            className="bg-gray-900 text-white px-4 py-2 rounded-lg border border-gray-700 focus:border-purple-500 focus:outline-none"
          >
            <option value="all">All Documents</option>
            <option value="Monthly Statement">Monthly Statements</option>
            <option value="Trade Confirmation">Trade Confirmations</option>
            <option value="Tax Document">Tax Documents</option>
          </select>
        </div>
        <div>
          <label className="block text-sm font-medium text-gray-400 mb-2">Year</label>
          <select
            value={selectedYear}
            onChange={(e) => setSelectedYear(e.target.value)}
            className="bg-gray-900 text-white px-4 py-2 rounded-lg border border-gray-700 focus:border-purple-500 focus:outline-none"
          >
            <option value="2024">2024</option>
            <option value="2023">2023</option>
            <option value="2022">2022</option>
          </select>
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Documents List */}
        <div className="lg:col-span-2">
          <div className="bg-gray-900 rounded-xl overflow-hidden">
            <div className="p-4 border-b border-gray-700 flex items-center justify-between">
              <h2 className="text-xl font-semibold text-white">
                Documents ({filteredDocuments.length})
              </h2>
              <button className="bg-purple-600 hover:bg-purple-700 text-white px-4 py-2 rounded-lg text-sm font-medium transition-colors">
                📥 Download All
              </button>
            </div>
            <div className="divide-y divide-gray-700">
              {filteredDocuments.length === 0 ? (
                <EmptyState
                  icon={
                    <svg className="w-16 h-16" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="1.5" d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
                    </svg>
                  }
                  title="No Documents Found"
                  message={selectedType === 'all'
                    ? `No documents available for ${selectedYear}. Your statements will appear here after your first trade.`
                    : `No ${selectedType.toLowerCase()}s found for ${selectedYear}.`
                  }
                />
              ) : (
                filteredDocuments.map((doc) => (
                  <div key={doc.id} className="p-4 hover:bg-gray-800 transition-colors">
                    <div className="flex items-center justify-between">
                      <div className="flex items-center space-x-4 flex-1">
                        <div className="w-12 h-12 bg-gradient-to-br from-purple-500 to-blue-500 rounded-lg flex items-center justify-center flex-shrink-0">
                          <span className="text-2xl">{getDocumentIcon(doc.type)}</span>
                        </div>
                        <div className="flex-1">
                          <div className="text-white font-medium">{doc.description}</div>
                          <div className="flex items-center space-x-3 text-sm text-gray-400 mt-1">
                            <span className="text-purple-400">{doc.type}</span>
                            <span>•</span>
                            <span>{new Date(doc.date).toLocaleDateString()}</span>
                            <span>•</span>
                            <span>{doc.size}</span>
                          </div>
                        </div>
                      </div>
                      <div className="flex items-center space-x-2">
                        <button className="bg-gray-700 hover:bg-gray-600 text-white p-2 rounded-lg transition-colors">
                          <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 12a3 3 0 11-6 0 3 3 0 016 0z" />
                            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M2.458 12C3.732 7.943 7.523 5 12 5c4.478 0 8.268 2.943 9.542 7-1.274 4.057-5.064 7-9.542 7-4.477 0-8.268-2.943-9.542-7z" />
                          </svg>
                        </button>
                        <button className="bg-purple-600 hover:bg-purple-700 text-white px-4 py-2 rounded-lg text-sm font-medium transition-colors">
                          Download
                        </button>
                      </div>
                    </div>
                  </div>
                ))
              )}
            </div>
          </div>
        </div>

        {/* Sidebar */}
        <div className="space-y-6">
          {/* Tax Center */}
          <div className="bg-gradient-to-br from-yellow-900 to-orange-900 rounded-xl p-4">
            <h3 className="text-lg font-semibold text-white mb-2">📋 Tax Center</h3>
            <p className="text-sm text-gray-200 mb-4">
              Your 2023 tax documents are ready for download
            </p>
            <div className="space-y-2">
              <button className="w-full bg-white/20 hover:bg-white/30 backdrop-blur text-white px-4 py-2 rounded-lg text-sm font-medium transition-colors">
                Download 1099-B
              </button>
              <button className="w-full bg-white/20 hover:bg-white/30 backdrop-blur text-white px-4 py-2 rounded-lg text-sm font-medium transition-colors">
                Download 1099-DIV
              </button>
              <button className="w-full bg-white/20 hover:bg-white/30 backdrop-blur text-white px-4 py-2 rounded-lg text-sm font-medium transition-colors">
                Tax Summary Report
              </button>
            </div>
          </div>

          {/* Document Breakdown */}
          <div className="bg-gray-900 rounded-xl p-4">
            <h3 className="text-lg font-semibold text-white mb-4">📊 Document Breakdown</h3>
            <div className="space-y-3">
              <div className="flex items-center justify-between">
                <div className="flex items-center space-x-2">
                  <span className="text-2xl">📊</span>
                  <span className="text-gray-300 text-sm">Monthly Statements</span>
                </div>
                <span className="text-white font-semibold">{documentsByType.monthly}</span>
              </div>
              <div className="flex items-center justify-between">
                <div className="flex items-center space-x-2">
                  <span className="text-2xl">📋</span>
                  <span className="text-gray-300 text-sm">Trade Confirmations</span>
                </div>
                <span className="text-white font-semibold">{documentsByType.trades}</span>
              </div>
              <div className="flex items-center justify-between">
                <div className="flex items-center space-x-2">
                  <span className="text-2xl">📄</span>
                  <span className="text-gray-300 text-sm">Tax Documents</span>
                </div>
                <span className="text-white font-semibold">{documentsByType.tax}</span>
              </div>
            </div>
          </div>

          {/* Delivery Preferences */}
          <div className="bg-gray-900 rounded-xl p-4">
            <h3 className="text-lg font-semibold text-white mb-3">⚙️ Delivery Preferences</h3>
            <div className="space-y-3">
              <div className="flex items-center justify-between">
                <span className="text-gray-300 text-sm">Email Notifications</span>
                <label className="relative inline-flex items-center cursor-pointer">
                  <input type="checkbox" className="sr-only peer" defaultChecked />
                  <div className="w-11 h-6 bg-gray-700 peer-focus:outline-none rounded-full peer peer-checked:after:translate-x-full peer-checked:after:border-white after:content-[''] after:absolute after:top-[2px] after:left-[2px] after:bg-white after:border-gray-300 after:border after:rounded-full after:h-5 after:w-5 after:transition-all peer-checked:bg-purple-600"></div>
                </label>
              </div>
              <div className="flex items-center justify-between">
                <span className="text-gray-300 text-sm">Paperless Statements</span>
                <label className="relative inline-flex items-center cursor-pointer">
                  <input type="checkbox" className="sr-only peer" defaultChecked />
                  <div className="w-11 h-6 bg-gray-700 peer-focus:outline-none rounded-full peer peer-checked:after:translate-x-full peer-checked:after:border-white after:content-[''] after:absolute after:top-[2px] after:left-[2px] after:bg-white after:border-gray-300 after:border after:rounded-full after:h-5 after:w-5 after:transition-all peer-checked:bg-purple-600"></div>
                </label>
              </div>
              <div className="flex items-center justify-between">
                <span className="text-gray-300 text-sm">Trade Confirmations</span>
                <label className="relative inline-flex items-center cursor-pointer">
                  <input type="checkbox" className="sr-only peer" defaultChecked />
                  <div className="w-11 h-6 bg-gray-700 peer-focus:outline-none rounded-full peer peer-checked:after:translate-x-full peer-checked:after:border-white after:content-[''] after:absolute after:top-[2px] after:left-[2px] after:bg-white after:border-gray-300 after:border after:rounded-full after:h-5 after:w-5 after:transition-all peer-checked:bg-purple-600"></div>
                </label>
              </div>
            </div>
          </div>

          {/* Help */}
          <div className="bg-gray-900 rounded-xl p-4">
            <h3 className="text-lg font-semibold text-white mb-3">💡 Need Help?</h3>
            <div className="text-sm text-gray-300 space-y-2">
              <p>• Statements are generated monthly</p>
              <p>• Trade confirmations sent after each trade</p>
              <p>• Tax documents available by Jan 31st</p>
              <p>• Contact support for missing documents</p>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default StatementsPage;
