import React, { useState } from 'react';
import { formatCurrency, formatDateTime } from '../../utils/formatters';
import Loading from '../common/Loading';
import { Select } from '../common/Select';
import { useTradingContext } from '../../contexts/TradingContext';
import { useGetOrderHistoryQuery } from '../../services/tradingApi';

interface TradeRowProps {
  id: string;
  symbol: string;
  tradeType: string;
  quantity: number;
  price?: number;
  filledPrice?: number;
  status: string;
  createdAt: string;
}

const TradeRow: React.FC<TradeRowProps> = ({
  symbol,
  tradeType,
  quantity,
  price,
  filledPrice,
  status,
  createdAt
}) => {
  const displayPrice = filledPrice || price || 0;
  const totalValue = quantity * displayPrice;

  return (
    <tr className="border-b border-gray-700 hover:bg-gray-700/50 transition-colors">
      <td className="py-3 px-4">
        <div className="flex items-center">
          <span className={`w-2 h-2 rounded-full mr-2 ${
            tradeType === 'BUY' ? 'bg-green-500' : 'bg-red-500'
          }`} />
          <span className="font-medium text-white">{symbol}</span>
        </div>
      </td>
      <td className="py-3 px-4">
        <span className={`font-medium ${tradeType === 'BUY' ? 'text-green-400' : 'text-red-400'}`}>
          {tradeType}
        </span>
      </td>
      <td className="py-3 px-4 text-white">
        {quantity.toFixed(8)}
      </td>
      <td className="py-3 px-4 text-white">
        {formatCurrency(displayPrice)}
      </td>
      <td className="py-3 px-4 text-white font-medium">
        {formatCurrency(totalValue)}
      </td>
      <td className="py-3 px-4">
        <span className={`px-2 py-1 rounded text-xs font-medium ${
          status === 'FILLED' || status === 'COMPLETED' ? 'bg-green-900 text-green-300' :
          status === 'PENDING' || status === 'NEW' ? 'bg-yellow-900 text-yellow-300' :
          status === 'CANCELLED' ? 'bg-gray-900 text-gray-300' :
          'bg-red-900 text-red-300'
        }`}>
          {status}
        </span>
      </td>
      <td className="py-3 px-4 text-gray-400 text-sm">
        {formatDateTime(createdAt)}
      </td>
    </tr>
  );
};

const TradeHistory: React.FC = () => {
  const { mode } = useTradingContext();
  const [pageSize, setPageSize] = useState(20);
  const [currentPage, setCurrentPage] = useState(1);

  // Fetch real order history
  const {
    data: orderHistory,
    isLoading,
    error
  } = useGetOrderHistoryQuery(
    { mode, limit: 100 }, // Get more orders than we display for client-side pagination
    { pollingInterval: 30000 } // Refresh every 30 seconds
  );

  // Client-side pagination
  const trades = orderHistory || [];
  const totalTrades = trades.length;
  const totalPages = Math.ceil(totalTrades / pageSize);
  const startIndex = (currentPage - 1) * pageSize;
  const endIndex = Math.min(startIndex + pageSize, totalTrades);
  const paginatedTrades = trades.slice(startIndex, endIndex);

  if (isLoading && trades.length === 0) {
    return (
      <div className="bg-gray-800 rounded-lg p-6">
        <Loading text="Loading trade history..." />
      </div>
    );
  }

  return (
    <div className="bg-gray-800 rounded-lg overflow-hidden">
      <div className="p-4 border-b border-gray-700 flex flex-col sm:flex-row justify-between items-start sm:items-center gap-4">
        <div>
          <h2 className="text-xl font-semibold text-white">Trade History</h2>
          <p className="text-xs text-gray-400 mt-1">
            {mode === 'paper' ? 'Paper Trading' : 'Live Account'}
          </p>
        </div>
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
        </div>
      </div>

      {error ? (
        <div className="p-6 text-center">
          <div className="text-red-400">
            <p className="text-lg font-medium">Failed to load trade history</p>
            <p className="text-sm mt-1">
              {error && typeof error === 'object' && 'message' in error
                ? String(error.message)
                : 'Unable to fetch order history'}
            </p>
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
                    <th className="py-3 px-4 text-left text-sm font-medium text-gray-300">Quantity</th>
                    <th className="py-3 px-4 text-left text-sm font-medium text-gray-300">Price</th>
                    <th className="py-3 px-4 text-left text-sm font-medium text-gray-300">Total</th>
                    <th className="py-3 px-4 text-left text-sm font-medium text-gray-300">Status</th>
                    <th className="py-3 px-4 text-left text-sm font-medium text-gray-300">Time</th>
                  </tr>
                </thead>
                <tbody>
                  {paginatedTrades.map((order) => (
                    <TradeRow
                      key={order.id}
                      id={order.id}
                      symbol={order.symbol}
                      tradeType={order.trade_type}
                      quantity={order.quantity}
                      price={order.price}
                      filledPrice={order.filled_price}
                      status={order.status}
                      createdAt={order.created_at}
                    />
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

          {isLoading && trades.length > 0 && (
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