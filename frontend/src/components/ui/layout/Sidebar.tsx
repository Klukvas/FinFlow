import React, { useState, useEffect } from 'react';
import { useTranslation } from 'react-i18next';
import { Link, useLocation } from 'react-router-dom';
import { useAuth } from '@/contexts/AuthContext';
import {
  FaHome,
  FaFolder,
  FaSignOutAlt,
  FaTimes,
  FaUser,
  FaDollarSign,
  FaRedo,
  FaBullseye,
  FaFilePdf,
  FaWallet
} from 'react-icons/fa';

interface SidebarProps {
  isOpen: boolean;
  onClose: () => void;
}

export const Sidebar: React.FC<SidebarProps> = ({ isOpen, onClose }) => {
  const { logout, user, isLoading } = useAuth();
  const location = useLocation();
  const [isMobile, setIsMobile] = useState(false);
  const { t } = useTranslation();

  useEffect(() => {
    const checkMobile = () => {
      const mobile = window.innerWidth < 1024;
      setIsMobile(mobile);
    };
    
    checkMobile();
    window.addEventListener('resize', checkMobile);
    return () => window.removeEventListener('resize', checkMobile);
  }, []);

  const handleLogout = () => {
    logout();
    onClose();
  };

  const navigationItems = [
    { path: '/category', icon: FaFolder, label: t('navigation.categories') },
    { path: '/account', icon: FaWallet, label: t('navigation.accounts') },
    { path: '/expense', icon: FaHome, label: t('navigation.expenses') },
    { path: '/income', icon: FaDollarSign, label: t('navigation.income') },
    { path: '/debts', icon: FaDollarSign, label: t('navigation.debts') },
    { path: '/recurring', icon: FaRedo, label: t('navigation.recurring') },
    { path: '/goals', icon: FaBullseye, label: t('navigation.goals') },
    { path: '/pdf-parser', icon: FaFilePdf, label: t('navigation.pdfParser') },
  ];

  const sidebarContent = (
    <div data-testid="sidebar" className="flex flex-col h-full theme-surface theme-shadow theme-transition">
      {/* Header */}
      <div className="flex items-center justify-between p-4 theme-border border-b">
        <h1 className="text-lg font-bold theme-text-primary">{t('header.appTitle')}</h1>
        {isMobile && (
          <button
            onClick={onClose}
            className="p-2 rounded-md hover:theme-surface-hover theme-transition"
          >
            <FaTimes className="w-5 h-5 theme-text-primary" />
          </button>
        )}
      </div>

      {/* Navigation */}
      <nav className="flex-1 px-4 py-6 space-y-2">
        {navigationItems.map((item) => {
          const Icon = item.icon;
          const isActive = location.pathname === item.path;
          
          return (
            <Link
              key={item.path}
              to={item.path}
              data-testid={`sidebar-${item.path.split('/')[1]}-link`}
              onClick={isMobile ? onClose : undefined}
              className={`flex items-center px-4 py-3 rounded-lg theme-transition ${
                isActive
                  ? 'theme-accent-light theme-accent font-medium'
                  : 'theme-text-secondary hover:theme-surface-hover hover:theme-text-primary'
              }`}
            >
              <Icon className="w-5 h-5 mr-3" />
              <span className="text-sm">{item.label}</span>
            </Link>
          );
        })}
      </nav>

      {/* User Section */}
      <div className="p-4 theme-border border-t" data-testid="user-profile-button-sidebar">
        <Link
          data-testid="sidebar-profile-link"
          to="/profile"
          onClick={isMobile ? onClose : undefined}
          className="flex items-center mb-4 hover:theme-surface-hover rounded-lg p-2 -m-2 theme-transition group cursor-pointer"
          title="Перейти к профилю"
        >
          <div className="w-8 h-8 theme-accent-light rounded-full flex items-center justify-center group-hover:theme-accent-hover theme-transition">
            <FaUser className="w-4 h-4 theme-accent" />
          </div>
          <div className="ml-3">
            <p className="text-sm font-medium theme-text-primary group-hover:theme-text-secondary" data-testid="user-name">
              {isLoading ? t('common.loading') : user?.username || t('header.user')}
            </p>
            <p className="text-xs theme-text-tertiary" data-testid="user-email">
              {user?.email || t('navigation.profile')}
            </p>
          </div>
        </Link>
        
        <button
          data-testid="logout-button"
          onClick={handleLogout}
          className="w-full flex items-center px-4 py-2 text-sm theme-error hover:theme-error-light rounded-lg theme-transition"
        >
          <FaSignOutAlt className="w-4 h-4 mr-3" />
          {t('navigation.logout')}
        </button>
      </div>
    </div>
  );

  if (isMobile) {
    return (
      <>
        {/* Mobile Overlay */}
        {isOpen && (
          <div
            className="fixed inset-0 bg-black/50 bg-opacity-50 z-40"
            onClick={onClose}
          />
        )}
        
        {/* Mobile Sidebar */}
        <div
          className={`fixed top-0 left-0 h-full w-64 z-50 transform transition-transform duration-300 ease-in-out ${
            isOpen ? 'translate-x-0' : '-translate-x-full'
          }`}
        >
          {sidebarContent}
        </div>
      </>
    );
  }

  // Desktop Sidebar - Collapsible
  return (
    <div className={`theme-surface theme-shadow theme-border border-r theme-transition transition-all duration-300 ${
      isOpen ? 'w-64' : 'w-0 overflow-hidden'
    }`}>
      {isOpen && sidebarContent}
    </div>
  );
};
