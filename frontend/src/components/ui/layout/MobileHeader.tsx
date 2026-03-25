import React from "react";
import { Menu } from "lucide-react";
import { ThemeToggle } from "../shared/ThemeToggle";
import { LanguageSelector } from "../shared/LanguageSelector";
import { WorkspaceSelector } from "../workspace/WorkspaceSelector";

interface AppHeaderProps {
  onMenuClick: () => void;
  title: string;
  isMobile: boolean;
}

export const AppHeader: React.FC<AppHeaderProps> = ({
  onMenuClick,
  title,
  isMobile,
}) => (
  <header
    className="sticky top-0 z-[var(--z-header)] h-[var(--header-height)] bg-[var(--bg-base)] border-b border-[var(--border)] flex items-center px-4 gap-3 flex-shrink-0"
    data-testid={isMobile ? "mobile-header" : "desktop-header"}
  >
    {/* Mobile: burger, Desktop: spacer */}
    {isMobile ? (
      <button
        onClick={onMenuClick}
        data-testid="mobile-menu-toggle"
        className="w-9 h-9 flex items-center justify-center rounded-[var(--radius-md)] text-[var(--text-secondary)] hover:bg-[var(--bg-raised)] hover:text-[var(--text-primary)] transition-colors touch-manipulation"
        aria-label="Toggle menu"
      >
        <Menu className="w-[18px] h-[18px]" strokeWidth={1.5} />
      </button>
    ) : (
      <div className="w-9" />
    )}

    {/* Title */}
    <h1
      className="text-[15px] font-semibold tracking-[-0.01em] text-[var(--text-primary)] truncate flex-1 text-center"
      data-testid="app-title"
    >
      {title}
    </h1>

    {/* Right actions */}
    <div className="flex items-center gap-1">
      {!isMobile && (
        <>
          <WorkspaceSelector compact />
          <div className="w-px h-5 bg-[var(--border)] flex-shrink-0 mx-1" />
        </>
      )}
      <LanguageSelector compact={isMobile} />
      <ThemeToggle compact={isMobile} />
    </div>
  </header>
);

// Backward compat
export const MobileHeader = AppHeader;
