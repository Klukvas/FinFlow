import React from "react";
import { useTheme, type Theme } from "@/contexts/ThemeContext";
import { Sun, Moon, Monitor } from "lucide-react";

interface ThemeToggleProps {
  className?: string;
  showLabel?: boolean;
  compact?: boolean;
}

const THEME_CYCLE: Theme[] = ["dark", "light", "system"];

const THEME_CONFIG: Record<Theme, { icon: typeof Sun; label: string; tooltip: string }> = {
  dark: { icon: Moon, label: "Dark", tooltip: "Dark theme" },
  light: { icon: Sun, label: "Light", tooltip: "Light theme" },
  system: { icon: Monitor, label: "System", tooltip: "System theme" },
};

export const ThemeToggle: React.FC<ThemeToggleProps> = ({
  className = "",
  showLabel = false,
  compact = false,
}) => {
  const { theme, setTheme } = useTheme();

  const cycleTheme = () => {
    const currentIndex = THEME_CYCLE.indexOf(theme);
    const nextIndex = (currentIndex + 1) % THEME_CYCLE.length;
    setTheme(THEME_CYCLE[nextIndex]);
  };

  const config = THEME_CONFIG[theme];
  const Icon = config.icon;

  return (
    <button
      onClick={cycleTheme}
      className={`
        flex items-center gap-2 rounded-[var(--radius-md)]
        bg-transparent border border-[var(--border)]
        text-[var(--text-secondary)]
        hover:border-[var(--border-hover)] hover:text-[var(--text-primary)] hover:bg-[var(--bg-raised)]
        transition-all duration-150
        ${compact ? "p-2" : "px-3 py-2"}
        ${className}
      `}
      title={config.tooltip}
      aria-label={config.tooltip}
    >
      <Icon className="w-4 h-4" strokeWidth={1.5} />
      {showLabel && (
        <span className="text-sm font-medium">{config.label}</span>
      )}
    </button>
  );
};

export default ThemeToggle;
