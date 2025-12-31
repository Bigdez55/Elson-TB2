import React, { useState, useEffect } from 'react';
import { Button } from '../common/Button';
import { Input } from '../common/Input';
import { Select } from '../common/Select';
import { EducationalTooltip } from '../common/EducationalTooltip';
import { formatCurrency } from '../../utils/formatters';

interface InvestmentCalculatorProps {
  onSelectAmount?: (amount: number) => void;
}

export const InvestmentCalculator: React.FC<InvestmentCalculatorProps> = ({ 
  onSelectAmount 
}) => {
  const [calculatorType, setCalculatorType] = useState<'dollar' | 'share'>('dollar');
  const [stockPrice, setStockPrice] = useState<number>(150);
  const [investmentAmount, setInvestmentAmount] = useState<number>(100);
  const [shareCount, setShareCount] = useState<number>(1);
  const [recurrenceFrequency, setRecurrenceFrequency] = useState<string>('once');
  const [recurrencePeriod, setRecurrencePeriod] = useState<number>(12);
  const [estimatedGrowth, setEstimatedGrowth] = useState<number>(7);
  
  // Calculated results
  const [sharesResult, setSharesResult] = useState<number>(0);
  const [investmentResult, setInvestmentResult] = useState<number>(0);
  const [futureValue, setFutureValue] = useState<number>(0);

  // Recalculate when inputs change
  useEffect(() => {
    if (calculatorType === 'dollar') {
      // Calculate shares from dollar amount
      const shares = stockPrice > 0 ? investmentAmount / stockPrice : 0;
      setSharesResult(shares);
    } else {
      // Calculate dollar amount from shares
      const amount = shareCount * stockPrice;
      setInvestmentResult(amount);
    }
    
    // Calculate future value based on recurrence
    calculateFutureValue();
  }, [calculatorType, stockPrice, investmentAmount, shareCount, recurrenceFrequency, recurrencePeriod, estimatedGrowth]);
  
  const calculateFutureValue = () => {
    const totalInvestment = calculatorType === 'dollar' ? investmentAmount : (shareCount * stockPrice);
    let periodsPerYear = 1;
    let totalPeriods = 1;
    
    // Calculate based on frequency
    switch (recurrenceFrequency) {
      case 'weekly':
        periodsPerYear = 52;
        totalPeriods = 52 * recurrencePeriod;
        break;
      case 'monthly':
        periodsPerYear = 12;
        totalPeriods = 12 * recurrencePeriod;
        break;
      case 'quarterly':
        periodsPerYear = 4;
        totalPeriods = 4 * recurrencePeriod;
        break;
      case 'yearly':
        periodsPerYear = 1;
        totalPeriods = recurrencePeriod;
        break;
      default: // once
        periodsPerYear = 0;
        totalPeriods = 1;
        break;
    }
    
    // For recurring investments, use future value of periodic payments formula
    if (recurrenceFrequency !== 'once') {
      const ratePerPeriod = estimatedGrowth / 100 / periodsPerYear;
      // Future Value = PMT × ((1 + r)^n - 1) / r
      const futureVal = totalInvestment * ((Math.pow(1 + ratePerPeriod, totalPeriods) - 1) / ratePerPeriod);
      setFutureValue(futureVal);
    } else {
      // For one-time investments, use compound interest formula
      // Future Value = PV × (1 + r)^t
      const futureVal = totalInvestment * Math.pow(1 + (estimatedGrowth / 100), recurrencePeriod);
      setFutureValue(futureVal);
    }
  };
  
  const handleUseThisAmount = () => {
    if (onSelectAmount) {
      const amount = calculatorType === 'dollar' ? investmentAmount : investmentResult;
      onSelectAmount(amount);
    }
  };
  
  return (
    <div className="bg-white rounded-lg shadow-md p-4">
      <div className="flex items-center mb-4">
        <h2 className="text-xl font-semibold">Investment Calculator</h2>
        <EducationalTooltip 
          content="This calculator helps you estimate how many shares you can buy with a specific dollar amount, or how much it will cost to buy a specific number of shares."
          position="right"
        />
      </div>
      
      {/* Calculator Type Selection */}
      <div className="mb-4">
        <div className="flex space-x-4">
          <button
            onClick={() => setCalculatorType('dollar')}
            className={`px-4 py-2 rounded-md ${
              calculatorType === 'dollar' 
                ? 'bg-blue-500 text-white' 
                : 'bg-gray-200 text-gray-700'
            }`}
          >
            Dollars to Shares
          </button>
          <button
            onClick={() => setCalculatorType('share')}
            className={`px-4 py-2 rounded-md ${
              calculatorType === 'share' 
                ? 'bg-blue-500 text-white' 
                : 'bg-gray-200 text-gray-700'
            }`}
          >
            Shares to Dollars
          </button>
        </div>
      </div>
      
      {/* Stock Price Input */}
      <div className="mb-4">
        <label className="block text-sm font-medium text-gray-700 mb-1">
          Stock Price
          <EducationalTooltip 
            content="The current market price per share of the stock."
            position="right"
          />
        </label>
        <div className="relative">
          <div className="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none">
            <span className="text-gray-500">$</span>
          </div>
          <Input
            type="number"
            value={stockPrice}
            onChange={(e) => setStockPrice(parseFloat(e.target.value) || 0)}
            placeholder="Stock Price"
            min="0.01"
            step="0.01"
            required
            className="pl-7"
          />
        </div>
      </div>
      
      {/* Input based on calculator type */}
      {calculatorType === 'dollar' ? (
        <div className="mb-4">
          <label className="block text-sm font-medium text-gray-700 mb-1">
            Investment Amount
            <EducationalTooltip 
              content="How much money you want to invest in this stock."
              position="right"
            />
          </label>
          <div className="relative">
            <div className="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none">
              <span className="text-gray-500">$</span>
            </div>
            <Input
              type="number"
              value={investmentAmount}
              onChange={(e) => setInvestmentAmount(parseFloat(e.target.value) || 0)}
              placeholder="Investment Amount"
              min="1"
              step="1"
              required
              className="pl-7"
            />
          </div>
        </div>
      ) : (
        <div className="mb-4">
          <label className="block text-sm font-medium text-gray-700 mb-1">
            Number of Shares
            <EducationalTooltip 
              content="How many shares of the stock you want to buy."
              position="right"
            />
          </label>
          <Input
            type="number"
            value={shareCount}
            onChange={(e) => setShareCount(parseFloat(e.target.value) || 0)}
            placeholder="Number of Shares"
            min="0.001"
            step="0.001"
            required
          />
        </div>
      )}
      
      {/* Recurrence options */}
      <div className="mb-4">
        <label className="block text-sm font-medium text-gray-700 mb-1">
          Investment Frequency
          <EducationalTooltip 
            content="How often you plan to make this investment. This helps calculate the potential future value."
            position="right"
          />
        </label>
        <Select
          value={recurrenceFrequency}
          onChange={(e) => setRecurrenceFrequency(e.target.value)}
        >
          <option value="once">One-time Investment</option>
          <option value="weekly">Weekly</option>
          <option value="monthly">Monthly</option>
          <option value="quarterly">Quarterly</option>
          <option value="yearly">Yearly</option>
        </Select>
      </div>
      
      {/* Time period */}
      <div className="mb-4">
        <label className="block text-sm font-medium text-gray-700 mb-1">
          {recurrenceFrequency === 'once' ? 'Investment Period (Years)' : 'Investment Duration (Years)'}
          <EducationalTooltip 
            content={recurrenceFrequency === 'once' 
              ? "How many years you plan to hold this investment."
              : "How many years you plan to continue making these periodic investments."
            }
            position="right"
          />
        </label>
        <Input
          type="number"
          value={recurrencePeriod}
          onChange={(e) => setRecurrencePeriod(parseInt(e.target.value) || 1)}
          placeholder="Years"
          min="1"
          max="50"
          required
        />
      </div>
      
      {/* Estimated annual growth rate */}
      <div className="mb-4">
        <label className="block text-sm font-medium text-gray-700 mb-1">
          Estimated Annual Growth Rate (%)
          <EducationalTooltip 
            content="An estimate of how much the investment might grow each year. The historical average for the S&P 500 is about 7% after inflation."
            position="right"
          />
        </label>
        <div className="relative">
          <Input
            type="number"
            value={estimatedGrowth}
            onChange={(e) => setEstimatedGrowth(parseFloat(e.target.value) || 0)}
            placeholder="Annual Growth Rate"
            min="0"
            max="30"
            step="0.1"
            required
            className="pr-7"
          />
          <div className="absolute inset-y-0 right-0 pr-3 flex items-center pointer-events-none">
            <span className="text-gray-500">%</span>
          </div>
        </div>
      </div>
      
      {/* Results */}
      <div className="bg-gray-50 rounded-lg p-4 mb-4">
        <h3 className="font-semibold text-lg mb-2">Results</h3>
        
        {calculatorType === 'dollar' ? (
          <div className="mb-2">
            <span className="text-gray-700">Shares you can buy: </span>
            <span className="font-semibold">{sharesResult.toFixed(8)}</span>
          </div>
        ) : (
          <div className="mb-2">
            <span className="text-gray-700">Total cost: </span>
            <span className="font-semibold">{formatCurrency(investmentResult)}</span>
          </div>
        )}
        
        {recurrenceFrequency !== 'once' && (
          <div className="mb-2">
            <span className="text-gray-700">Total invested over time: </span>
            <span className="font-semibold">
              {formatCurrency(
                calculatorType === 'dollar' 
                  ? investmentAmount * (recurrencePeriod * 
                      (recurrenceFrequency === 'weekly' ? 52 : 
                       recurrenceFrequency === 'monthly' ? 12 : 
                       recurrenceFrequency === 'quarterly' ? 4 : 1))
                  : investmentResult * (recurrencePeriod * 
                      (recurrenceFrequency === 'weekly' ? 52 : 
                       recurrenceFrequency === 'monthly' ? 12 : 
                       recurrenceFrequency === 'quarterly' ? 4 : 1))
              )}
            </span>
          </div>
        )}
        
        <div>
          <span className="text-gray-700">Estimated future value: </span>
          <span className="font-semibold text-green-600">{formatCurrency(futureValue)}</span>
          <EducationalTooltip 
            content="This is a simplified projection based on a constant growth rate. Actual investment performance will vary due to market fluctuations and other factors."
            position="right"
          />
        </div>
      </div>
      
      {/* Use This Amount button - only show if the callback is provided */}
      {onSelectAmount && (
        <Button
          onClick={handleUseThisAmount}
          className="w-full"
        >
          {calculatorType === 'dollar' 
            ? `Use $${investmentAmount} as Investment Amount` 
            : `Use $${investmentResult.toFixed(2)} as Investment Amount`}
        </Button>
      )}
      
      {/* Disclaimer */}
      <div className="mt-4 text-xs text-gray-500">
        <p>Disclaimer: This calculator provides estimates only. Actual investment results may vary significantly. Past performance does not guarantee future results.</p>
      </div>
    </div>
  );
};

export default InvestmentCalculator;