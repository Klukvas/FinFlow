import React, { useEffect } from 'react';
import { useLocation } from 'react-router-dom';
import { useTranslation } from 'react-i18next';
import { PublicHeader } from './PublicHeader';
import { PublicFooter } from './PublicFooter';
import { AnimatedBackground } from './AnimatedBackground';

interface PublicLayoutProps {
  children: React.ReactNode;
}

export const PublicLayout: React.FC<PublicLayoutProps> = ({ children }) => {
  const location = useLocation();
  const { t } = useTranslation();

  // Update document title for public pages
  useEffect(() => {
    const getPublicPageTitle = () => {
      switch (location.pathname) {
        case '/about':
          return t('aboutPage.title');
        case '/features':
          return t('featuresPage.title');
        case '/pricing':
          return t('pricingPage.title');
        case '/contact':
          return t('contactPage.title');
        default:
          return t('header.appTitle');
      }
    };

    const pageTitle = getPublicPageTitle();
    document.title = pageTitle;
  }, [location.pathname, t]);

  return (
    <div className="min-h-screen theme-bg theme-transition flex flex-col relative">
      {/* Animated background layers */}
      <AnimatedBackground />
      
      {/* Public Header */}
      <PublicHeader />

      {/* Main Content */}
      <main className="flex-1 relative" style={{ zIndex: 10 }}>
        {children}
      </main>

      {/* Public Footer */}
      <PublicFooter />
    </div>
  );
};
