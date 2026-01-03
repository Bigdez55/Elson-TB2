import React, { useState, useEffect, useRef, memo } from 'react';
import { formatCurrency } from '../../utils/formatters';

interface PriceDisplayProps {
  price: number | null;
  previousPrice?: number | null;
  className?: string;
  size?: 'sm' | 'md' | 'lg' | 'xl';
  showChange?: boolean;
  changePercent?: number;
  flashOnChange?: boolean;
}

/**
 * PriceDisplay Component with Flash Animation
 * Shows price with green/red flash animation when price changes
 */
export const PriceDisplay: React.FC<PriceDisplayProps> = memo(({
  price,
  previousPrice,
  className = '',
  size = 'md',
  showChange = false,
  changePercent,
  flashOnChange = true,
}) => {
  const [flashClass, setFlashClass] = useState<string>('');
  const prevPriceRef = useRef<number | null>(previousPrice ?? null);

  // Detect price changes and trigger flash animation
  useEffect(() => {
    if (!flashOnChange || price === null) return;

    const prevPrice = prevPriceRef.current;
    
    if (prevPrice !== null && price !== prevPrice) {
      if (price > prevPrice) {
        setFlashClass('flash-up');
      } else if (price < prevPrice) {
        setFlashClass('flash-down');
      }

      // Clear flash class after animation completes
      const timer = setTimeout(() => {
        setFlashClass('');
      }, 500);

      return () => clearTimeout(timer);
    }

    prevPriceRef.current = price;
  }, [price, flashOnChange]);

  // Update ref when price changes
  useEffect(() => {
    if (price !== null) {
      prevPriceRef.current = price;
    }
  }, [price]);

  const sizeClasses = {
    sm: 'text-sm',
    md: 'text-base',
    lg: 'text-lg',
    xl: 'text-2xl font-bold',
  };

  const changeDirection = changePercent 
    ? changePercent > 0 ? 'up' : changePercent < 0 ? 'down' : 'neutral'
    : 'neutral';

  const changeColorClass = 
    changeDirection === 'up' ? 'text-green-400' :
    changeDirection === 'down' ? 'text-red-400' :
    'text-gray-400';

  if (price === null) {
    return (
      <span className={`text-gray-500 ${sizeClasses[size]} ${className}`}>
        —
      </span>
    );
  }

  return (
    <span className={`inline-flex items-center gap-2 ${className}`}>
      <span 
        className={`
          ${sizeClasses[size]} 
          ${flashClass} 
          font-medium text-white
          transition-colors duration-150
          rounded px-1 -mx-1
        `}
      >
        {formatCurrency(price)}
      </span>
      {showChange && changePercent !== undefined && (
        <span className={`text-sm ${changeColorClass}`}>
          {changePercent > 0 ? '+' : ''}{changePercent.toFixed(2)}%
        </span>
      )}
    </span>
  );
});

PriceDisplay.displayName = 'PriceDisplay';

/**
 * Compact Price Display for tables and lists
 */
export const CompactPriceDisplay: React.FC<{
  price: number;
  change?: number;
  changePercent?: number;
  className?: string;
}> = memo(({ price, change, changePercent, className = '' }) => {
  const [flashClass, setFlashClass] = useState<string>('');
  const prevPriceRef = useRef<number>(price);

  useEffect(() => {
    if (price !== prevPriceRef.current) {
      if (price > prevPriceRef.current) {
        setFlashClass('flash-up');
      } else {
        setFlashClass('flash-down');
      }

      const timer = setTimeout(() => setFlashClass(''), 500);
      prevPriceRef.current = price;
      return () => clearTimeout(timer);
    }
  }, [price]);

  const isPositive = (change ?? 0) >= 0;
  const changeColor = isPositive ? 'text-green-400' : 'text-red-400';

  return (
    <div className={`flex flex-col items-end ${className}`}>
      <span className={`font-medium text-white ${flashClass} rounded px-1 -mx-1`}>
        {formatCurrency(price)}
      </span>
      {change !== undefined && (
        <span className={`text-xs ${changeColor}`}>
          {isPositive ? '+' : ''}{formatCurrency(change)}
          {changePercent !== undefined && (
            <span className="ml-1">({isPositive ? '+' : ''}{changePercent.toFixed(2)}%)</span>
          )}
        </span>
      )}
    </div>
  );
});

CompactPriceDisplay.displayName = 'CompactPriceDisplay';

/**
 * Large Price Display for stock headers
 */
export const LargePriceDisplay: React.FC<{
  price: number | null;
  change?: number;
  changePercent?: number;
  symbol?: string;
  className?: string;
}> = memo(({ price, change, changePercent, symbol, className = '' }) => {
  const [flashClass, setFlashClass] = useState<string>('');
  const prevPriceRef = useRef<number | null>(price);

  useEffect(() => {
    if (price !== null && prevPriceRef.current !== null && price !== prevPriceRef.current) {
      if (price > prevPriceRef.current) {
        setFlashClass('flash-up');
      } else {
        setFlashClass('flash-down');
      }

      const timer = setTimeout(() => setFlashClass(''), 500);
      return () => clearTimeout(timer);
    }
    prevPriceRef.current = price;
  }, [price]);

  const isPositive = (change ?? 0) >= 0;
  const changeColor = isPositive ? 'text-green-400' : 'text-red-400';
  const changeBgColor = isPositive ? 'bg-green-400/10' : 'bg-red-400/10';

  if (price === null) {
    return (
      <div className={`${className}`}>
        <div className="h-10 w-32 bg-gray-700 animate-pulse rounded" />
      </div>
    );
  }

  return (
    <div className={`${className}`}>
      <div className="flex items-baseline gap-3">
        <span 
          className={`
            text-4xl font-bold text-white 
            ${flashClass} 
            rounded-lg px-2 -mx-2
          `}
        >
          {formatCurrency(price)}
        </span>
        {change !== undefined && changePercent !== undefined && (
          <span className={`px-2 py-1 rounded-md text-sm font-medium ${changeColor} ${changeBgColor}`}>
            {isPositive ? '+' : ''}{formatCurrency(change)} ({isPositive ? '+' : ''}{changePercent.toFixed(2)}%)
          </span>
        )}
      </div>
      {symbol && (
        <div className="text-sm text-gray-400 mt-1">
          Real-time price for {symbol}
        </div>
      )}
    </div>
  );
});

LargePriceDisplay.displayName = 'LargePriceDisplay';

export default PriceDisplay;
