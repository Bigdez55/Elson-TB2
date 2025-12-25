import React, { useEffect, useState } from 'react';
import { formatCurrency, formatPercentage } from '../../utils/formatters';
import Loading from '../common/Loading';
import type { AssetLegacy } from '../../types';

interface AssetRowProps {
  asset: AssetLegacy;
}

const AssetRow: React.FC<AssetRowProps> = ({ asset }) => {
  const profitLoss = asset.totalValue - (asset.averagePrice * asset.amount);
  const profitLossPercentage = ((asset.currentPrice - asset.averagePrice) / asset.averagePrice) * 100;
  const allocationPercentage = 25; // This would be calculated based on total portfolio value

  return (
    <tr className="border-b border-gray-700 hover:bg-gray-700/30 transition-colors">
      <td className="py-4 px-6">
        <div className="flex flex-col">
          <span className="font-medium text-white">{asset.symbol}</span>
          <span className="text-sm text-gray-400">{asset.amount.toFixed(8)} shares</span>
        </div>
      </td>
      <td className="py-4 px-6">
        <div className="flex flex-col">
          <span className="text-white">{formatCurrency(asset.currentPrice)}</span>
          <span className="text-sm text-gray-400">Avg. {formatCurrency(asset.averagePrice)}</span>
        </div>
      </td>
      <td className="py-4 px-6">
        <div className="flex flex-col">
          <span className="text-white font-medium">{formatCurrency(asset.totalValue)}</span>
          <span className={`text-sm ${profitLoss >= 0 ? 'text-green-400' : 'text-red-400'}`}>
            {formatCurrency(profitLoss)} ({formatPercentage(profitLossPercentage)})
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
  const [portfolio, setPortfolio] = useState<{
    assets: AssetLegacy[];
    totalValue: number;
    loading: boolean;
    error: string | null;
  }>({
    assets: [],
    totalValue: 0,
    loading: true,
    error: null,
  });

  useEffect(() => {
    const loadPortfolio = async () => {
      try {
        setPortfolio(prev => ({ ...prev, loading: true, error: null }));
        
        // Mock data for demonstration
        const mockPortfolio = {
          assets: [
            {
              symbol: 'AAPL',
              amount: 10,
              currentPrice: 150.25,
              averagePrice: 145.50,
              totalValue: 1502.50,
            },
            {
              symbol: 'MSFT',
              amount: 5,
              currentPrice: 310.75,
              averagePrice: 300.00,
              totalValue: 1553.75,
            },
            {
              symbol: 'GOOGL',
              amount: 3,
              currentPrice: 140.85,
              averagePrice: 138.20,
              totalValue: 422.55,
            },
            {
              symbol: 'TSLA',
              amount: 8,
              currentPrice: 245.60,
              averagePrice: 250.00,
              totalValue: 1964.80,
            },
          ],
          totalValue: 5443.60,
        };

        setTimeout(() => {
          setPortfolio({
            assets: mockPortfolio.assets,
            totalValue: mockPortfolio.totalValue,
            loading: false,
            error: null,
          });
        }, 1000);
      } catch (err) {
        setPortfolio(prev => ({
          ...prev,
          loading: false,
          error: err instanceof Error ? err.message : 'Failed to load portfolio',
        }));
      }
    };

    loadPortfolio();
    
    // Refresh portfolio every minute
    const interval = setInterval(loadPortfolio, 60000);
    return () => clearInterval(interval);
  }, []);

  // Calculate total profit/loss
  const totalProfitLoss = portfolio.assets.reduce((total, asset) => {
    return total + (asset.totalValue - (asset.averagePrice * asset.amount));
  }, 0);

  const totalProfitLossPercentage = portfolio.assets.length > 0 
    ? (totalProfitLoss / portfolio.assets.reduce((total, asset) => total + (asset.averagePrice * asset.amount), 0)) * 100
    : 0;

  if (portfolio.loading && portfolio.assets.length === 0) {
    return (
      <div className="bg-gray-800 rounded-lg p-6">
        <Loading text="Loading portfolio..." />
      </div>
    );
  }

  if (portfolio.error) {
    return (
      <div className="bg-gray-800 rounded-lg p-6">
        <div className="text-red-400 text-center">
          <p className="text-lg font-medium">Failed to load portfolio</p>
          <p className="text-sm mt-1">{portfolio.error}</p>
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
              {formatCurrency(portfolio.totalValue)}
            </p>
          </div>
          <div className="text-right">
            <p className="text-sm text-gray-400">Total P&L</p>
            <p className={`text-lg font-semibold ${totalProfitLoss >= 0 ? 'text-green-400' : 'text-red-400'}`}>
              {formatCurrency(totalProfitLoss)}
            </p>
            <p className={`text-sm ${totalProfitLoss >= 0 ? 'text-green-400' : 'text-red-400'}`}>
              ({formatPercentage(totalProfitLossPercentage)})
            </p>
          </div>
        </div>
        
        {portfolio.loading && (
          <div className="mt-3 flex items-center text-sm text-gray-400">
            <div className="w-3 h-3 border border-gray-600 border-t-blue-500 rounded-full animate-spin mr-2" />
            Updating...
          </div>
        )}
      </div>

      {/* Portfolio Table */}
      {portfolio.assets.length > 0 ? (
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
              {portfolio.assets.map((asset: AssetLegacy) => (
                <AssetRow key={asset.symbol} asset={asset} />
              ))}
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