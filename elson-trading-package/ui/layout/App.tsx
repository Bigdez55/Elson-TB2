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

// Authentication & Onboarding Pages
import EmailVerification from '../../../pages/EmailVerification';
import WelcomeOnboarding from '../../../pages/WelcomeOnboarding';

// Trading & Investment Pages
import CryptoTrading from '../../../pages/CryptoTrading';
import DiscoverInvestments from '../../../pages/DiscoverInvestments';
import PaperTrading from '../../../pages/PaperTrading';

// User Dashboard & Portfolio Pages
import GoalsPerformance from '../../../pages/GoalsPerformance';
import ElsonCard from '../../../pages/ElsonCard';

// Family Account Pages
import AddFamilyMember from '../../../pages/family/AddFamilyMember';
import CustodialAccountView from '../../../pages/family/CustodialAccountView';
import FamilySettings from '../../../pages/family/FamilySettings';

// Settings Pages
import ConnectedDevices from '../../../pages/settings/ConnectedDevices';
import AccessibilityPreferences from '../../../pages/settings/AccessibilityPreferences';

// Support Pages
import SupportTicket from '../../../pages/support/SupportTicket';
import LiveChat from '../../../pages/support/LiveChat';
import Feedback from '../../../pages/support/Feedback';

// Admin Pages
import AdminDashboard from '../../../pages/admin/AdminDashboard';
import UserManagement from '../../../pages/admin/UserManagement';
import KYCVerification from '../../../pages/admin/KYCVerification';

// New Pages
import Home from '../../../pages/Home';
import AboutUs from '../../../pages/AboutUs';
import HelpCenter from '../../../pages/HelpCenter';
import Contact from '../../../pages/Contact';
import HighYieldSavings from '../../../pages/HighYieldSavings';

// Analytics pages
import AnalyticsLayout from '../../../pages/analytics/AnalyticsLayout';
import Analytics from '../../../pages/analytics/Analytics';
import TradingAnalytics from '../../../pages/analytics/consolidated/TradingAnalytics';
import PortfolioAnalytics from '../../../pages/analytics/consolidated/PortfolioAnalytics';
import MarketAnalytics from '../../../pages/analytics/consolidated/MarketAnalytics';
import ModelAnalytics from '../../../pages/analytics/consolidated/ModelAnalytics';

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
              <Route path="/" element={<Home />} />
              <Route path="/login" element={<Login />} />
              <Route path="/register" element={<Register />} />
              <Route path="/forgot-password" element={<ForgotPassword />} />
              <Route path="/reset-password" element={<ResetPassword />} />
              <Route path="/two-factor-auth" element={<TwoFactorAuth />} />
              <Route path="/pricing" element={<Pricing />} />
              <Route path="/about" element={<AboutUs />} />
              <Route path="/help-center" element={<HelpCenter />} />
              <Route path="/contact" element={<Contact />} />
              <Route path="/subscription/success" element={<SubscriptionSuccess />} />
              <Route path="/subscription/cancel" element={<SubscriptionCancel />} />
              <Route path="/ws-test" element={<WebSocketTest />} />
              
              {/* Authentication & Onboarding Routes */}
              <Route path="/email-verification" element={<EmailVerification />} />
              <Route path="/welcome" element={<WelcomeOnboarding />} />
            
            {/* Protected routes - Core pages */}
            <Route 
              path="/home" 
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
            <Route 
              path="/family/add-member" 
              element={
                <ProtectedRoute requiredSubscription="FAMILY" requiredRole="GUARDIAN">
                  <LayoutWrapper>
                    <ErrorBoundary>
                      <AddFamilyMember />
                    </ErrorBoundary>
                  </LayoutWrapper>
                </ProtectedRoute>
              } 
            />
            <Route 
              path="/family/account/:id" 
              element={
                <ProtectedRoute requiredSubscription="FAMILY" requiredRole="GUARDIAN">
                  <LayoutWrapper>
                    <ErrorBoundary>
                      <CustodialAccountView />
                    </ErrorBoundary>
                  </LayoutWrapper>
                </ProtectedRoute>
              } 
            />
            <Route 
              path="/family/settings" 
              element={
                <ProtectedRoute requiredSubscription="FAMILY" requiredRole="GUARDIAN">
                  <LayoutWrapper>
                    <ErrorBoundary>
                      <FamilySettings />
                    </ErrorBoundary>
                  </LayoutWrapper>
                </ProtectedRoute>
              } 
            />
            
            {/* Settings Routes */}
            <Route 
              path="/settings/devices" 
              element={
                <ProtectedRoute>
                  <LayoutWrapper>
                    <ErrorBoundary>
                      <ConnectedDevices />
                    </ErrorBoundary>
                  </LayoutWrapper>
                </ProtectedRoute>
              } 
            />
            <Route 
              path="/settings/accessibility" 
              element={
                <ProtectedRoute>
                  <LayoutWrapper>
                    <ErrorBoundary>
                      <AccessibilityPreferences />
                    </ErrorBoundary>
                  </LayoutWrapper>
                </ProtectedRoute>
              } 
            />
            
            {/* Support Routes */}
            <Route 
              path="/support/ticket" 
              element={
                <ProtectedRoute>
                  <LayoutWrapper>
                    <ErrorBoundary>
                      <SupportTicket />
                    </ErrorBoundary>
                  </LayoutWrapper>
                </ProtectedRoute>
              } 
            />
            <Route 
              path="/support/chat" 
              element={
                <ProtectedRoute>
                  <LayoutWrapper>
                    <ErrorBoundary>
                      <LiveChat />
                    </ErrorBoundary>
                  </LayoutWrapper>
                </ProtectedRoute>
              } 
            />
            <Route 
              path="/support/feedback" 
              element={
                <ProtectedRoute>
                  <LayoutWrapper>
                    <ErrorBoundary>
                      <Feedback />
                    </ErrorBoundary>
                  </LayoutWrapper>
                </ProtectedRoute>
              } 
            />
            
            {/* Admin Routes */}
            <Route 
              path="/admin/dashboard" 
              element={
                <ProtectedRoute requiredRole="ADMIN">
                  <LayoutWrapper>
                    <ErrorBoundary>
                      <AdminDashboard />
                    </ErrorBoundary>
                  </LayoutWrapper>
                </ProtectedRoute>
              } 
            />
            <Route 
              path="/admin/users" 
              element={
                <ProtectedRoute requiredRole="ADMIN">
                  <LayoutWrapper>
                    <ErrorBoundary>
                      <UserManagement />
                    </ErrorBoundary>
                  </LayoutWrapper>
                </ProtectedRoute>
              } 
            />
            <Route 
              path="/admin/kyc" 
              element={
                <ProtectedRoute requiredRole="ADMIN">
                  <LayoutWrapper>
                    <ErrorBoundary>
                      <KYCVerification />
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
              <Route path="model" element={<ModelAnalytics />} />
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
            
            {/* Trading & Investment Routes */}
            <Route 
              path="/crypto-trading" 
              element={
                <ProtectedRoute>
                  <LayoutWrapper>
                    <ErrorBoundary>
                      <CryptoTrading />
                    </ErrorBoundary>
                  </LayoutWrapper>
                </ProtectedRoute>
              } 
            />
            
            <Route 
              path="/discover" 
              element={
                <ProtectedRoute>
                  <LayoutWrapper>
                    <ErrorBoundary>
                      <DiscoverInvestments />
                    </ErrorBoundary>
                  </LayoutWrapper>
                </ProtectedRoute>
              } 
            />
            
            <Route 
              path="/paper-trading" 
              element={
                <ProtectedRoute>
                  <LayoutWrapper>
                    <ErrorBoundary>
                      <PaperTrading />
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
            
            {/* High-Yield Savings */}
            <Route 
              path="/high-yield-savings" 
              element={
                <ProtectedRoute requiredSubscription="PREMIUM">
                  <LayoutWrapper>
                    <ErrorBoundary>
                      <HighYieldSavings />
                    </ErrorBoundary>
                  </LayoutWrapper>
                </ProtectedRoute>
              } 
            />
            
            {/* User Dashboard & Portfolio Routes */}
            <Route 
              path="/goals-performance" 
              element={
                <ProtectedRoute>
                  <LayoutWrapper>
                    <ErrorBoundary>
                      <GoalsPerformance />
                    </ErrorBoundary>
                  </LayoutWrapper>
                </ProtectedRoute>
              } 
            />
            
            <Route 
              path="/elson-card" 
              element={
                <ProtectedRoute>
                  <LayoutWrapper>
                    <ErrorBoundary>
                      <ElsonCard />
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