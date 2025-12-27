import React, { useState, ReactNode } from 'react';
import { useTradingContext } from '../../contexts/TradingContext';
import { TradingConfirmationModal } from './TradingConfirmationModal';

interface TradingSafeguardWrapperProps {
  children: ReactNode;
  requiresConfirmation?: boolean;
  actionType: 'order' | 'modeSwitch' | 'risk' | 'general';
  title?: string;
  message?: string;
  orderDetails?: {
    symbol?: string;
    quantity?: number;
    price?: number;
    action?: 'buy' | 'sell';
    orderType?: string;
  };
  onExecute?: () => void;
  disabled?: boolean;
}

export const TradingSafeguardWrapper: React.FC<TradingSafeguardWrapperProps> = ({
  children,
  requiresConfirmation = false,
  actionType,
  title = 'Confirm Action',
  message = 'Are you sure you want to proceed?',
  orderDetails,
  onExecute,
  disabled = false,
}) => {
  const { mode, isBlocked } = useTradingContext();
  const [showConfirmation, setShowConfirmation] = useState(false);

  const handleClick = (e: React.MouseEvent) => {
    if (isBlocked || disabled) {
      e.preventDefault();
      e.stopPropagation();
      return;
    }

    if (requiresConfirmation || (mode === 'live' && actionType === 'order')) {
      e.preventDefault();
      e.stopPropagation();
      setShowConfirmation(true);
    }
  };

  const handleConfirm = () => {
    setShowConfirmation(false);
    if (onExecute) {
      onExecute();
    }
  };

  const handleCancel = () => {
    setShowConfirmation(false);
  };

  return (
    <div className="relative">
      <div 
        onClick={handleClick}
        className={`${isBlocked || disabled ? 'opacity-50 cursor-not-allowed' : ''}`}
      >
        {children}
      </div>
      
      <TradingConfirmationModal
        isOpen={showConfirmation}
        onClose={handleCancel}
        onConfirm={handleConfirm}
        title={title}
        message={message}
        type={actionType}
        orderDetails={orderDetails}
      />
    </div>
  );
};

// Risk Limit Warning Component
interface RiskLimitWarningProps {
  currentValue: number;
  limit: number;
  type: 'orders' | 'loss' | 'position';
  className?: string;
}

export const RiskLimitWarning: React.FC<RiskLimitWarningProps> = ({
  currentValue,
  limit,
  type,
  className = '',
}) => {
  const percentage = (currentValue / limit) * 100;
  
  const getWarningLevel = () => {
    if (percentage >= 90) return 'critical';
    if (percentage >= 75) return 'high';
    if (percentage >= 50) return 'medium';
    return 'low';
  };
  
  const getWarningColor = () => {
    const level = getWarningLevel();
    switch (level) {
      case 'critical': return 'bg-red-100 border-red-500 text-red-800';
      case 'high': return 'bg-orange-100 border-orange-500 text-orange-800';
      case 'medium': return 'bg-yellow-100 border-yellow-500 text-yellow-800';
      default: return 'bg-green-100 border-green-500 text-green-800';
    }
  };

  const getWarningIcon = () => {
    const level = getWarningLevel();
    switch (level) {
      case 'critical': return '🚨';
      case 'high': return '⚠️';
      case 'medium': return '⚡';
      default: return '✅';
    }
  };

  if (percentage < 50) return null; // Only show when approaching limits

  return (
    <div className={`border rounded-lg p-3 ${getWarningColor()} ${className}`}>
      <div className="flex items-center">
        <span className="mr-2">{getWarningIcon()}</span>
        <div>
          <p className="font-medium text-sm">
            {type === 'orders' && `Daily Order Limit: ${currentValue}/${limit}`}
            {type === 'loss' && `Daily Loss Limit: $${currentValue.toLocaleString()}/$${limit.toLocaleString()}`}
            {type === 'position' && `Position Size: $${currentValue.toLocaleString()}/$${limit.toLocaleString()}`}
          </p>
          <p className="text-xs">
            {percentage >= 90 && 'Critical: Limit almost reached'}
            {percentage >= 75 && percentage < 90 && 'Warning: Approaching limit'}
            {percentage >= 50 && percentage < 75 && 'Notice: Limit usage increasing'}
          </p>
        </div>
      </div>
    </div>
  );
};

// Trading Mode Status Alert
export const TradingModeStatusAlert: React.FC = () => {
  const { mode, isBlocked, blockReason } = useTradingContext();
  
  if (!isBlocked && mode === 'paper') return null;

  return (
    <div className="sticky top-0 z-40">
      {mode === 'live' && !isBlocked && (
        <div className="bg-gradient-to-r from-red-600 to-red-700 text-white p-2 text-center text-sm font-medium">
          <span className="mr-2">🔴</span>
          LIVE TRADING ACTIVE - Real money transactions enabled
        </div>
      )}
      
      {isBlocked && (
        <div className="bg-gradient-to-r from-red-800 to-red-900 text-white p-3 text-center">
          <div className="font-bold">🚫 TRADING BLOCKED</div>
          <div className="text-xs mt-1">{blockReason}</div>
        </div>
      )}
    </div>
  );
};

// Trading Session Timer Component
interface TradingSessionTimerProps {
  className?: string;
}

export const TradingSessionTimer: React.FC<TradingSessionTimerProps> = ({ className = '' }) => {
  const { mode, lastModeSwitch } = useTradingContext();
  const [timeInMode, setTimeInMode] = React.useState<string>('');

  React.useEffect(() => {
    if (!lastModeSwitch) return;

    const interval = setInterval(() => {
      const now = new Date();
      const diff = now.getTime() - lastModeSwitch.getTime();
      const minutes = Math.floor(diff / 60000);
      const hours = Math.floor(minutes / 60);
      
      if (hours > 0) {
        setTimeInMode(`${hours}h ${minutes % 60}m`);
      } else {
        setTimeInMode(`${minutes}m`);
      }
    }, 60000);

    return () => clearInterval(interval);
  }, [lastModeSwitch]);

  if (!lastModeSwitch || !timeInMode) return null;

  return (
    <div className={`text-xs text-gray-500 ${className}`}>
      In {mode} mode for {timeInMode}
    </div>
  );
};

export default TradingSafeguardWrapper;