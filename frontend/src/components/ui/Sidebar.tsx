import React, { useState, useEffect } from 'react';
import { Link, useLocation } from 'react-router-dom';
import { useAuth } from '@/contexts/AuthContext';
import {
  FaHome,
  FaChartBar,
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

  useEffect(() => {
    const checkMobile = () => {
      const mobile = window.innerWidth < 1024;
      console.log('Sidebar - window.innerWidth:', window.innerWidth, 'isMobile:', mobile);
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
    { path: '/category', icon: FaFolder, label: 'Категории' },
    { path: '/account', icon: FaWallet, label: 'Аккаунты' },
    { path: '/expense', icon: FaHome, label: 'Расходы' },
    { path: '/income', icon: FaDollarSign, label: 'Доходы' },
    { path: '/debts', icon: FaDollarSign, label: 'Долги' },
    { path: '/recurring', icon: FaRedo, label: 'Повторяющиеся' },
    { path: '/goals', icon: FaBullseye, label: 'Цели' },
    { path: '/pdf-parser', icon: FaFilePdf, label: 'PDF Парсер' },
  ];

  const sidebarContent = (
    <div className="flex flex-col h-full theme-surface theme-shadow theme-transition">
      {/* Header */}
      <div className="flex items-center justify-between p-4 theme-border border-b">
        <h1 className="text-lg font-bold theme-text-primary">Финансовый учет</h1>
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
      <div className="p-4 theme-border border-t">
        <Link
          to="/profile"
          onClick={isMobile ? onClose : undefined}
          className="flex items-center mb-4 hover:theme-surface-hover rounded-lg p-2 -m-2 theme-transition group cursor-pointer"
          title="Перейти к профилю"
        >
          <div className="w-8 h-8 theme-accent-light rounded-full flex items-center justify-center group-hover:theme-accent-hover theme-transition">
            <FaUser className="w-4 h-4 theme-accent" />
          </div>
          <div className="ml-3">
            <p className="text-sm font-medium theme-text-primary group-hover:theme-text-secondary">
              {isLoading ? 'Загрузка...' : user?.username || 'Пользователь'}
            </p>
            <p className="text-xs theme-text-tertiary">
              {user?.email || 'Аккаунт'}
            </p>
          </div>
        </Link>
        
        <button
          onClick={handleLogout}
          className="w-full flex items-center px-4 py-2 text-sm theme-error hover:theme-error-light rounded-lg theme-transition"
        >
          <FaSignOutAlt className="w-4 h-4 mr-3" />
          Выйти
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
