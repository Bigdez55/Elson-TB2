import React, { createContext, useContext, useState, useCallback, useMemo, ReactNode } from 'react';
import { useSelector } from 'react-redux';
import { useNavigate } from 'react-router-dom';
import type { RootState } from '../store/store';

// Trading mode types
export type TradingMode = 'paper' | 'live';

// Risk profile interface
export interface RiskProfile {
  level: 'conservative' | 'moderate' | 'aggressive';
  maxPositionSize: number;
  dailyLossLimit: number;
  maxLeverage: number;
}

// Daily limits tracking
export interface DailyLimits {
  ordersRemaining: number;
  dailyOrderLimit: number;
  lossRemaining: number;
  dailyLossLimit: number;
}

// Trading context state
export interface TradingContextState {
  mode: TradingMode;
  accountId: string;
  riskProfile: RiskProfile;
  dailyLimits: DailyLimits;
  isBlocked: boolean;
  blockReason?: string;
  lastModeSwitch?: Date;
}

// Computed context properties
export interface TradingContextComputed {
  isLiveMode: boolean;
  isPaperMode: boolean;
  canAccessLiveTrading: boolean;
}

// Trading context actions
export interface TradingContextActions {
  switchMode: (newMode: TradingMode) => Promise<boolean>;
  setMode: (mode: TradingMode) => void;
  updateRiskProfile: (profile: Partial<RiskProfile>) => void;
  updateDailyLimits: (limits: Partial<DailyLimits>) => void;
  blockTrading: (reason: string) => void;
  unblockTrading: () => void;
  getBaseRoute: () => '/paper' | '/live';
  confirmModeSwitch: (mode: TradingMode, redirectPath: string) => Promise<void>;
}

// Combined context interface
export interface TradingContextValue extends TradingContextState, TradingContextComputed, TradingContextActions {}

// Default state
const defaultState: TradingContextState = {
  mode: 'paper',
  accountId: '',
  riskProfile: {
    level: 'moderate',
    maxPositionSize: 10000,
    dailyLossLimit: 1000,
    maxLeverage: 1,
  },
  dailyLimits: {
    ordersRemaining: 50,
    dailyOrderLimit: 50,
    lossRemaining: 1000,
    dailyLossLimit: 1000,
  },
  isBlocked: false,
};

// Create context
const TradingContext = createContext<TradingContextValue | undefined>(undefined);

// Context provider props
interface TradingContextProviderProps {
  children: ReactNode;
  initialMode?: TradingMode;
  accountId?: string;
}

// Trading context provider component
export const TradingContextProvider: React.FC<TradingContextProviderProps> = ({
  children,
  initialMode = 'paper',
  accountId = 'default',
}) => {
  const [state, setState] = useState<TradingContextState>({
    ...defaultState,
    mode: initialMode,
    accountId,
  });

  // Get auth state from Redux for permission checking
  const authState = useSelector((reduxState: RootState) => reduxState.auth);
  const navigate = useNavigate();

  // Computed properties
  const isLiveMode = state.mode === 'live';
  const isPaperMode = state.mode === 'paper';

  // Check if user can access live trading based on subscription and verification
  const canAccessLiveTrading = useMemo(() => {
    if (!authState.user || !authState.isAuthenticated) {
      return false;
    }
    const user = authState.user as { subscription_type?: string; is_verified?: boolean };
    const hasValidSubscription = user.subscription_type === 'premium' || user.subscription_type === 'pro';
    const isVerified = user.is_verified === true;
    return hasValidSubscription && isVerified;
  }, [authState.user, authState.isAuthenticated]);

  // Switch trading mode with confirmation
  const switchMode = useCallback(async (newMode: TradingMode): Promise<boolean> => {
    if (newMode === state.mode) {
      return true;
    }

    // If switching to live mode, require explicit confirmation
    if (newMode === 'live') {
      const confirmed = await showLiveTradingConfirmation();
      if (!confirmed) {
        return false;
      }
    }

    setState(prev => ({
      ...prev,
      mode: newMode,
      lastModeSwitch: new Date(),
      // Reset some limits when switching modes
      dailyLimits: {
        ...prev.dailyLimits,
        ordersRemaining: prev.dailyLimits.dailyOrderLimit,
      },
    }));

    // Store mode preference
    localStorage.setItem('tradingMode', newMode);
    
    return true;
  }, [state.mode]);

  // Update risk profile
  const updateRiskProfile = useCallback((profile: Partial<RiskProfile>) => {
    setState(prev => ({
      ...prev,
      riskProfile: { ...prev.riskProfile, ...profile },
    }));
  }, []);

  // Update daily limits
  const updateDailyLimits = useCallback((limits: Partial<DailyLimits>) => {
    setState(prev => ({
      ...prev,
      dailyLimits: { ...prev.dailyLimits, ...limits },
    }));
  }, []);

  // Block trading
  const blockTrading = useCallback((reason: string) => {
    setState(prev => ({
      ...prev,
      isBlocked: true,
      blockReason: reason,
    }));
  }, []);

  // Unblock trading
  const unblockTrading = useCallback(() => {
    setState(prev => ({
      ...prev,
      isBlocked: false,
      blockReason: undefined,
    }));
  }, []);

  // Synchronous mode setter (calls switchMode without returning promise)
  const setMode = useCallback((mode: TradingMode) => {
    if (!canAccessLiveTrading && mode === 'live') {
      console.warn('User cannot access live trading: insufficient permissions');
      return;
    }
    switchMode(mode);
  }, [canAccessLiveTrading, switchMode]);

  // Get base route based on current mode
  const getBaseRoute = useCallback((): '/paper' | '/live' => {
    return state.mode === 'live' ? '/live' : '/paper';
  }, [state.mode]);

  // Confirm mode switch with navigation
  const confirmModeSwitch = useCallback(async (mode: TradingMode, redirectPath: string): Promise<void> => {
    if (mode === 'live' && !canAccessLiveTrading) {
      console.warn('User cannot access live trading: insufficient permissions');
      return;
    }

    if (mode === 'live') {
      const confirmed = window.confirm(
        'You are about to switch to live trading mode. This will use real money. Are you sure you want to proceed?'
      );
      if (!confirmed) {
        return;
      }
    }

    setState(prev => ({
      ...prev,
      mode,
      lastModeSwitch: new Date(),
      dailyLimits: {
        ...prev.dailyLimits,
        ordersRemaining: prev.dailyLimits.dailyOrderLimit,
      },
    }));
    localStorage.setItem('tradingMode', mode);
    navigate(redirectPath);
  }, [canAccessLiveTrading, navigate]);

  const contextValue: TradingContextValue = {
    ...state,
    // Computed properties
    isLiveMode,
    isPaperMode,
    canAccessLiveTrading,
    // Actions
    switchMode,
    setMode,
    updateRiskProfile,
    updateDailyLimits,
    blockTrading,
    unblockTrading,
    getBaseRoute,
    confirmModeSwitch,
  };

  return (
    <TradingContext.Provider value={contextValue}>
      {children}
    </TradingContext.Provider>
  );
};

// Hook to use trading context
export const useTradingContext = (): TradingContextValue => {
  const context = useContext(TradingContext);
  if (!context) {
    throw new Error('useTradingContext must be used within a TradingContextProvider');
  }
  return context;
};

// Trading mode confirmation dialog
const showLiveTradingConfirmation = (): Promise<boolean> => {
  return new Promise((resolve) => {
    // Create modal element
    const modal = document.createElement('div');
    modal.className = 'fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50';
    
    modal.innerHTML = `
      <div class="bg-red-50 border-2 border-red-200 rounded-lg p-6 max-w-md mx-4">
        <h2 class="text-red-800 font-bold text-xl mb-4">⚠️ SWITCH TO LIVE TRADING</h2>
        <p class="text-red-700 mb-4">
          You are about to switch to LIVE trading with real money. 
          All subsequent orders will execute with real funds.
        </p>
        <div class="space-y-2 text-sm text-red-600 mb-6">
          <label class="flex items-center">
            <input type="checkbox" id="understand-money" class="mr-2" />
            I understand this uses real money
          </label>
          <label class="flex items-center">
            <input type="checkbox" id="understand-risk" class="mr-2" />
            I have reviewed my risk limits
          </label>
          <label class="flex items-center">
            <input type="checkbox" id="understand-auth" class="mr-2" />
            I am authorized to trade in this account
          </label>
        </div>
        <div class="flex space-x-2">
          <button id="confirm-live" class="bg-red-600 text-white px-6 py-2 rounded-lg font-medium" disabled>
            CONFIRM LIVE TRADING
          </button>
          <button id="cancel-live" class="bg-gray-500 text-white px-6 py-2 rounded-lg font-medium">
            Cancel
          </button>
        </div>
      </div>
    `;

    document.body.appendChild(modal);

    // Handle checkbox validation
    const checkboxes = modal.querySelectorAll('input[type="checkbox"]');
    const confirmBtn = modal.querySelector('#confirm-live') as HTMLButtonElement;
    
    const validateCheckboxes = () => {
      const allChecked = Array.from(checkboxes).every(cb => (cb as HTMLInputElement).checked);
      confirmBtn.disabled = !allChecked;
      confirmBtn.className = allChecked 
        ? 'bg-red-600 text-white px-6 py-2 rounded-lg font-medium hover:bg-red-700'
        : 'bg-gray-400 text-gray-600 px-6 py-2 rounded-lg font-medium cursor-not-allowed';
    };

    checkboxes.forEach(cb => cb.addEventListener('change', validateCheckboxes));

    // Handle confirm
    confirmBtn.addEventListener('click', () => {
      document.body.removeChild(modal);
      resolve(true);
    });

    // Handle cancel
    const cancelBtn = modal.querySelector('#cancel-live')!;
    cancelBtn.addEventListener('click', () => {
      document.body.removeChild(modal);
      resolve(false);
    });

    // Handle escape key
    const handleEscape = (e: KeyboardEvent) => {
      if (e.key === 'Escape') {
        document.body.removeChild(modal);
        document.removeEventListener('keydown', handleEscape);
        resolve(false);
      }
    };
    document.addEventListener('keydown', handleEscape);
  });
};

// Utility function to get trading mode display info
export const getTradingModeInfo = (mode: TradingMode) => {
  switch (mode) {
    case 'paper':
      return {
        label: '📄 PAPER TRADING',
        className: 'bg-yellow-600 text-black',
        description: 'Practice mode - no real money',
      };
    case 'live':
      return {
        label: '🔴 LIVE TRADING',
        className: 'bg-red-600 text-white animate-pulse',
        description: 'Real money trading active',
      };
  }
};

export default TradingContext;