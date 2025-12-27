import React from 'react';
import { useTradingContext, getTradingModeInfo } from '../../contexts/TradingContext';

interface TradingModeIndicatorProps {
  showSwitcher?: boolean;
  position?: 'fixed' | 'relative';
  size?: 'sm' | 'md' | 'lg';
}

export const TradingModeIndicator: React.FC<TradingModeIndicatorProps> = ({
  showSwitcher = false,
  position = 'fixed',
  size = 'md',
}) => {
  const { mode, switchMode, isBlocked } = useTradingContext();
  const modeInfo = getTradingModeInfo(mode);

  const sizeClasses = {
    sm: 'px-2 py-1 text-xs',
    md: 'px-4 py-2 text-sm',
    lg: 'px-6 py-3 text-base',
  };

  const positionClasses = position === 'fixed'
    ? 'fixed top-4 right-4 z-50'
    : 'relative';

  const handleModeSwitch = async () => {
    const newMode = mode === 'paper' ? 'live' : 'paper';
    await switchMode(newMode);
  };

  return (
    <div className={`${positionClasses} flex items-center space-x-2`}>
      {/* Trading Mode Indicator */}
      <div className={`
        ${modeInfo.className} 
        ${sizeClasses[size]} 
        rounded-full font-bold shadow-lg border-2 border-opacity-20 border-white
        ${isBlocked ? 'opacity-50' : ''}
      `}>
        <div className="flex items-center space-x-1">
          <span>{modeInfo.label}</span>
          {isBlocked && (
            <span className="text-xs">🚫</span>
          )}
        </div>
      </div>

      {/* Mode Switcher */}
      {showSwitcher && (
        <button
          onClick={handleModeSwitch}
          disabled={isBlocked}
          className={`
            px-3 py-1 rounded-lg text-xs font-medium transition-colors
            ${isBlocked 
              ? 'bg-gray-400 text-gray-600 cursor-not-allowed' 
              : mode === 'paper'
                ? 'bg-red-600 text-white hover:bg-red-700'
                : 'bg-yellow-600 text-black hover:bg-yellow-700'
            }
          `}
          title={isBlocked ? 'Trading is blocked' : `Switch to ${mode === 'paper' ? 'Live' : 'Paper'} Trading`}
        >
          Switch to {mode === 'paper' ? 'Live' : 'Paper'}
        </button>
      )}
    </div>
  );
};

interface TradingModeCardProps {
  className?: string;
  showDetails?: boolean;
}

export const TradingModeCard: React.FC<TradingModeCardProps> = ({
  className = '',
  showDetails = true,
}) => {
  const { 
    mode, 
    switchMode, 
    isBlocked, 
    blockReason, 
    dailyLimits, 
    riskProfile 
  } = useTradingContext();
  
  const modeInfo = getTradingModeInfo(mode);

  return (
    <div className={`bg-gray-900 rounded-xl p-4 ${className}`}>
      <div className="flex items-center justify-between mb-3">
        <h3 className="text-white font-medium">Trading Mode</h3>
        <div className={`px-3 py-1 rounded-full text-sm font-bold ${modeInfo.className}`}>
          {modeInfo.label}
        </div>
      </div>

      <p className="text-gray-400 text-sm mb-4">{modeInfo.description}</p>

      {isBlocked && (
        <div className="bg-red-900 bg-opacity-30 border border-red-700 rounded-lg p-3 mb-4">
          <div className="flex items-center">
            <span className="text-red-400 mr-2">🚫</span>
            <div>
              <p className="text-red-300 font-medium">Trading Blocked</p>
              <p className="text-red-400 text-sm">{blockReason}</p>
            </div>
          </div>
        </div>
      )}

      {showDetails && (
        <div className="space-y-3">
          <div className="bg-gray-800 rounded-lg p-3">
            <h4 className="text-gray-300 text-sm font-medium mb-2">Daily Limits</h4>
            <div className="grid grid-cols-2 gap-2 text-xs">
              <div>
                <span className="text-gray-400">Orders:</span>
                <span className="text-white ml-1">
                  {dailyLimits.ordersRemaining}/{dailyLimits.dailyOrderLimit}
                </span>
              </div>
              <div>
                <span className="text-gray-400">Loss Limit:</span>
                <span className="text-white ml-1">
                  ${dailyLimits.lossRemaining.toLocaleString()}
                </span>
              </div>
            </div>
          </div>

          <div className="bg-gray-800 rounded-lg p-3">
            <h4 className="text-gray-300 text-sm font-medium mb-2">Risk Profile</h4>
            <div className="space-y-1 text-xs">
              <div className="flex justify-between">
                <span className="text-gray-400">Level:</span>
                <span className="text-white capitalize">{riskProfile.level}</span>
              </div>
              <div className="flex justify-between">
                <span className="text-gray-400">Max Position:</span>
                <span className="text-white">${riskProfile.maxPositionSize.toLocaleString()}</span>
              </div>
            </div>
          </div>

          <button
            onClick={() => switchMode(mode === 'paper' ? 'live' : 'paper')}
            disabled={isBlocked}
            className={`w-full py-2 rounded-lg text-sm font-medium transition-colors ${
              isBlocked
                ? 'bg-gray-600 text-gray-400 cursor-not-allowed'
                : mode === 'paper'
                ? 'bg-red-600 text-white hover:bg-red-700'
                : 'bg-yellow-600 text-black hover:bg-yellow-700'
            }`}
          >
            Switch to {mode === 'paper' ? 'Live' : 'Paper'} Trading
          </button>
        </div>
      )}
    </div>
  );
};

// Banner component for critical trading mode warnings
export const TradingModeBanner: React.FC = () => {
  const { mode, isBlocked, blockReason } = useTradingContext();
  
  if (!isBlocked && mode === 'paper') {
    return null; // No banner needed for normal paper trading
  }

  if (mode === 'live') {
    return (
      <div className="bg-gradient-to-r from-red-800 to-red-600 text-white p-3 text-center shadow-lg">
        <div className="flex items-center justify-center space-x-2">
          <span className="text-lg">🔴</span>
          <span className="font-bold">LIVE TRADING ACTIVE</span>
          <span className="text-lg">🔴</span>
        </div>
        <p className="text-xs mt-1 opacity-90">
          Real money transactions are enabled. Exercise caution with all orders.
        </p>
      </div>
    );
  }

  if (isBlocked) {
    return (
      <div className="bg-gradient-to-r from-red-900 to-red-800 text-white p-3 text-center shadow-lg">
        <div className="flex items-center justify-center space-x-2">
          <span className="text-lg">🚫</span>
          <span className="font-bold">TRADING BLOCKED</span>
          <span className="text-lg">🚫</span>
        </div>
        <p className="text-xs mt-1 opacity-90">
          {blockReason || 'Trading has been temporarily suspended'}
        </p>
      </div>
    );
  }

  return null;
};

export default TradingModeIndicator;