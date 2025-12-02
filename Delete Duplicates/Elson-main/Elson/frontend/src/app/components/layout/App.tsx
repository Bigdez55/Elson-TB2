import React, { useEffect, useState, Suspense } from 'react';
import { Routes, Route, Navigate, useLocation, useNavigate } from 'react-router-dom';
import { useSelector, useDispatch } from 'react-redux';
import Layout from './Layout';
import { RootState } from '../../store/store';
import { fetchUserProfile } from '../../store/slices/userSlice';
import SubscriptionProvider from '../subscription/SubscriptionProvider';
import { ToastProvider } from '../common/ToastProvider';
import ErrorBoundary from '../common/ErrorBoundary';
import { GlobalLoadingProvider } from '../../hooks/useGlobalLoading';
import { AccessibilityProvider } from '../../hooks/useAccessibility';
import { SkipNavLink } from '../common/SkipNav';
import LoadingSpinner from '../common/LoadingSpinner';

// Lazy load the mobile layout to reduce initial bundle size
const MobileLayout = React.lazy(() => import('./MobileLayout'));

// Import pages
import Dashboard from '../../../pages/Dashboard';
import Login from '../../../pages/Login';
import Register from '../../../pages/Register';
import Trading from '../../../pages/Trading';
import TradingView from '../../../pages/TradingView';
import Portfolio from '../../../pages/Portfolio';
import Settings from '../../../pages/Settings';
import Profile from '../../../pages/Profile';
import Learning from '../../../pages/Learning';
import FamilyDashboard from '../../../pages/FamilyDashboard';
import GuardianPermissions from '../../../pages/family/GuardianPermissions';
import GuardianNotifications from '../../../pages/family/GuardianNotifications';
import APIKeys from '../../../pages/APIKeys';
import AlertConfig from '../../../pages/AlertConfig';
import Pricing from '../../../pages/Pricing';
import ForgotPassword from '../../../pages/ForgotPassword';
import ResetPassword from '../../../pages/ResetPassword';
import TwoFactorAuth from '../../../pages/TwoFactorAuth';
import SubscriptionSuccess from '../../../pages/subscription/Success';
import SubscriptionCancel from '../../../pages/subscription/Cancel';
import WebSocketTest from '../../../pages/WebSocketTest';
import RoundupTransactions from '../../../pages/RoundupTransactions';
import LoadingSpinner from '../common/LoadingSpinner';

// Analytics pages
import AnalyticsLayout from '../../../pages/analytics/AnalyticsLayout';
import Analytics from '../../../pages/analytics/Analytics';
import TradingAnalytics from '../../../pages/analytics/TradingAnalytics';
import PortfolioAnalytics from '../../../pages/analytics/PortfolioAnalytics';
import MarketAnalytics from '../../../pages/analytics/MarketAnalytics';
import RiskAnalytics from '../../../pages/analytics/RiskAnalytics';
import PerformanceAnalytics from '../../../pages/analytics/PerformanceAnalytics';
import BacktestAnalytics from '../../../pages/analytics/BacktestAnalytics';
import StrategyAnalytics from '../../../pages/analytics/StrategyAnalytics';
import TradingBotAnalytics from '../../../pages/analytics/TradingBotAnalytics';
import TradingPairAnalytics from '../../../pages/analytics/TradingPairAnalytics';
import CorrelationAnalytics from '../../../pages/analytics/CorrelationAnalytics';
import ModelPerformanceAnalytics from '../../../pages/analytics/ModelPerformanceAnalytics';
import ExchangeAnalytics from '../../../pages/analytics/ExchangeAnalytics';
import EventAnalytics from '../../../pages/analytics/EventAnalytics';
import ErrorAnalytics from '../../../pages/analytics/ErrorAnalytics';
import DataImportAnalytics from '../../../pages/analytics/DataImportAnalytics';
import OrderbookAnalytics from '../../../pages/analytics/OrderbookAnalytics';
import ReportingAnalytics from '../../../pages/analytics/ReportingAnalytics';
import PredictionAnalytics from '../../../pages/analytics/PredictionAnalytics';
import TaxAnalytics from '../../../pages/analytics/TaxAnalytics';

// Protected route wrapper component
interface ProtectedRouteProps {
  children: React.ReactNode;
  requiredRole?: string;
  requiredPermission?: string;
  requiredSubscription?: string;
}

const ProtectedRoute: React.FC<ProtectedRouteProps> = ({ 
  children, 
  requiredRole,
  requiredPermission,
  requiredSubscription
}) => {
  const { token, loading, user, subscription } = useSelector((state: RootState) => state.user);
  const location = useLocation();
  const navigate = useNavigate();
  const dispatch = useDispatch();

  // Check if user is authenticated and session is still valid
  useEffect(() => {
    if (token && !loading && !user) {
      // Token exists but no user, try to fetch user profile
      dispatch(fetchUserProfile());
    }
  }, [token, loading, user, dispatch]);

  if (loading) {
    return (
      <div className="flex items-center justify-center min-h-screen bg-gray-900">
        <LoadingSpinner size="large" color="text-purple-600" text="Loading..." />
      </div>
    );
  }

  // Not authenticated
  if (!token) {
    // Save the location they were trying to access for redirection after login
    return <Navigate to="/login" state={{ from: location }} replace />;
  }

  // Check subscription requirements if specified
  if (requiredSubscription && user) {
    const hasRequiredSubscription = subscription && 
      subscription.status === 'active' && 
      subscription.plan >= requiredSubscription;
    
    if (!hasRequiredSubscription) {
      return <Navigate to="/pricing" state={{ from: location }} replace />;
    }
  }

  // Check role requirements if specified
  if (requiredRole && user) {
    const hasRequiredRole = user.roles && user.roles.includes(requiredRole);
    
    if (!hasRequiredRole) {
      return <Navigate to="/dashboard" state={{ from: location, accessDenied: true }} replace />;
    }
  }

  // Check permission requirements if specified
  if (requiredPermission && user) {
    const hasRequiredPermission = user.permissions && 
      user.permissions.includes(requiredPermission);
    
    if (!hasRequiredPermission) {
      return <Navigate to="/dashboard" state={{ from: location, accessDenied: true }} replace />;
    }
  }

  return <>{children}</>;
};

const App: React.FC = () => {
  const dispatch = useDispatch();
  const { token, loading } = useSelector((state: RootState) => state.user);
  const [isMobile, setIsMobile] = useState(false);
  
  // Try to load user profile on app start if we have a token
  useEffect(() => {
    if (token && !loading) {
      dispatch(fetchUserProfile());
    }
  }, [dispatch, token, loading]);

  // Detect mobile devices and listen for resize events
  useEffect(() => {
    const checkIfMobile = () => {
      setIsMobile(window.innerWidth < 768); // Standard breakpoint for mobile
    };

    // Initial check
    checkIfMobile();

    // Add resize listener
    window.addEventListener('resize', checkIfMobile);
    
    return () => {
      window.removeEventListener('resize', checkIfMobile);
    };
  }, []);

  // Create a layout wrapper that switches between mobile and desktop layouts
  const LayoutWrapper: React.FC<{ children: React.ReactNode }> = ({ children }) => {
    if (isMobile) {
      return (
        <Suspense fallback={
          <div className="flex items-center justify-center min-h-screen bg-gray-900">
            <LoadingSpinner size="large" color="text-purple-600" text="Loading mobile view..." />
          </div>
        }>
          <MobileLayout>{children}</MobileLayout>
        </Suspense>
      );
    }
    
    return <Layout>{children}</Layout>;
  };

  return (
    <ErrorBoundary>
      <GlobalLoadingProvider>
        <AccessibilityProvider>
          <ToastProvider position="top-right">
            <SubscriptionProvider>
              {/* Global skip navigation for keyboard users */}
              <SkipNavLink />
              
              <Routes>
              {/* Public routes */}
              <Route path="/login" element={<Login />} />
              <Route path="/register" element={<Register />} />
              <Route path="/forgot-password" element={<ForgotPassword />} />
              <Route path="/reset-password" element={<ResetPassword />} />
              <Route path="/two-factor-auth" element={<TwoFactorAuth />} />
              <Route path="/pricing" element={<Pricing />} />
              <Route path="/subscription/success" element={<SubscriptionSuccess />} />
              <Route path="/subscription/cancel" element={<SubscriptionCancel />} />
              <Route path="/ws-test" element={<WebSocketTest />} />
            
            {/* Protected routes - Core pages */}
            <Route 
              path="/" 
              element={
                <ProtectedRoute>
                  <LayoutWrapper>
                    <ErrorBoundary>
                      <Dashboard />
                    </ErrorBoundary>
                  </LayoutWrapper>
                </ProtectedRoute>
              } 
            />
            <Route 
              path="/dashboard" 
              element={
                <ProtectedRoute>
                  <LayoutWrapper>
                    <ErrorBoundary>
                      <Dashboard />
                    </ErrorBoundary>
                  </LayoutWrapper>
                </ProtectedRoute>
              } 
            />
            <Route 
              path="/trading" 
              element={
                <ProtectedRoute>
                  <LayoutWrapper>
                    <ErrorBoundary>
                      <Trading />
                    </ErrorBoundary>
                  </LayoutWrapper>
                </ProtectedRoute>
              } 
            />
            <Route 
              path="/trading-view" 
              element={
                <ProtectedRoute>
                  <LayoutWrapper>
                    <ErrorBoundary>
                      <TradingView />
                    </ErrorBoundary>
                  </LayoutWrapper>
                </ProtectedRoute>
              } 
            />
            <Route 
              path="/portfolio" 
              element={
                <ProtectedRoute>
                  <LayoutWrapper>
                    <ErrorBoundary>
                      <Portfolio />
                    </ErrorBoundary>
                  </LayoutWrapper>
                </ProtectedRoute>
              } 
            />
            <Route 
              path="/settings" 
              element={
                <ProtectedRoute>
                  <LayoutWrapper>
                    <ErrorBoundary>
                      <Settings />
                    </ErrorBoundary>
                  </LayoutWrapper>
                </ProtectedRoute>
              } 
            />
            <Route 
              path="/profile" 
              element={
                <ProtectedRoute>
                  <LayoutWrapper>
                    <ErrorBoundary>
                      <Profile />
                    </ErrorBoundary>
                  </LayoutWrapper>
                </ProtectedRoute>
              } 
            />
            <Route 
              path="/learning" 
              element={
                <ProtectedRoute>
                  <LayoutWrapper>
                    <ErrorBoundary>
                      <Learning />
                    </ErrorBoundary>
                  </LayoutWrapper>
                </ProtectedRoute>
              } 
            />
            <Route 
              path="/api-keys" 
              element={
                <ProtectedRoute>
                  <LayoutWrapper>
                    <ErrorBoundary>
                      <APIKeys />
                    </ErrorBoundary>
                  </LayoutWrapper>
                </ProtectedRoute>
              } 
            />
            <Route 
              path="/alerts" 
              element={
                <ProtectedRoute>
                  <LayoutWrapper>
                    <ErrorBoundary>
                      <AlertConfig />
                    </ErrorBoundary>
                  </LayoutWrapper>
                </ProtectedRoute>
              } 
            />
            
            {/* Family/Custodial Routes */}
            <Route 
              path="/family" 
              element={
                <ProtectedRoute requiredSubscription="FAMILY">
                  <LayoutWrapper>
                    <ErrorBoundary>
                      <FamilyDashboard />
                    </ErrorBoundary>
                  </LayoutWrapper>
                </ProtectedRoute>
              } 
            />
            <Route 
              path="/family/permissions" 
              element={
                <ProtectedRoute requiredSubscription="FAMILY" requiredRole="GUARDIAN">
                  <LayoutWrapper>
                    <ErrorBoundary>
                      <GuardianPermissions />
                    </ErrorBoundary>
                  </LayoutWrapper>
                </ProtectedRoute>
              } 
            />
            <Route 
              path="/family/notifications" 
              element={
                <ProtectedRoute requiredSubscription="FAMILY" requiredRole="GUARDIAN">
                  <LayoutWrapper>
                    <ErrorBoundary>
                      <GuardianNotifications />
                    </ErrorBoundary>
                  </LayoutWrapper>
                </ProtectedRoute>
              } 
            />
            
            {/* Analytics Routes */}
            <Route 
              path="/analytics" 
              element={
                <ProtectedRoute requiredSubscription="PREMIUM">
                  <LayoutWrapper>
                    <ErrorBoundary>
                      <AnalyticsLayout />
                    </ErrorBoundary>
                  </LayoutWrapper>
                </ProtectedRoute>
              }
            >
              <Route index element={<Analytics />} />
              <Route path="trading" element={<TradingAnalytics />} />
              <Route path="portfolio" element={<PortfolioAnalytics />} />
              <Route path="market" element={<MarketAnalytics />} />
              <Route path="risk" element={<RiskAnalytics />} />
              <Route path="performance" element={<PerformanceAnalytics />} />
              <Route path="backtest" element={<BacktestAnalytics />} />
              <Route path="strategy" element={<StrategyAnalytics />} />
              <Route path="trading-bot" element={<TradingBotAnalytics />} />
              <Route path="trading-pair" element={<TradingPairAnalytics />} />
              <Route path="correlation" element={<CorrelationAnalytics />} />
              <Route path="model-performance" element={<ModelPerformanceAnalytics />} />
              <Route path="exchange" element={<ExchangeAnalytics />} />
              <Route path="event" element={<EventAnalytics />} />
              <Route path="error" element={<ErrorAnalytics />} />
              <Route path="data-import" element={<DataImportAnalytics />} />
              <Route path="orderbook" element={<OrderbookAnalytics />} />
              <Route path="reporting" element={<ReportingAnalytics />} />
              <Route path="prediction" element={<PredictionAnalytics />} />
              <Route path="tax" element={<TaxAnalytics />} />
            </Route>
            
            {/* WebSocket Test Route */}
            <Route 
              path="/websocket-test" 
              element={
                <ProtectedRoute>
                  <LayoutWrapper>
                    <ErrorBoundary>
                      <WebSocketTest />
                    </ErrorBoundary>
                  </LayoutWrapper>
                </ProtectedRoute>
              } 
            />
            
            {/* Micro-Investing Routes */}
            <Route 
              path="/roundup-transactions" 
              element={
                <ProtectedRoute requiredPermission="micro_investing">
                  <LayoutWrapper>
                    <ErrorBoundary>
                      <RoundupTransactions />
                    </ErrorBoundary>
                  </LayoutWrapper>
                </ProtectedRoute>
              } 
            />
            
            {/* Catch-all route */}
            <Route path="*" element={<Navigate to="/" replace />} />
          </Routes>
          </SubscriptionProvider>
        </ToastProvider>
        </AccessibilityProvider>
      </GlobalLoadingProvider>
    </ErrorBoundary>
  );
};

export default App;