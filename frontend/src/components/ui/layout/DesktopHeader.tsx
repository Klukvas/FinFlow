import React, { useMemo, useCallback } from 'react';
import { Link, useLocation } from 'react-router-dom';
import { useTranslation } from 'react-i18next';
import { useAuth } from '@/contexts/AuthContext';
import { ThemeToggle } from '../shared/ThemeToggle';
import { LanguageSelector } from '../shared/LanguageSelector';
import {
  FaHome,
  FaFolder,
  FaSignOutAlt,
  FaUser,
  FaDollarSign,
  FaRedo
} from 'react-icons/fa';

export const DesktopHeader = React.memo(() => {
  const { logout, user, isLoading } = useAuth();
  const { t } = useTranslation();
  const location = useLocation();

  const handleLogout = useCallback(() => {
    logout();
  }, [logout]);

  const navigationItems = useMemo(() => [
    { path: '/category', icon: FaFolder, label: t('navigation.categories') },
    { path: '/expense', icon: FaHome, label: t('navigation.expenses') },
    { path: '/income', icon: FaDollarSign, label: t('navigation.income') },
    { path: '/recurring', icon: FaRedo, label: t('navigation.recurring') },
  ], [t]);


  return (
    <header className="theme-surface theme-border border-b theme-shadow theme-transition" data-testid="desktop-header">
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
                    data-testid={`sidebar-${item.path.split('/')[1]}-link`}
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

          {/* User Menu and Theme Toggle */}
          <div className="flex items-center space-x-4" data-testid="header-actions">
            <ThemeToggle />
            <LanguageSelector />
            
            <Link
              to="/profile"
              data-testid="user-profile-button"
              className="flex items-center space-x-2 hover:theme-surface-hover rounded-lg px-3 py-2 theme-transition group cursor-pointer"
              title={t('header.goToProfile')}
            >
              <div className="w-8 h-8 theme-accent-light rounded-full flex items-center justify-center group-hover:theme-accent-hover theme-transition">
                <FaUser className="w-4 h-4 theme-accent" />
              </div>
              <span className="text-sm font-medium theme-text-secondary group-hover:theme-text-primary">
                {isLoading ? t('common.loading') : user?.username || t('header.user')}
              </span>
            </Link>
            
            <button
              onClick={handleLogout}
              data-testid="logout-button"
              className="flex items-center px-3 py-2 text-sm theme-error hover:theme-error-light rounded-lg theme-transition"
              title={t('navigation.logout')}
            >
              <FaSignOutAlt className="w-4 h-4 mr-2" />
              {t('navigation.logout')}
            </button>
          </div>
        </div>
      </div>
    </header>
  );
});

DesktopHeader.displayName = 'DesktopHeader';
