import React, { useEffect, useState } from 'react';
import { useDispatch, useSelector } from 'react-redux';
import { RootState } from '../../store/store';
import { fetchPortfolio, updatePosition, Position } from '../../store/slices/tradingSlice';
import { Card } from '../common/Card';
import { Button } from '../common/Button';
import { formatCurrency, formatPercentage } from '../../utils/formatters';
import { useMarketWebSocket } from '../../hooks/useMarketWebSocket';

interface PositionsListProps {
  onSelectPosition?: (position: Position) => void;
  showActions?: boolean;
}

export const PositionsList: React.FC<PositionsListProps> = ({
  onSelectPosition,
  showActions = true,
}) => {
  const dispatch = useDispatch();
  const { positions, portfolio, loading, error } = useSelector((state: RootState) => state.trading);
  const [sortBy, setSortBy] = useState<'symbol' | 'pnl' | 'value'>('value');
  const [sortOrder, setSortOrder] = useState<'asc' | 'desc'>('desc');

  // Subscribe to real-time price updates for all positions
  const symbols = positions.map(p => p.symbol);
  const { quotes, isConnected, subscribe } = useMarketWebSocket({ autoConnect: true });

  useEffect(() => {
    dispatch(fetchPortfolio() as any);
  }, [dispatch]);

  // Subscribe to symbols when positions change
  useEffect(() => {
    if (isConnected && symbols.length > 0) {
      subscribe(symbols);
    }
  }, [isConnected, symbols.length, subscribe]);

  // Update positions with real-time prices
  useEffect(() => {
    if (quotes && Object.keys(quotes).length > 0) {
      positions.forEach(position => {
        const quote = quotes[position.symbol];
        if (quote && quote.price !== position.current_price) {
          const updatedPosition: Position = {
            ...position,
            current_price: quote.price,
            market_value: quote.price * position.quantity,
            unrealized_pnl: (quote.price - position.avg_cost) * position.quantity,
            unrealized_pnl_percent: ((quote.price - position.avg_cost) / position.avg_cost) * 100,
            last_updated: new Date().toISOString(),
          };
          dispatch(updatePosition(updatedPosition));
        }
      });
    }
  }, [quotes, positions, dispatch]);

  const sortedPositions = [...positions].sort((a, b) => {
    let aValue: number, bValue: number;
    
    switch (sortBy) {
      case 'symbol':
        return sortOrder === 'asc' 
          ? a.symbol.localeCompare(b.symbol)
          : b.symbol.localeCompare(a.symbol);
      case 'pnl':
        aValue = a.unrealized_pnl;
        bValue = b.unrealized_pnl;
        break;
      case 'value':
        aValue = a.market_value;
        bValue = b.market_value;
        break;
      default:
        return 0;
    }
    
    return sortOrder === 'asc' ? aValue - bValue : bValue - aValue;
  });

  const handleSort = (field: 'symbol' | 'pnl' | 'value') => {
    if (sortBy === field) {
      setSortOrder(sortOrder === 'asc' ? 'desc' : 'asc');
    } else {
      setSortBy(field);
      setSortOrder('desc');
    }
  };

  const getTotalPortfolioValue = () => {
    return positions.reduce((total, pos) => total + pos.market_value, 0);
  };

  const getTotalPnL = () => {
    return positions.reduce((total, pos) => total + pos.unrealized_pnl, 0);
  };

  const getPositionAllocation = (position: Position) => {
    const totalValue = getTotalPortfolioValue();
    return totalValue > 0 ? (position.market_value / totalValue) * 100 : 0;
  };

  if (loading) {
    return (
      <Card className="p-6">
        <div className="animate-pulse space-y-4">
          <div className="h-4 bg-gray-200 rounded w-1/4"></div>
          <div className="space-y-2">
            {[1, 2, 3].map(i => (
              <div key={i} className="h-12 bg-gray-100 rounded"></div>
            ))}
          </div>
        </div>
      </Card>
    );
  }

  if (error) {
    return (
      <Card className="p-6">
        <div className="text-red-600">
          <p className="font-medium">Error loading positions</p>
          <p className="text-sm">{error}</p>
        </div>
      </Card>
    );
  }

  if (positions.length === 0) {
    return (
      <Card className="p-6 text-center">
        <div className="text-gray-500">
          <p className="font-medium">No positions found</p>
          <p className="text-sm">Start trading to see your positions here</p>
        </div>
      </Card>
    );
  }

  return (
    <div className="space-y-4">
      {/* Portfolio Summary */}
      <Card className="p-4">
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
          <div>
            <p className="text-sm text-gray-500">Total Value</p>
            <p className="text-lg font-semibold">{formatCurrency(getTotalPortfolioValue())}</p>
          </div>
          <div>
            <p className="text-sm text-gray-500">Total P&L</p>
            <p className={`text-lg font-semibold ${getTotalPnL() >= 0 ? 'text-green-600' : 'text-red-600'}`}>
              {formatCurrency(getTotalPnL())}
            </p>
          </div>
          <div>
            <p className="text-sm text-gray-500">Cash Balance</p>
            <p className="text-lg font-semibold">{formatCurrency(portfolio.balance)}</p>
          </div>
          <div className="flex items-center space-x-2">
            <div className={`w-2 h-2 rounded-full ${isConnected ? 'bg-green-500' : 'bg-red-500'}`}></div>
            <span className="text-sm text-gray-500">
              {isConnected ? 'Live Data' : 'Disconnected'}
            </span>
          </div>
        </div>
      </Card>

      {/* Positions Table */}
      <Card className="overflow-hidden">
        <div className="px-4 py-3 bg-gray-50 border-b">
          <h3 className="text-lg font-medium">Positions ({positions.length})</h3>
        </div>
        
        {/* Table Header */}
        <div className="grid grid-cols-6 gap-4 px-4 py-2 bg-gray-50 text-sm font-medium text-gray-700 border-b">
          <button 
            onClick={() => handleSort('symbol')}
            className="text-left hover:text-blue-600 focus:outline-none"
          >
            Symbol {sortBy === 'symbol' && (sortOrder === 'asc' ? '↑' : '↓')}
          </button>
          <div>Quantity</div>
          <div>Avg Cost</div>
          <div>Current Price</div>
          <button 
            onClick={() => handleSort('value')}
            className="text-left hover:text-blue-600 focus:outline-none"
          >
            Market Value {sortBy === 'value' && (sortOrder === 'asc' ? '↑' : '↓')}
          </button>
          <button 
            onClick={() => handleSort('pnl')}
            className="text-left hover:text-blue-600 focus:outline-none"
          >
            P&L {sortBy === 'pnl' && (sortOrder === 'asc' ? '↑' : '↓')}
          </button>
        </div>

        {/* Position Rows */}
        <div className="divide-y">
          {sortedPositions.map((position) => (
            <div 
              key={position.id}
              className={`grid grid-cols-6 gap-4 px-4 py-3 hover:bg-gray-50 transition-colors ${
                onSelectPosition ? 'cursor-pointer' : ''
              }`}
              onClick={() => onSelectPosition?.(position)}
            >
              <div>
                <div className="font-medium">{position.symbol}</div>
                <div className="text-xs text-gray-500">
                  {formatPercentage(getPositionAllocation(position))} of portfolio
                </div>
              </div>
              
              <div>
                <div className="font-medium">{position.quantity.toLocaleString()}</div>
                <div className="text-xs text-gray-500">{position.side}</div>
              </div>
              
              <div className="font-medium">
                {formatCurrency(position.avg_cost)}
              </div>
              
              <div>
                <div className="font-medium">{formatCurrency(position.current_price)}</div>
                {quotes[position.symbol] && (
                  <div className="text-xs text-green-500">Live</div>
                )}
              </div>
              
              <div className="font-medium">
                {formatCurrency(position.market_value)}
              </div>
              
              <div>
                <div className={`font-medium ${position.unrealized_pnl >= 0 ? 'text-green-600' : 'text-red-600'}`}>
                  {formatCurrency(position.unrealized_pnl)}
                </div>
                <div className={`text-xs ${position.unrealized_pnl >= 0 ? 'text-green-600' : 'text-red-600'}`}>
                  {formatPercentage(position.unrealized_pnl_percent)}
                </div>
              </div>
            </div>
          ))}
        </div>
      </Card>

      {showActions && (
        <div className="flex justify-end space-x-2">
          <Button 
            variant="outline" 
            onClick={() => dispatch(fetchPortfolio() as any)}
          >
            Refresh
          </Button>
        </div>
      )}
    </div>
  );
};