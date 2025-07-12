import React, { useEffect } from 'react';
import { useDispatch, useSelector } from 'react-redux';
import { formatCurrency, formatPercentage } from '../../utils/formatters';
import { fetchPortfolio } from '../../store/slices/tradingSlice';
import Loading from '../common/Loading';
import type { Asset } from '../../types';

interface AssetRowProps {
  asset: Asset;
}

const AssetRow: React.FC<AssetRowProps> = ({ asset }) => {
  const profitLoss = asset.totalValue - (asset.averagePrice * asset.amount);
  const profitLossPercentage = ((asset.currentPrice - asset.averagePrice) / asset.averagePrice) * 100;

  return (
    <tr className="border-b border-gray-700">
      <td className="py-4 px-6">
        <div className="flex flex-col">
          <span className="font-medium">{asset.symbol}</span>
          <span className="text-sm text-gray-400">{asset.amount.toFixed(8)}</span>
        </div>
      </td>
      <td className="py-4 px-6">
        <div className="flex flex-col">
          <span>{formatCurrency(asset.currentPrice)}</span>
          <span className="text-sm text-gray-400">Avg. {formatCurrency(asset.averagePrice)}</span>
        </div>
      </td>
      <td className="py-4 px-6">
        <div className="flex flex-col">
          <span>{formatCurrency(asset.totalValue)}</span>
          <span className={`text-sm ${profitLoss >= 0 ? 'text-green-500' : 'text-red-500'}`}>
            {formatCurrency(profitLoss)} ({formatPercentage(profitLossPercentage)})
          </span>
        </div>
      </td>
      <td className="py-4 px-6">
        <div className="w-full bg-gray-700 rounded-full h-2">
          <div
            className="bg-primary-600 rounded-full h-2"
            style={{ width: `${(asset.totalValue / asset.totalValue) * 100}%` }}
          />
        </div>
      </td>
    </tr>
  );
};

const Portfolio: React.FC = () => {
  const dispatch = useDispatch();
  const { assets, totalValue, loading, error } = useSelector((state: any) => state.trading.portfolio);

  useEffect(() => {
    dispatch(fetchPortfolio());
    
    // Refresh portfolio every minute
    const interval = setInterval(() => {
      dispatch(fetchPortfolio());
    }, 60000);

    return () => clearInterval(interval);
  }, [dispatch]);

  if (loading) {
    return <Loading />;
  }

  if (error) {
    return (
      <div className="text-red-500 p-4">
        Failed to load portfolio: {error}
      </div>
    );
  }

  return (
    <div className="bg-gray-800 rounded-lg overflow-hidden">
      <div className="p-6 border-b border-gray-700">
        <h2 className="text-xl font-semibold">Portfolio</h2>
        <p className="text-2xl mt-2">{formatCurrency(totalValue)}</p>
      </div>

      <div className="overflow-x-auto">
        <table className="w-full">
          <thead className="bg-gray-700">
            <tr>
              <th className="py-3 px-6 text-left">Asset</th>
              <th className="py-3 px-6 text-left">Price</th>
              <th className="py-3 px-6 text-left">Value</th>
              <th className="py-3 px-6 text-left">Allocation</th>
            </tr>
          </thead>
          <tbody>
            {assets.map((asset: Asset) => (
              <AssetRow key={asset.symbol} asset={asset} />
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
};

export default Portfolio;