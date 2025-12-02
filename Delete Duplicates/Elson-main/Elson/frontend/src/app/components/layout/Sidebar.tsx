import React, { useState, useEffect } from 'react';
import { useTheme } from '@mui/material/styles';
import useMediaQuery from '@mui/material/useMediaQuery';
import { NavLink, useLocation, useNavigate } from 'react-router-dom';
import { useSelector, useDispatch } from 'react-redux';
import { fetchActiveSubscription } from '../../store/slices/subscriptionSlice';

interface SidebarProps {
  isOpen: boolean;
  onClose: () => void;
}

interface NavItemProps {
  to: string;
  icon: React.ReactNode;
  label: string;
  onClick?: () => void;
}

const NavItem: React.FC<NavItemProps> = ({ to, icon, label, onClick }) => {
  const location = useLocation();
  const isActive = location.pathname === to;
  
  // Use media query for responsive design
  const theme = useTheme();
  const isMobile = useMediaQuery(theme.breakpoints.down('sm'));

  return (
    <NavLink
      to={to}
      className={`flex items-center px-4 ${isMobile ? 'py-3' : 'py-2'} text-gray-300 rounded-lg hover:bg-gray-800 transition-colors ${
        isActive ? 'bg-gray-800 text-white' : ''
      }`}
      onClick={onClick}
    >
      <div className={`${isMobile ? 'mr-4 text-lg' : 'mr-3'} text-purple-400`}>{icon}</div>
      <span className={isMobile ? 'text-base' : ''}>{label}</span>
      {isActive && isMobile && (
        <svg className="ml-auto h-5 w-5 text-purple-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M9 5l7 7-7 7" />
        </svg>
      )}
    </NavLink>
  );
};

// Collapsible section component for mobile optimization
const CollapsibleSection: React.FC<{
  title: string;
  children: React.ReactNode;
  initiallyExpanded?: boolean;
}> = ({ title, children, initiallyExpanded = true }) => {
  const [isExpanded, setIsExpanded] = useState(initiallyExpanded);
  
  // Use media query for responsive design
  const theme = useTheme();
  const isMobile = useMediaQuery(theme.breakpoints.down('sm'));
  
  return (
    <div className={`px-4 ${isMobile ? 'py-3 mb-1' : 'py-2'}`}>
      <div
        className={`flex items-center justify-between cursor-pointer ${isMobile ? 'py-1' : ''}`}
        onClick={() => setIsExpanded(!isExpanded)}
      >
        <h3 className={`${isMobile ? 'text-sm' : 'text-xs'} uppercase ${isExpanded ? 'text-purple-400' : 'text-gray-500'} font-semibold tracking-wider`}>{title}</h3>
        <svg
          className={`${isMobile ? 'h-5 w-5' : 'h-4 w-4'} ${isExpanded ? 'text-purple-400' : 'text-gray-500'} transform transition-transform ${isExpanded ? 'rotate-180' : ''}`}
          fill="none"
          stroke="currentColor"
          viewBox="0 0 24 24"
          xmlns="http://www.w3.org/2000/svg"
        >
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M19 9l-7 7-7-7" />
        </svg>
      </div>
      <div className={`${isMobile ? 'mt-3' : 'mt-2'} space-y-1 transition-all duration-300 ${isExpanded ? 'max-h-96 opacity-100' : 'max-h-0 opacity-0 overflow-hidden'}`}>
        {children}
      </div>
    </div>
  );
};

const Sidebar: React.FC<SidebarProps> = ({ isOpen, onClose }) => {
  const navigate = useNavigate();
  const dispatch = useDispatch();
  const { isPremium, subscription } = useSelector((state: any) => state.subscription);
  const location = useLocation();
  
  // Responsive design breakpoints
  const theme = useTheme();
  const isMobile = useMediaQuery(theme.breakpoints.down('sm'));
  const isTablet = useMediaQuery(theme.breakpoints.between('sm', 'md'));
  
  // Fetch subscription data if not already loaded
  React.useEffect(() => {
    if (!subscription) {
      dispatch(fetchActiveSubscription());
    }
  }, [dispatch, subscription]);

  // Get current section to auto-expand the relevant section on mobile
  const getCurrentSection = () => {
    const path = location.pathname;
    if (path.includes('/portfolio') || path.includes('/transfers') || path.includes('/statements')) {
      return 'account';
    }
    if (path.includes('/trading') || path.includes('/ai-invest') || path.includes('/crypto') || path.includes('/round-ups')) {
      return 'trading';
    }
    if (path.includes('/savings') || path.includes('/card') || path.includes('/insurance') || path.includes('/retirement')) {
      return 'wealth';
    }
    if (path.includes('/settings') || path.includes('/security') || path.includes('/premium')) {
      return 'settings';
    }
    return 'account';
  };

  const currentSection = getCurrentSection();

  return (
    <>
      {/* Overlay for mobile */}
      {isOpen && (
        <div
          className="fixed inset-0 bg-black bg-opacity-50 md:hidden z-20"
          onClick={onClose}
        />
      )}

      {/* Sidebar */}
      <div
        className={`sidebar bg-gray-900 min-h-screen py-4 ${isMobile ? 'px-3' : 'px-2'} fixed md:static inset-y-0 left-0 transform ${
          isOpen ? 'translate-x-0' : '-translate-x-full'
        } md:translate-x-0 transition-transform duration-200 ease-in-out z-30 ${isMobile ? 'w-[85vw]' : 'w-64'} md:w-auto`}
      >
        {/* Close button - only visible on mobile */}
        <div className="flex items-center justify-between md:hidden px-4 pb-4 pt-2">
          <div className="text-xl font-bold text-white">Menu</div>
          <button
            onClick={onClose}
            className="p-2 rounded-full text-gray-400 hover:bg-gray-800 hover:text-white focus:outline-none"
            aria-label="Close sidebar"
          >
            <svg className="h-6 w-6" fill="none" stroke="currentColor" viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M6 18L18 6M6 6l12 12" />
            </svg>
          </button>
        </div>

        {/* Navigation sections */}
        <div className="flex flex-col h-full overflow-y-auto pt-2 md:pt-0">
          {/* Account Section */}
          <CollapsibleSection title="Account" initiallyExpanded={currentSection === 'account'}>
            <ul className="space-y-1">
              <li>
                <NavItem 
                  to="/portfolio" 
                  icon={
                    <svg className="h-5 w-5" fill="none" stroke="currentColor" viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M16 8v8m-4-5v5m-4-2v2m-2 4h12a2 2 0 002-2V6a2 2 0 00-2-2H6a2 2 0 00-2 2v12a2 2 0 002 2z"></path>
                    </svg>
                  } 
                  label="Portfolio"
                  onClick={onClose}
                />
              </li>
              <li>
                <NavItem 
                  to="/transfers" 
                  icon={
                    <svg className="h-5 w-5" fill="none" stroke="currentColor" viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M12 8c-1.657 0-3 .895-3 2s1.343 2 3 2 3 .895 3 2-1.343 2-3 2m0-8c1.11 0 2.08.402 2.599 1M12 8V7m0 1v8m0 0v1m0-1c-1.11 0-2.08-.402-2.599-1M21 12a9 9 0 11-18 0 9 9 0 0118 0z"></path>
                    </svg>
                  } 
                  label="Transfers"
                  onClick={onClose}
                />
              </li>
              <li>
                <NavItem 
                  to="/statements" 
                  icon={
                    <svg className="h-5 w-5" fill="none" stroke="currentColor" viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M9 5H7a2 2 0 00-2 2v12a2 2 0 002 2h10a2 2 0 002-2V7a2 2 0 00-2-2h-2M9 5a2 2 0 002 2h2a2 2 0 002-2M9 5a2 2 0 012-2h2a2 2 0 012 2m-3 7h3m-3 4h3m-6-4h.01M9 16h.01"></path>
                    </svg>
                  } 
                  label="Statements"
                  onClick={onClose}
                />
              </li>
            </ul>
          </CollapsibleSection>
          
          {/* Trading Section */}
          <CollapsibleSection title="Trading" initiallyExpanded={currentSection === 'trading'}>
            <ul className="space-y-1">
              <li>
                <NavItem 
                  to="/trading" 
                  icon={
                    <svg className="h-5 w-5" fill="none" stroke="currentColor" viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M13 7h8m0 0v8m0-8l-8 8-4-4-6 6"></path>
                    </svg>
                  } 
                  label="Stocks & ETFs"
                  onClick={onClose}
                />
              </li>
              <li>
                <NavItem 
                  to="/ai-invest" 
                  icon={
                    <svg className="h-5 w-5" fill="none" stroke="currentColor" viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M9 12l2 2 4-4m5.618-4.016A11.955 11.955 0 0112 2.944a11.955 11.955 0 01-8.618 3.04A12.02 12.02 0 003 9c0 5.591 3.824 10.29 9 11.622 5.176-1.332 9-6.03 9-11.622 0-1.042-.133-2.052-.382-3.016z"></path>
                    </svg>
                  } 
                  label="AI Auto-Invest"
                  onClick={onClose}
                />
              </li>
              <li>
                <NavItem 
                  to="/crypto" 
                  icon={
                    <svg className="h-5 w-5" fill="none" stroke="currentColor" viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M12 8c-1.657 0-3 .895-3 2s1.343 2 3 2 3 .895 3 2-1.343 2-3 2m0-8c1.11 0 2.08.402 2.599 1M12 8V7m0 1v8m0 0v1m0-1c-1.11 0-2.08-.402-2.599-1M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
                    </svg>
                  } 
                  label="Crypto"
                  onClick={onClose}
                />
              </li>
              <li>
                <NavItem 
                  to="/roundup-transactions" 
                  icon={
                    <svg className="h-5 w-5" fill="none" stroke="currentColor" viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15" />
                    </svg>
                  } 
                  label="Round-Up Transactions"
                  onClick={onClose}
                />
              </li>
            </ul>
          </CollapsibleSection>
          
          {/* Wealth & Savings Section */}
          <CollapsibleSection title="Wealth & Savings" initiallyExpanded={currentSection === 'wealth'}>
            <ul className="space-y-1">
              <li>
                <NavItem 
                  to="/savings" 
                  icon={
                    <svg className="h-5 w-5" fill="none" stroke="currentColor" viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M17 9V7a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2m2 4h10a2 2 0 002-2v-6a2 2 0 00-2-2H9a2 2 0 00-2 2v6a2 2 0 002 2zm7-5a2 2 0 11-4 0 2 2 0 014 0z" />
                    </svg>
                  } 
                  label="High-Yield Savings"
                  onClick={onClose}
                />
              </li>
              <li>
                <NavItem 
                  to="/card" 
                  icon={
                    <svg className="h-5 w-5" fill="none" stroke="currentColor" viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M3 10h18M7 15h1m4 0h1m-7 4h12a3 3 0 003-3V8a3 3 0 00-3-3H6a3 3 0 00-3 3v8a3 3 0 003 3z" />
                    </svg>
                  } 
                  label="Elson Card"
                  onClick={onClose}
                />
              </li>
              <li>
                <NavItem 
                  to="/insurance" 
                  icon={
                    <svg className="h-5 w-5" fill="none" stroke="currentColor" viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M9 12l2 2 4-4m5.618-4.016A11.955 11.955 0 0112 2.944a11.955 11.955 0 01-8.618 3.04A12.02 12.02 0 003 9c0 5.591 3.824 10.29 9 11.622 5.176-1.332 9-6.03 9-11.622 0-1.042-.133-2.052-.382-3.016z" />
                    </svg>
                  } 
                  label="Insurance"
                  onClick={onClose}
                />
              </li>
              <li>
                <NavItem 
                  to="/retirement" 
                  icon={
                    <svg className="h-5 w-5" fill="none" stroke="currentColor" viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M8 7V3m8 4V3m-9 8h10M5 21h14a2 2 0 002-2V7a2 2 0 00-2-2H5a2 2 0 00-2 2v12a2 2 0 002 2z" />
                    </svg>
                  } 
                  label="Retirement"
                  onClick={onClose}
                />
              </li>
            </ul>
          </CollapsibleSection>
          
          {/* Settings Section */}
          <CollapsibleSection title="Settings" initiallyExpanded={currentSection === 'settings'}>
            <ul className="space-y-1">
              <li>
                <NavItem 
                  to="/settings" 
                  icon={
                    <svg className="h-5 w-5" fill="none" stroke="currentColor" viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M10.325 4.317c.426-1.756 2.924-1.756 3.35 0a1.724 1.724 0 002.573 1.066c1.543-.94 3.31.826 2.37 2.37a1.724 1.724 0 001.065 2.572c1.756.426 1.756 2.924 0 3.35a1.724 1.724 0 00-1.066 2.573c.94 1.543-.826 3.31-2.37 2.37a1.724 1.724 0 00-2.572 1.065c-.426 1.756-2.924 1.756-3.35 0a1.724 1.724 0 00-2.573-1.066c-1.543.94-3.31-.826-2.37-2.37a1.724 1.724 0 00-1.065-2.572c-1.756-.426-1.756-2.924 0-3.35a1.724 1.724 0 001.066-2.573c-.94-1.543.826-3.31 2.37-2.37.996.608 2.296.07 2.572-1.065z"></path>
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M15 12a3 3 0 11-6 0 3 3 0 016 0z"></path>
                    </svg>
                  } 
                  label="Account Settings"
                  onClick={onClose}
                />
              </li>
              <li>
                <NavItem 
                  to="/security" 
                  icon={
                    <svg className="h-5 w-5" fill="none" stroke="currentColor" viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M12 15v2m-6 4h12a2 2 0 002-2v-6a2 2 0 00-2-2H6a2 2 0 00-2 2v6a2 2 0 002 2zm10-10V7a4 4 0 00-8 0v4h8z"></path>
                    </svg>
                  } 
                  label="Security"
                  onClick={onClose}
                />
              </li>
              <li>
                <NavItem 
                  to="/premium" 
                  icon={
                    <svg className="h-5 w-5" fill="none" stroke="currentColor" viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M5 3v4M3 5h4M6 17v4m-2-2h4m5-16l2.286 6.857L21 12l-5.714 2.143L13 21l-2.286-6.857L5 12l5.714-2.143L13 3z" />
                    </svg>
                  } 
                  label="Premium Features"
                  onClick={onClose}
                />
              </li>
              <li>
                <NavItem 
                  to="/logout" 
                  icon={
                    <svg className="h-5 w-5" fill="none" stroke="currentColor" viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M17 16l4-4m0 0l-4-4m4 4H7m6 4v1a3 3 0 01-3 3H6a3 3 0 01-3-3V7a3 3 0 013-3h4a3 3 0 013 3v1"></path>
                    </svg>
                  } 
                  label="Logout"
                  onClick={onClose}
                />
              </li>
            </ul>
          </CollapsibleSection>
          
          {/* Premium Upgrade - Bottom fixed on mobile */}
          {!isPremium && (
            <div className="mt-8 px-4 sticky bottom-0 bg-gray-900 py-4">
              <div className="bg-gray-800 rounded-xl p-4 shadow-lg">
                <h3 className="text-white font-medium mb-2 text-lg">Upgrade to Premium</h3>
                <p className="text-gray-400 text-sm mb-3">Get AI-powered trades and advanced analytics</p>
                <button 
                  onClick={() => {
                    navigate('/pricing');
                    onClose();
                  }}
                  className={`bg-purple-600 hover:bg-purple-700 text-white ${isMobile ? 'text-base w-full py-3' : 'text-sm px-4 py-2'} rounded-full inline-flex items-center justify-center`}
                >
                  <span>Upgrade Now</span>
                  <svg className="ml-2 h-4 w-4" fill="none" stroke="currentColor" viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M9 5l7 7-7 7"></path>
                  </svg>
                </button>
              </div>
            </div>
          )}
        </div>
      </div>
    </>
  );
};

export default Sidebar;