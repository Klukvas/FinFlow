import React from 'react';
import { Link, useLocation } from 'react-router-dom';
import { useAuth } from '@/contexts/AuthContext';
import { ThemeToggle } from './ThemeToggle';
import {
  FaHome,
  FaChartBar,
  FaFolder,
  FaSignOutAlt,
  FaUser,
  FaDollarSign,
  FaRedo
} from 'react-icons/fa';

export const DesktopHeader: React.FC = () => {
  const { logout, user, isLoading } = useAuth();
  const location = useLocation();

  const handleLogout = () => {
    logout();
  };

  const navigationItems = [
    { path: '/category', icon: FaFolder, label: 'Категории' },
    { path: '/expense', icon: FaHome, label: 'Расходы' },
    { path: '/income', icon: FaDollarSign, label: 'Доходы' },
    { path: '/recurring', icon: FaRedo, label: 'Повторяющиеся' },
  ];


  return (
    <header className="theme-surface theme-border border-b theme-shadow theme-transition">
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

          {/* User Menu and Theme Toggle */}
          <div className="flex items-center space-x-4">
            <ThemeToggle />
            
            <Link
              to="/profile"
              className="flex items-center space-x-2 hover:theme-surface-hover rounded-lg px-3 py-2 theme-transition group cursor-pointer"
              title="Перейти к профилю"
            >
              <div className="w-8 h-8 theme-accent-light rounded-full flex items-center justify-center group-hover:theme-accent-hover theme-transition">
                <FaUser className="w-4 h-4 theme-accent" />
              </div>
              <span className="text-sm font-medium theme-text-secondary group-hover:theme-text-primary">
                {isLoading ? 'Загрузка...' : user?.username || 'Пользователь'}
              </span>
            </Link>
            
            <button
              onClick={handleLogout}
              className="flex items-center px-3 py-2 text-sm theme-error hover:theme-error-light rounded-lg theme-transition"
              title="Выйти"
            >
              <FaSignOutAlt className="w-4 h-4 mr-2" />
              Выйти
            </button>
          </div>
        </div>
      </div>
    </header>
  );
};
