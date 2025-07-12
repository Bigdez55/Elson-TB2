import React, { useState, useEffect } from 'react';
import { useSelector } from 'react-redux';
import { useNavigate } from 'react-router-dom';
import { Button } from '../common/Button';
import { Input } from '../common/Input';
import { Select } from '../common/Select';
import { EducationalTooltip } from '../common/EducationalTooltip';
import { formatCurrency } from '../../utils/formatters';
import { tradingService } from '../../services/tradingService';
import { RootState } from '../../store/store';

interface DollarBasedInvestmentProps {
  onSuccess?: () => void;
  defaultSymbol?: string;
  isMinorAccount?: boolean;
}

export const DollarBasedInvestment: React.FC<DollarBasedInvestmentProps> = ({
  onSuccess,
  defaultSymbol = '',
  isMinorAccount = false,
}) => {
  // State for form fields
  const [symbol, setSymbol] = useState(defaultSymbol);
  const [amount, setAmount] = useState('');
  const [portfolio, setPortfolio] = useState('');
  const [isRecurring, setIsRecurring] = useState(false);
  const [frequency, setFrequency] = useState('monthly');
  
  // State for dynamic data
  const [symbolData, setSymbolData] = useState<{ price: number; name: string } | null>(null);
  const [estimatedShares, setEstimatedShares] = useState<number | null>(null);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState('');
  const [successMessage, setSuccessMessage] = useState('');
  
  // Get user portfolios from redux store
  const { portfolios } = useSelector((state: RootState) => state.user);
  const { minInvestmentAmount } = useSelector((state: RootState) => state.trading);
  
  const navigate = useNavigate();
  
  // Set default portfolio if available
  useEffect(() => {
    if (portfolios && portfolios.length > 0 && !portfolio) {
      setPortfolio(portfolios[0].id);
    }
  }, [portfolios, portfolio]);
  
  // Fetch symbol data when symbol changes
  useEffect(() => {
    if (!symbol) {
      setSymbolData(null);
      setEstimatedShares(null);
      return;
    }
    
    const fetchSymbolData = async () => {
      try {
        const data = await tradingService.getSymbolInfo(symbol);
        setSymbolData(data);
        
        // Calculate estimated shares if amount is provided
        if (amount && !isNaN(parseFloat(amount))) {
          const shares = parseFloat(amount) / data.price;
          setEstimatedShares(shares);
        }
      } catch (err) {
        console.error('Error fetching symbol data:', err);
        setError('Error fetching symbol information');
        setSymbolData(null);
      }
    };
    
    fetchSymbolData();
  }, [symbol, amount]);
  
  // Calculate estimated shares when amount changes
  useEffect(() => {
    if (symbolData && amount && !isNaN(parseFloat(amount))) {
      const shares = parseFloat(amount) / symbolData.price;
      setEstimatedShares(shares);
    } else {
      setEstimatedShares(null);
    }
  }, [amount, symbolData]);
  
  // Handle form submission
  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setIsLoading(true);
    setError('');
    setSuccessMessage('');
    
    try {
      // Validate input
      if (!symbol) {
        throw new Error('Please enter a valid stock symbol');
      }
      
      if (!amount || isNaN(parseFloat(amount)) || parseFloat(amount) <= 0) {
        throw new Error('Please enter a valid investment amount');
      }
      
      if (parseFloat(amount) < minInvestmentAmount) {
        throw new Error(`Minimum investment amount is $${minInvestmentAmount}`);
      }
      
      if (!portfolio) {
        throw new Error('Please select a portfolio');
      }
      
      if (isRecurring) {
        // Submit recurring investment
        const recurringOrder = {
          symbol,
          investment_amount: parseFloat(amount),
          portfolio_id: portfolio,
          trade_type: 'BUY',
          frequency,
          start_date: new Date().toISOString(),
        };
        
        const result = await tradingService.createRecurringInvestment(recurringOrder);
        
        setSuccessMessage(`Successfully set up recurring investment of $${amount} in ${symbol} ${frequency}!`);
      } else {
        // Submit one-time order
        const order = {
          symbol,
          investment_amount: parseFloat(amount),
          portfolio_id: portfolio,
          investment_type: 'DOLLAR_BASED',
          trade_type: 'BUY',
          is_fractional: true,
        };
        
        const result = await tradingService.submitOrder(order);
        
        if (isMinorAccount) {
          setSuccessMessage(`Order submitted for approval. Once approved, you'll invest $${amount} in ${symbol}.`);
        } else {
          setSuccessMessage(`Successfully invested $${amount} in ${symbol}!`);
        }
      }
      
      // Clear form
      setAmount('');
      setIsRecurring(false);
      
      // Callback if provided
      if (onSuccess) {
        onSuccess();
      }
    } catch (err: any) {
      console.error('Error submitting order:', err);
      setError(err.message || 'Error submitting investment order');
    } finally {
      setIsLoading(false);
    }
  };
  
  // Calculate a safe minimum investment (minimum $1, but respects configured minimum)
  const safeMinAmount = Math.max(1, minInvestmentAmount || 1);
  
  return (
    <div className="bg-white rounded-lg shadow-md p-4">
      <div className="flex items-center mb-4">
        <h2 className="text-xl font-semibold">Dollar-Based Investment</h2>
        <EducationalTooltip 
          content="Dollar-based investing lets you invest a specific dollar amount rather than buying whole shares. This makes it easier to invest smaller amounts and maintain specific portfolio allocations."
          position="right"
        />
      </div>
      
      {/* Error and success messages */}
      {error && (
        <div className="bg-red-100 border border-red-400 text-red-700 px-4 py-2 rounded mb-4">
          {error}
        </div>
      )}
      
      {successMessage && (
        <div className="bg-green-100 border border-green-400 text-green-700 px-4 py-2 rounded mb-4">
          {successMessage}
        </div>
      )}
      
      <form onSubmit={handleSubmit}>
        {/* Symbol input */}
        <div className="mb-4">
          <label className="block text-sm font-medium text-gray-700 mb-1">
            Stock Symbol
            <EducationalTooltip 
              content="A stock symbol is a unique series of letters assigned to a security for trading purposes. For example, AAPL is Apple Inc."
              position="right"
            />
          </label>
          <Input
            type="text"
            value={symbol}
            onChange={(e) => setSymbol(e.target.value.toUpperCase())}
            placeholder="Enter stock symbol (e.g., AAPL)"
            required
          />
          
          {symbolData && (
            <div className="text-sm text-gray-600 mt-1">
              {symbolData.name} - Current price: {formatCurrency(symbolData.price)}
            </div>
          )}
        </div>
        
        {/* Investment amount */}
        <div className="mb-4">
          <label className="block text-sm font-medium text-gray-700 mb-1">
            Investment Amount (USD)
            <EducationalTooltip 
              content={`Enter how much money you want to invest in this stock. The minimum investment is $${safeMinAmount}.`}
              position="right"
            />
          </label>
          <div className="relative">
            <div className="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none">
              <span className="text-gray-500">$</span>
            </div>
            <Input
              type="number"
              value={amount}
              onChange={(e) => setAmount(e.target.value)}
              placeholder={`Minimum $${safeMinAmount}`}
              min={safeMinAmount}
              step="0.01"
              required
              className="pl-7"
            />
          </div>
          
          {estimatedShares !== null && (
            <div className="text-sm text-gray-600 mt-1">
              Estimated shares: {estimatedShares.toFixed(8)} shares
              <EducationalTooltip 
                content="This is an estimate based on the current market price. The actual number of shares may vary slightly when the order is executed."
                position="right"
              />
            </div>
          )}
        </div>
        
        {/* Portfolio selection */}
        <div className="mb-4">
          <label className="block text-sm font-medium text-gray-700 mb-1">
            Portfolio
          </label>
          <Select
            value={portfolio}
            onChange={(e) => setPortfolio(e.target.value)}
            required
          >
            <option value="">Select a portfolio</option>
            {portfolios && portfolios.map((p) => (
              <option key={p.id} value={p.id}>
                {p.name}
              </option>
            ))}
          </Select>
        </div>
        
        {/* Recurring investment options */}
        <div className="mb-4">
          <div className="flex items-center">
            <input
              id="is-recurring"
              type="checkbox"
              className="h-4 w-4 text-blue-600 border-gray-300 rounded focus:ring-blue-500"
              checked={isRecurring}
              onChange={(e) => setIsRecurring(e.target.checked)}
            />
            <label htmlFor="is-recurring" className="ml-2 block text-sm font-medium text-gray-700">
              Set up recurring investment
              <EducationalTooltip 
                content="Recurring investments automatically invest a fixed amount at regular intervals, helping you build wealth consistently over time."
                position="right"
              />
            </label>
          </div>
          
          {isRecurring && (
            <div className="mt-3 ml-6">
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Frequency
              </label>
              <Select
                value={frequency}
                onChange={(e) => setFrequency(e.target.value)}
                className="w-full"
              >
                <option value="daily">Daily</option>
                <option value="weekly">Weekly</option>
                <option value="monthly">Monthly</option>
                <option value="quarterly">Quarterly</option>
              </Select>
              <p className="mt-1 text-sm text-gray-500">
                We'll automatically invest ${amount || '0'} {frequency} in {symbol || 'this stock'}.
              </p>
            </div>
          )}
        </div>
        
        {/* Information box */}
        <div className="bg-blue-50 p-3 rounded-md mb-4 text-sm text-blue-800">
          <h3 className="font-semibold">How Dollar-Based Investing Works</h3>
          <ul className="list-disc pl-5 mt-1 space-y-1">
            <li>You specify how much money you want to invest</li>
            <li>We buy the exact amount of shares (including fractional shares) for that dollar amount</li>
            <li>Your order may be combined with other orders to buy whole shares efficiently</li>
            <li>There are no additional fees for fractional investing</li>
            {isRecurring && (
              <li>Recurring investments help you build wealth through consistent investing over time</li>
            )}
          </ul>
        </div>
        
        {/* Submit button */}
        <Button
          type="submit"
          disabled={isLoading}
          className="w-full"
        >
          {isLoading ? 'Processing...' : 
            isRecurring ? 
            `Set up ${frequency} investment of ${amount ? `$${amount}` : ''} in ${symbol || 'Stock'}` : 
            `Invest ${amount ? `$${amount}` : ''} in ${symbol || 'Stock'}`
          }
        </Button>
      </form>
    </div>
  );
};

export default DollarBasedInvestment;