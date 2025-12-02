import React, { useState } from 'react';
import { useDispatch } from 'react-redux';
import Button from '../common/Button';
import Input from '../common/Input';
import Select from '../common/Select';
import { submitOrder } from '../../store/slices/tradingSlice';
import { isValidNumber } from '../../utils/validators';

interface OrderFormProps {
  symbol: string;
  currentPrice: number;
}

type OrderType = 'MARKET' | 'LIMIT' | 'STOP' | 'STOP_LIMIT';
type OrderSide = 'BUY' | 'SELL';

const OrderForm: React.FC<OrderFormProps> = ({ symbol, currentPrice }) => {
  const dispatch = useDispatch();
  
  // Form state
  const [orderType, setOrderType] = useState<OrderType>('MARKET');
  const [side, setSide] = useState<OrderSide>('BUY');
  const [amount, setAmount] = useState('');
  const [price, setPrice] = useState(currentPrice.toString());
  const [stopPrice, setStopPrice] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  // Handle form submission
  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError(null);
    setLoading(true);

    try {
      const orderData = {
        symbol,
        type: orderType,
        side,
        amount: parseFloat(amount),
        price: orderType !== 'MARKET' ? parseFloat(price) : undefined,
        stopPrice: ['STOP', 'STOP_LIMIT'].includes(orderType) ? parseFloat(stopPrice) : undefined,
      };

      await dispatch(submitOrder(orderData));
      // Reset form after successful submission
      setAmount('');
      setPrice(currentPrice.toString());
      setStopPrice('');
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to submit order');
    } finally {
      setLoading(false);
    }
  };

  // Calculate total order value
  const calculateTotal = () => {
    const amountNum = parseFloat(amount) || 0;
    const priceNum = parseFloat(price) || currentPrice;
    return (amountNum * priceNum).toFixed(2);
  };

  return (
    <form onSubmit={handleSubmit} className="space-y-4 p-4 bg-gray-800 rounded-lg">
      {/* Order Type Selection */}
      <div className="flex space-x-2">
        <Button
          type="button"
          variant={side === 'BUY' ? 'success' : 'secondary'}
          onClick={() => setSide('BUY')}
          fullWidth
        >
          Buy
        </Button>
        <Button
          type="button"
          variant={side === 'SELL' ? 'danger' : 'secondary'}
          onClick={() => setSide('SELL')}
          fullWidth
        >
          Sell
        </Button>
      </div>

      <Select
        label="Order Type"
        value={orderType}
        onChange={(value) => setOrderType(value as OrderType)}
        options={[
          { value: 'MARKET', label: 'Market' },
          { value: 'LIMIT', label: 'Limit' },
          { value: 'STOP', label: 'Stop' },
          { value: 'STOP_LIMIT', label: 'Stop Limit' }
        ]}
      />

      <Input
        label="Amount"
        type="number"
        value={amount}
        onChange={(e) => setAmount(e.target.value)}
        placeholder="0.00"
        required
        min="0"
        step="0.0001"
      />

      {orderType !== 'MARKET' && (
        <Input
          label="Price"
          type="number"
          value={price}
          onChange={(e) => setPrice(e.target.value)}
          placeholder={currentPrice.toString()}
          required
          min="0"
          step="0.01"
        />
      )}

      {['STOP', 'STOP_LIMIT'].includes(orderType) && (
        <Input
          label="Stop Price"
          type="number"
          value={stopPrice}
          onChange={(e) => setStopPrice(e.target.value)}
          placeholder="0.00"
          required
          min="0"
          step="0.01"
        />
      )}

      <div className="flex justify-between text-sm text-gray-400">
        <span>Total</span>
        <span>${calculateTotal()}</span>
      </div>

      {error && (
        <div className="text-red-500 text-sm">{error}</div>
      )}

      <Button
        type="submit"
        variant={side === 'BUY' ? 'success' : 'danger'}
        fullWidth
        isLoading={loading}
      >
        {side === 'BUY' ? 'Buy' : 'Sell'} {symbol}
      </Button>
    </form>
  );
};

export default OrderForm;