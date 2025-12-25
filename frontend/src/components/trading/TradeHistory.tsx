import React, { useEffect, useState } from 'react';
import { formatCurrency, formatDateTime } from '../../utils/formatters';
import Loading from '../common/Loading';
import { Select } from '../common/Select';
import type { TradeLegacy } from '../../types';

interface TradeRowProps {
  trade: TradeLegacy;
}

const TradeRow: React.FC<TradeRowProps> = ({ trade }) => {
  const totalValue = trade.amount * trade.price;
  const fee = trade.fee || 0;
  
  return (
    <tr className="border-b border-gray-700 hover:bg-gray-700/50 transition-colors">
      <td className="py-3 px-4">
        <div className="flex items-center">
          <span className={`w-2 h-2 rounded-full mr-2 ${
            trade.type === 'BUY' ? 'bg-green-500' : 'bg-red-500'
          }`} />
          <span className="font-medium text-white">{trade.symbol}</span>
        </div>
      </td>
      <td className="py-3 px-4">
        <span className={`font-medium ${trade.type === 'BUY' ? 'text-green-400' : 'text-red-400'}`}>
          {trade.type}
        </span>
      </td>
      <td className="py-3 px-4 text-white">
        {trade.amount.toFixed(8)}
      </td>
      <td className="py-3 px-4 text-white">
        {formatCurrency(trade.price)}
      </td>
      <td className="py-3 px-4 text-white font-medium">
        {formatCurrency(totalValue)}
      </td>
      {fee > 0 && (
        <td className="py-3 px-4 text-gray-400">
          {formatCurrency(fee)}
        </td>
      )}
      <td className="py-3 px-4">
        <span className={`px-2 py-1 rounded text-xs font-medium ${
          trade.status === 'COMPLETED' ? 'bg-green-900 text-green-300' :
          trade.status === 'PENDING' ? 'bg-yellow-900 text-yellow-300' :
          trade.status === 'CANCELLED' ? 'bg-gray-900 text-gray-300' :
          'bg-red-900 text-red-300'
        }`}>
          {trade.status}
        </span>
      </td>
      <td className="py-3 px-4 text-gray-400 text-sm">
        {formatDateTime(trade.timestamp)}
      </td>
    </tr>
  );
};

const TradeHistory: React.FC = () => {
  const [trades, setTrades] = useState<TradeLegacy[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [timeframe, setTimeframe] = useState('7d');
  const [pageSize, setPageSize] = useState(20);
  const [currentPage, setCurrentPage] = useState(1);

  useEffect(() => {
    const loadTradeHistory = async () => {
      try {
        setLoading(true);
        setError(null);
        
        // Mock trade history data
        const mockTrades: TradeLegacy[] = [
          {
            id: '1',
            symbol: 'AAPL',
            type: 'BUY',
            amount: 10,
            price: 150.25,
            status: 'COMPLETED',
            timestamp: new Date().toISOString(),
            fee: 1.50,
          },
          {
            id: '2',
            symbol: 'MSFT',
            type: 'BUY',
            amount: 5,
            price: 310.75,
            status: 'COMPLETED',
            timestamp: new Date(Date.now() - 86400000).toISOString(),
            fee: 2.25,
          },
          {
            id: '3',
            symbol: 'GOOGL',
            type: 'SELL',
            amount: 2,
            price: 140.85,
            status: 'COMPLETED',
            timestamp: new Date(Date.now() - 172800000).toISOString(),
            fee: 1.75,
          },
          {
            id: '4',
            symbol: 'TSLA',
            type: 'BUY',
            amount: 8,
            price: 245.60,
            status: 'PENDING',
            timestamp: new Date(Date.now() - 3600000).toISOString(),
            fee: 0,
          },
          {
            id: '5',
            symbol: 'NVDA',
            type: 'BUY',
            amount: 3,
            price: 450.20,
            status: 'FAILED',
            timestamp: new Date(Date.now() - 7200000).toISOString(),
            fee: 0,
          },
        ];

        setTimeout(() => {
          setTrades(mockTrades);
          setLoading(false);
        }, 1000);
      } catch (err) {
        setError(err instanceof Error ? err.message : 'Failed to load trade history');
        setLoading(false);
      }
    };

    loadTradeHistory();
    
    const interval = setInterval(loadTradeHistory, 30000);
    return () => clearInterval(interval);
  }, [timeframe, currentPage, pageSize]);

  // Calculate pagination
  const totalTrades = trades.length;
  const totalPages = Math.ceil(totalTrades / pageSize);
  const startIndex = (currentPage - 1) * pageSize;
  const endIndex = Math.min(startIndex + pageSize, totalTrades);
  const paginatedTrades = trades.slice(startIndex, endIndex);

  if (loading && trades.length === 0) {
    return (
      <div className="bg-gray-800 rounded-lg p-6">
        <Loading text="Loading trade history..." />
      </div>
    );
  }

  return (
    <div className="bg-gray-800 rounded-lg overflow-hidden">
      <div className="p-4 border-b border-gray-700 flex flex-col sm:flex-row justify-between items-start sm:items-center gap-4">
        <h2 className="text-xl font-semibold text-white">Trade History</h2>
        <div className="flex flex-col sm:flex-row space-y-2 sm:space-y-0 sm:space-x-4">
          <Select
            value={pageSize.toString()}
            onChange={(value) => {
              setPageSize(Number(value));
              setCurrentPage(1);
            }}
            options={[
              { value: '10', label: '10 per page' },
              { value: '20', label: '20 per page' },
              { value: '50', label: '50 per page' },
              { value: '100', label: '100 per page' }
            ]}
            className="w-36"
          />
          <Select
            value={timeframe}
            onChange={(value) => {
              setTimeframe(value);
              setCurrentPage(1);
            }}
            options={[
              { value: '24h', label: 'Last 24 Hours' },
              { value: '7d', label: 'Last 7 Days' },
              { value: '30d', label: 'Last 30 Days' },
              { value: 'all', label: 'All Time' }
            ]}
            className="w-48"
          />
        </div>
      </div>

      {error ? (
        <div className="p-6 text-center">
          <div className="text-red-400">
            <p className="text-lg font-medium">Failed to load trade history</p>
            <p className="text-sm mt-1">{error}</p>
          </div>
        </div>
      ) : (
        <>
          {paginatedTrades.length > 0 ? (
            <div className="overflow-x-auto">
              <table className="w-full">
                <thead className="bg-gray-700">
                  <tr>
                    <th className="py-3 px-4 text-left text-sm font-medium text-gray-300">Symbol</th>
                    <th className="py-3 px-4 text-left text-sm font-medium text-gray-300">Type</th>
                    <th className="py-3 px-4 text-left text-sm font-medium text-gray-300">Amount</th>
                    <th className="py-3 px-4 text-left text-sm font-medium text-gray-300">Price</th>
                    <th className="py-3 px-4 text-left text-sm font-medium text-gray-300">Total</th>
                    <th className="py-3 px-4 text-left text-sm font-medium text-gray-300">Fee</th>
                    <th className="py-3 px-4 text-left text-sm font-medium text-gray-300">Status</th>
                    <th className="py-3 px-4 text-left text-sm font-medium text-gray-300">Time</th>
                  </tr>
                </thead>
                <tbody>
                  {paginatedTrades.map((trade: TradeLegacy) => (
                    <TradeRow key={trade.id} trade={trade} />
                  ))}
                </tbody>
              </table>
            </div>
          ) : (
            <div className="p-8 text-center text-gray-400">
              <p className="text-lg">No trades found</p>
              <p className="text-sm mt-1">Your trade history will appear here once you start trading</p>
            </div>
          )}

          {/* Pagination */}
          {totalPages > 1 && (
            <div className="flex justify-between items-center p-4 border-t border-gray-700">
              <div className="text-sm text-gray-400">
                Showing {startIndex + 1} to {endIndex} of {totalTrades} entries
              </div>
              <div className="flex space-x-2">
                <button
                  onClick={() => setCurrentPage(prev => Math.max(1, prev - 1))}
                  disabled={currentPage === 1}
                  className="px-3 py-1 rounded bg-gray-700 text-white disabled:opacity-50 disabled:cursor-not-allowed hover:bg-gray-600 transition-colors"
                >
                  Previous
                </button>
                <span className="px-3 py-1 text-gray-400">
                  Page {currentPage} of {totalPages}
                </span>
                <button
                  onClick={() => setCurrentPage(prev => Math.min(totalPages, prev + 1))}
                  disabled={currentPage === totalPages}
                  className="px-3 py-1 rounded bg-gray-700 text-white disabled:opacity-50 disabled:cursor-not-allowed hover:bg-gray-600 transition-colors"
                >
                  Next
                </button>
              </div>
            </div>
          )}
          
          {loading && (
            <div className="p-4 border-t border-gray-700 text-center">
              <div className="flex items-center justify-center text-sm text-gray-400">
                <div className="w-3 h-3 border border-gray-600 border-t-blue-500 rounded-full animate-spin mr-2" />
                Updating...
              </div>
            </div>
          )}
        </>
      )}
    </div>
  );
};

export default TradeHistory;