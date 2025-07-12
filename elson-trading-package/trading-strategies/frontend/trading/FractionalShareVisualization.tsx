import React from 'react';
import { EducationalTooltip } from '../common/EducationalTooltip';
import { formatCurrency } from '../../utils/formatters';

interface FractionalShareVisualizationProps {
  symbol: string;
  sharePrice: number;
  quantity: number;
  totalValue: number;
  companyName?: string;
}

export const FractionalShareVisualization: React.FC<FractionalShareVisualizationProps> = ({
  symbol,
  sharePrice,
  quantity,
  totalValue,
  companyName
}) => {
  // Calculate visual elements
  const wholeShares = Math.floor(quantity);
  const fractionalShare = quantity - wholeShares;
  
  // Create array of whole shares to render
  const wholeShareElements = Array.from({ length: wholeShares }, (_, i) => i);
  
  // Format numbers for display
  const formattedPrice = formatCurrency(sharePrice);
  const formattedTotalValue = formatCurrency(totalValue);
  const formattedFractional = fractionalShare.toFixed(6);
  
  return (
    <div className="bg-white rounded-lg shadow p-4">
      <div className="flex items-center justify-between mb-4">
        <div>
          <h3 className="text-lg font-semibold">{symbol}</h3>
          {companyName && <p className="text-sm text-gray-600">{companyName}</p>}
        </div>
        <div className="text-right">
          <p className="text-sm text-gray-600">Share Price</p>
          <p className="font-medium">{formattedPrice}</p>
        </div>
      </div>
      
      <div className="mb-4">
        <div className="flex items-center mb-2">
          <h4 className="text-sm font-medium mr-2">Your Shares</h4>
          <EducationalTooltip
            content="Fractional shares let you own a portion of a share. This visualization shows your whole shares and the fraction you own."
            position="right"
          />
        </div>
        
        <div className="flex items-center mb-3">
          <div className="flex-grow">
            <div className="flex items-center space-x-1.5 flex-wrap">
              {/* Render whole shares */}
              {wholeShareElements.map((index) => (
                <div 
                  key={index}
                  className="w-12 h-12 bg-blue-500 rounded-full flex items-center justify-center text-white font-semibold shadow-sm"
                  title="1 whole share"
                >
                  1
                </div>
              ))}
              
              {/* Render fractional share */}
              {fractionalShare > 0 && (
                <div className="relative">
                  <div 
                    className="w-12 h-12 rounded-full border-2 border-blue-500 shadow-sm"
                  ></div>
                  <div 
                    className="absolute top-0 left-0 w-12 h-12 rounded-full overflow-hidden"
                    style={{ clipPath: `inset(0 ${100 - (fractionalShare * 100)}% 0 0)` }}
                  >
                    <div 
                      className="w-12 h-12 bg-blue-500 rounded-full flex items-center justify-center text-white font-semibold"
                    >
                      {fractionalShare < 0.1 ? '' : fractionalShare.toFixed(2)}
                    </div>
                  </div>
                </div>
              )}
            </div>
          </div>
          
          <div className="flex flex-col items-end ml-4">
            <span className="text-lg font-semibold">{quantity.toFixed(6)}</span>
            <span className="text-xs text-gray-500">shares</span>
          </div>
        </div>
      </div>
      
      <div className="border-t pt-3">
        <div className="flex justify-between items-center">
          <div>
            <span className="text-sm text-gray-600">Total Value</span>
            <EducationalTooltip
              content={`This is calculated by multiplying your share count (${quantity.toFixed(6)}) by the current share price (${formattedPrice}).`}
              position="right"
            />
          </div>
          <div className="text-xl font-semibold text-green-700">
            {formattedTotalValue}
          </div>
        </div>
      </div>
      
      <div className="mt-4 bg-gray-50 p-3 rounded text-sm">
        <h5 className="font-medium mb-1">Understanding Fractional Shares</h5>
        <p className="text-gray-700">
          You own {wholeShares} whole share{wholeShares !== 1 ? 's' : ''} 
          {fractionalShare > 0 ? ` plus ${formattedFractional} of a share` : ''} of {symbol}.
          Fractional shares give you the same proportional ownership and value as whole shares,
          making it easier to invest specific dollar amounts.
        </p>
      </div>
    </div>
  );
};

export default FractionalShareVisualization;