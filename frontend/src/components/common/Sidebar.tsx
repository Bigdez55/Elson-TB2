import React from 'react';
import { Link, useLocation, useNavigate } from 'react-router-dom';
import { useDispatch } from 'react-redux';
import { useTradingContext } from '../../contexts/TradingContext';
import { TradingModeIndicator } from '../trading/TradingModeIndicator';
import { logout } from '../../store/slices/authSlice';
import { SidebarItem } from '../elson';
import {
  DashboardIcon,
  AIIcon,
  InvestIcon,
  LearnIcon,
  AccountIcon,
  UsersIcon,
  TrendingIcon,
  TransferIcon,
  DocumentIcon,
  CashIcon,
  ShieldIcon,
} from '../icons/ElsonIcons';

interface SidebarProps {
  className?: string;
}

export const Sidebar: React.FC<SidebarProps> = ({ className = '' }) => {
  const location = useLocation();
  const navigate = useNavigate();
  const dispatch = useDispatch();
  const { mode } = useTradingContext();

  const mainNavItems = [
    { icon: DashboardIcon, label: 'Dashboard', path: '/dashboard' },
    { icon: AIIcon, label: 'Elson AI', path: '/ai' },
    { icon: InvestIcon, label: 'Invest', path: `/${mode}/trading` },
    { icon: LearnIcon, label: 'Learn', path: '/learn' },
    { icon: AccountIcon, label: 'Account', path: '/settings' },
  ];

  const tradingItems = [
    { icon: TrendingIcon, label: 'Stocks & ETFs', path: `/${mode}/trading` },
    { icon: InvestIcon, label: 'Advanced Trading', path: `/${mode}/advanced-trading` },
    { icon: CashIcon, label: 'Portfolio', path: '/portfolio' },
  ];

  const accountItems = [
    { icon: UsersIcon, label: 'Family Accounts', path: '/family' },
    { icon: TransferIcon, label: 'Transfers', path: '/transfers' },
    { icon: DocumentIcon, label: 'Statements', path: '/statements' },
    { icon: ShieldIcon, label: 'Security', path: '/settings/security' },
  ];

  const handleLogout = () => {
    dispatch(logout());
    localStorage.removeItem('token');
    localStorage.removeItem('tradingMode');
    navigate('/home');
  };

  const isActive = (path: string) => {
    if (path.includes('/trading')) {
      return location.pathname.includes('/trading');
    }
    return location.pathname === path || location.pathname.startsWith(path + '/');
  };

  return (
    <div
      className={`hidden lg:block min-h-screen py-4 px-3 ${className}`}
      style={{ width: '260px', backgroundColor: '#0D1B2A', borderRight: '1px solid rgba(201, 162, 39, 0.1)' }}
    >
      {/* Logo */}
      <div className="px-4 mb-6">
        <Link to="/dashboard" className="flex items-center gap-2">
          <div
            className="w-10 h-10 rounded-xl flex items-center justify-center"
            style={{ background: 'linear-gradient(to bottom right, #C9A227, #E8D48B)' }}
          >
            <span className="text-[#0D1B2A] font-bold text-lg">E</span>
          </div>
          <span className="text-xl font-bold text-white">Elson</span>
        </Link>
      </div>

      {/* Trading Mode Indicator */}
      <div className="px-2 mb-6">
        <TradingModeIndicator
          showSwitcher={true}
          position="relative"
          size="sm"
        />
      </div>

      {/* Main Navigation */}
      <div className="space-y-1 mb-6">
        {mainNavItems.map((item) => (
          <SidebarItem
            key={item.path}
            icon={item.icon}
            label={item.label}
            active={isActive(item.path)}
            onClick={() => navigate(item.path)}
          />
        ))}
      </div>

      {/* Trading Section */}
      <div className="mb-6">
        <p className="px-4 text-xs text-gray-500 uppercase tracking-wider mb-2">
          Trading ({mode.toUpperCase()})
        </p>
        <div className="space-y-1">
          {tradingItems.map((item) => (
            <SidebarItem
              key={item.path}
              icon={item.icon}
              label={item.label}
              active={isActive(item.path)}
              onClick={() => navigate(item.path)}
            />
          ))}
        </div>
      </div>

      {/* Account Section */}
      <div className="mb-6">
        <p className="px-4 text-xs text-gray-500 uppercase tracking-wider mb-2">Account</p>
        <div className="space-y-1">
          {accountItems.map((item) => (
            <SidebarItem
              key={item.path}
              icon={item.icon}
              label={item.label}
              active={isActive(item.path)}
              onClick={() => navigate(item.path)}
            />
          ))}
        </div>
      </div>

      {/* Logout */}
      <div className="mt-auto pt-4">
        <button
          onClick={handleLogout}
          className="w-full flex items-center gap-3 px-4 py-3 rounded-xl text-sm font-medium text-gray-400 hover:bg-[#C9A227]/10 hover:text-gray-200 transition-all min-h-[44px]"
        >
          <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="1.5" d="M17 16l4-4m0 0l-4-4m4 4H7m6 4v1a3 3 0 01-3 3H6a3 3 0 01-3-3V7a3 3 0 013-3h4a3 3 0 013 3v1" />
          </svg>
          <span>Logout</span>
        </button>
      </div>

      {/* Upgrade Card */}
      <div className="mt-6 px-2">
        <div
          className="rounded-xl p-4"
          style={{ background: 'linear-gradient(to bottom right, rgba(201, 162, 39, 0.2), rgba(201, 162, 39, 0.05))', border: '1px solid rgba(201, 162, 39, 0.2)' }}
        >
          <h3 className="text-white font-medium mb-2">Upgrade to Growth</h3>
          <p className="text-gray-400 text-sm mb-3">Get AI-powered trades and family accounts</p>
          <Link
            to="/pricing"
            className="inline-flex items-center px-4 py-2 rounded-lg text-[#0D1B2A] text-sm font-semibold transition-all"
            style={{ background: 'linear-gradient(to right, #C9A227, #E8D48B)' }}
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
