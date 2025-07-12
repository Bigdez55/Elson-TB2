import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { useSelector } from 'react-redux';
import { Button } from '../common/Button';
import { Input } from '../common/Input';
import { Select } from '../common/Select';
import { EducationalTooltip } from '../common/EducationalTooltip';
import { tradingService } from '../../services/tradingService';
import { formatCurrency } from '../../utils/formatters';

interface Portfolio {
  id: number;
  name: string;
}

interface RecurringInvestmentFormProps {
  portfolios?: Portfolio[];
  onSuccess?: () => void;
  onCancel?: () => void;
  symbol?: string;
  initialInvestmentAmount?: number;
  darkMode?: boolean;
}

export const RecurringInvestmentForm: React.FC<RecurringInvestmentFormProps> = ({
  portfolios = [],
  onSuccess,
  onCancel,
  symbol = '',
  initialInvestmentAmount = 100,
  darkMode = true
}) => {
  const navigate = useNavigate();
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [error, setError] = useState('');
  
  // Check subscription status to limit recurring investments
  const { isPremium, isFamily } = useSelector((state: any) => state.subscription);
  
  // Form state
  const [formState, setFormState] = useState({
    symbol: symbol,
    portfolio_id: portfolios.length > 0 ? portfolios[0].id : '',
    investment_amount: initialInvestmentAmount,
    frequency: 'monthly',
    trade_type: 'BUY',
    start_date: new Date(Date.now() + 24 * 60 * 60 * 1000).toISOString().split('T')[0], // Tomorrow
    end_date: '',
    description: '',
    // Advanced scheduling options
    useSpecificDay: false,
    specificWeekday: '1', // Default to Monday (0 = Sunday in JS, but we use 1-7 for UX clarity)
    specificMonthDay: '1', // Default to 1st day of month
  });
  
  // Calculate total annual investment
  const calculateAnnualInvestment = (): number => {
    const amount = formState.investment_amount;
    switch (formState.frequency) {
      case 'daily':
        return amount * 365;
      case 'weekly':
        return amount * 52;
      case 'monthly':
        return amount * 12;
      case 'quarterly':
        return amount * 4;
      default:
        return amount * 12;
    }
  };
  
  // Handle input change
  const handleChange = (e: React.ChangeEvent<HTMLInputElement | HTMLSelectElement>) => {
    const { name, value } = e.target;
    
    // Special handling for investment amount to ensure it's numeric
    if (name === 'investment_amount') {
      const numValue = parseFloat(value);
      if (!isNaN(numValue) && numValue > 0) {
        setFormState(prev => ({ ...prev, [name]: numValue }));
      }
    } else {
      setFormState(prev => ({ ...prev, [name]: value }));
    }
  };
  
  // Handle form submission
  const handleSubmit = async (e: React.FormEvent) => {
    if (!isPremium && !isFamily) {
      setError('Recurring investments require a Premium or Family subscription');
      return;
    }
    e.preventDefault();
    setIsSubmitting(true);
    setError('');
    
    try {
      // Validate form
      if (!formState.symbol.trim()) {
        throw new Error('Symbol is required');
      }
      
      if (formState.investment_amount <= 0) {
        throw new Error('Investment amount must be greater than 0');
      }
      
      // Prepare data for submission
      // Create a copy of the form data with necessary transformations
      const submissionData = {
        ...formState,
        // Convert IDs to numbers if they're stored as strings
        portfolio_id: Number(formState.portfolio_id),
        // Add metadata with scheduling preferences if enabled
        metadata: formState.useSpecificDay ? {
          specific_day: formState.frequency === 'weekly' 
            ? String(Number(formState.specificWeekday) - 1) // Convert 1-7 to 0-6 format
            : formState.specificMonthDay === 'last' 
              ? '-1' 
              : formState.specificMonthDay
        } : undefined
      };
      
      // Remove UI-only fields before sending to API
      delete submissionData.useSpecificDay;
      delete submissionData.specificWeekday;
      delete submissionData.specificMonthDay;
      
      // Submit form
      await tradingService.createRecurringInvestment(submissionData);
      
      // Handle success
      if (onSuccess) {
        onSuccess();
      } else {
        navigate('/trading');
      }
    } catch (err: any) {
      console.error('Error creating recurring investment:', err);
      setError(err.message || 'Failed to create recurring investment');
    } finally {
      setIsSubmitting(false);
    }
  };
  
  if (darkMode) {
    return (
      <div className="bg-gray-900 rounded-xl p-6 shadow-md">
        <h2 className="text-xl font-semibold text-white mb-6">Set Up Recurring Investment</h2>
        
        {error && (
          <div className="bg-red-900 border border-red-700 text-red-100 px-4 py-3 rounded-lg mb-6">
            {error}
          </div>
        )}
        
        <form onSubmit={handleSubmit} className="space-y-6">
          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            <div>
              <label className="block text-sm font-medium text-gray-300 mb-1">
                Symbol
              </label>
              <Input
                name="symbol"
                value={formState.symbol}
                onChange={handleChange}
                placeholder="e.g. AAPL, MSFT, VOO"
                required
                className="w-full bg-gray-800 border-gray-700 text-white"
              />
              <p className="mt-1 text-xs text-gray-400">Enter stock symbol</p>
            </div>
            
            {portfolios.length > 0 && (
              <div>
                <label className="block text-sm font-medium text-gray-300 mb-1">
                  Portfolio
                </label>
                <Select
                  name="portfolio_id"
                  value={formState.portfolio_id}
                  onChange={handleChange}
                  className="w-full bg-gray-800 border-gray-700 text-white"
                  required
                >
                  {portfolios.map(portfolio => (
                    <option key={portfolio.id} value={portfolio.id}>
                      {portfolio.name}
                    </option>
                  ))}
                </Select>
              </div>
            )}
          </div>
          
          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            <div>
              <label className="block text-sm font-medium text-gray-300 mb-1">
                Investment Amount ($)
              </label>
              <div className="relative">
                <div className="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none">
                  <span className="text-gray-400 sm:text-sm">$</span>
                </div>
                <Input
                  name="investment_amount"
                  type="number"
                  min="1"
                  step="1"
                  value={formState.investment_amount}
                  onChange={handleChange}
                  className="pl-7 w-full bg-gray-800 border-gray-700 text-white"
                  required
                />
              </div>
              <p className="mt-1 text-xs text-gray-400">Amount to invest each period</p>
            </div>
            
            <div>
              <label className="block text-sm font-medium text-gray-300 mb-1">
                Frequency
              </label>
              <Select
                name="frequency"
                value={formState.frequency}
                onChange={handleChange}
                className="w-full bg-gray-800 border-gray-700 text-white"
                required
              >
                <option value="daily">Daily</option>
                <option value="weekly">Weekly</option>
                <option value="monthly">Monthly</option>
                <option value="quarterly">Quarterly</option>
              </Select>
              
              {/* Advanced scheduling checkbox */}
              <div className="mt-2">
                <label className="inline-flex items-center">
                  <input
                    type="checkbox"
                    className="form-checkbox h-4 w-4 text-purple-600 bg-gray-800 border-gray-700"
                    checked={formState.useSpecificDay}
                    onChange={(e) => setFormState(prev => ({
                      ...prev,
                      useSpecificDay: e.target.checked
                    }))}
                  />
                  <span className="ml-2 text-xs text-gray-400">
                    Specify exact day
                  </span>
                </label>
              </div>
            </div>
          </div>
          
          {/* Show specific day selectors when enabled */}
          {formState.useSpecificDay && (
            <div className="p-4 border border-gray-700 rounded-md bg-gray-800 mb-4">
              <h3 className="text-sm font-medium text-white mb-3">Advanced Scheduling</h3>
              
              {formState.frequency === 'weekly' && (
                <div>
                  <label className="block text-sm font-medium text-gray-300 mb-1">
                    Day of Week
                  </label>
                  <Select
                    name="specificWeekday"
                    value={formState.specificWeekday}
                    onChange={handleChange}
                    className="w-full bg-gray-800 border-gray-700 text-white"
                  >
                    <option value="1">Monday</option>
                    <option value="2">Tuesday</option>
                    <option value="3">Wednesday</option>
                    <option value="4">Thursday</option>
                    <option value="5">Friday</option>
                    <option value="6">Saturday</option>
                    <option value="7">Sunday</option>
                  </Select>
                </div>
              )}
              
              {(formState.frequency === 'monthly' || formState.frequency === 'quarterly') && (
                <div>
                  <label className="block text-sm font-medium text-gray-300 mb-1">
                    Day of Month
                  </label>
                  <Select
                    name="specificMonthDay"
                    value={formState.specificMonthDay}
                    onChange={handleChange}
                    className="w-full bg-gray-800 border-gray-700 text-white"
                  >
                    {[...Array(31)].map((_, i) => (
                      <option key={i+1} value={(i+1).toString()}>
                        {(i+1).toString()}{(i+1) === 1 ? 'st' : (i+1) === 2 ? 'nd' : (i+1) === 3 ? 'rd' : 'th'}
                      </option>
                    ))}
                    <option value="last">Last day of month</option>
                  </Select>
                </div>
              )}
            </div>
          )}
          
          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            <div>
              <label className="block text-sm font-medium text-gray-300 mb-1">
                Start Date
              </label>
              <Input
                name="start_date"
                type="date"
                value={formState.start_date}
                onChange={handleChange}
                className="w-full bg-gray-800 border-gray-700 text-white"
                required
                min={new Date().toISOString().split('T')[0]}
              />
            </div>
            
            <div>
              <label className="block text-sm font-medium text-gray-300 mb-1">
                End Date (Optional)
              </label>
              <Input
                name="end_date"
                type="date"
                value={formState.end_date}
                onChange={handleChange}
                className="w-full bg-gray-800 border-gray-700 text-white"
                min={formState.start_date}
              />
              <p className="mt-1 text-xs text-gray-400">Leave blank for no end date</p>
            </div>
          </div>
          
          <div>
            <label className="block text-sm font-medium text-gray-300 mb-1">
              Description (Optional)
            </label>
            <Input
              name="description"
              value={formState.description}
              onChange={handleChange}
              placeholder="E.g., Monthly investment for retirement"
              className="w-full bg-gray-800 border-gray-700 text-white"
            />
          </div>
          
          <div className="bg-gray-800 p-4 rounded-lg mt-4">
            <h3 className="font-medium text-white mb-2">Investment Summary</h3>
            <div className="grid grid-cols-2 gap-x-4 gap-y-2 text-sm">
              <div className="text-gray-400">Per Investment:</div>
              <div className="font-medium text-white">{formatCurrency(formState.investment_amount)}</div>
              
              <div className="text-gray-400">Frequency:</div>
              <div className="font-medium text-white capitalize">{formState.frequency}</div>
              
              <div className="text-gray-400">Annual Total:</div>
              <div className="font-medium text-white">{formatCurrency(calculateAnnualInvestment())}</div>
              
              <div className="text-gray-400">First Investment:</div>
              <div className="font-medium text-white">{new Date(formState.start_date).toLocaleDateString()}</div>
            </div>
          </div>
          
          <div className="mt-6 flex justify-end space-x-3">
            <Button
              type="button"
              onClick={onCancel}
              className="bg-gray-700 hover:bg-gray-600 text-white border border-gray-600"
            >
              Cancel
            </Button>
            <Button
              type="submit"
              className="bg-purple-600 hover:bg-purple-500 text-white"
              disabled={isSubmitting}
            >
              {isSubmitting ? 'Creating...' : 'Create Recurring Investment'}
            </Button>
          </div>
        </form>
        
        <div className="mt-8 p-4 bg-gray-800 rounded-lg">
          <h3 className="text-sm font-medium text-white mb-2">How Recurring Investments Work</h3>
          <ul className="text-sm text-gray-400 space-y-2 list-disc pl-5">
            <li>Investments will be automatically processed on the schedule you select</li>
            <li>Funds will be drawn from your available cash balance</li>
            <li>Investments are made at market price at the time of execution</li>
            <li>You can modify or cancel recurring investments at any time</li>
            <li>Dollar-cost averaging helps reduce the impact of volatility</li>
          </ul>
        </div>
      </div>
    );
  }
  
  // Light mode version
  return (
    <div className="bg-white rounded-lg shadow-md p-6">
      <div className="flex items-center justify-between mb-6">
        <div>
          <h2 className="text-xl font-semibold">Create Recurring Investment</h2>
          <p className="text-gray-600 text-sm">
            Automatically invest at regular intervals
          </p>
        </div>
        <EducationalTooltip 
          content="Recurring investments help you build wealth consistently through dollar-cost averaging, reducing the impact of market volatility by investing at regular intervals regardless of market conditions."
          position="left"
        />
      </div>
      
      {error && (
        <div className="bg-red-100 border border-red-400 text-red-700 px-4 py-3 rounded mb-4">
          {error}
        </div>
      )}
      
      <form onSubmit={handleSubmit}>
        <div className="space-y-4">
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Symbol
              </label>
              <Input
                name="symbol"
                value={formState.symbol}
                onChange={handleChange}
                placeholder="AAPL"
                required
                className="w-full"
              />
              <p className="mt-1 text-xs text-gray-500">Enter stock symbol</p>
            </div>
            
            {portfolios.length > 0 && (
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Portfolio
                </label>
                <Select
                  name="portfolio_id"
                  value={formState.portfolio_id}
                  onChange={handleChange}
                  className="w-full"
                  required
                >
                  {portfolios.map(portfolio => (
                    <option key={portfolio.id} value={portfolio.id}>
                      {portfolio.name}
                    </option>
                  ))}
                </Select>
              </div>
            )}
          </div>
          
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Investment Amount
              </label>
              <div className="relative">
                <div className="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none">
                  <span className="text-gray-500 sm:text-sm">$</span>
                </div>
                <Input
                  name="investment_amount"
                  type="number"
                  min="1"
                  step="1"
                  value={formState.investment_amount}
                  onChange={handleChange}
                  className="pl-7 w-full"
                  required
                />
              </div>
              <p className="mt-1 text-xs text-gray-500">Amount to invest each period</p>
            </div>
            
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Frequency
              </label>
              <Select
                name="frequency"
                value={formState.frequency}
                onChange={handleChange}
                className="w-full"
                required
              >
                <option value="daily">Daily</option>
                <option value="weekly">Weekly</option>
                <option value="monthly">Monthly</option>
                <option value="quarterly">Quarterly</option>
              </Select>
              
              {/* Advanced scheduling checkbox */}
              <div className="mt-2">
                <label className="inline-flex items-center">
                  <input
                    type="checkbox"
                    className="form-checkbox h-4 w-4 text-indigo-600"
                    checked={formState.useSpecificDay}
                    onChange={(e) => setFormState(prev => ({
                      ...prev,
                      useSpecificDay: e.target.checked
                    }))}
                  />
                  <span className="ml-2 text-xs text-gray-600">
                    Specify exact day
                  </span>
                </label>
              </div>
            </div>
          </div>
          
          {/* Show specific day selectors when enabled */}
          {formState.useSpecificDay && (
            <div className="p-4 border border-gray-200 rounded-md bg-gray-50 mb-4">
              <h3 className="text-sm font-medium text-gray-700 mb-3">Advanced Scheduling</h3>
              
              {formState.frequency === 'weekly' && (
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    Day of Week
                  </label>
                  <Select
                    name="specificWeekday"
                    value={formState.specificWeekday}
                    onChange={handleChange}
                    className="w-full"
                  >
                    <option value="1">Monday</option>
                    <option value="2">Tuesday</option>
                    <option value="3">Wednesday</option>
                    <option value="4">Thursday</option>
                    <option value="5">Friday</option>
                    <option value="6">Saturday</option>
                    <option value="7">Sunday</option>
                  </Select>
                </div>
              )}
              
              {(formState.frequency === 'monthly' || formState.frequency === 'quarterly') && (
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    Day of Month
                  </label>
                  <Select
                    name="specificMonthDay"
                    value={formState.specificMonthDay}
                    onChange={handleChange}
                    className="w-full"
                  >
                    {[...Array(31)].map((_, i) => (
                      <option key={i+1} value={(i+1).toString()}>
                        {(i+1).toString()}{(i+1) === 1 ? 'st' : (i+1) === 2 ? 'nd' : (i+1) === 3 ? 'rd' : 'th'}
                      </option>
                    ))}
                    <option value="last">Last day of month</option>
                  </Select>
                </div>
              )}
            </div>
          )}
          
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Start Date
              </label>
              <Input
                name="start_date"
                type="date"
                value={formState.start_date}
                onChange={handleChange}
                className="w-full"
                required
                min={new Date().toISOString().split('T')[0]}
              />
            </div>
            
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                End Date (Optional)
              </label>
              <Input
                name="end_date"
                type="date"
                value={formState.end_date}
                onChange={handleChange}
                className="w-full"
                min={formState.start_date}
              />
              <p className="mt-1 text-xs text-gray-500">Leave blank for no end date</p>
            </div>
          </div>
          
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              Description (Optional)
            </label>
            <Input
              name="description"
              value={formState.description}
              onChange={handleChange}
              placeholder="E.g., Monthly investment for retirement"
              className="w-full"
            />
          </div>
          
          <div className="bg-indigo-50 p-4 rounded-lg mt-4">
            <h3 className="font-medium text-indigo-800 mb-2">Investment Summary</h3>
            <div className="grid grid-cols-2 gap-x-4 gap-y-2 text-sm">
              <div className="text-gray-600">Per Investment:</div>
              <div className="font-medium">{formatCurrency(formState.investment_amount)}</div>
              
              <div className="text-gray-600">Frequency:</div>
              <div className="font-medium capitalize">{formState.frequency}</div>
              
              <div className="text-gray-600">Annual Total:</div>
              <div className="font-medium">{formatCurrency(calculateAnnualInvestment())}</div>
              
              <div className="text-gray-600">First Investment:</div>
              <div className="font-medium">{new Date(formState.start_date).toLocaleDateString()}</div>
            </div>
          </div>
        </div>
        
        <div className="mt-6 flex justify-end space-x-3">
          <Button
            type="button"
            onClick={onCancel}
            className="bg-white text-gray-700 border border-gray-300"
          >
            Cancel
          </Button>
          <Button
            type="submit"
            className="bg-indigo-600 text-white"
            disabled={isSubmitting}
          >
            {isSubmitting ? 'Creating...' : 'Create Recurring Investment'}
          </Button>
        </div>
      </form>
      
      <div className="mt-4 pt-4 border-t border-gray-200">
        <div className="text-sm text-gray-600">
          <p className="mb-1">
            <strong>About Recurring Investments:</strong>
          </p>
          <ul className="list-disc pl-5 space-y-1">
            <li>Investments are processed during market hours</li>
            <li>You can cancel at any time</li>
            <li>Dollar-cost averaging helps reduce the impact of volatility</li>
            <li>Regular investing helps build wealth consistently over time</li>
          </ul>
        </div>
      </div>
    </div>
  );
};

export default RecurringInvestmentForm;