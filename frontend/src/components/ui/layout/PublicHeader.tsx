import React, { useState, useEffect } from 'react';
import { Link, useLocation } from 'react-router-dom';
import { useTranslation } from 'react-i18next';
import { ThemeToggle } from '../shared/ThemeToggle';
import { LanguageSelector } from '../shared/LanguageSelector';
import { AuthModals } from '../auth/AuthModals';
import { useModal } from '@/contexts/ModalContext';
import {
  FaHome,
  FaFolder,
  FaDollarSign,
  FaSignInAlt,
  FaUserPlus,
  FaBars,
  FaTimes
} from 'react-icons/fa';

export const PublicHeader: React.FC = () => {
  const location = useLocation();
  const { t } = useTranslation();
  const [mobileMenuOpen, setMobileMenuOpen] = useState(false);
  const { openLoginModal, openRegisterModal } = useModal();

  // Close mobile menu when route changes
  useEffect(() => {
    setMobileMenuOpen(false);
  }, [location.pathname]);

  const navigationItems = [
    { path: '/', icon: FaHome, label: t('publicNav.howItWorks') },
    { path: '/features', icon: FaFolder, label: t('publicNav.features') },
    { path: '/pricing', icon: FaDollarSign, label: t('publicNav.pricing') },
  ];

  const toggleMobileMenu = () => {
    setMobileMenuOpen(!mobileMenuOpen);
  };

  const closeMobileMenu = () => {
    setMobileMenuOpen(false);
  };

  return (
    <>
            {/* Mobile Header */}
            <header className="theme-surface theme-border border-b theme-shadow theme-transition lg:hidden" data-testid="mobile-header">
        <div className="px-4 py-3">
          <div className="flex items-center justify-between">
            <button
              onClick={toggleMobileMenu}
              data-testid="mobile-menu-toggle"
              className="p-2 rounded-md hover:theme-surface-hover theme-transition"
              aria-label={t('common.openMenu')}
            >
              <FaBars className="w-5 h-5 theme-text-primary" />
            </button>
            
            <h1 className="text-lg font-bold theme-text-primary" data-testid="app-title">{t('header.appTitle')}</h1>
            
            <div className="flex items-center space-x-2">
              <LanguageSelector />
              <ThemeToggle />
              <button
                onClick={openLoginModal}
                data-testid="login-modal-trigger-mobile"
                className="p-2 theme-text-primary hover:theme-surface-hover rounded-lg theme-transition"
                title={t('navigation.login')}
              >
                <FaSignInAlt className="w-4 h-4" />
              </button>
            </div>
          </div>
        </div>
      </header>

            {/* Desktop Header */}
            <header className="theme-surface theme-border border-b theme-shadow theme-transition hidden lg:block" data-testid="desktop-header">
        <div className="px-6 py-4">
          <div className="flex items-center justify-between">
            {/* Logo and Page Title */}
            <div className="flex items-center space-x-6">
              <h1 className="text-2xl font-bold theme-text-primary" data-testid="app-title">{t('header.appTitle')}</h1>
              
              {/* Navigation Tabs */}
              <nav className="flex space-x-1" data-testid="desktop-navigation">
                {navigationItems.map((item) => {
                  const Icon = item.icon;
                  const isActive = location.pathname === item.path;
                  
                  return (
                    <Link
                      key={item.path}
                      to={item.path}
                      data-testid={`header-${item.path.split('/')[1]}-link`}
                      className={`flex items-center px-4 py-2 rounded-lg text-sm font-medium theme-transition ${
                        isActive
                          ? 'theme-accent-light theme-accent'
                          : 'theme-text-secondary hover:theme-surface-hover hover:theme-text-primary'
                      }`}
                    >
                      <Icon className="w-4 h-4 mr-2" />
                      {item.label}
                    </Link>
                  );
                })}
              </nav>
            </div>

            {/* Auth Buttons and Theme Toggle */}
            <div className="flex items-center space-x-4" data-testid="header-actions">
              <LanguageSelector />
              <ThemeToggle />
              
              <button
                onClick={openLoginModal}
                data-testid="login-modal-trigger"
                className="flex items-center px-4 py-2 text-sm theme-text-primary hover:theme-surface-hover rounded-lg theme-transition"
                title={t('navigation.login')}
              >
                <FaSignInAlt className="w-4 h-4 mr-2" />
                {t('navigation.login')}
              </button>
              
              <button
                onClick={openRegisterModal}
                data-testid="register-modal-trigger"
                className="flex items-center px-4 py-2 text-sm theme-accent-bg theme-text-inverse hover:theme-accent-hover rounded-lg theme-transition"
                title={t('navigation.register')}
              >
                <FaUserPlus className="w-4 h-4 mr-2" />
                {t('navigation.register')}
              </button>
            </div>
          </div>
        </div>
      </header>

      {/* Mobile Menu Overlay */}
      {mobileMenuOpen && (
        <div
          className="mobile-overlay"
          data-testid="mobile-menu-overlay"
          onClick={closeMobileMenu}
        />
      )}
      
      {/* Mobile Menu */}
      <div className={`mobile-menu theme-surface theme-shadow ${mobileMenuOpen ? 'open' : ''}`} data-testid="mobile-menu">
        <div className="flex items-center justify-between p-4 theme-border border-b">
          <h2 className="text-lg font-bold theme-text-primary">{t('common.menu')}</h2>
          <button
            onClick={closeMobileMenu}
            data-testid="mobile-menu-close"
            className="p-2 rounded-md hover:theme-surface-hover theme-transition"
          >
            <FaTimes className="w-5 h-5 theme-text-primary" />
          </button>
        </div>
        
        <nav className="p-4 space-y-2" data-testid="mobile-navigation">
          {navigationItems.map((item) => {
            const Icon = item.icon;
            const isActive = location.pathname === item.path;
            
            return (
              <Link
                key={item.path}
                to={item.path}
                onClick={closeMobileMenu}
                data-testid={`mobile-${item.path.split('/')[1]}-link`}
                className={`flex items-center px-4 py-3 rounded-lg theme-transition ${
                  isActive
                    ? 'theme-accent-light theme-accent font-medium'
                    : 'theme-text-secondary hover:theme-surface-hover hover:theme-text-primary'
                }`}
              >
                <Icon className="w-5 h-5 mr-3" />
                {item.label}
              </Link>
            );
          })}
        </nav>
        
        <div className="p-4 theme-border border-t space-y-2" data-testid="mobile-auth-section">
          {/* Language Selector and Theme Toggle */}
          <div className="flex items-center justify-center space-x-4 px-4 py-3">
            <LanguageSelector />
            <ThemeToggle />
          </div>
          
          <button
            onClick={() => {
              openLoginModal();
              closeMobileMenu();
            }}
            data-testid="mobile-login-button"
            className="w-full flex items-center justify-center px-4 py-3 text-sm theme-text-primary hover:theme-surface-hover rounded-lg theme-transition theme-border border"
          >
            <FaSignInAlt className="w-4 h-4 mr-2" />
            {t('navigation.login')}
          </button>
          <button
            onClick={() => {
              openRegisterModal();
              closeMobileMenu();
            }}
            data-testid="mobile-register-button"
            className="w-full flex items-center justify-center px-4 py-3 text-sm theme-accent-bg theme-text-inverse hover:theme-accent-hover rounded-lg theme-transition"
          >
            <FaUserPlus className="w-4 h-4 mr-2" />
            {t('navigation.register')}
          </button>
        </div>
      </div>

      {/* Auth Modals */}
      <AuthModals />
    </>
  );
};
