import React, { useState, useEffect } from 'react';
import { useSelector, useDispatch } from 'react-redux';
import { useNavigate, Link } from 'react-router-dom';
import { logout } from '../../store/slices/userSlice';
import { fetchActiveSubscription } from '../../store/slices/subscriptionSlice';

interface HeaderProps {
  onMenuClick: () => void;
}

const Header: React.FC<HeaderProps> = ({ onMenuClick }) => {
  const dispatch = useDispatch();
  const navigate = useNavigate();
  const [isProfileMenuOpen, setIsProfileMenuOpen] = useState(false);
  const [isNotificationsOpen, setIsNotificationsOpen] = useState(false);
  
  const { user } = useSelector((state: any) => state.user);
  const { unreadNotifications } = useSelector((state: any) => state.notifications);
  const { isPremium, subscription } = useSelector((state: any) => state.subscription);
  
  // Fetch subscription data if not already loaded
  useEffect(() => {
    if (!subscription) {
      dispatch(fetchActiveSubscription());
    }
  }, [dispatch, subscription]);

  const handleLogout = () => {
    dispatch(logout());
    navigate('/login');
  };

  return (
    <nav className="bg-gray-900 shadow-sm fixed w-full z-10">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="flex justify-between h-16">
          <div className="flex">
            <div className="flex-shrink-0 flex items-center">
              <button
                onClick={onMenuClick}
                className="p-2 rounded-lg text-gray-400 hover:bg-gray-800 md:hidden"
              >
                <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M4 6h16M4 12h16M4 18h16" />
                </svg>
              </button>
              <div className="text-2xl font-bold">
                <span className="text-purple-400">Elson</span>
              </div>
            </div>
            <div className="hidden sm:ml-6 sm:flex sm:space-x-8">
              <Link to="/dashboard" className="border-purple-500 text-purple-300 hover:border-purple-500 hover:text-purple-300 inline-flex items-center px-1 pt-1 border-b-2 text-sm font-medium">
                Dashboard
              </Link>
              <Link to="/trading" className="border-transparent text-gray-300 hover:border-purple-500 hover:text-purple-300 inline-flex items-center px-1 pt-1 border-b-2 text-sm font-medium">
                Trade
              </Link>
              <Link to="/portfolio" className="border-transparent text-gray-300 hover:border-purple-500 hover:text-purple-300 inline-flex items-center px-1 pt-1 border-b-2 text-sm font-medium">
                Discover
              </Link>
              <Link to="/learning" className="border-transparent text-gray-300 hover:border-purple-500 hover:text-purple-300 inline-flex items-center px-1 pt-1 border-b-2 text-sm font-medium">
                Learn
              </Link>
              <Link to="/family" className="border-transparent text-gray-300 hover:border-purple-500 hover:text-purple-300 inline-flex items-center px-1 pt-1 border-b-2 text-sm font-medium">
                Wealth
              </Link>
              <Link to="/crypto" className="border-transparent text-gray-300 hover:border-purple-500 hover:text-purple-300 inline-flex items-center px-1 pt-1 border-b-2 text-sm font-medium">
                Crypto
              </Link>
            </div>
          </div>
          <div className="flex items-center">
            <button 
              onClick={() => setIsNotificationsOpen(!isNotificationsOpen)}
              className="text-gray-300 hover:text-white p-2 rounded-full"
            >
              <svg className="h-6 w-6" fill="none" stroke="currentColor" viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M15 17h5l-1.405-1.405A2.032 2.032 0 0118 14.158V11a6.002 6.002 0 00-4-5.659V5a2 2 0 10-4 0v.341C7.67 6.165 6 8.388 6 11v3.159c0 .538-.214 1.055-.595 1.436L4 17h5m6 0v1a3 3 0 11-6 0v-1m6 0H9"></path>
              </svg>
              {unreadNotifications > 0 && (
                <span className="absolute top-1 right-1 block h-4 w-4 rounded-full bg-red-500 text-xs text-white text-center">
                  {unreadNotifications}
                </span>
              )}
            </button>

            {isNotificationsOpen && (
              <div className="absolute right-0 top-16 mt-2 w-80 bg-gray-800 rounded-lg shadow-lg border border-gray-700 z-20">
                {/* Notification items would go here */}
                <div className="p-4">
                  <h4 className="text-white font-medium mb-2">Notifications</h4>
                  <div className="divide-y divide-gray-700">
                    <div className="py-3">
                      <p className="text-sm text-gray-300">New trading opportunity detected</p>
                      <p className="text-xs text-gray-400 mt-1">5 minutes ago</p>
                    </div>
                    <div className="py-3">
                      <p className="text-sm text-gray-300">Deposit completed successfully</p>
                      <p className="text-xs text-gray-400 mt-1">2 hours ago</p>
                    </div>
                  </div>
                </div>
              </div>
            )}

            <div className="ml-3 relative flex items-center">
              {isPremium && (
                <div className="mr-3">
                  <span className="premium-badge px-2 py-1 rounded-full text-xs font-medium text-white bg-gradient-to-r from-yellow-500 to-red-500">Premium</span>
                </div>
              )}
              <button 
                onClick={() => setIsProfileMenuOpen(!isProfileMenuOpen)}
                className="flex items-center text-sm focus:outline-none focus:border-gray-300"
              >
                <img className="h-8 w-8 rounded-full" src="https://via.placeholder.com/32" alt="User avatar" />
                <span className="ml-2 text-gray-300 hidden md:inline">{user?.username || 'Alex Morgan'}</span>
                <svg className="ml-1 h-5 w-5 text-gray-400" fill="currentColor" viewBox="0 0 20 20">
                  <path fillRule="evenodd" d="M5.293 7.293a1 1 0 011.414 0L10 10.586l3.293-3.293a1 1 0 111.414 1.414l-4 4a1 1 0 01-1.414 0l-4-4a1 1 0 010-1.414z" clipRule="evenodd"></path>
                </svg>
              </button>

              {isProfileMenuOpen && (
                <div className="absolute right-0 top-10 mt-2 w-48 bg-gray-800 rounded-lg shadow-lg border border-gray-700 z-20">
                  <div className="p-2">
                    <button
                      onClick={() => navigate('/profile')}
                      className="w-full text-left px-4 py-2 text-sm text-gray-300 hover:bg-gray-700 rounded"
                    >
                      Profile Settings
                    </button>
                    <button
                      onClick={() => navigate('/settings')}
                      className="w-full text-left px-4 py-2 text-sm text-gray-300 hover:bg-gray-700 rounded"
                    >
                      Account Settings
                    </button>
                    {!isPremium && (
                      <button
                        onClick={() => navigate('/pricing')}
                        className="w-full text-left px-4 py-2 text-sm text-purple-300 hover:bg-gray-700 rounded"
                      >
                        Upgrade to Premium
                      </button>
                    )}
                    <hr className="my-2 border-gray-700" />
                    <button
                      onClick={handleLogout}
                      className="w-full text-left px-4 py-2 text-sm text-red-400 hover:bg-gray-700 rounded"
                    >
                      Logout
                    </button>
                  </div>
                </div>
              )}
            </div>
          </div>
        </div>
      </div>
    </nav>
  );
};

export default Header;