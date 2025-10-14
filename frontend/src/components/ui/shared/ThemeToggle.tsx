import React from 'react';
import { useTheme } from '@/contexts/ThemeContext';
import { MdLightMode, MdDarkMode, MdSettings } from 'react-icons/md';

interface ThemeToggleProps {
  className?: string;
  showLabel?: boolean;
}

export const ThemeToggle: React.FC<ThemeToggleProps> = ({ 
  className = '', 
  showLabel = false 
}) => {
  const { theme, actualTheme, toggleTheme } = useTheme();

  const getIcon = () => {
    return actualTheme === 'dark' ? 
      <MdDarkMode className="w-5 h-5" /> : 
      <MdLightMode className="w-5 h-5" />;
  };

  const getLabel = () => {
    return actualTheme === 'dark' ? 'Dark' : 'Light';
  };

  const getTooltip = () => {
    return actualTheme === 'dark' 
      ? 'Switch to light theme' 
      : 'Switch to dark mode';
  };

  return (
    <button
      onClick={toggleTheme}
      className={`
        flex items-center gap-2 px-3 py-2 rounded-lg
        theme-surface theme-border border
        hover:theme-surface-hover theme-transition
        focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500
        ${className}
      `}
      title={getTooltip()}
      aria-label={getTooltip()}
    >
      {getIcon()}
      {showLabel && (
        <span className="theme-text-primary text-sm font-medium">
          {getLabel()}
        </span>
      )}
    </button>
  );
};

export default ThemeToggle;
