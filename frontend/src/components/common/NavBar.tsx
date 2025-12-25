import React from 'react';
import { Link, useLocation } from 'react-router-dom';

interface NavBarProps {
  user?: {
    name?: string;
    avatar?: string;
    isPremium?: boolean;
  };
}

export const NavBar: React.FC<NavBarProps> = ({ user }) => {
  const location = useLocation();

  const navItems = [
    { name: 'Dashboard', path: '/dashboard' },
    { name: 'Trade', path: '/trading' },
    { name: 'Discover', path: '/discover' },
    { name: 'Learn', path: '/learn' },
    { name: 'Wealth', path: '/wealth' },
    { name: 'Crypto', path: '/crypto' },
  ];

  return (
    <nav className="bg-gray-900 shadow-sm fixed w-full z-10">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="flex justify-between h-16">
          <div className="flex">
            <div className="flex-shrink-0 flex items-center">
              <div className="text-2xl font-bold">
                <span className="text-purple-400">Elson</span>
              </div>
            </div>
            <div className="hidden sm:ml-6 sm:flex sm:space-x-8">
              {navItems.map((item) => (
                <Link
                  key={item.path}
                  to={item.path}
                  className={`${
                    location.pathname === item.path
                      ? 'border-purple-500 text-purple-300'
                      : 'border-transparent text-gray-300 hover:border-purple-500 hover:text-purple-300'
                  } inline-flex items-center px-1 pt-1 border-b-2 text-sm font-medium transition-colors`}
                >
                  {item.name}
                </Link>
              ))}
            </div>
          </div>
          <div className="flex items-center">
            <button className="text-gray-300 hover:text-white p-2 rounded-full transition-colors">
              <svg className="h-6 w-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M15 17h5l-1.405-1.405A2.032 2.032 0 0118 14.158V11a6.002 6.002 0 00-4-5.659V5a2 2 0 10-4 0v.341C7.67 6.165 6 8.388 6 11v3.159c0 .538-.214 1.055-.595 1.436L4 17h5m6 0v1a3 3 0 11-6 0v-1m6 0H9" />
              </svg>
            </button>
            <div className="ml-3 relative flex items-center">
              {user?.isPremium && (
                <div className="mr-3">
                  <span className="bg-gradient-to-r from-yellow-400 to-red-500 px-2 py-1 rounded-full text-xs font-medium text-white">
                    Premium
                  </span>
                </div>
              )}
              <button className="flex items-center text-sm focus:outline-none focus:border-gray-300">
                <img className="h-8 w-8 rounded-full" src={user?.avatar || "/api/placeholder/32/32"} alt="User avatar" />
                <span className="ml-2 text-gray-300">{user?.name || 'Alex Morgan'}</span>
                <svg className="ml-1 h-5 w-5 text-gray-400" fill="currentColor" viewBox="0 0 20 20">
                  <path fillRule="evenodd" d="M5.293 7.293a1 1 0 011.414 0L10 10.586l3.293-3.293a1 1 0 111.414 1.414l-4 4a1 1 0 01-1.414 0l-4-4a1 1 0 010-1.414z" clipRule="evenodd" />
                </svg>
              </button>
            </div>
          </div>
        </div>
      </div>
    </nav>
  );
};