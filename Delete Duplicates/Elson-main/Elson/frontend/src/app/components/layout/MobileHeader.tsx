import React, { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import { useAccessibility } from '../../hooks/useAccessibility';

interface MobileHeaderProps {
  onMenuToggle: () => void;
  isMenuOpen: boolean;
}

const MobileHeader: React.FC<MobileHeaderProps> = ({ onMenuToggle, isMenuOpen }) => {
  const { isDarkMode, toggleDarkMode, announce } = useAccessibility();
  const [isScrolled, setIsScrolled] = useState(false);
  
  // Check if page is scrolled down
  useEffect(() => {
    const handleScroll = () => {
      setIsScrolled(window.scrollY > 10);
    };
    
    window.addEventListener('scroll', handleScroll);
    return () => window.removeEventListener('scroll', handleScroll);
  }, []);
  
  // Handle dark mode toggle with announcement
  const handleDarkModeToggle = () => {
    toggleDarkMode();
    announce(`${isDarkMode ? 'Light' : 'Dark'} mode enabled`, false);
  };
  
  return (
    <header
      className={`fixed top-0 left-0 right-0 z-40 transition-all duration-200 ${
        isScrolled
          ? isDarkMode
            ? 'bg-gray-900 shadow-lg shadow-gray-900/20'
            : 'bg-white shadow-lg shadow-gray-200/50'
          : isDarkMode
          ? 'bg-gray-900'
          : 'bg-white'
      }`}
    >
      <div className="px-4 flex items-center justify-between h-16">
        {/* Logo and site title */}
        <div className="flex items-center">
          <Link to="/" className="flex items-center" aria-label="Go to dashboard">
            <div className="h-8 w-8 rounded-md bg-purple-600 flex items-center justify-center text-white mr-3">
              <svg xmlns="http://www.w3.org/2000/svg" className="h-5 w-5" viewBox="0 0 20 20" fill="currentColor">
                <path d="M2 10a8 8 0 018-8v8h8a8 8 0 11-16 0z" />
                <path d="M12 2.252A8.014 8.014 0 0117.748 8H12V2.252z" />
              </svg>
            </div>
            <span className={`font-bold text-lg ${isDarkMode ? 'text-white' : 'text-gray-900'}`}>
              Elson
            </span>
          </Link>
        </div>

        {/* Action buttons */}
        <div className="flex items-center space-x-1">
          {/* Dark mode toggle */}
          <button
            onClick={handleDarkModeToggle}
            className={`p-2 rounded-full touch-target
              ${isDarkMode 
                ? 'text-yellow-200 hover:bg-gray-800' 
                : 'text-gray-600 hover:bg-gray-100'
              }`}
            aria-label={`Switch to ${isDarkMode ? 'light' : 'dark'} mode`}
          >
            {isDarkMode ? (
              <svg xmlns="http://www.w3.org/2000/svg" className="h-6 w-6" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  strokeWidth={2}
                  d="M12 3v1m0 16v1m9-9h-1M4 12H3m15.364 6.364l-.707-.707M6.343 6.343l-.707-.707m12.728 0l-.707.707M6.343 17.657l-.707.707M16 12a4 4 0 11-8 0 4 4 0 018 0z"
                />
              </svg>
            ) : (
              <svg xmlns="http://www.w3.org/2000/svg" className="h-6 w-6" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  strokeWidth={2}
                  d="M20.354 15.354A9 9 0 018.646 3.646 9.003 9.003 0 0012 21a9.003 9.003 0 008.354-5.646z"
                />
              </svg>
            )}
          </button>

          {/* Notifications */}
          <Link
            to="/notifications"
            className={`p-2 rounded-full touch-target
              ${isDarkMode 
                ? 'text-gray-300 hover:bg-gray-800' 
                : 'text-gray-600 hover:bg-gray-100'
              }`}
            aria-label="View notifications"
          >
            <svg xmlns="http://www.w3.org/2000/svg" className="h-6 w-6" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path
                strokeLinecap="round"
                strokeLinejoin="round"
                strokeWidth={2}
                d="M15 17h5l-1.405-1.405A2.032 2.032 0 0118 14.158V11a6.002 6.002 0 00-4-5.659V5a2 2 0 10-4 0v.341C7.67 6.165 6 8.388 6 11v3.159c0 .538-.214 1.055-.595 1.436L4 17h5m6 0v1a3 3 0 11-6 0v-1m6 0H9"
              />
            </svg>
          </Link>

          {/* Menu Button */}
          <button
            onClick={onMenuToggle}
            className={`p-2 rounded-full touch-target
              ${isMenuOpen
                ? isDarkMode 
                  ? 'bg-gray-800 text-purple-400' 
                  : 'bg-gray-100 text-purple-600'
                : isDarkMode 
                  ? 'text-gray-300 hover:bg-gray-800' 
                  : 'text-gray-600 hover:bg-gray-100'
              }`}
            aria-expanded={isMenuOpen}
            aria-label={isMenuOpen ? "Close menu" : "Open menu"}
          >
            {isMenuOpen ? (
              <svg xmlns="http://www.w3.org/2000/svg" className="h-6 w-6" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
              </svg>
            ) : (
              <svg xmlns="http://www.w3.org/2000/svg" className="h-6 w-6" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 6h16M4 12h16M4 18h16" />
              </svg>
            )}
          </button>
        </div>
      </div>
    </header>
  );
};

export default MobileHeader;