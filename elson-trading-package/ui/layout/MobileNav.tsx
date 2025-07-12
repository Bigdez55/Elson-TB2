import React from 'react';
import { Link } from 'react-router-dom';
import { useAccessibility } from '../../hooks/useAccessibility';

interface MobileNavProps {
  currentPath: string;
}

const MobileNav: React.FC<MobileNavProps> = ({ currentPath }) => {
  const { isDarkMode } = useAccessibility();
  
  // Define mobile navigation items
  const navItems = [
    {
      name: 'Dashboard',
      path: '/dashboard',
      icon: (
        <svg xmlns="http://www.w3.org/2000/svg" className="h-6 w-6" fill="none" viewBox="0 0 24 24" stroke="currentColor">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M3 12l2-2m0 0l7-7 7 7M5 10v10a1 1 0 001 1h3m10-11l2 2m-2-2v10a1 1 0 01-1 1h-3m-6 0a1 1 0 001-1v-4a1 1 0 011-1h2a1 1 0 011 1v4a1 1 0 001 1m-6 0h6" />
        </svg>
      ),
    },
    {
      name: 'Portfolio',
      path: '/portfolio',
      icon: (
        <svg xmlns="http://www.w3.org/2000/svg" className="h-6 w-6" fill="none" viewBox="0 0 24 24" stroke="currentColor">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M16 8v8m-4-5v5m-4-2v2m-2 4h12a2 2 0 002-2V6a2 2 0 00-2-2H6a2 2 0 00-2 2v12a2 2 0 002 2z" />
        </svg>
      ),
    },
    {
      name: 'Trading',
      path: '/trading',
      icon: (
        <svg xmlns="http://www.w3.org/2000/svg" className="h-6 w-6" fill="none" viewBox="0 0 24 24" stroke="currentColor">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 7h8m0 0v8m0-8l-8 8-4-4-6 6" />
        </svg>
      ),
    },
    {
      name: 'Learning',
      path: '/learning',
      icon: (
        <svg xmlns="http://www.w3.org/2000/svg" className="h-6 w-6" fill="none" viewBox="0 0 24 24" stroke="currentColor">
          <path d="M12 14l9-5-9-5-9 5 9 5z" />
          <path d="M12 14l6.16-3.422a12.083 12.083 0 01.665 6.479A11.952 11.952 0 0012 20.055a11.952 11.952 0 00-6.824-2.998 12.078 12.078 0 01.665-6.479L12 14z" />
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 14l9-5-9-5-9 5 9 5zm0 0l6.16-3.422a12.083 12.083 0 01.665 6.479A11.952 11.952 0 0012 20.055a11.952 11.952 0 00-6.824-2.998 12.078 12.078 0 01.665-6.479L12 14zm-4 6v-7.5l4-2.222" />
        </svg>
      ),
    },
    {
      name: 'Account',
      path: '/profile',
      icon: (
        <svg xmlns="http://www.w3.org/2000/svg" className="h-6 w-6" fill="none" viewBox="0 0 24 24" stroke="currentColor">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M16 7a4 4 0 11-8 0 4 4 0 018 0zM12 14a7 7 0 00-7 7h14a7 7 0 00-7-7z" />
        </svg>
      ),
    },
  ];

  return (
    <nav 
      className={`fixed bottom-0 left-0 right-0 z-40 border-t ${
        isDarkMode 
          ? 'bg-gray-900 border-gray-800 text-gray-300' 
          : 'bg-white border-gray-200 text-gray-700'
      } transition-colors duration-150 ease-in-out`}
      aria-label="Mobile navigation"
    >
      <div className="grid grid-cols-5 h-16">
        {navItems.map((item) => {
          const isActive = currentPath === item.path || 
                          (item.path !== '/dashboard' && currentPath.startsWith(item.path));
          
          return (
            <Link
              key={item.name}
              to={item.path}
              className={`flex flex-col items-center justify-center px-2 py-2 text-xs 
                touch-target transition-colors
                ${isActive 
                  ? isDarkMode 
                    ? 'text-purple-400' 
                    : 'text-purple-600' 
                  : 'hover:text-gray-500 dark:hover:text-gray-300'
                }
              `}
              aria-current={isActive ? 'page' : undefined}
            >
              <div className={`mb-1 ${isActive ? 'text-purple-500' : ''}`}>{item.icon}</div>
              <span className="text-center truncate w-full">{item.name}</span>
            </Link>
          );
        })}
      </div>
    </nav>
  );
};

export default MobileNav;