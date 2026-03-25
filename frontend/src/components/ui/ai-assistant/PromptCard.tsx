import React from "react";
import { useTranslation } from "react-i18next";
import {
  ArrowDown,
  PiggyBank,
  AlertTriangle,
  Target,
  Zap,
  ListOrdered,
  ArrowUpCircle,
  Shield,
  Map,
} from "lucide-react";

const ICON_MAP: Record<string, React.ComponentType<{ className?: string }>> = {
  TrendingDown: ArrowDown,
  PiggyBank: PiggyBank,
  AlertTriangle: AlertTriangle,
  Target: Target,
  Zap: Zap,
  ListOrdered: ListOrdered,
  ArrowUpCircle: ArrowUpCircle,
  Shield: Shield,
  Map: Map,
};

interface PromptCardProps {
  titleKey: string;
  descriptionKey: string;
  icon: string;
  isLoading: boolean;
  isActive: boolean;
  onClick: () => void;
}

export const PromptCard: React.FC<PromptCardProps> = ({
  titleKey,
  descriptionKey,
  icon,
  isLoading,
  isActive,
  onClick,
}) => {
  const { t } = useTranslation();
  const IconComponent = ICON_MAP[icon] || Target;

  return (
    <button
      onClick={onClick}
      disabled={isLoading}
      aria-pressed={isActive}
      aria-busy={isLoading}
      className={`w-full text-left p-4 rounded-lg border-[var(--border)] border transition-colors
 ${isActive ? "bg-[var(--accent-dim)] ring-2 ring-[var(--accent)]" : "hover:bg-surface-alt"}
 ${isLoading ? "opacity-60 cursor-wait" : "cursor-pointer"}
 `}
    >
      <div className="flex items-start gap-3">
        <div className="flex-shrink-0 w-10 h-10 rounded-lg bg-[var(--accent-dim)] flex items-center justify-center">
          <IconComponent className="w-5 h-5 text-accent-base" />
        </div>
        <div className="min-w-0">
          <h3 className="text-sm font-medium text-content">{t(titleKey)}</h3>
          <p className="text-xs text-content-secondary mt-1">
            {t(descriptionKey)}
          </p>
        </div>
      </div>
    </button>
  );
};
