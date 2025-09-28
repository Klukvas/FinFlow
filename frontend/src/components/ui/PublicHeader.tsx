import React, { useState, useEffect } from 'react';
import { Link, useLocation } from 'react-router-dom';
import { ThemeToggle } from './ThemeToggle';
import { AuthModals } from './AuthModals';
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
  const [mobileMenuOpen, setMobileMenuOpen] = useState(false);
  const { openLoginModal, openRegisterModal } = useModal();

  // Close mobile menu when route changes
  useEffect(() => {
    setMobileMenuOpen(false);
  }, [location.pathname]);

  const navigationItems = [
    { path: '/', icon: FaHome, label: 'Как это работает' },
    { path: '/features', icon: FaFolder, label: 'Что вы получаете' },
    { path: '/pricing', icon: FaDollarSign, label: 'Цены' },
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
            <header className="theme-surface theme-border border-b theme-shadow theme-transition lg:hidden">
        <div className="px-4 py-3">
          <div className="flex items-center justify-between">
            <button
              onClick={toggleMobileMenu}
              className="p-2 rounded-md hover:theme-surface-hover theme-transition"
              aria-label="Открыть меню"
            >
              <FaBars className="w-5 h-5 theme-text-primary" />
            </button>
            
            <h1 className="text-lg font-bold theme-text-primary">Финансовый учет</h1>
            
            <div className="flex items-center space-x-2">
              <ThemeToggle />
              <button
                onClick={openLoginModal}
                className="p-2 theme-text-primary hover:theme-surface-hover rounded-lg theme-transition"
                title="Войти в систему"
              >
                <FaSignInAlt className="w-4 h-4" />
              </button>
            </div>
          </div>
        </div>
      </header>

            {/* Desktop Header */}
            <header className="theme-surface theme-border border-b theme-shadow theme-transition hidden lg:block">
        <div className="px-6 py-4">
          <div className="flex items-center justify-between">
            {/* Logo and Page Title */}
            <div className="flex items-center space-x-6">
              <h1 className="text-2xl font-bold theme-text-primary">Финансовый учет</h1>
              
              {/* Navigation Tabs */}
              <nav className="flex space-x-1">
                {navigationItems.map((item) => {
                  const Icon = item.icon;
                  const isActive = location.pathname === item.path;
                  
                  return (
                    <Link
                      key={item.path}
                      to={item.path}
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
            <div className="flex items-center space-x-4">
              <ThemeToggle />
              
              <button
                onClick={openLoginModal}
                className="flex items-center px-4 py-2 text-sm theme-text-primary hover:theme-surface-hover rounded-lg theme-transition"
                title="Войти в систему"
              >
                <FaSignInAlt className="w-4 h-4 mr-2" />
                Войти
              </button>
              
              <button
                onClick={openRegisterModal}
                className="flex items-center px-4 py-2 text-sm theme-accent-bg theme-text-inverse hover:theme-accent-hover rounded-lg theme-transition"
                title="Зарегистрироваться"
              >
                <FaUserPlus className="w-4 h-4 mr-2" />
                Регистрация
              </button>
            </div>
          </div>
        </div>
      </header>

      {/* Mobile Menu Overlay */}
      {mobileMenuOpen && (
        <div
          className="mobile-overlay"
          onClick={closeMobileMenu}
        />
      )}
      
      {/* Mobile Menu */}
      <div className={`mobile-menu theme-surface theme-shadow ${mobileMenuOpen ? 'open' : ''}`}>
        <div className="flex items-center justify-between p-4 theme-border border-b">
          <h2 className="text-lg font-bold theme-text-primary">Меню</h2>
          <button
            onClick={closeMobileMenu}
            className="p-2 rounded-md hover:theme-surface-hover theme-transition"
          >
            <FaTimes className="w-5 h-5 theme-text-primary" />
          </button>
        </div>
        
        <nav className="p-4 space-y-2">
          {navigationItems.map((item) => {
            const Icon = item.icon;
            const isActive = location.pathname === item.path;
            
            return (
              <Link
                key={item.path}
                to={item.path}
                onClick={closeMobileMenu}
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
        
        <div className="p-4 theme-border border-t space-y-2">
          {/* Theme Toggle */}
          <div className="flex items-center justify-center px-4 py-3">
            <ThemeToggle />
          </div>
          
          <button
            onClick={() => {
              openLoginModal();
              closeMobileMenu();
            }}
            className="w-full flex items-center justify-center px-4 py-3 text-sm theme-text-primary hover:theme-surface-hover rounded-lg theme-transition theme-border border"
          >
            <FaSignInAlt className="w-4 h-4 mr-2" />
            Войти
          </button>
          <button
            onClick={() => {
              openRegisterModal();
              closeMobileMenu();
            }}
            className="w-full flex items-center justify-center px-4 py-3 text-sm theme-accent-bg theme-text-inverse hover:theme-accent-hover rounded-lg theme-transition"
          >
            <FaUserPlus className="w-4 h-4 mr-2" />
            Регистрация
          </button>
        </div>
      </div>

      {/* Auth Modals */}
      <AuthModals />
    </>
  );
};
