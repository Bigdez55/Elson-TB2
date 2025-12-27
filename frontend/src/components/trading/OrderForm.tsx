import React, { useState, useMemo } from 'react';
import { Link } from 'react-router-dom';
import { Button } from '../common/Button';
import { useExecuteTradeMutation } from '../../services/tradingApi';
import { useTradingContext } from '../../contexts/TradingContext';
import { validateOrderAmount, validatePrice } from '../../utils/validators';
import { useGetMyPermissionsQuery, useListPermissionsQuery } from '../../services/educationApi';

interface OrderFormProps {
  symbol: string;
  currentPrice: number;
  availableBalance?: number;
}

type OrderType = 'MARKET' | 'LIMIT' | 'STOP' | 'STOP_LIMIT';
type OrderSide = 'BUY' | 'SELL';

const OrderForm: React.FC<OrderFormProps> = ({
  symbol,
  currentPrice,
  availableBalance = 10000
}) => {
  const { mode } = useTradingContext();
  const [executeTrade, { isLoading }] = useExecuteTradeMutation();

  // Permission checking
  const { data: userPermissions = [], isLoading: permissionsLoading } = useGetMyPermissionsQuery();
  const { data: allPermissions = [], isLoading: allPermissionsLoading } = useListPermissionsQuery();

  // Form state
  const [orderType, setOrderType] = useState<OrderType>('MARKET');
  const [side, setSide] = useState<OrderSide>('BUY');
  const [amount, setAmount] = useState('');
  const [price, setPrice] = useState(currentPrice.toString());
  const [stopPrice, setStopPrice] = useState('');
  const [error, setError] = useState<string | null>(null);
  const [success, setSuccess] = useState<string | null>(null);

  // Check if user has stock trading permission
  const hasStockTradingPermission = useMemo(() => {
    if (permissionsLoading || allPermissionsLoading) return false;

    // Find the stock trading permission definition
    const stockTradingPerm = allPermissions.find(p =>
      p.permission_type === 'trade_stocks' || p.name.toLowerCase().includes('stock trading')
    );

    if (!stockTradingPerm) return true; // If permission doesn't exist, allow trading

    // Check if user has this permission granted
    const userPerm = userPermissions.find(up =>
      up.permission_id === stockTradingPerm.id && up.is_granted
    );

    return !!userPerm;
  }, [userPermissions, allPermissions, permissionsLoading, allPermissionsLoading]);

  // Get required permission info for display
  const requiredPermission = useMemo(() => {
    if (allPermissionsLoading) return null;
    return allPermissions.find(p =>
      p.permission_type === 'trade_stocks' || p.name.toLowerCase().includes('stock trading')
    );
  }, [allPermissions, allPermissionsLoading]);

  // Handle form submission
  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError(null);
    setSuccess(null);

    // Check trading permission (only in live mode)
    if (mode === 'live' && !hasStockTradingPermission) {
      setError('You need to complete educational requirements before trading. Visit the Learn page to get started.');
      return;
    }

    try {
      // Validation
      const amountError = validateOrderAmount(amount, availableBalance);
      if (amountError) {
        setError(amountError);
        return;
      }

      if (orderType !== 'MARKET') {
        const priceError = validatePrice(price);
        if (priceError) {
          setError(priceError);
          return;
        }
      }

      if (['STOP', 'STOP_LIMIT'].includes(orderType)) {
        const stopPriceError = validatePrice(stopPrice);
        if (stopPriceError) {
          setError(`Stop price: ${stopPriceError}`);
          return;
        }
      }

      // Map local order type to API order type
      const apiOrderType: 'MARKET' | 'LIMIT' | 'STOP_LIMIT' | 'STOP_LOSS' =
        orderType === 'STOP' ? 'STOP_LOSS' : orderType as 'MARKET' | 'LIMIT' | 'STOP_LIMIT';

      const orderData = {
        symbol,
        trade_type: side,
        order_type: apiOrderType,
        quantity: parseFloat(amount),
        price: orderType !== 'MARKET' ? parseFloat(price) : undefined,
        stop_price: ['STOP', 'STOP_LIMIT'].includes(orderType) ? parseFloat(stopPrice) : undefined,
        mode,
      };

      const result = await executeTrade(orderData).unwrap();

      // Reset form after successful submission
      setAmount('');
      setPrice(currentPrice.toString());
      setStopPrice('');
      setSuccess(`${side} order for ${amount} ${symbol} submitted successfully! Order ID: ${result.trade_id}`);
    } catch (err: any) {
      setError(err?.data?.message || err?.message || 'Failed to submit order');
    }
  };

  // Calculate total order value
  const calculateTotal = () => {
    const amountNum = parseFloat(amount) || 0;
    const priceNum = parseFloat(price) || currentPrice;
    return (amountNum * priceNum).toFixed(2);
  };

  return (
    <div className="bg-gray-900 rounded-xl p-6">
      <div className="flex justify-between items-center mb-6">
        <h3 className="text-lg font-medium text-white">Place Order</h3>
        <div className="flex space-x-2">
          <button
            type="button"
            onClick={() => setSide('BUY')}
            className={`px-4 py-1 rounded-lg text-sm transition-colors ${
              side === 'BUY'
                ? 'bg-green-600 text-white'
                : 'bg-gray-800 text-gray-400 hover:bg-green-600 hover:text-white'
            }`}
          >
            Buy
          </button>
          <button
            type="button"
            onClick={() => setSide('SELL')}
            className={`px-4 py-1 rounded-lg text-sm transition-colors ${
              side === 'SELL'
                ? 'bg-red-600 text-white'
                : 'bg-gray-800 text-gray-400 hover:bg-red-600 hover:text-white'
            }`}
          >
            Sell
          </button>
        </div>
      </div>

      {/* Permission Warning Banner - Live Mode Only */}
      {mode === 'live' && !hasStockTradingPermission && !permissionsLoading && (
        <div className="mb-4 bg-yellow-900/30 border border-yellow-600 rounded-lg p-4">
          <div className="flex items-start space-x-3">
            <span className="text-2xl">🔒</span>
            <div className="flex-1">
              <h4 className="text-yellow-300 font-semibold mb-1">Educational Requirements Needed</h4>
              <p className="text-yellow-200 text-sm mb-3">
                {requiredPermission?.description || 'You need to complete educational requirements before you can trade stocks in live mode.'}
              </p>
              <Link
                to="/learn"
                className="inline-block bg-yellow-600 hover:bg-yellow-700 text-white text-sm font-medium px-4 py-2 rounded-lg transition-colors"
              >
                Complete Learning Requirements
              </Link>
              <p className="text-yellow-200/70 text-xs mt-2">
                Paper trading is available without restrictions. Switch to Paper mode to practice risk-free.
              </p>
            </div>
          </div>
        </div>
      )}

      {/* Loading State for Permissions */}
      {permissionsLoading && mode === 'live' && (
        <div className="mb-4 bg-gray-800 border border-gray-700 rounded-lg p-4">
          <div className="flex items-center space-x-3">
            <div className="animate-spin rounded-full h-5 w-5 border-b-2 border-purple-500"></div>
            <span className="text-gray-400 text-sm">Checking trading permissions...</span>
          </div>
        </div>
      )}

      <form onSubmit={handleSubmit} className="space-y-4">
        {/* Order Type */}
        <div>
          <label className="block text-gray-400 text-sm mb-1">Order Type</label>
          <select
            value={orderType}
            onChange={(e) => setOrderType(e.target.value as OrderType)}
            className="bg-gray-800 border border-gray-700 rounded-lg p-2 w-full text-white focus:outline-none focus:border-purple-500 transition-colors"
          >
            <option value="MARKET">Market Order</option>
            <option value="LIMIT">Limit Order</option>
            <option value="STOP">Stop Order</option>
            <option value="STOP_LIMIT">Stop Limit Order</option>
          </select>
        </div>

        {/* Quantity */}
        <div>
          <label className="block text-gray-400 text-sm mb-1">Quantity</label>
          <div className="flex">
            <input
              type="number"
              value={amount}
              onChange={(e) => setAmount(e.target.value)}
              placeholder="10"
              className="bg-gray-800 border border-gray-700 rounded-l-lg p-2 w-full text-white focus:outline-none focus:border-purple-500 transition-colors"
              min="0"
              step="0.0001"
              required
            />
            <button
              type="button"
              className="bg-gray-700 border border-gray-700 rounded-r-lg px-3 text-white"
            >
              Shares
            </button>
          </div>
        </div>

        {/* Market Price */}
        <div>
          <label className="block text-gray-400 text-sm mb-1">Market Price</label>
          <input
            type="text"
            value={`$${currentPrice.toFixed(2)}`}
            disabled
            className="bg-gray-800 border border-gray-700 rounded-lg p-2 w-full text-white opacity-70"
          />
        </div>

        {/* Price (for non-market orders) */}
        {orderType !== 'MARKET' && (
          <div>
            <label className="block text-gray-400 text-sm mb-1">Limit Price</label>
            <input
              type="number"
              value={price}
              onChange={(e) => setPrice(e.target.value)}
              placeholder={currentPrice.toString()}
              className="bg-gray-800 border border-gray-700 rounded-lg p-2 w-full text-white focus:outline-none focus:border-purple-500 transition-colors"
              min="0"
              step="0.01"
              required
            />
          </div>
        )}

        {/* Stop Price (for stop orders) */}
        {['STOP', 'STOP_LIMIT'].includes(orderType) && (
          <div>
            <label className="block text-gray-400 text-sm mb-1">Stop Price</label>
            <input
              type="number"
              value={stopPrice}
              onChange={(e) => setStopPrice(e.target.value)}
              placeholder="0.00"
              className="bg-gray-800 border border-gray-700 rounded-lg p-2 w-full text-white focus:outline-none focus:border-purple-500 transition-colors"
              min="0"
              step="0.01"
              required
            />
          </div>
        )}

        {/* Estimated Cost */}
        <div>
          <label className="block text-gray-400 text-sm mb-1">Estimated Cost</label>
          <input
            type="text"
            value={`$${calculateTotal()}`}
            disabled
            className="bg-gray-800 border border-gray-700 rounded-lg p-2 w-full text-white opacity-70"
          />
        </div>

        {/* Error Display */}
        {error && (
          <div className="bg-red-900/30 border border-red-500 rounded p-3 text-red-300 text-sm">
            {error}
          </div>
        )}

        {/* Success Display */}
        {success && (
          <div className="bg-green-900/30 border border-green-500 rounded p-3 text-green-300 text-sm">
            {success}
          </div>
        )}

        {/* Submit Button */}
        <div className="pt-2">
          <button
            type="submit"
            disabled={isLoading || (mode === 'live' && !hasStockTradingPermission)}
            className={`w-full rounded-lg p-3 font-medium transition-colors ${
              side === 'BUY'
                ? 'bg-green-600 hover:bg-green-700 text-white'
                : 'bg-red-600 hover:bg-red-700 text-white'
            } ${isLoading || (mode === 'live' && !hasStockTradingPermission) ? 'opacity-50 cursor-not-allowed' : ''}`}
          >
            {isLoading ? 'Processing...' :
             mode === 'live' && !hasStockTradingPermission ? '🔒 Complete Education to Trade' :
             `${side === 'BUY' ? 'Buy' : 'Sell'} ${amount || '0'} ${symbol} Shares`}
          </button>
        </div>

        {/* Terms & Conditions */}
        <div className="pt-3">
          <p className="text-gray-400 text-xs">
            By placing this order, you agree to our{' '}
            <a href="#" className="text-purple-400 hover:text-purple-300">Terms of Service</a>
            {' '}and acknowledge you have read our{' '}
            <a href="#" className="text-purple-400 hover:text-purple-300">Risk Disclosure</a>.
          </p>
        </div>
      </form>
    </div>
  );
};

export default OrderForm;