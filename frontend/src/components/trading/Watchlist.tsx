import React, { useEffect, useState } from 'react';
import { formatCurrency, formatPercentage } from '../../utils/formatters';
import { Button } from '../common/Button';
import { Input } from '../common/Input';
import Loading from '../common/Loading';
import { isValidSymbol } from '../../utils/validators';
import { logger } from '../../utils/logger';

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
          <span className="font-medium text-white">{item.symbol}</span>
          <button
            onClick={(e) => {
              e.stopPropagation();
              onRemove(item.symbol);
            }}
            className="text-gray-400 hover:text-red-500 transition-colors p-1 rounded hover:bg-gray-600"
            title="Remove from watchlist"
          >
            <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
            </svg>
          </button>
        </div>
      </td>
      <td className="py-3 px-4 text-white font-medium">
        {formatCurrency(item.price)}
      </td>
      <td className="py-3 px-4">
        <span className={`font-medium ${item.change24h >= 0 ? 'text-green-400' : 'text-red-400'}`}>
          {formatPercentage(item.change24h)}
        </span>
      </td>
      <td className="py-3 px-4">
        <div className="flex flex-col text-sm">
          <span className="text-green-400">H: {formatCurrency(item.high24h)}</span>
          <span className="text-red-400">L: {formatCurrency(item.low24h)}</span>
        </div>
      </td>
      <td className="py-3 px-4 text-gray-300">
        {(item.volume24h / 1000000).toFixed(2)}M
      </td>
    </tr>
  );
};

const Watchlist: React.FC<{ onSymbolSelect?: (symbol: string) => void }> = ({ 
  onSymbolSelect 
}) => {
  const [items, setItems] = useState<WatchlistItem[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [newSymbol, setNewSymbol] = useState('');
  const [filter, setFilter] = useState('');
  const [addingSymbol, setAddingSymbol] = useState(false);

  useEffect(() => {
    const loadWatchlist = async () => {
      try {
        setLoading(true);
        setError(null);
        
        // Mock watchlist data
        const mockItems: WatchlistItem[] = [
          {
            symbol: 'AAPL',
            price: 150.25,
            change24h: 2.5,
            volume24h: 45000000,
            high24h: 152.50,
            low24h: 148.00,
          },
          {
            symbol: 'MSFT',
            price: 310.75,
            change24h: -1.2,
            volume24h: 32000000,
            high24h: 315.00,
            low24h: 308.50,
          },
          {
            symbol: 'GOOGL',
            price: 140.85,
            change24h: 0.8,
            volume24h: 28000000,
            high24h: 142.20,
            low24h: 139.50,
          },
          {
            symbol: 'TSLA',
            price: 245.60,
            change24h: -3.2,
            volume24h: 55000000,
            high24h: 252.00,
            low24h: 243.10,
          },
          {
            symbol: 'NVDA',
            price: 450.20,
            change24h: 5.7,
            volume24h: 38000000,
            high24h: 458.90,
            low24h: 442.30,
          },
        ];

        setTimeout(() => {
          setItems(mockItems);
          setLoading(false);
        }, 1000);
      } catch (err) {
        setError(err instanceof Error ? err.message : 'Failed to load watchlist');
        setLoading(false);
      }
    };

    loadWatchlist();
    
    const interval = setInterval(loadWatchlist, 10000);
    return () => clearInterval(interval);
  }, []);

  const handleAddSymbol = async () => {
    const trimmedSymbol = newSymbol.trim().toUpperCase();
    
    if (!trimmedSymbol) {
      setError('Please enter a symbol');
      return;
    }
    
    if (!isValidSymbol(trimmedSymbol)) {
      setError('Please enter a valid symbol (e.g., AAPL, MSFT)');
      return;
    }
    
    if (items.some(item => item.symbol === trimmedSymbol)) {
      setError('Symbol already in watchlist');
      return;
    }

    try {
      setAddingSymbol(true);
      setError(null);
      
      // Mock adding symbol
      const newItem: WatchlistItem = {
        symbol: trimmedSymbol,
        price: Math.random() * 200 + 50,
        change24h: (Math.random() - 0.5) * 10,
        volume24h: Math.random() * 50000000,
        high24h: 0,
        low24h: 0,
      };
      
      newItem.high24h = newItem.price * 1.05;
      newItem.low24h = newItem.price * 0.95;

      setTimeout(() => {
        setItems(prev => [...prev, newItem]);
        setNewSymbol('');
        setAddingSymbol(false);
      }, 500);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to add symbol');
      setAddingSymbol(false);
    }
  };

  const handleRemoveSymbol = async (symbol: string) => {
    try {
      setItems(prev => prev.filter(item => item.symbol !== symbol));
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to remove symbol');
    }
  };

  const handleSelectSymbol = (symbol: string) => {
    if (onSymbolSelect) {
      onSymbolSelect(symbol);
    } else {
      logger.info('Selected symbol:', symbol);
    }
  };

  const handleKeyPress = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter') {
      handleAddSymbol();
    }
  };

  const filteredItems = items.filter((item: WatchlistItem) =>
    item.symbol.toLowerCase().includes(filter.toLowerCase())
  );

  if (loading && items.length === 0) {
    return (
      <div className="bg-gray-800 rounded-lg p-6">
        <Loading text="Loading watchlist..." />
      </div>
    );
  }

  return (
    <div className="bg-gray-800 rounded-lg overflow-hidden">
      <div className="p-4 border-b border-gray-700">
        <h2 className="text-xl font-semibold mb-4 text-white">Watchlist</h2>
        
        <div className="flex space-x-2 mb-3">
          <Input
            value={newSymbol}
            onChange={(e) => {
              setNewSymbol(e.target.value);
              if (error) setError(null);
            }}
            onKeyPress={handleKeyPress}
            placeholder="Add symbol (e.g., AAPL)"
            className="flex-1"
          />
          <Button 
            onClick={handleAddSymbol}
            isLoading={addingSymbol}
            disabled={!newSymbol.trim()}
          >
            Add
          </Button>
        </div>

        <Input
          value={filter}
          onChange={(e) => setFilter(e.target.value)}
          placeholder="Filter symbols..."
        />
        
        {error && (
          <div className="mt-3 bg-red-900/30 border border-red-500 rounded p-2 text-red-300 text-sm">
            {error}
          </div>
        )}
      </div>

      {filteredItems.length > 0 ? (
        <div className="overflow-x-auto">
          <table className="w-full">
            <thead className="bg-gray-700">
              <tr>
                <th className="py-3 px-4 text-left text-sm font-medium text-gray-300">Symbol</th>
                <th className="py-3 px-4 text-left text-sm font-medium text-gray-300">Price</th>
                <th className="py-3 px-4 text-left text-sm font-medium text-gray-300">24h Change</th>
                <th className="py-3 px-4 text-left text-sm font-medium text-gray-300">24h High/Low</th>
                <th className="py-3 px-4 text-left text-sm font-medium text-gray-300">Volume</th>
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
      ) : (
        <div className="p-8 text-center text-gray-400">
          <p className="text-lg">
            {filter ? 'No symbols match your filter' : 'No symbols in watchlist'}
          </p>
          <p className="text-sm mt-1">
            {filter ? 'Try a different filter' : 'Add symbols to track their prices'}
          </p>
        </div>
      )}
      
      {loading && items.length > 0 && (
        <div className="p-3 border-t border-gray-700 text-center">
          <div className="flex items-center justify-center text-sm text-gray-400">
            <div className="w-3 h-3 border border-gray-600 border-t-blue-500 rounded-full animate-spin mr-2" />
            Updating prices...
          </div>
        </div>
      )}
    </div>
  );
};

export default Watchlist;