import React, { useState, useLayoutEffect } from 'react';
import { useLocation } from 'react-router-dom';
import { Sidebar } from './Sidebar';
import { AppHeader } from './MobileHeader';
import { PublicFooter } from './PublicFooter';

interface LayoutProps {
  children: React.ReactNode;
}

export const Layout: React.FC<LayoutProps> = ({ children }) => {
  const [sidebarOpen, setSidebarOpen] = useState(false);
  const [isMobile, setIsMobile] = useState(false);
  const location = useLocation();

  useLayoutEffect(() => {
    const checkMobile = () => {
      const width = window.innerWidth;
      const mobile = width < 1024;
      console.log('Layout - window.innerWidth:', width, 'isMobile:', mobile, 'should show sidebar:', mobile);
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

  const getPageTitle = () => {
    switch (location.pathname) {
      case '/category':
        return 'Категории';
      case '/account':
        return 'Аккаунты';
      case '/expense':
        return 'Расходы';
      case '/income':
        return 'Доходы';
      case '/recurring':
        return 'Повторяющиеся';
      case '/goals':
        return 'Цели';
      case '/profile':
        return 'Профиль';
      default:
        return 'Финансовый учет';
    }
  };

  const handleSidebarToggle = () => {
    setSidebarOpen(!sidebarOpen);
  };

  const handleSidebarClose = () => {
    setSidebarOpen(false);
  };

  console.log('Layout render - isMobile:', isMobile, 'sidebarOpen:', sidebarOpen);
  
  return (
    <div className="min-h-screen theme-bg theme-transition">
      {/* App Header - Shows on both mobile and desktop */}
      <AppHeader
        onMenuClick={handleSidebarToggle}
        title={getPageTitle()}
        isMobile={isMobile}
      />

      <div className="flex min-h-[calc(100vh-4rem)]">
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