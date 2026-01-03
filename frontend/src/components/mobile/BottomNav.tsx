import React from 'react';
import { NavLink, useLocation } from 'react-router-dom';
import { useTradingContext } from '../../contexts/TradingContext';

interface NavItem {
  path: string;
  label: string;
  icon: React.ReactNode;
}

/**
 * Mobile Bottom Navigation Component
 * Displays a fixed bottom navigation bar on mobile devices (<768px)
 * Hides on scroll down, shows on scroll up for better UX
 */
export const BottomNav: React.FC = () => {
  const location = useLocation();
  const { mode } = useTradingContext();
  const [isVisible, setIsVisible] = React.useState(true);
  const [lastScrollY, setLastScrollY] = React.useState(0);

  // Handle scroll behavior - hide on scroll down, show on scroll up
  React.useEffect(() => {
    const handleScroll = () => {
      const currentScrollY = window.scrollY;

      if (currentScrollY > lastScrollY && currentScrollY > 100) {
        // Scrolling down & past threshold
        setIsVisible(false);
      } else {
        // Scrolling up
        setIsVisible(true);
      }

      setLastScrollY(currentScrollY);
    };

    window.addEventListener('scroll', handleScroll, { passive: true });
    return () => window.removeEventListener('scroll', handleScroll);
  }, [lastScrollY]);

  // Trading path prefix based on mode
  const tradingPrefix = mode === 'paper' ? '/paper' : '/live';

  const navItems: NavItem[] = [
    {
      path: '/dashboard',
      label: 'Home',
      icon: (
        <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M3 12l2-2m0 0l7-7 7 7M5 10v10a1 1 0 001 1h3m10-11l2 2m-2-2v10a1 1 0 01-1 1h-3m-6 0a1 1 0 001-1v-4a1 1 0 011-1h2a1 1 0 011 1v4a1 1 0 001 1m-6 0h6" />
        </svg>
      ),
    },
    {
      path: `${tradingPrefix}/portfolio`,
      label: 'Portfolio',
      icon: (
        <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z" />
        </svg>
      ),
    },
    {
      path: `${tradingPrefix}/trading`,
      label: 'Invest',
      icon: (
        <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M12 8c-1.657 0-3 .895-3 2s1.343 2 3 2 3 .895 3 2-1.343 2-3 2m0-8c1.11 0 2.08.402 2.599 1M12 8V7m0 1v8m0 0v1m0-1c-1.11 0-2.08-.402-2.599-1M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
        </svg>
      ),
    },
    {
      path: '/discover',
      label: 'Discover',
      icon: (
        <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z" />
        </svg>
      ),
    },
    {
      path: '/settings',
      label: 'Settings',
      icon: (
        <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M10.325 4.317c.426-1.756 2.924-1.756 3.35 0a1.724 1.724 0 002.573 1.066c1.543-.94 3.31.826 2.37 2.37a1.724 1.724 0 001.065 2.572c1.756.426 1.756 2.924 0 3.35a1.724 1.724 0 00-1.066 2.573c.94 1.543-.826 3.31-2.37 2.37a1.724 1.724 0 00-2.572 1.065c-.426 1.756-2.924 1.756-3.35 0a1.724 1.724 0 00-2.573-1.066c-1.543.94-3.31-.826-2.37-2.37a1.724 1.724 0 00-1.065-2.572c-1.756-.426-1.756-2.924 0-3.35a1.724 1.724 0 001.066-2.573c-.94-1.543.826-3.31 2.37-2.37.996.608 2.296.07 2.572-1.065z" />
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M15 12a3 3 0 11-6 0 3 3 0 016 0z" />
        </svg>
      ),
    },
  ];

  // Check if current path matches (including nested routes)
  const isActive = (path: string) => {
    if (path === '/dashboard') {
      return location.pathname === '/dashboard' || location.pathname === '/';
    }
    return location.pathname.startsWith(path);
  };

  return (
    <nav
      className={`
        md:hidden fixed bottom-0 left-0 right-0 z-50
        bg-gray-900/95 backdrop-blur-lg border-t border-gray-800
        transform transition-transform duration-300 ease-in-out
        ${isVisible ? 'translate-y-0' : 'translate-y-full'}
        safe-area-bottom
      `}
      style={{ paddingBottom: 'env(safe-area-inset-bottom)' }}
      role="navigation"
      aria-label="Main navigation"
    >
      <div className="flex justify-around items-center h-16">
        {navItems.map((item) => {
          const active = isActive(item.path);
          return (
            <NavLink
              key={item.path}
              to={item.path}
              className={`
                flex flex-col items-center justify-center
                w-full h-full px-2 py-1
                transition-colors duration-200
                ${active
                  ? 'text-purple-400'
                  : 'text-gray-400 hover:text-gray-300 active:text-purple-300'
                }
              `}
              aria-current={active ? 'page' : undefined}
            >
              <div className={`
                relative p-1 rounded-lg transition-colors
                ${active ? 'bg-purple-500/20' : ''}
              `}>
                {item.icon}
                {/* Active indicator dot */}
                {active && (
                  <span className="absolute -top-0.5 -right-0.5 w-2 h-2 bg-purple-500 rounded-full" />
                )}
              </div>
              <span className={`
                text-xs mt-1 font-medium
                ${active ? 'text-purple-400' : 'text-gray-500'}
              `}>
                {item.label}
              </span>
            </NavLink>
          );
        })}
      </div>
    </nav>
  );
};

/**
 * Quick Action Button (FAB) for mobile
 * Shows a floating action button for quick trading access
 */
export const QuickTradeButton: React.FC = () => {
  const { mode } = useTradingContext();
  const tradingPath = mode === 'paper' ? '/paper/trading' : '/live/trading';

  return (
    <NavLink
      to={tradingPath}
      className="
        md:hidden fixed bottom-20 right-4 z-40
        w-14 h-14 rounded-full
        bg-gradient-to-r from-purple-600 to-blue-600
        shadow-lg shadow-purple-500/30
        flex items-center justify-center
        active:scale-95 transition-transform
      "
      aria-label="Quick trade"
    >
      <svg className="w-6 h-6 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M12 4v16m8-8H4" />
      </svg>
    </NavLink>
  );
};

/**
 * Mobile page wrapper that adds bottom padding for the nav
 */
export const MobilePageWrapper: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  return (
    <div className="pb-20 md:pb-0">
      {children}
    </div>
  );
};

export default BottomNav;
