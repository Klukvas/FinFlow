import React from 'react';
import { FaBars } from 'react-icons/fa';
import { ThemeToggle } from '../shared/ThemeToggle';
import { LanguageSelector } from '../shared/LanguageSelector';
import { WorkspaceSelector } from '../workspace/WorkspaceSelector';

interface AppHeaderProps {
 onMenuClick: () => void;
 title: string;
 isMobile: boolean;
}

export const AppHeader: React.FC<AppHeaderProps> = ({ onMenuClick, title, isMobile }) => {
 return (
 <header className={`bg-elevated text-content border-[var(--color-border)] border-b transition-colors ${
 isMobile ? 'lg:hidden' : 'hidden lg:block'
 }`} data-testid={isMobile ? "mobile-header" : "desktop-header"}>
 <div className="flex items-center justify-between px-4 py-3">
 {/* Mobile: show burger menu, Desktop: just spacing */}
 {isMobile ? (
 <button
 onClick={onMenuClick}
 data-testid="mobile-menu-toggle"
 className="p-2 rounded-md hover:bg-surface-alt transition-colors"
 aria-label="Открыть меню"
 >
 <FaBars className="w-5 h-5 text-content" />
 </button>
 ) : (
 <div className="w-9" /> // Spacer for alignment
 )}
 
 <h1 className="text-lg font-semibold truncate flex-1 text-center" data-testid="app-title">{title}</h1>
 
 <div className="flex items-center space-x-1">
 {/* Desktop: show workspace selector, Mobile: hide (it's in sidebar) */}
 {!isMobile && <WorkspaceSelector compact />}
 <LanguageSelector compact={isMobile} />
 <ThemeToggle compact={isMobile} />
 </div>
 </div>
 </header>
 );
};

// Keep MobileHeader for backward compatibility
export const MobileHeader = AppHeader;
