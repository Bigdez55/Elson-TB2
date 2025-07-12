import React, { useState, useEffect } from 'react';
import { useLocation } from 'react-router-dom';
import { SkipNavLink, SkipNavContent } from '../common/SkipNav';
import { useAccessibility } from '../../hooks/useAccessibility';

// Import components lazily
const MobileHeader = React.lazy(() => import('./MobileHeader'));
const MobileNav = React.lazy(() => import('./MobileNav'));
const MobileMenu = React.lazy(() => import('./MobileMenu'));

interface MobileLayoutProps {
  children: React.ReactNode;
}

/**
 * A mobile-optimized layout component with accessibility features
 */
const MobileLayout: React.FC<MobileLayoutProps> = ({ children }) => {
  const [menuOpen, setMenuOpen] = useState(false);
  const location = useLocation();
  const { 
    isDarkMode, 
    prefersReducedMotion,
    announce 
  } = useAccessibility();
  
  // Handle navigation announcement for screen readers
  useEffect(() => {
    // Extract the page name from the path
    const pathSegments = location.pathname.split('/').filter(Boolean);
    const pageName = pathSegments.length > 0 
      ? pathSegments[pathSegments.length - 1].replace(/-/g, ' ') 
      : 'home';
    
    // Announce page change
    announce(`Navigated to ${pageName} page`, false);
    
    // Close menu when route changes
    setMenuOpen(false);
  }, [location.pathname, announce]);
  
  // Apply dark mode and reduced motion classes
  useEffect(() => {
    document.documentElement.classList.toggle('dark', isDarkMode);
  }, [isDarkMode]);
  
  useEffect(() => {
    document.documentElement.classList.toggle('reduce-motion', prefersReducedMotion);
  }, [prefersReducedMotion]);
  
  return (
    <div className="flex flex-col min-h-screen bg-gray-50 dark:bg-gray-900">
      {/* Accessibility skip link */}
      <SkipNavLink />
      
      {/* Mobile header with menu toggle */}
      <React.Suspense fallback={<div className="h-16 bg-gray-900"></div>}>
        <MobileHeader 
          onMenuToggle={() => setMenuOpen(!menuOpen)} 
          isMenuOpen={menuOpen}
        />
      </React.Suspense>
      
      {/* Main content area */}
      <main id="main-content" className="flex-1 relative" tabIndex={-1}>
        <SkipNavContent />
        
        {/* Off-canvas menu */}
        <React.Suspense fallback={null}>
          <MobileMenu 
            isOpen={menuOpen} 
            onClose={() => setMenuOpen(false)} 
            currentPath={location.pathname}
          />
        </React.Suspense>
        
        {/* Page content */}
        <div className="py-4 px-4">
          {children}
        </div>
      </main>
      
      {/* Bottom navigation bar */}
      <React.Suspense fallback={<div className="h-16 bg-gray-900"></div>}>
        <MobileNav currentPath={location.pathname} />
      </React.Suspense>
      
      {/* Accessibility status announcer (hidden visually) */}
      <div id="status-announcer" className="sr-only" aria-live="polite"></div>
    </div>
  );
};

export default MobileLayout;