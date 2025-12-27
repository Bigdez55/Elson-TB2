import React from 'react';
import { formatCurrency, formatPercentage } from '../../utils/formatters';
import Loading from '../common/Loading';
import { useTradingContext } from '../../contexts/TradingContext';
import { useGetPortfolioQuery, useGetPositionsQuery } from '../../services/tradingApi';

interface AssetRowProps {
  symbol: string;
  quantity: number;
  currentPrice: number;
  averagePrice: number;
  marketValue: number;
  unrealizedPnl: number;
  unrealizedPnlPercent: number;
  allocationPercentage: number;
}

const AssetRow: React.FC<AssetRowProps> = ({
  symbol,
  quantity,
  currentPrice,
  averagePrice,
  marketValue,
  unrealizedPnl,
  unrealizedPnlPercent,
  allocationPercentage
}) => {
  return (
    <tr className="border-b border-gray-700 hover:bg-gray-700/30 transition-colors">
      <td className="py-4 px-6">
        <div className="flex flex-col">
          <span className="font-medium text-white">{symbol}</span>
          <span className="text-sm text-gray-400">{quantity.toFixed(8)} shares</span>
        </div>
      </td>
      <td className="py-4 px-6">
        <div className="flex flex-col">
          <span className="text-white">{formatCurrency(currentPrice)}</span>
          <span className="text-sm text-gray-400">Avg. {formatCurrency(averagePrice)}</span>
        </div>
      </td>
      <td className="py-4 px-6">
        <div className="flex flex-col">
          <span className="text-white font-medium">{formatCurrency(marketValue)}</span>
          <span className={`text-sm ${unrealizedPnl >= 0 ? 'text-green-400' : 'text-red-400'}`}>
            {formatCurrency(unrealizedPnl)} ({formatPercentage(unrealizedPnlPercent)})
          </span>
        </div>
      </td>
      <td className="py-4 px-6">
        <div className="flex items-center space-x-2">
          <div className="w-full bg-gray-700 rounded-full h-2 max-w-[100px]">
            <div
              className="bg-blue-500 rounded-full h-2 transition-all duration-300"
              style={{ width: `${Math.min(100, allocationPercentage)}%` }}
            />
          </div>
          <span className="text-sm text-gray-400 min-w-[40px]">
            {allocationPercentage.toFixed(1)}%
          </span>
        </div>
      </td>
    </tr>
  );
};

const Portfolio: React.FC = () => {
  const { mode } = useTradingContext();

  // Fetch real portfolio and positions data
  const {
    data: portfolioData,
    isLoading: isPortfolioLoading,
    error: portfolioError
  } = useGetPortfolioQuery({ mode }, { pollingInterval: 30000 }); // Refresh every 30 seconds

  const {
    data: positions,
    isLoading: isPositionsLoading,
    error: positionsError
  } = useGetPositionsQuery({ mode }, { pollingInterval: 30000 });

  const isLoading = isPortfolioLoading || isPositionsLoading;
  const error = portfolioError || positionsError;

  // Calculate total portfolio value and allocation percentages
  const totalPortfolioValue = portfolioData?.total_value || 0;
  const totalPnl = portfolioData?.total_pnl || 0;
  const totalPnlPercent = portfolioData?.total_pnl_percent || 0;

  if (isLoading && (!positions || positions.length === 0)) {
    return (
      <div className="bg-gray-800 rounded-lg p-6">
        <Loading text="Loading portfolio..." />
      </div>
    );
  }

  if (error) {
    return (
      <div className="bg-gray-800 rounded-lg p-6">
        <div className="text-red-400 text-center">
          <p className="text-lg font-medium">Failed to load portfolio</p>
          <p className="text-sm mt-1">
            {error && typeof error === 'object' && 'message' in error
              ? String(error.message)
              : 'Unable to fetch portfolio data'}
          </p>
        </div>
      </div>
    );
  }

  return (
    <div className="bg-gray-800 rounded-lg overflow-hidden">
      {/* Portfolio Header */}
      <div className="p-6 border-b border-gray-700">
        <div className="flex justify-between items-start">
          <div>
            <h2 className="text-xl font-semibold text-white">Portfolio</h2>
            <p className="text-3xl font-bold text-white mt-2">
              {formatCurrency(totalPortfolioValue)}
            </p>
            <p className="text-xs text-gray-400 mt-1">
              {mode === 'paper' ? 'Paper Trading' : 'Live Account'}
            </p>
          </div>
          <div className="text-right">
            <p className="text-sm text-gray-400">Total P&L</p>
            <p className={`text-lg font-semibold ${totalPnl >= 0 ? 'text-green-400' : 'text-red-400'}`}>
              {formatCurrency(totalPnl)}
            </p>
            <p className={`text-sm ${totalPnl >= 0 ? 'text-green-400' : 'text-red-400'}`}>
              ({formatPercentage(totalPnlPercent)})
            </p>
          </div>
        </div>

        {isLoading && positions && positions.length > 0 && (
          <div className="mt-3 flex items-center text-sm text-gray-400">
            <div className="w-3 h-3 border border-gray-600 border-t-blue-500 rounded-full animate-spin mr-2" />
            Updating...
          </div>
        )}
      </div>

      {/* Portfolio Table */}
      {positions && positions.length > 0 ? (
        <div className="overflow-x-auto">
          <table className="w-full">
            <thead className="bg-gray-700">
              <tr>
                <th className="py-3 px-6 text-left text-sm font-medium text-gray-300">Asset</th>
                <th className="py-3 px-6 text-left text-sm font-medium text-gray-300">Price</th>
                <th className="py-3 px-6 text-left text-sm font-medium text-gray-300">Value</th>
                <th className="py-3 px-6 text-left text-sm font-medium text-gray-300">Allocation</th>
              </tr>
            </thead>
            <tbody>
              {positions.map((position) => {
                // Calculate allocation percentage based on market value
                const allocationPercentage = totalPortfolioValue > 0
                  ? (position.market_value / totalPortfolioValue) * 100
                  : 0;

                return (
                  <AssetRow
                    key={position.id}
                    symbol={position.symbol}
                    quantity={position.quantity}
                    currentPrice={position.current_price}
                    averagePrice={position.average_cost}
                    marketValue={position.market_value}
                    unrealizedPnl={position.unrealized_pnl}
                    unrealizedPnlPercent={position.unrealized_pnl_percent}
                    allocationPercentage={allocationPercentage}
                  />
                );
              })}
            </tbody>
          </table>
        </div>
      ) : (
        <div className="p-8 text-center text-gray-400">
          <p className="text-lg">No assets in portfolio</p>
          <p className="text-sm mt-1">Start trading to build your portfolio</p>
        </div>
      )}
    </div>
  );
};

export default Portfolio;