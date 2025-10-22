import React, { useState, useLayoutEffect, useEffect } from 'react';
import { useLocation } from 'react-router-dom';
import { useTranslation } from 'react-i18next';
import { Sidebar } from './Sidebar';
import { AppHeader } from './MobileHeader';
import { PublicFooter } from './PublicFooter';
import { AnimatedBackground } from './AnimatedBackground';

interface LayoutProps {
  children: React.ReactNode;
}

export const Layout: React.FC<LayoutProps> = ({ children }) => {
  const [sidebarOpen, setSidebarOpen] = useState(false);
  const [isMobile, setIsMobile] = useState(false);
  const location = useLocation();
  const { t } = useTranslation();

  useLayoutEffect(() => {
    const checkMobile = () => {
      const width = window.innerWidth;
      const mobile = width < 1024;
      setIsMobile(mobile);
      if (!mobile) {
        setSidebarOpen(true); // Show sidebar on desktop by default
      }
    };
    
    // Check immediately on mount
    checkMobile();
    
    // Add event listener for resize
    window.addEventListener('resize', checkMobile);
    return () => window.removeEventListener('resize', checkMobile);
  }, []);

  // Update document title when location or language changes
  useEffect(() => {
    const pageTitle = getPageTitle();
    document.title = pageTitle;
  }, [location.pathname, t]);

  const getPageTitle = () => {
    switch (location.pathname) {
      case '/category':
        return t('navigation.categories');
      case '/account':
        return t('navigation.accounts');
      case '/expense':
        return t('navigation.expenses');
      case '/income':
        return t('navigation.income');
      case '/recurring':
        return t('navigation.recurring');
      case '/goals':
        return t('navigation.goals');
      case '/profile':
        return t('navigation.profile');
      default:
        return t('header.appTitle');
    }
  };

  const handleSidebarToggle = () => {
    setSidebarOpen(!sidebarOpen);
  };

  const handleSidebarClose = () => {
    setSidebarOpen(false);
  };

  
  return (
    <div className="min-h-screen theme-bg theme-transition relative">
      {/* Animated background layers */}
      <AnimatedBackground />
      
      {/* App Header - Shows on both mobile and desktop */}
      <AppHeader
        onMenuClick={handleSidebarToggle}
        title={getPageTitle()}
        isMobile={isMobile}
      />

      <div className="flex min-h-[calc(100vh-4rem)] relative" style={{ zIndex: 10 }}>
        {/* Sidebar - Always visible, but collapsible on desktop */}
        <Sidebar isOpen={sidebarOpen} onClose={handleSidebarClose} />

        {/* Main Content */}
        <div className="flex-1 flex flex-col">
          {/* Page Content */}
          <main className="flex-1">
            <div className="p-4 sm:p-6 lg:p-6 min-h-[calc(100vh-8rem)] main-content">
              {children}
            </div>
          </main>
          
          {/* Footer */}
          <PublicFooter />
        </div>
        
      </div>
    </div>
  );
}; 