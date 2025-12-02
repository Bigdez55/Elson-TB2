import React from 'react';
import { Outlet } from 'react-router-dom';
import { useDispatch, useSelector } from 'react-redux';
import { RootState } from '../store/store';
import { logout } from '../store/slices/authSlice';
import { NavBar } from './common/NavBar';
import { Sidebar } from './common/Sidebar';

const Layout: React.FC = () => {
  const dispatch = useDispatch();
  const { user } = useSelector((state: RootState) => state.auth);

  const handleLogout = () => {
    dispatch(logout());
  };

  const userData = {
    name: user?.full_name || user?.email || 'Alex Morgan',
    avatar: '/api/placeholder/32/32',
    isPremium: true, // This should come from user subscription data
  };

  return (
    <div className="min-h-screen bg-gray-800">
      <NavBar user={userData} />
      
      <div className="flex pt-16">
        <Sidebar />
        
        <main className="flex-1 bg-gray-800 min-h-screen">
          <Outlet />
        </main>
      </div>
    </div>
  );
};

export default Layout;