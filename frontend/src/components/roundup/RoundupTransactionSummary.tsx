import React, { useState, useEffect } from 'react';
import { LoadingSpinner } from '../common/LoadingSpinner';
import { ErrorDisplay } from '../common/ErrorDisplay';
import { tradingService } from '../../services/api';
import { formatCurrency, formatDate } from '../../utils/formatters';
import type { RoundupSummary } from '../../types';

interface RoundupTransactionSummaryProps {
  darkMode?: boolean;
  onRefresh?: () => void;
}

export const RoundupTransactionSummary: React.FC<RoundupTransactionSummaryProps> = ({
  darkMode = true,
  onRefresh
}) => {
  const [summary, setSummary] = useState<RoundupSummary | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  
  // Load summary data
  useEffect(() => {
    const fetchSummary = async () => {
      try {
        setLoading(true);
        const data = await tradingService.getRoundupSummary(true);
        setSummary(data);
        setError('');
      } catch (err: any) {
        console.error('Error fetching roundup summary:', err);
        setError(err.message || 'Failed to load roundup summary');
      } finally {
        setLoading(false);
      }
    };
    
    fetchSummary();
  }, []);
  
  if (loading) {
    return (
      <div className={`flex justify-center items-center p-4 ${darkMode ? 'text-white' : 'text-gray-800'}`}>
        <LoadingSpinner size="md" />
        <span className="ml-2">Loading summary...</span>
      </div>
    );
  }
  
  if (error) {
    return <ErrorDisplay error={error} />;
  }
  
  if (!summary) {
    return null;
  }
  
  return (
    <div className={`${darkMode ? 'bg-gray-800 text-white' : 'bg-white text-gray-800'} rounded-lg shadow p-4`}>
      <h3 className={`text-lg font-medium mb-4 ${darkMode ? 'text-blue-300' : 'text-blue-600'}`}>
        Roundup Summary
      </h3>
      
      <div className="grid grid-cols-2 md:grid-cols-3 gap-4">
        <div>
          <p className={`text-sm ${darkMode ? 'text-gray-400' : 'text-gray-500'}`}>Total Roundups</p>
          <p className="text-xl font-semibold">{summary.total_roundups}</p>
        </div>
        
        <div>
          <p className={`text-sm ${darkMode ? 'text-gray-400' : 'text-gray-500'}`}>Total Amount</p>
          <p className="text-xl font-semibold">{formatCurrency(summary.total_amount)}</p>
        </div>
        
        <div>
          <p className={`text-sm ${darkMode ? 'text-gray-400' : 'text-gray-500'}`}>Pending Amount</p>
          <p className="text-xl font-semibold">{formatCurrency(summary.pending_amount)}</p>
        </div>
        
        <div>
          <p className={`text-sm ${darkMode ? 'text-gray-400' : 'text-gray-500'}`}>Invested Amount</p>
          <p className="text-xl font-semibold">{formatCurrency(summary.invested_amount)}</p>
        </div>
        
        <div>
          <p className={`text-sm ${darkMode ? 'text-gray-400' : 'text-gray-500'}`}>Total Investments</p>
          <p className="text-xl font-semibold">{summary.total_investments}</p>
        </div>
        
        <div>
          <p className={`text-sm ${darkMode ? 'text-gray-400' : 'text-gray-500'}`}>Last Investment</p>
          <p className="text-xl font-semibold">
            {summary.last_investment_date ? formatDate(summary.last_investment_date) : 'None'}
          </p>
        </div>
      </div>
    </div>
  );
};

export default RoundupTransactionSummary;
