import React, { useEffect, useRef } from 'react';
import { Link } from 'react-router-dom';
import { useAccessibility } from '../../hooks/useAccessibility';

interface MobileMenuProps {
  isOpen: boolean;
  onClose: () => void;
  currentPath: string;
}

/**
 * Mobile off-canvas menu component with accessibility features
 */
const MobileMenu: React.FC<MobileMenuProps> = ({ isOpen, onClose, currentPath }) => {
  const menuRef = useRef<HTMLDivElement>(null);
  const closeButtonRef = useRef<HTMLButtonElement>(null);
  const { isDarkMode, toggleDarkMode, prefersReducedMotion, announce } = useAccessibility();
  
  // Navigation menu items
  const navItems = [
    { path: '/dashboard', label: 'Dashboard', icon: 'home' },
    { path: '/trading', label: 'Trading', icon: 'chart-line' },
    { path: '/portfolio', label: 'Portfolio', icon: 'briefcase' },
    { path: '/analytics', label: 'Analytics', icon: 'chart-bar' },
    { path: '/learning', label: 'Learning', icon: 'book' },
    { path: '/settings', label: 'Settings', icon: 'cog' },
    { path: '/profile', label: 'Profile', icon: 'user' },
  ];
  
  // Handle keyboard interactions
  useEffect(() => {
    const handleEscape = (e: KeyboardEvent) => {
      if (e.key === 'Escape' && isOpen) {
        onClose();
        announce('Menu closed', false);
      }
    };
    
    if (isOpen) {
      // Focus trap
      closeButtonRef.current?.focus();
      document.addEventListener('keydown', handleEscape);
      
      // Prevent body scrolling when menu is open
      document.body.style.overflow = 'hidden';
      
      // Announce to screen readers
      announce('Navigation menu opened', false);
    } else {
      document.body.style.overflow = '';
    }
    
    return () => {
      document.removeEventListener('keydown', handleEscape);
      document.body.style.overflow = '';
    };
  }, [isOpen, onClose, announce]);
  
  // Calculate the animation classes based on state and preferences
  const menuClasses = `
    fixed top-0 bottom-0 left-0 z-50 w-64 px-4 py-4 bg-white dark:bg-gray-800 shadow-lg 
    transform transition-transform ${prefersReducedMotion ? '' : 'duration-300'} 
    ${isOpen ? 'translate-x-0' : '-translate-x-full'}
  `;
  
  // Calculate the backdrop classes
  const backdropClasses = `
    fixed inset-0 z-40 bg-black bg-opacity-50 
    transition-opacity ${prefersReducedMotion ? '' : 'duration-300'} 
    ${isOpen ? 'opacity-100' : 'opacity-0 pointer-events-none'}
  `;
  
  return (
    <>
      {/* Semi-transparent backdrop */}
      <div 
        className={backdropClasses}
        onClick={onClose}
        aria-hidden="true"
      />
      
      {/* Menu panel */}
      <div 
        ref={menuRef}
        className={menuClasses}
        role="dialog"
        aria-modal="true"
        aria-label="Navigation menu"
      >
        {/* Header with close button */}
        <div className="flex items-center justify-between border-b border-gray-200 dark:border-gray-700 pb-4 mb-4">
          <div className="text-xl font-semibold text-gray-900 dark:text-white">Menu</div>
          <button
            ref={closeButtonRef}
            className="p-2 text-gray-600 dark:text-gray-400 hover:text-gray-900 dark:hover:text-white rounded-full"
            onClick={onClose}
            aria-label="Close menu"
          >
            <svg xmlns="http://www.w3.org/2000/svg" className="h-6 w-6" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
            </svg>
          </button>
        </div>
        
        {/* Navigation links */}
        <nav>
          <ul className="space-y-2">
            {navItems.map((item) => {
              const isActive = currentPath === item.path || 
                (item.path !== '/dashboard' && currentPath.startsWith(item.path));
                
              return (
                <li key={item.path}>
                  <Link
                    to={item.path}
                    className={`
                      flex items-center px-3 py-2 rounded-lg 
                      ${isActive 
                        ? 'bg-purple-100 dark:bg-purple-900 text-purple-700 dark:text-purple-200 font-medium' 
                        : 'text-gray-700 dark:text-gray-300 hover:bg-gray-100 dark:hover:bg-gray-700'
                      }
                    `}
                    onClick={onClose}
                    aria-current={isActive ? 'page' : undefined}
                  >
                    <span className="flex-1">{item.label}</span>
                  </Link>
                </li>
              );
            })}
          </ul>
        </nav>
        
        {/* Accessibility controls */}
        <div className="mt-6 pt-6 border-t border-gray-200 dark:border-gray-700">
          <h3 className="text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">Display Settings</h3>
          <div className="flex items-center justify-between py-2">
            <span className="text-sm text-gray-600 dark:text-gray-400">Dark Mode</span>
            <button
              onClick={() => {
                toggleDarkMode();
                announce(`Dark mode ${!isDarkMode ? 'enabled' : 'disabled'}`, false);
              }}
              className={`
                relative inline-flex h-6 w-11 flex-shrink-0 cursor-pointer rounded-full border-2 
                border-transparent transition-colors duration-200 ease-in-out focus:outline-none focus:ring-2 
                focus:ring-purple-500 focus:ring-offset-2
                ${isDarkMode ? 'bg-purple-600' : 'bg-gray-200'}
              `}
              role="switch"
              aria-checked={isDarkMode}
            >
              <span className="sr-only">Toggle dark mode</span>
              <span
                aria-hidden="true"
                className={`
                  pointer-events-none inline-block h-5 w-5 transform rounded-full 
                  bg-white shadow ring-0 transition duration-200 ease-in-out
                  ${isDarkMode ? 'translate-x-5' : 'translate-x-0'}
                `}
              />
            </button>
          </div>
        </div>
      </div>
    </>
  );
};

export default MobileMenu;