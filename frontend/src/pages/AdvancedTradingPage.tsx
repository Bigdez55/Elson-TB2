import React, { useState } from 'react';
import { useSelector } from 'react-redux';
import { RootState } from '../store/store';
import AdvancedTradingDashboard from '../components/AdvancedTrading/AdvancedTradingDashboard';
import { AutoTradingSettings } from '../components/trading/AutoTradingSettings';

const AdvancedTradingPage: React.FC = () => {
  const { portfolio } = useSelector((state: RootState) => state.portfolio);
  const [activeTab, setActiveTab] = useState<'manual' | 'automated'>('automated');

  // Default portfolio ID - in a real app, this would come from the selected portfolio
  const portfolioId = portfolio?.id || 1;

  return (
    <div className="min-h-screen bg-gray-900">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        {/* Header */}
        <div className="mb-8">
          <h1 className="text-3xl font-bold text-white mb-2">Advanced Trading</h1>
          <p className="text-gray-400">
            Automated strategies and advanced trading features
          </p>
        </div>

        {/* Tab Navigation */}
        <div className="flex gap-4 mb-6 border-b border-gray-700">
          <button
            onClick={() => setActiveTab('automated')}
            className={`pb-4 px-2 font-medium transition-colors relative ${
              activeTab === 'automated'
                ? 'text-purple-400'
                : 'text-gray-400 hover:text-gray-300'
            }`}
          >
            Automated Trading
            {activeTab === 'automated' && (
              <div className="absolute bottom-0 left-0 right-0 h-0.5 bg-purple-400" />
            )}
          </button>
          <button
            onClick={() => setActiveTab('manual')}
            className={`pb-4 px-2 font-medium transition-colors relative ${
              activeTab === 'manual'
                ? 'text-purple-400'
                : 'text-gray-400 hover:text-gray-300'
            }`}
          >
            Manual Strategies
            {activeTab === 'manual' && (
              <div className="absolute bottom-0 left-0 right-0 h-0.5 bg-purple-400" />
            )}
          </button>
        </div>

        {/* Content */}
        {activeTab === 'automated' ? (
          <AutoTradingSettings portfolioId={portfolioId} />
        ) : (
          <div className="bg-gray-900">
            <AdvancedTradingDashboard portfolioId={portfolioId} />
          </div>
        )}
      </div>
    </div>
  );
};

export default AdvancedTradingPage;