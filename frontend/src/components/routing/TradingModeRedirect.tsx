import React from 'react';
import { Navigate, useParams } from 'react-router-dom';
import { useTradingContext } from '../../contexts/TradingContext';

interface TradingModeRedirectProps {
  basePath: string;
}

export const TradingModeRedirect: React.FC<TradingModeRedirectProps> = ({ basePath }) => {
  const { mode } = useTradingContext();
  const params = useParams();
  
  // Build the new path with the current trading mode
  let newPath = `/${mode}${basePath}`;
  
  // Add symbol parameter if it exists
  if (params.symbol) {
    newPath = newPath.replace(':symbol', params.symbol);
  }
  
  return <Navigate to={newPath} replace />;
};

interface TradingRouteGuardProps {
  children: React.ReactNode;
  requiredMode?: 'paper' | 'live';
}

export const TradingRouteGuard: React.FC<TradingRouteGuardProps> = ({ 
  children, 
  requiredMode 
}) => {
  const { mode, isBlocked } = useTradingContext();
  
  // Block access if trading is blocked
  if (isBlocked) {
    return <Navigate to="/dashboard" replace />;
  }
  
  // If a specific mode is required and current mode doesn't match, redirect
  if (requiredMode && mode !== requiredMode) {
    return <Navigate to={`/${requiredMode}/trading`} replace />;
  }
  
  return <>{children}</>;
};

export default TradingModeRedirect;