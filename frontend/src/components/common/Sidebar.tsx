import React, { useState } from 'react';
import { Link, useLocation, useNavigate } from 'react-router-dom';
import { useDispatch } from 'react-redux';
import { useTradingContext } from '../../contexts/TradingContext';
import { TradingModeIndicator } from '../trading/TradingModeIndicator';
import { logout } from '../../store/slices/authSlice';

interface SidebarProps {
  className?: string;
}

export const Sidebar: React.FC<SidebarProps> = ({ className = '' }) => {
  const location = useLocation();
  const navigate = useNavigate();
  const dispatch = useDispatch();
  const { mode, switchMode, isBlocked } = useTradingContext();
  const [showModeConfirm, setShowModeConfirm] = useState(false);

  const learningItems = [
    { name: 'Learning Hub', path: '/learn', icon: 'M12 6.253v13m0-13C10.832 5.477 9.246 5 7.5 5S4.168 5.477 3 6.253v13C4.168 18.477 5.754 18 7.5 18s3.332.477 4.5 1.253m0-13C13.168 5.477 14.754 5 16.5 5c1.747 0 3.332.477 4.5 1.253v13C19.832 18.477 18.247 18 16.5 18c-1.746 0-3.332.477-4.5 1.253' },
    { name: 'Market Discovery', path: '/discover', icon: 'M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z' },
  ];

  const wealthItems = [
    { name: 'Portfolio', path: '/portfolio', icon: 'M16 8v8m-4-5v5m-4-2v2m-2 4h12a2 2 0 002-2V6a2 2 0 00-2-2H6a2 2 0 00-2 2v12a2 2 0 002 2z' },
    { name: 'Transfers', path: '/transfers', icon: 'M12 8c-1.657 0-3 .895-3 2s1.343 2 3 2 3 .895 3 2-1.343 2-3 2m0-8c1.11 0 2.08.402 2.599 1M12 8V7m0 1v8m0 0v1m0-1c-1.11 0-2.08-.402-2.599-1M21 12a9 9 0 11-18 0 9 9 0 0118 0z' },
    { name: 'Statements', path: '/statements', icon: 'M9 5H7a2 2 0 00-2 2v12a2 2 0 002 2h10a2 2 0 002-2V7a2 2 0 00-2-2h-2M9 5a2 2 0 002 2h2a2 2 0 002-2M9 5a2 2 0 012-2h2a2 2 0 012 2m-3 7h3m-3 4h3m-6-4h.01M9 16h.01' },
    { name: 'High-Yield Savings', path: '/savings', icon: 'M17 9V7a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2m2 4h10a2 2 0 002-2v-6a2 2 0 00-2-2H9a2 2 0 00-2 2v6a2 2 0 002 2zm7-5a2 2 0 11-4 0 2 2 0 014 0z' },
    { name: 'Elson Card', path: '/card', icon: 'M3 10h18M7 15h1m4 0h1m-7 4h12a3 3 0 003-3V8a3 3 0 00-3-3H6a3 3 0 00-3 3v8a3 3 0 003 3z' },
    { name: 'Insurance', path: '/insurance', icon: 'M9 12l2 2 4-4m5.618-4.016A11.955 11.955 0 0112 2.944a11.955 11.955 0 01-8.618 3.04A12.02 12.02 0 003 9c0 5.591 3.824 10.29 9 11.622 5.176-1.332 9-6.03 9-11.622 0-1.042-.133-2.052-.382-3.016z' },
    { name: 'Retirement', path: '/retirement', icon: 'M8 7V3m8 4V3m-9 8h10M5 21h14a2 2 0 002-2V7a2 2 0 00-2-2H5a2 2 0 00-2 2v12a2 2 0 002 2z' },
  ];

  // Create mode-aware trading navigation
  const handleTradingNavigation = async (path: string) => {
    if (mode === 'live' && isBlocked) {
      alert('Live trading is currently blocked');
      return;
    }
    
    const fullPath = `/${mode}${path}`;
    navigate(fullPath);
  };

  const tradingItems = [
    { 
      name: 'Stocks & ETFs', 
      path: '/trading', 
      icon: 'M13 7h8m0 0v8m0-8l-8 8-4-4-6 6',
      requiresConfirmation: mode === 'live',
      fullPath: `/${mode}/trading`
    },
    { 
      name: 'Advanced Trading', 
      path: '/advanced-trading', 
      icon: 'M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z',
      requiresConfirmation: mode === 'live',
      fullPath: `/${mode}/advanced-trading`
    },
    { 
      name: 'Portfolio', 
      path: '/portfolio', 
      icon: 'M16 8v8m-4-5v5m-4-2v2m-2 4h12a2 2 0 002-2V6a2 2 0 00-2-2H6a2 2 0 00-2 2v12a2 2 0 002 2z',
      requiresConfirmation: false,
      fullPath: `/${mode}/portfolio`
    },
  ];

  const settingsItems = [
    { name: 'Account Settings', path: '/settings/profile', icon: 'M10.325 4.317c.426-1.756 2.924-1.756 3.35 0a1.724 1.724 0 002.573 1.066c1.543-.94 3.31.826 2.37 2.37a1.724 1.724 0 001.065 2.572c1.756.426 1.756 2.924 0 3.35a1.724 1.724 0 00-1.066 2.573c.94 1.543-.826 3.31-2.37 2.37a1.724 1.724 0 00-2.572 1.065c-.426 1.756-2.924 1.756-3.35 0a1.724 1.724 0 00-2.573-1.066c-1.543.94-3.31-.826-2.37-2.37a1.724 1.724 0 00-1.065-2.572c-1.756-.426-1.756-2.924 0-3.35a1.724 1.724 0 001.066-2.573c-.94-1.543.826-3.31 2.37-2.37.996.608 2.296.07 2.572-1.065z' },
    { name: 'Security', path: '/settings/security', icon: 'M12 15v2m-6 4h12a2 2 0 002-2v-6a2 2 0 00-2-2H6a2 2 0 00-2 2v6a2 2 0 002 2zm10-10V7a4 4 0 00-8 0v4h8z' },
    { name: 'Premium Features', path: '/settings/premium', icon: 'M5 3v4M3 5h4M6 17v4m-2-2h4m5-16l2.286 6.857L21 12l-5.714 2.143L13 21l-2.286-6.857L5 12l5.714-2.143L13 3z' },
  ];

  const handleLogout = () => {
    dispatch(logout());
    localStorage.removeItem('token');
    localStorage.removeItem('tradingMode');
    navigate('/home');
  };

  const SidebarSection = ({ title, items }: { title: string; items: any[] }) => (
    <div className="px-4 py-2">
      <h3 className="text-xs uppercase text-gray-500 font-semibold tracking-wider">{title}</h3>
      <ul className="mt-3 space-y-1">
        {items.map((item) => (
          <li key={item.path}>
            <Link
              to={item.path}
              className={`flex items-center px-4 py-2 rounded-lg transition-colors ${
                location.pathname === item.path
                  ? 'bg-purple-900 text-purple-300'
                  : 'text-gray-300 hover:bg-gray-800'
              }`}
            >
              <svg className="h-5 w-5 mr-3 text-purple-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d={item.icon} />
              </svg>
              <span>{item.name}</span>
            </Link>
          </li>
        ))}
      </ul>
    </div>
  );

  const TradingSidebarSection = ({ title, items }: { title: string; items: any[] }) => {
    const handleClick = async (e: React.MouseEvent, item: any) => {
      e.preventDefault();
      
      if (isBlocked) {
        window.alert('Trading is currently blocked');
        return;
      }
      
      if (item.requiresConfirmation && mode === 'live') {
        const confirmed = window.confirm(`You are about to access ${item.name} in LIVE trading mode with real money. Continue?`);
        if (!confirmed) return;
      }
      
      handleTradingNavigation(item.path);
    };

    return (
      <div className="px-4 py-2">
        <h3 className="text-xs uppercase text-gray-500 font-semibold tracking-wider">{title}</h3>
        <ul className="mt-3 space-y-1">
          {items.map((item) => (
            <li key={item.path}>
              <a
                href={item.fullPath}
                onClick={(e) => handleClick(e, item)}
                className={`flex items-center px-4 py-2 rounded-lg transition-colors relative ${
                  location.pathname === item.fullPath
                    ? 'bg-purple-900 text-purple-300'
                    : 'text-gray-300 hover:bg-gray-800'
                } ${isBlocked ? 'opacity-50 cursor-not-allowed' : ''}`}
              >
                <svg className="h-5 w-5 mr-3 text-purple-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d={item.icon} />
                </svg>
                <span>{item.name}</span>
                {mode === 'live' && item.requiresConfirmation && (
                  <div className="ml-auto">
                    <span className="text-red-400 text-xs">🔴</span>
                  </div>
                )}
                {isBlocked && (
                  <div className="ml-auto">
                    <span className="text-gray-500 text-xs">🚫</span>
                  </div>
                )}
              </a>
            </li>
          ))}
        </ul>
      </div>
    );
  };

  return (
    <div className={`bg-gray-900 min-h-screen py-4 px-2 ${className}`} style={{ width: '280px' }}>
      {/* Trading Mode Indicator */}
      <div className="px-4 mb-6">
        <TradingModeIndicator 
          showSwitcher={true} 
          position="relative" 
          size="sm" 
        />
      </div>
      
      <div className="mt-8">
        <TradingSidebarSection title={`Trading (${mode.toUpperCase()})`} items={tradingItems} />
      </div>
      <div className="mt-8">
        <SidebarSection title="Wealth & Savings" items={wealthItems} />
      </div>
      <div className="mt-8">
        <SidebarSection title="Learning" items={learningItems} />
      </div>
      <div className="mt-8">
        <SidebarSection title="Settings" items={settingsItems} />
      </div>
      <div className="mt-8 px-4">
        <button
          onClick={handleLogout}
          className="w-full flex items-center px-4 py-2 rounded-lg transition-colors text-gray-300 hover:bg-gray-800"
        >
          <svg className="h-5 w-5 mr-3 text-purple-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M17 16l4-4m0 0l-4-4m4 4H7m6 4v1a3 3 0 01-3 3H6a3 3 0 01-3-3V7a3 3 0 013-3h4a3 3 0 013 3v1" />
          </svg>
          <span>Logout</span>
        </button>
      </div>
      
      <div className="mt-8 px-4">
        <div className="bg-gray-800 rounded-xl p-4">
          <h3 className="text-white font-medium mb-2">Upgrade to Premium</h3>
          <p className="text-gray-400 text-sm mb-3">Get AI-powered trades and advanced analytics</p>
          <Link 
            to="/upgrade"
            className="bg-purple-600 hover:bg-purple-700 text-white text-sm px-4 py-2 rounded-full inline-flex items-center transition-colors"
          >
            Upgrade Now
            <svg className="ml-1 h-4 w-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M9 5l7 7-7 7" />
            </svg>
          </Link>
        </div>
      </div>
    </div>
  );
};