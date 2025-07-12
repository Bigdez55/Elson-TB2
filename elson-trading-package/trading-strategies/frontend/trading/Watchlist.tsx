import React, { useEffect, useState } from 'react';
import { useDispatch, useSelector } from 'react-redux';
import { formatCurrency, formatPercentage } from '../../utils/formatters';
import { fetchWatchlist, addToWatchlist, removeFromWatchlist } from '../../store/slices/tradingSlice';
import Button from '../common/Button';
import Input from '../common/Input';
import Loading from '../common/Loading';

interface WatchlistItem {
  symbol: string;
  price: number;
  change24h: number;
  volume24h: number;
  high24h: number;
  low24h: number;
}

const WatchlistRow: React.FC<{
  item: WatchlistItem;
  onRemove: (symbol: string) => void;
  onSelect: (symbol: string) => void;
}> = ({ item, onRemove, onSelect }) => {
  return (
    <tr className="border-b border-gray-700 hover:bg-gray-700/50 transition-colors cursor-pointer"
        onClick={() => onSelect(item.symbol)}>
      <td className="py-3 px-4">
        <div className="flex items-center justify-between">
          <span className="font-medium">{item.symbol}</span>
          <button
            onClick={(e) => {
              e.stopPropagation();
              onRemove(item.symbol);
            }}
            className="text-gray-400 hover:text-red-500 transition-colors"
          >
            <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
            </svg>
          </button>
        </div>
      </td>
      <td className="py-3 px-4">{formatCurrency(item.price)}</td>
      <td className="py-3 px-4">
        <span className={item.change24h >= 0 ? 'text-green-500' : 'text-red-500'}>
          {formatPercentage(item.change24h)}
        </span>
      </td>
      <td className="py-3 px-4">
        <div className="flex flex-col">
          <span className="text-xs text-gray-400">H: {formatCurrency(item.high24h)}</span>
          <span className="text-xs text-gray-400">L: {formatCurrency(item.low24h)}</span>
        </div>
      </td>
      <td className="py-3 px-4">{formatCurrency(item.volume24h)}</td>
    </tr>
  );
};

const Watchlist: React.FC = () => {
  const dispatch = useDispatch();
  const { items, loading, error } = useSelector((state: any) => state.trading.watchlist);
  const [newSymbol, setNewSymbol] = useState('');
  const [filter, setFilter] = useState('');

  useEffect(() => {
    dispatch(fetchWatchlist());
    
    const interval = setInterval(() => {
      dispatch(fetchWatchlist());
    }, 10000);

    return () => clearInterval(interval);
  }, [dispatch]);

  const handleAddSymbol = () => {
    if (newSymbol) {
      dispatch(addToWatchlist(newSymbol.toUpperCase()));
      setNewSymbol('');
    }
  };

  const handleRemoveSymbol = (symbol: string) => {
    dispatch(removeFromWatchlist(symbol));
  };

  const handleSelectSymbol = (symbol: string) => {
    // Navigate to trading view or update selected symbol
    console.log('Selected symbol:', symbol);
  };

  const filteredItems = items.filter((item: WatchlistItem) =>
    item.symbol.toLowerCase().includes(filter.toLowerCase())
  );

  if (loading && !items.length) {
    return <Loading />;
  }

  return (
    <div className="bg-gray-800 rounded-lg overflow-hidden">
      <div className="p-4 border-b border-gray-700">
        <h2 className="text-xl font-semibold mb-4">Watchlist</h2>
        
        <div className="flex space-x-2">
          <Input
            value={newSymbol}
            onChange={(e) => setNewSymbol(e.target.value)}
            placeholder="Add symbol (e.g., BTC/USD)"
            className="flex-1"
          />
          <Button onClick={handleAddSymbol}>Add</Button>
        </div>

        <Input
          value={filter}
          onChange={(e) => setFilter(e.target.value)}
          placeholder="Filter symbols..."
          className="mt-2"
        />
      </div>

      {error ? (
        <div className="text-red-500 p-4">
          Failed to load watchlist: {error}
        </div>
      ) : (
        <div className="overflow-x-auto">
          <table className="w-full">
            <thead className="bg-gray-700">
              <tr>
                <th className="py-3 px-4 text-left">Symbol</th>
                <th className="py-3 px-4 text-left">Price</th>
                <th className="py-3 px-4 text-left">24h Change</th>
                <th className="py-3 px-4 text-left">24h High/Low</th>
                <th className="py-3 px-4 text-left">Volume</th>
              </tr>
            </thead>
            <tbody>
              {filteredItems.map((item: WatchlistItem) => (
                <WatchlistRow
                  key={item.symbol}
                  item={item}
                  onRemove={handleRemoveSymbol}
                  onSelect={handleSelectSymbol}
                />
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  );
};

export default Watchlist;