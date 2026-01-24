import { useState, useEffect } from 'react';

interface MarketTimerState {
  hours: number;
  minutes: number;
  isOpen: boolean;
}

export const useMarketTimer = () => {
  const [state, setState] = useState<MarketTimerState>({
    hours: 2,
    minutes: 34,
    isOpen: true,
  });

  useEffect(() => {
    const interval = setInterval(() => {
      setState((prev) => {
        let { hours, minutes, isOpen } = prev;
        minutes--;
        if (minutes < 0) {
          minutes = 59;
          hours--;
        }
        if (hours < 0) {
          hours = 6;
          minutes = 30;
          isOpen = !isOpen;
        }
        return { hours, minutes, isOpen };
      });
    }, 60000);
    return () => clearInterval(interval);
  }, []);

  return {
    isOpen: state.isOpen,
    timeStr: `${state.hours}h ${state.minutes}m`,
  };
};
