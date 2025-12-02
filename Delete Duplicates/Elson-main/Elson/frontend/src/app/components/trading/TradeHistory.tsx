import React, { useEffect, useState } from 'react';
import { useDispatch, useSelector } from 'react-redux';
import { fetchTradeHistory } from '../../store/slices/tradingSlice';
import { formatCurrency, formatDateTime } from '../../utils/formatters';
import Loading from '../common/Loading';
import Select from '../common/Select';
import type { Trade } from '../../types';

interface TradeRowProps {
  trade: Trade;
}

const TradeRow: React.FC<TradeRowProps> = ({ trade }) => {
  const totalValue = trade.amount * trade.price;
  
  return (
    <tr className="border-b border-gray-700 hover:bg-gray-700/50 transition-colors">
      <td className="py-3 px-4">
        <div className="flex items-center">
          <span className={`w-2 h-2 rounded-full mr-2 ${
            trade.type === 'BUY' ? 'bg-green-500' : 'bg-red-500'
          }`} />
          <span>{trade.symbol}</span>
        </div>
      </td>
      <td className="py-3 px-4">
        <span className={trade.type === 'BUY' ? 'text-green-500' : 'text-red-500'}>
          {trade.type}
        </span>
      </td>
      <td className="py-3 px-4">{trade.amount.toFixed(8)}</td>
      <td className="py-3 px-4">{formatCurrency(trade.price)}</td>
      <td className="py-3 px-4">{formatCurrency(totalValue)}</td>
      <td className="py-3 px-4">
        <span className={`px-2 py-1 rounded text-xs ${
          trade.status === 'COMPLETED' ? 'bg-green-900 text-green-300' :
          trade.status === 'PENDING' ? 'bg-yellow-900 text-yellow-300' :
          'bg-red-900 text-red-300'
        }`}>
          {trade.status}
        </span>
      </td>
      <td className="py-3 px-4 text-gray-400">{formatDateTime(trade.timestamp)}</td>
    </tr>
  );
};

const TradeHistory: React.FC = () => {
  const dispatch = useDispatch();
  const { trades, loading, error } = useSelector((state: any) => state.trading.history);
  const [timeframe, setTimeframe] = useState('24h');
  const [pageSize, setPageSize] = useState(20);
  const [currentPage, setCurrentPage] = useState(1);

  useEffect(() => {
    dispatch(fetchTradeHistory({ timeframe, page: currentPage, pageSize }));
    
    const interval = setInterval(() => {
      dispatch(fetchTradeHistory({ timeframe, page: currentPage, pageSize }));
    }, 30000);

    return () => clearInterval(interval);
  }, [dispatch, timeframe, currentPage, pageSize]);

  if (loading && !trades.length) {
    return <Loading />;
  }

  return (
    <div className="bg-gray-800 rounded-lg overflow-hidden">
      <div className="p-4 border-b border-gray-700 flex justify-between items-center">
        <h2 className="text-xl font-semibold">Trade History</h2>
        <div className="flex space-x-4">
          <Select
            value={pageSize.toString()}
            onChange={(value) => setPageSize(Number(value))}
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
            onChange={(value) => setTimeframe(value)}
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
        <div className="text-red-500 p-4">
          Failed to load trade history: {error}
        </div>
      ) : (
        <>
          <div className="overflow-x-auto">
            <table className="w-full">
              <thead className="bg-gray-700">
                <tr>
                  <th className="py-3 px-4 text-left">Pair</th>
                  <th className="py-3 px-4 text-left">Type</th>
                  <th className="py-3 px-4 text-left">Amount</th>
                  <th className="py-3 px-4 text-left">Price</th>
                  <th className="py-3 px-4 text-left">Total</th>
                  <th className="py-3 px-4 text-left">Status</th>
                  <th className="py-3 px-4 text-left">Time</th>
                </tr>
              </thead>
              <tbody>
                {trades.map((trade: Trade) => (
                  <TradeRow key={trade.id} trade={trade} />
                ))}
              </tbody>
            </table>
          </div>

          {/* Pagination */}
          <div className="flex justify-between items-center p-4 border-t border-gray-700">
            <div className="text-sm text-gray-400">
              Showing {((currentPage - 1) * pageSize) + 1} to {Math.min(currentPage * pageSize, trades.length)} of {trades.length} entries
            </div>
            <div className="flex space-x-2">
              <button
                onClick={() => setCurrentPage(prev => Math.max(1, prev - 1))}
                disabled={currentPage === 1}
                className="px-3 py-1 rounded bg-gray-700 disabled:opacity-50"
              >
                Previous
              </button>
              <button
                onClick={() => setCurrentPage(prev => prev + 1)}
                disabled={currentPage * pageSize >= trades.length}
                className="px-3 py-1 rounded bg-gray-700 disabled:opacity-50"
              >
                Next
              </button>
            </div>
          </div>
        </>
      )}
    </div>
  );
};

export default TradeHistory;