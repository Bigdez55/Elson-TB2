import { useEffect } from 'react';
import { useLocation } from 'react-router-dom';
import { useTradingContext, TradingMode } from '../../contexts/TradingContext';

export const TradingModeSync: React.FC = () => {
  const location = useLocation();
  const { mode, switchMode } = useTradingContext();

  useEffect(() => {
    // Determine the required mode based on the current path
    let requiredMode: TradingMode | null = null;
    
    if (location.pathname.startsWith('/paper/')) {
      requiredMode = 'paper';
    } else if (location.pathname.startsWith('/live/')) {
      requiredMode = 'live';
    }

    // If we're on a trading route and the mode doesn't match, update it
    if (requiredMode && requiredMode !== mode) {
      switchMode(requiredMode).catch(() => {
        // Handle failed mode switch (e.g., user denied live trading confirmation)
        console.warn('Failed to switch trading mode to match route');
      });
    }
  }, [location.pathname, mode, switchMode]);

  return null; // This component doesn't render anything
};

export default TradingModeSync;