import React, { useEffect, useState } from 'react';
import { useDispatch, useSelector } from 'react-redux';
import { RootState } from '../../store/store';
import { fetchOrders, fetchTrades, cancelOrder, Order, Trade } from '../../store/slices/tradingSlice';
import { Card } from '../common/Card';
import { Button } from '../common/Button';
import { Badge } from '../common/Badge';
import { Tabs } from '../common/Tabs';
import { formatCurrency, formatDate } from '../../utils/formatters';

interface OrderHistoryProps {
  onOrderSelect?: (order: Order) => void;
  showPendingOnly?: boolean;
}

export const OrderHistory: React.FC<OrderHistoryProps> = ({
  onOrderSelect,
  showPendingOnly = false,
}) => {
  const dispatch = useDispatch();
  const { orders, trades, pendingOrders, loading, error } = useSelector((state: RootState) => state.trading);
  const [activeTab, setActiveTab] = useState<'pending' | 'filled' | 'all'>('pending');
  const [sortBy, setSortBy] = useState<'created_at' | 'symbol' | 'status'>('created_at');
  const [sortOrder, setSortOrder] = useState<'asc' | 'desc'>('desc');

  useEffect(() => {
    dispatch(fetchOrders() as any);
    dispatch(fetchTrades() as any);
  }, [dispatch]);

  const handleCancelOrder = async (orderId: string) => {
    if (window.confirm('Are you sure you want to cancel this order?')) {
      dispatch(cancelOrder(orderId) as any);
    }
  };

  const getStatusBadgeColor = (status: string) => {
    switch (status) {
      case 'filled':
        return 'green';
      case 'pending':
        return 'yellow';
      case 'partially_filled':
        return 'blue';
      case 'cancelled':
        return 'gray';
      case 'rejected':
        return 'red';
      default:
        return 'gray';
    }
  };

  const getOrderTypeDisplay = (order: Order) => {
    let display = order.order_type;
    if (order.price && order.order_type === 'limit') {
      display += ` @ ${formatCurrency(order.price)}`;
    }
    if (order.stop_price && order.order_type.includes('stop')) {
      display += ` (Stop: ${formatCurrency(order.stop_price)})`;
    }
    return display;
  };

  const getFilteredOrders = () => {
    let filtered = orders;
    
    if (showPendingOnly || activeTab === 'pending') {
      filtered = orders.filter(order => order.status === 'pending');
    } else if (activeTab === 'filled') {
      filtered = orders.filter(order => order.status === 'filled' || order.status === 'partially_filled');
    }
    
    return filtered.sort((a, b) => {
      let aValue: any, bValue: any;
      
      switch (sortBy) {
        case 'symbol':
          aValue = a.symbol;
          bValue = b.symbol;
          break;
        case 'status':
          aValue = a.status;
          bValue = b.status;
          break;
        case 'created_at':
        default:
          aValue = new Date(a.created_at).getTime();
          bValue = new Date(b.created_at).getTime();
          break;
      }
      
      if (typeof aValue === 'string') {
        return sortOrder === 'asc' 
          ? aValue.localeCompare(bValue)
          : bValue.localeCompare(aValue);
      }
      
      return sortOrder === 'asc' ? aValue - bValue : bValue - aValue;
    });
  };

  const handleSort = (field: typeof sortBy) => {
    if (sortBy === field) {
      setSortOrder(sortOrder === 'asc' ? 'desc' : 'asc');
    } else {
      setSortBy(field);
      setSortOrder('desc');
    }
  };

  const tabs = [
    { id: 'pending', label: `Pending (${pendingOrders.length})` },
    { id: 'filled', label: 'Filled' },
    { id: 'all', label: 'All Orders' },
  ];

  if (loading) {
    return (
      <Card className="p-6">
        <div className="animate-pulse space-y-4">
          <div className="h-4 bg-gray-200 rounded w-1/4"></div>
          <div className="space-y-2">
            {[1, 2, 3].map(i => (
              <div key={i} className="h-16 bg-gray-100 rounded"></div>
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
          <p className="font-medium">Error loading orders</p>
          <p className="text-sm">{error}</p>
        </div>
      </Card>
    );
  }

  const filteredOrders = getFilteredOrders();

  return (
    <div className="space-y-4">
      {!showPendingOnly && (
        <Card className="p-4">
          <Tabs
            tabs={tabs}
            activeTab={activeTab}
            onTabChange={setActiveTab as (tab: string) => void}
          />
        </Card>
      )}

      <Card className="overflow-hidden">
        <div className="px-4 py-3 bg-gray-50 border-b">
          <div className="flex justify-between items-center">
            <h3 className="text-lg font-medium">
              {showPendingOnly ? 'Pending Orders' : 'Order History'}
              {filteredOrders.length > 0 && ` (${filteredOrders.length})`}
            </h3>
            <Button 
              variant="outline" 
              size="sm"
              onClick={() => {
                dispatch(fetchOrders() as any);
                dispatch(fetchTrades() as any);
              }}
            >
              Refresh
            </Button>
          </div>
        </div>

        {filteredOrders.length === 0 ? (
          <div className="p-6 text-center text-gray-500">
            <p className="font-medium">No orders found</p>
            <p className="text-sm">
              {activeTab === 'pending' 
                ? 'No pending orders' 
                : 'Your order history will appear here'
              }
            </p>
          </div>
        ) : (
          <>
            {/* Table Header */}
            <div className="grid grid-cols-7 gap-4 px-4 py-2 bg-gray-50 text-sm font-medium text-gray-700 border-b">
              <button 
                onClick={() => handleSort('created_at')}
                className="text-left hover:text-blue-600 focus:outline-none"
              >
                Date {sortBy === 'created_at' && (sortOrder === 'asc' ? '↑' : '↓')}
              </button>
              <button 
                onClick={() => handleSort('symbol')}
                className="text-left hover:text-blue-600 focus:outline-none"
              >
                Symbol {sortBy === 'symbol' && (sortOrder === 'asc' ? '↑' : '↓')}
              </button>
              <div>Side</div>
              <div>Type</div>
              <div>Quantity</div>
              <button 
                onClick={() => handleSort('status')}
                className="text-left hover:text-blue-600 focus:outline-none"
              >
                Status {sortBy === 'status' && (sortOrder === 'asc' ? '↑' : '↓')}
              </button>
              <div>Actions</div>
            </div>

            {/* Order Rows */}
            <div className="divide-y">
              {filteredOrders.map((order) => (
                <div 
                  key={order.id}
                  className={`grid grid-cols-7 gap-4 px-4 py-3 hover:bg-gray-50 transition-colors ${
                    onOrderSelect ? 'cursor-pointer' : ''
                  }`}
                  onClick={() => onOrderSelect?.(order)}
                >
                  <div>
                    <div className="text-sm font-medium">
                      {formatDate(order.created_at)}
                    </div>
                    <div className="text-xs text-gray-500">
                      {new Date(order.created_at).toLocaleTimeString()}
                    </div>
                  </div>

                  <div className="font-medium">{order.symbol}</div>

                  <div>
                    <Badge 
                      color={order.side === 'buy' ? 'green' : 'red'}
                      size="sm"
                    >
                      {order.side.toUpperCase()}
                    </Badge>
                  </div>

                  <div>
                    <div className="text-sm font-medium">
                      {getOrderTypeDisplay(order)}
                    </div>
                    <div className="text-xs text-gray-500">
                      {order.time_in_force.toUpperCase()}
                    </div>
                  </div>

                  <div>
                    <div className="text-sm font-medium">
                      {order.filled_qty > 0 && order.filled_qty < order.quantity
                        ? `${order.filled_qty}/${order.quantity}`
                        : order.quantity.toLocaleString()
                      }
                    </div>
                    {order.remaining_qty > 0 && (
                      <div className="text-xs text-gray-500">
                        {order.remaining_qty} remaining
                      </div>
                    )}
                  </div>

                  <div>
                    <Badge 
                      color={getStatusBadgeColor(order.status)}
                      size="sm"
                    >
                      {order.status.replace('_', ' ').toUpperCase()}
                    </Badge>
                  </div>

                  <div className="flex space-x-2">
                    {order.status === 'pending' && (
                      <Button
                        variant="outline"
                        size="sm"
                        onClick={(e) => {
                          e.stopPropagation();
                          handleCancelOrder(order.id);
                        }}
                        className="text-red-600 hover:text-red-700"
                      >
                        Cancel
                      </Button>
                    )}
                  </div>
                </div>
              ))}
            </div>
          </>
        )}
      </Card>

      {/* Recent Trades Section */}
      {!showPendingOnly && trades.length > 0 && (
        <Card className="overflow-hidden">
          <div className="px-4 py-3 bg-gray-50 border-b">
            <h3 className="text-lg font-medium">Recent Trades</h3>
          </div>
          
          <div className="divide-y max-h-96 overflow-y-auto">
            {trades.slice(0, 10).map((trade) => (
              <div key={trade.id} className="px-4 py-3 flex justify-between items-center">
                <div className="flex-1">
                  <div className="flex items-center space-x-2">
                    <span className="font-medium">{trade.symbol}</span>
                    <Badge 
                      color={trade.side === 'buy' ? 'green' : 'red'}
                      size="sm"
                    >
                      {trade.side.toUpperCase()}
                    </Badge>
                    <Badge 
                      color={getStatusBadgeColor(trade.status)}
                      size="sm"
                    >
                      {trade.status.replace('_', ' ').toUpperCase()}
                    </Badge>
                  </div>
                  <div className="text-sm text-gray-500">
                    {trade.filled_qty > 0 ? trade.filled_qty : trade.quantity} shares
                    {trade.filled_avg_price && ` @ ${formatCurrency(trade.filled_avg_price)}`}
                  </div>
                </div>
                
                <div className="text-right">
                  <div className="text-sm font-medium">
                    {formatDate(trade.created_at)}
                  </div>
                  {trade.commission && (
                    <div className="text-xs text-gray-500">
                      Commission: {formatCurrency(trade.commission)}
                    </div>
                  )}
                </div>
              </div>
            ))}
          </div>
        </Card>
      )}
    </div>
  );
};