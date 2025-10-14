import React from 'react';
import { FaBars } from 'react-icons/fa';
import { ThemeToggle } from '../shared/ThemeToggle';
import { LanguageSelector } from '../shared/LanguageSelector';

interface AppHeaderProps {
  onMenuClick: () => void;
  title: string;
  isMobile: boolean;
}

export const AppHeader: React.FC<AppHeaderProps> = ({ onMenuClick, title, isMobile }) => {
  return (
    <header className={`theme-accent-bg theme-text-inverse theme-shadow theme-transition ${
      isMobile ? 'lg:hidden' : 'hidden lg:block'
    }`} data-testid={isMobile ? "mobile-header" : "desktop-header"}>
      <div className="flex items-center justify-between px-4 py-3">
        <button
          onClick={onMenuClick}
          data-testid={isMobile ? "mobile-menu-toggle" : "sidebar-toggle"}
          className="p-2 rounded-md hover:theme-accent-hover theme-transition"
          aria-label={isMobile ? "Открыть меню" : "Переключить сайдбар"}
        >
          <FaBars className="w-5 h-5" />
        </button>
        
        <h1 className="text-lg font-semibold truncate" data-testid="app-title">{title}</h1>
        
        <div className="flex items-center space-x-2">
          <LanguageSelector />
          <ThemeToggle className="theme-surface theme-text-primary" />
        </div>
      </div>
    </header>
  );
};

// Keep MobileHeader for backward compatibility
export const MobileHeader = AppHeader;
