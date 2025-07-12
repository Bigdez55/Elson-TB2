import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { Button } from '../common/Button';
import { formatCurrency } from '../../utils/formatters';
import { tradingService } from '../../services/tradingService';
import { RecurringInvestment } from '../../types';
import { EducationalTooltip } from '../common/EducationalTooltip';

interface RecurringInvestmentListProps {
  onSelectInvestment?: (investment: RecurringInvestment) => void;
}

export const RecurringInvestmentList: React.FC<RecurringInvestmentListProps> = ({
  onSelectInvestment
}) => {
  const [investments, setInvestments] = useState<RecurringInvestment[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState('');
  
  const navigate = useNavigate();
  
  // Load recurring investments
  useEffect(() => {
    const fetchInvestments = async () => {
      setIsLoading(true);
      setError('');
      
      try {
        const data = await tradingService.getRecurringInvestments();
        setInvestments(data);
      } catch (err: any) {
        console.error('Error fetching recurring investments:', err);
        setError(err.message || 'Error loading recurring investments');
      } finally {
        setIsLoading(false);
      }
    };
    
    fetchInvestments();
  }, []);
  
  const handleCancelInvestment = async (id: number, e: React.MouseEvent) => {
    e.stopPropagation();
    
    if (!window.confirm('Are you sure you want to cancel this recurring investment?')) {
      return;
    }
    
    try {
      await tradingService.cancelRecurringInvestment(id);
      
      // Update the local state to mark the investment as inactive
      setInvestments(investments.map(investment => 
        investment.id === id 
          ? { ...investment, is_active: false }
          : investment
      ));
    } catch (err: any) {
      console.error('Error cancelling investment:', err);
      alert('Failed to cancel investment: ' + (err.message || 'Unknown error'));
    }
  };
  
  const formatFrequency = (frequency: string): string => {
    return frequency.charAt(0).toUpperCase() + frequency.slice(1);
  };
  
  const formatDate = (dateString: string): string => {
    return new Date(dateString).toLocaleDateString();
  };
  
  const calculateNextInvestmentIn = (nextDate: string): string => {
    const now = new Date();
    const next = new Date(nextDate);
    const diffTime = next.getTime() - now.getTime();
    
    if (diffTime < 0) {
      return 'Processing soon';
    }
    
    const diffDays = Math.ceil(diffTime / (1000 * 60 * 60 * 24));
    
    if (diffDays === 0) {
      // Calculate hours
      const diffHours = Math.ceil(diffTime / (1000 * 60 * 60));
      return diffHours <= 1 ? 'In less than an hour' : `In ${diffHours} hours`;
    } else if (diffDays === 1) {
      return 'Tomorrow';
    } else {
      return `In ${diffDays} days`;
    }
  };
  
  if (isLoading) {
    return (
      <div className="bg-white rounded-lg shadow-md p-6">
        <div className="animate-pulse flex flex-col space-y-4">
          <div className="h-6 bg-gray-200 rounded w-3/4"></div>
          <div className="space-y-3">
            <div className="h-20 bg-gray-200 rounded"></div>
            <div className="h-20 bg-gray-200 rounded"></div>
            <div className="h-20 bg-gray-200 rounded"></div>
          </div>
        </div>
      </div>
    );
  }
  
  if (error) {
    return (
      <div className="bg-white rounded-lg shadow-md p-6">
        <div className="bg-red-100 border border-red-400 text-red-700 px-4 py-3 rounded mb-4">
          {error}
        </div>
        <Button
          onClick={() => window.location.reload()}
          className="w-full"
        >
          Retry
        </Button>
      </div>
    );
  }
  
  if (investments.length === 0) {
    return (
      <div className="bg-white rounded-lg shadow-md p-6">
        <div className="text-center p-6">
          <h3 className="text-lg font-medium text-gray-900 mb-2">No Recurring Investments</h3>
          <p className="text-gray-600 mb-4">
            You don't have any recurring investments set up yet.
          </p>
          <Button
            onClick={() => navigate('/trading')}
            className="inline-block"
          >
            Create Recurring Investment
          </Button>
        </div>
      </div>
    );
  }
  
  return (
    <div className="bg-white rounded-lg shadow-md p-6">
      <div className="flex items-center justify-between mb-6">
        <div>
          <h2 className="text-xl font-semibold">Your Recurring Investments</h2>
          <p className="text-gray-600 text-sm">
            Automatically invest at regular intervals
          </p>
        </div>
        <EducationalTooltip 
          content="Recurring investments help you build wealth through dollar-cost averaging by investing a fixed amount at regular intervals, regardless of market conditions."
          position="left"
        />
      </div>
      
      <div className="divide-y divide-gray-200">
        {investments.map(investment => (
          <div 
            key={investment.id} 
            className={`py-4 ${!investment.is_active ? 'opacity-60' : ''} ${onSelectInvestment ? 'cursor-pointer' : ''}`}
            onClick={() => onSelectInvestment && investment.is_active && onSelectInvestment(investment)}
          >
            <div className="flex items-center justify-between mb-1">
              <div className="flex items-center">
                <span className="font-semibold text-lg">{investment.symbol}</span>
                <span className={`ml-3 px-2 py-1 text-xs rounded ${investment.is_active ? 'bg-green-100 text-green-800' : 'bg-gray-100 text-gray-800'}`}>
                  {investment.is_active ? 'Active' : 'Inactive'}
                </span>
              </div>
              <div className="text-right">
                <div className="font-semibold">{formatCurrency(investment.investment_amount)}</div>
                <div className="text-sm text-gray-600">{formatFrequency(investment.frequency)}</div>
              </div>
            </div>
            
            <div className="grid grid-cols-2 gap-4 text-sm mt-2">
              <div>
                <div className="text-gray-600">Started</div>
                <div>{formatDate(investment.start_date)}</div>
              </div>
              <div>
                <div className="text-gray-600">Next Investment</div>
                <div>{investment.is_active ? calculateNextInvestmentIn(investment.next_investment_date) : 'Cancelled'}</div>
              </div>
              <div>
                <div className="text-gray-600">Total Investments</div>
                <div>{investment.execution_count}</div>
              </div>
              <div>
                <div className="text-gray-600">Last Investment</div>
                <div>{investment.last_execution_date ? formatDate(investment.last_execution_date) : 'None'}</div>
              </div>
            </div>
            
            {investment.is_active && (
              <div className="mt-3 flex justify-end">
                <button
                  onClick={(e) => handleCancelInvestment(investment.id, e)}
                  className="text-sm text-red-600 hover:text-red-800"
                >
                  Cancel
                </button>
              </div>
            )}
          </div>
        ))}
      </div>
      
      <div className="mt-4 pt-4 border-t border-gray-200">
        <p className="text-sm text-gray-600 mb-2">
          Next processing times are estimates. Actual execution times may vary based on market hours and system processing.
        </p>
      </div>
    </div>
  );
};

export default RecurringInvestmentList;