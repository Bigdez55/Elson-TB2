import React, { useState, useEffect } from 'react';
import { useSelector } from 'react-redux';
import { Button } from '../common/Button';
import { LoadingSpinner } from '../common/LoadingSpinner';
import { ErrorDisplay } from '../common/ErrorDisplay';
import { tradingService } from '../../services/api';
import { formatCurrency, formatDate } from '../../utils/formatters';
import useFeatureAccess from '../../hooks/useFeatureAccess';
import { RoundupTransactionFilter } from './RoundupTransactionFilter';
import type { RoundupTransaction } from '../../types';

interface RoundupTransactionListProps {
  darkMode?: boolean;
  onInvestPending?: () => void;
}

export const RoundupTransactionList: React.FC<RoundupTransactionListProps> = ({
  darkMode = true,
  onInvestPending
}) => {
  const [transactions, setTransactions] = useState<RoundupTransaction[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [totalCount, setTotalCount] = useState(0);
  const [pageSize, setPageSize] = useState(10);
  const [currentPage, setCurrentPage] = useState(1);
  const [filters, setFilters] = useState({
    status: '',
    startDate: '',
    endDate: ''
  });
  
  // User role from redux store
  const { role } = useSelector((state: any) => state.user.currentUser || {});
  
  // Check permission for micro-investing
  const { hasAccess: hasMicroInvestPermission, isLoading: permissionLoading } =
    useFeatureAccess('micro_investing');
  
  // Load transactions
  useEffect(() => {
    const fetchTransactions = async () => {
      try {
        setLoading(true);
        const params = {
          status: filters.status || undefined,
          startDate: filters.startDate || undefined,
          endDate: filters.endDate || undefined,
          limit: pageSize,
          offset: (currentPage - 1) * pageSize
        };
        
        const data = await tradingService.getRoundupTransactions(params, true);
        setTransactions(data.transactions);
        setTotalCount(data.total);
        setError('');
      } catch (err: any) {
        console.error('Error fetching roundup transactions:', err);
        setError(err.message || 'Failed to load roundup transactions');
      } finally {
        setLoading(false);
      }
    };
    
    fetchTransactions();
  }, [filters, currentPage, pageSize]);
  
  // Handle investing pending roundups
  const handleInvestPending = async () => {
    if (role === 'MINOR' && !hasMicroInvestPermission) {
      setError('You need guardian permission to invest roundups');
      return;
    }
    
    try {
      if (window.confirm('Are you sure you want to invest all pending roundups?')) {
        await tradingService.investPendingRoundups();
        
        // Refresh the list
        const updatedData = await tradingService.getRoundupTransactions({
          limit: pageSize,
          offset: (currentPage - 1) * pageSize
        }, true);
        
        setTransactions(updatedData.transactions);
        setTotalCount(updatedData.total);
        
        if (onInvestPending) {
          onInvestPending();
        }
      }
    } catch (err: any) {
      console.error('Error investing roundups:', err);
      setError(err.message || 'Failed to invest roundups');
    }
  };
  
  // Get status badge color
  const getStatusBadgeClass = (status: string) => {
    if (darkMode) {
      switch (status) {
        case 'pending': return 'bg-yellow-900 text-yellow-300';
        case 'invested': return 'bg-green-900 text-green-300';
        case 'cancelled': return 'bg-red-900 text-red-300';
        default: return 'bg-gray-900 text-gray-300';
      }
    } else {
      switch (status) {
        case 'pending': return 'bg-yellow-100 text-yellow-800';
        case 'invested': return 'bg-green-100 text-green-800';
        case 'cancelled': return 'bg-red-100 text-red-800';
        default: return 'bg-gray-100 text-gray-800';
      }
    }
  };
  
  // Handle filter changes
  const handleFilterChange = (newFilters: any) => {
    setFilters(newFilters);
    setCurrentPage(1); // Reset to first page when filters change
  };
  
  // Pagination
  const totalPages = Math.ceil(totalCount / pageSize);
  
  if (loading) {
    return (
      <div className={`flex justify-center items-center p-8 ${darkMode ? 'text-white' : 'text-gray-800'}`}>
        <LoadingSpinner size="lg" />
        <span className="ml-2">Loading roundup transactions...</span>
      </div>
    );
  }
  
  if (error) {
    return <ErrorDisplay error={error} />;
  }
  
  if (transactions.length === 0) {
    return (
      <div className={`p-6 text-center ${darkMode ? 'bg-gray-800 text-gray-300' : 'bg-gray-100 text-gray-600'} rounded-lg`}>
        <p className="mb-4">You don't have any roundup transactions yet.</p>
        <p className="text-sm">Roundups help you invest small amounts from your everyday purchases.</p>
      </div>
    );
  }
  
  // Render based on theme
  const tableClassName = darkMode 
    ? "min-w-full bg-gray-900 text-white border-collapse"
    : "min-w-full bg-white text-gray-800 border-collapse shadow-md rounded-lg overflow-hidden";
    
  const headerClassName = darkMode
    ? "bg-gray-800"
    : "bg-gray-100";
    
  const rowClassName = darkMode
    ? "border-t border-gray-800 hover:bg-gray-800 transition-colors"
    : "border-t border-gray-100 hover:bg-gray-50 transition-colors";
  
  return (
    <div>
      {/* Permission notice for minors */}
      {role === 'MINOR' && (
        <div className={`border mb-4 px-4 py-3 rounded-lg ${
          hasMicroInvestPermission 
            ? (darkMode ? 'border-green-700 bg-green-900/30 text-white' : 'border-green-400 bg-green-50 text-green-800')
            : (darkMode ? 'border-amber-700 bg-amber-900/30 text-white' : 'border-amber-400 bg-amber-50 text-amber-800')
        }`}>
          {hasMicroInvestPermission 
            ? '✓ Your guardian has granted you permission to manage micro-investments.' 
            : '⚠️ You need guardian permission to manage micro-investments. Ask your guardian to enable this feature for you.'}
        </div>
      )}
      
      {/* Filters */}
      <div className="mb-4">
        <RoundupTransactionFilter 
          filters={filters} 
          onFilterChange={handleFilterChange}
          darkMode={darkMode}
        />
      </div>
      
      {/* Pending roundups button */}
      {transactions.some(t => t.status === 'pending') && (
        <div className="mb-4 flex justify-end">
          <Button
            className={`${darkMode ? 'bg-blue-600 hover:bg-blue-500' : 'bg-blue-500 hover:bg-blue-400'} text-white px-4 py-2`}
            onClick={handleInvestPending}
            disabled={role === 'MINOR' && !hasMicroInvestPermission}
          >
            Invest Pending Roundups
          </Button>
        </div>
      )}
    
      <div className="overflow-x-auto">
        <table className={tableClassName}>
          <thead>
            <tr className={headerClassName}>
              <th className="py-3 px-4 text-left">Date</th>
              <th className="py-3 px-4 text-left">Description</th>
              <th className="py-3 px-4 text-left">Original Amount</th>
              <th className="py-3 px-4 text-left">Roundup Amount</th>
              <th className="py-3 px-4 text-left">Source</th>
              <th className="py-3 px-4 text-left">Status</th>
            </tr>
          </thead>
          <tbody>
            {transactions.map((transaction) => (
              <tr key={transaction.id} className={rowClassName}>
                <td className="py-3 px-4">{formatDate(transaction.transaction_date)}</td>
                <td className="py-3 px-4">{transaction.description || 'N/A'}</td>
                <td className="py-3 px-4">{formatCurrency(transaction.transaction_amount)}</td>
                <td className="py-3 px-4">{formatCurrency(transaction.roundup_amount)}</td>
                <td className="py-3 px-4">{transaction.source || 'N/A'}</td>
                <td className="py-3 px-4">
                  <span className={`px-2 py-1 rounded-full text-xs font-medium ${getStatusBadgeClass(transaction.status)}`}>
                    {transaction.status.charAt(0).toUpperCase() + transaction.status.slice(1)}
                  </span>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
      
      {/* Pagination */}
      {totalPages > 1 && (
        <div className={`flex justify-between items-center mt-4 ${darkMode ? 'text-gray-300' : 'text-gray-700'}`}>
          <div>
            Showing {(currentPage - 1) * pageSize + 1} to {Math.min(currentPage * pageSize, totalCount)} of {totalCount} results
          </div>
          <div className="flex gap-2">
            <Button
              className={`${darkMode ? 'bg-gray-700 hover:bg-gray-600' : 'bg-gray-200 hover:bg-gray-300'} px-3 py-1`}
              onClick={() => setCurrentPage(Math.max(1, currentPage - 1))}
              disabled={currentPage === 1}
            >
              Previous
            </Button>
            <Button
              className={`${darkMode ? 'bg-gray-700 hover:bg-gray-600' : 'bg-gray-200 hover:bg-gray-300'} px-3 py-1`}
              onClick={() => setCurrentPage(Math.min(totalPages, currentPage + 1))}
              disabled={currentPage === totalPages}
            >
              Next
            </Button>
          </div>
        </div>
      )}
    </div>
  );
};

export default RoundupTransactionList;
