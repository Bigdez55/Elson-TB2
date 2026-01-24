import { useEffect } from 'react';
import { Routes, Route, Navigate, useLocation } from 'react-router-dom';
import { useDispatch, useSelector } from 'react-redux';
import { RootState } from './store/store';
import { checkAuth } from './store/slices/authSlice';
import { ThemeProvider } from './contexts/ThemeContext';
import { TradingContextProvider } from './contexts/TradingContext';
import { TradingModeBanner } from './components/trading/TradingModeIndicator';
import { TradingModeRedirect, TradingRouteGuard } from './components/routing/TradingModeRedirect';
import { TradingModeSync } from './components/routing/TradingModeSync';
import Layout from './components/Layout';
import { MobileLayout } from './components/elson-v2/layout/MobileLayout';
import { LiveDataProvider } from './components/layout/LiveDataProvider';
import PerformanceDashboard from './components/monitoring/PerformanceDashboard';
import { usePerformanceMonitoring } from './hooks/usePerformanceMonitoring';
import { initializeBundleOptimizations } from './utils/bundleOptimization';
import LoginPage from './pages/LoginPage';
import RegisterPage from './pages/RegisterPage';
import HomePage from './pages/HomePage';
import PricingPage from './pages/PricingPage';
import DashboardPage from './pages/DashboardPage';
import TradingPage from './pages/TradingPage';
import PortfolioPage from './pages/PortfolioPage';
import AdvancedTradingPage from './pages/AdvancedTradingPage';
import SettingsPage from './pages/SettingsPage';
import FamilyAccountsPage from './pages/FamilyAccountsPage';
import DiscoverPage from './pages/DiscoverPage';
import LearnPage from './pages/LearnPage';
import ElsonAIPage from './pages/ElsonAIPage';
import WealthPage from './pages/WealthPage';
import CryptoPage from './pages/CryptoPage';
import TransfersPage from './pages/TransfersPage';
import StatementsPage from './pages/StatementsPage';
import SavingsPage from './pages/SavingsPage';
import CardPage from './pages/CardPage';
import InsurancePage from './pages/InsurancePage';
import RetirementPage from './pages/RetirementPage';
import { LoadingSpinner } from './components/common/LoadingSpinner';
import { ToastContainer } from './components/common/ToastContainer';
import { BottomNav } from './components/mobile/BottomNav';

// Scroll to top on route change
function ScrollToTop() {
  const { pathname } = useLocation();

  useEffect(() => {
    window.scrollTo(0, 0);
  }, [pathname]);

  return null;
}

function App() {
  const dispatch = useDispatch();
  const { isAuthenticated, isLoading } = useSelector((state: RootState) => state.auth);

  // Initialize performance monitoring
  usePerformanceMonitoring({
    trackComponents: true,
    trackMemory: true,
    trackWebSockets: true,
    reportInterval: 60000 // Report every minute
  });

  useEffect(() => {
    // Initialize bundle optimizations
    initializeBundleOptimizations();
    // Check if user is already authenticated on app start
    const token = localStorage.getItem('token');
    if (token) {
      dispatch(checkAuth() as any);
    }
  }, [dispatch]);

  if (isLoading) {
    return <LoadingSpinner />;
  }

  return (
    <ThemeProvider>
      <TradingContextProvider>
        <TradingModeSync />
        <ScrollToTop />
        <div className="App">
          <TradingModeBanner />
          <Routes>
          {/* Public routes */}
          <Route path="/home" element={
            isAuthenticated ? <Navigate to="/dashboard" replace /> : <HomePage />
          } />
          <Route path="/pricing" element={<PricingPage />} />
          <Route path="/login" element={
            isAuthenticated ? <Navigate to="/dashboard" replace /> : <LoginPage />
          } />
          <Route path="/register" element={
            isAuthenticated ? <Navigate to="/dashboard" replace /> : <RegisterPage />
          } />
          
          {/* Protected routes - New Mobile-First UI */}
          <Route path="/" element={
            isAuthenticated ? (
              <LiveDataProvider autoConnect={true} showConnectionBanner={true}>
                <MobileLayout />
              </LiveDataProvider>
            ) : <Navigate to="/home" replace />
          } />

          {/* Legacy routes - redirect to new UI */}
          <Route path="/dashboard" element={
            isAuthenticated ? <Navigate to="/" replace /> : <Navigate to="/home" replace />
          } />
          <Route path="/ai" element={
            isAuthenticated ? <Navigate to="/" replace /> : <Navigate to="/home" replace />
          } />
          <Route path="/portfolio" element={
            isAuthenticated ? <Navigate to="/" replace /> : <Navigate to="/home" replace />
          } />
          <Route path="/settings" element={
            isAuthenticated ? <Navigate to="/" replace /> : <Navigate to="/home" replace />
          } />
          <Route path="/settings/*" element={
            isAuthenticated ? <Navigate to="/" replace /> : <Navigate to="/home" replace />
          } />

          {/* Desktop Layout routes (optional - can be enabled for desktop users) */}
          <Route path="/desktop" element={
            isAuthenticated ? (
              <LiveDataProvider autoConnect={true} showConnectionBanner={true}>
                <Layout />
              </LiveDataProvider>
            ) : <Navigate to="/home" replace />
          }>
            <Route index element={<Navigate to="/desktop/dashboard" replace />} />
            <Route path="dashboard" element={<DashboardPage />} />
            <Route path="ai" element={<ElsonAIPage />} />
            <Route path="portfolio" element={<PortfolioPage />} />
            <Route path="family" element={<FamilyAccountsPage />} />
            <Route path="discover" element={<DiscoverPage />} />
            <Route path="learn" element={<LearnPage />} />
            <Route path="wealth" element={<WealthPage />} />
            <Route path="savings" element={<SavingsPage />} />
            <Route path="card" element={<CardPage />} />
            <Route path="insurance" element={<InsurancePage />} />
            <Route path="retirement" element={<RetirementPage />} />
            <Route path="crypto" element={<CryptoPage />} />
            <Route path="transfers" element={<TransfersPage />} />
            <Route path="statements" element={<StatementsPage />} />
            <Route path="settings" element={<SettingsPage />} />
            <Route path="settings/*" element={<SettingsPage />} />

            {/* Paper Trading Routes */}
            <Route path="paper">
              <Route path="trading" element={
                <TradingRouteGuard requiredMode="paper">
                  <TradingPage />
                </TradingRouteGuard>
              } />
              <Route path="trading/:symbol" element={
                <TradingRouteGuard requiredMode="paper">
                  <TradingPage />
                </TradingRouteGuard>
              } />
              <Route path="advanced-trading" element={
                <TradingRouteGuard requiredMode="paper">
                  <AdvancedTradingPage />
                </TradingRouteGuard>
              } />
              <Route path="portfolio" element={
                <TradingRouteGuard requiredMode="paper">
                  <PortfolioPage />
                </TradingRouteGuard>
              } />
            </Route>

            {/* Live Trading Routes */}
            <Route path="live">
              <Route path="trading" element={
                <TradingRouteGuard requiredMode="live">
                  <TradingPage />
                </TradingRouteGuard>
              } />
              <Route path="trading/:symbol" element={
                <TradingRouteGuard requiredMode="live">
                  <TradingPage />
                </TradingRouteGuard>
              } />
              <Route path="advanced-trading" element={
                <TradingRouteGuard requiredMode="live">
                  <AdvancedTradingPage />
                </TradingRouteGuard>
              } />
              <Route path="portfolio" element={
                <TradingRouteGuard requiredMode="live">
                  <PortfolioPage />
                </TradingRouteGuard>
              } />
            </Route>

            {/* Legacy route redirects */}
            <Route path="trading" element={<TradingModeRedirect basePath="/desktop/trading" />} />
            <Route path="trading/:symbol" element={<TradingModeRedirect basePath="/desktop/trading/:symbol" />} />
            <Route path="advanced-trading" element={<TradingModeRedirect basePath="/desktop/advanced-trading" />} />
          </Route>
          
          {/* Catch all route */}
          <Route path="*" element={<Navigate to={isAuthenticated ? "/" : "/home"} replace />} />
        </Routes>

          {/* Performance Dashboard (only in development or for admin users) */}
          {(process.env.NODE_ENV === 'development' ||
            (isAuthenticated && (window as any).__ENABLE_PERFORMANCE_DASHBOARD)) && (
            <PerformanceDashboard autoRefresh={true} refreshInterval={5000} />
          )}

          {/* Toast Notifications */}
          <ToastContainer />

          {/* Mobile Bottom Navigation */}
          {isAuthenticated && <BottomNav />}
        </div>
      </TradingContextProvider>
    </ThemeProvider>
  );
}

export default App;