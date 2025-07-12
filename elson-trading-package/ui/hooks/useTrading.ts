import { useEffect, useCallback } from 'react';
import { useDispatch, useSelector } from 'react-redux';
import { AppDispatch, RootState } from '../store/store';
import {
  placeOrder,
  cancelOrder,
  fetchOrders,
  fetchTrades,
  fetchPortfolio,
} from '../store/slices/tradingSlice';
import {
  fetchMarketData,
  setSelectedSymbol,
  addToWatchlist,
  removeFromWatchlist,
} from '../store/slices/marketSlice';
import {
  createAlert,
  deleteAlert,
  updateAlert,
  fetchAlerts,
} from '../store/slices/alertsSlice';

export const useTrading = (symbol?: string) => {
  const dispatch = useDispatch<AppDispatch>();
  
  // Selectors
  const {
    orders,
    trades,
    portfolio,
    loading: tradingLoading,
    error: tradingError,
  } = useSelector((state: RootState) => state.trading);

  const {
    marketData,
    selectedSymbol,
    watchlist,
    loading: marketLoading,
    error: marketError,
  } = useSelector((state: RootState) => state.market);

  const {
    alerts,
    activeAlerts,
    loading: alertsLoading,
    error: alertsError,
  } = useSelector((state: RootState) => state.alerts);

  // Initialize data
  useEffect(() => {
    if (symbol) {
      dispatch(fetchMarketData(symbol));
      dispatch(fetchOrders());
      dispatch(fetchTrades());
      dispatch(fetchPortfolio());
      dispatch(fetchAlerts());
    }
  }, [dispatch, symbol]);

  // Trading actions
  const submitOrder = useCallback(
    async (orderData: any) => {
      try {
        await dispatch(placeOrder(orderData)).unwrap();
        return true;
      } catch (error) {
        return false;
      }
    },
    [dispatch]
  );

  const cancelExistingOrder = useCallback(
    async (orderId: string) => {
      try {
        await dispatch(cancelOrder(orderId)).unwrap();
        return true;
      } catch (error) {
        return false;
      }
    },
    [dispatch]
  );

  // Market actions
  const selectSymbol = useCallback(
    (newSymbol: string) => {
      dispatch(setSelectedSymbol(newSymbol));
    },
    [dispatch]
  );

  const addSymbolToWatchlist = useCallback(
    (symbol: string) => {
      dispatch(addToWatchlist(symbol));
    },
    [dispatch]
  );

  const removeSymbolFromWatchlist = useCallback(
    (symbol: string) => {
      dispatch(removeFromWatchlist(symbol));
    },
    [dispatch]
  );

  // Alert actions
  const createNewAlert = useCallback(
    async (alertData: any) => {
      try {
        await dispatch(createAlert(alertData)).unwrap();
        return true;
      } catch (error) {
        return false;
      }
    },
    [dispatch]
  );

  const removeAlert = useCallback(
    async (alertId: string) => {
      try {
        await dispatch(deleteAlert(alertId)).unwrap();
        return true;
      } catch (error) {
        return false;
      }
    },
    [dispatch]
  );

  const modifyAlert = useCallback(
    async (alertId: string, data: any) => {
      try {
        await dispatch(updateAlert({ alertId, data })).unwrap();
        return true;
      } catch (error) {
        return false;
      }
    },
    [dispatch]
  );

  return {
    // State
    orders,
    trades,
    portfolio,
    marketData,
    selectedSymbol,
    watchlist,
    alerts,
    activeAlerts,

    // Loading states
    isLoading: tradingLoading || marketLoading || alertsLoading,
    error: tradingError || marketError || alertsError,

    // Actions
    submitOrder,
    cancelOrder: cancelExistingOrder,
    selectSymbol,
    addToWatchlist: addSymbolToWatchlist,
    removeFromWatchlist: removeSymbolFromWatchlist,
    createAlert: createNewAlert,
    deleteAlert: removeAlert,
    updateAlert: modifyAlert,
  };
};

export default useTrading;