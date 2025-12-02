import React, { useState } from 'react';
import { Layout } from '../app/components/layout/Layout';
import { Header } from '../app/components/layout/Header';
import { RoundupTransactionList } from '../app/components/trading/RoundupTransactionList';
import { RoundupTransactionSummary } from '../app/components/trading/RoundupTransactionSummary';
import useTheme from '../app/hooks/useTheme';

const RoundupTransactionsPage: React.FC = () => {
  const { darkMode } = useTheme();
  const [refreshKey, setRefreshKey] = useState(0);
  
  const handleRefresh = () => {
    setRefreshKey(prev => prev + 1);
  };
  
  return (
    <Layout>
      <Header title="Roundup Transactions" />
      
      <div className="container mx-auto px-4 py-6">
        <div className="mb-6">
          <h1 className={`text-2xl font-bold mb-2 ${darkMode ? 'text-white' : 'text-gray-800'}`}>
            Roundup Transactions
          </h1>
          <p className={`${darkMode ? 'text-gray-300' : 'text-gray-600'}`}>
            View and manage your roundup transactions from everyday purchases.
          </p>
        </div>
        
        {/* Summary Section */}
        <div className="mb-6">
          <RoundupTransactionSummary 
            darkMode={darkMode} 
            onRefresh={handleRefresh}
            key={`summary-${refreshKey}`}
          />
        </div>
        
        {/* Transaction List */}
        <div>
          <RoundupTransactionList 
            darkMode={darkMode}
            onInvestPending={handleRefresh}
            key={`list-${refreshKey}`}
          />
        </div>
      </div>
    </Layout>
  );
};

export default RoundupTransactionsPage;
