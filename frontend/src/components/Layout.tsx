import React from 'react';
import { Outlet } from 'react-router-dom';
import { useSelector } from 'react-redux';
import { RootState } from '../store/store';
import { NavBar } from './common/NavBar';
import { Sidebar } from './common/Sidebar';
import { MarketStatusStrip } from './elson';

const Layout: React.FC = () => {
  const { user } = useSelector((state: RootState) => state.auth);

  const userData = {
    name: user?.full_name || user?.email || 'Alex Morgan',
    avatar: '/api/placeholder/32/32',
    isPremium: true,
  };

  return (
    <div className="min-h-screen" style={{ backgroundColor: '#0D1B2A' }}>
      {/* Market Status Strip */}
      <MarketStatusStrip />

      {/* Navigation */}
      <NavBar user={userData} />

      <div className="flex pt-16">
        {/* Sidebar */}
        <Sidebar />

        {/* Main Content */}
        <main className="flex-1 min-h-screen" style={{ backgroundColor: '#0D1B2A' }}>
          <Outlet />
        </main>
      </div>
    </div>
  );
};

export default Layout;
