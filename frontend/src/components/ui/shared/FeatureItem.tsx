import React from "react";
import { type LucideIcon } from "lucide-react";

interface FeatureItemProps {
  icon: LucideIcon;
  title: string;
  description: string;
}

export const FeatureItem: React.FC<FeatureItemProps> = ({
  icon: Icon,
  title,
  description,
}) => {
  return (
    <div className="group rounded-xl border border-[var(--border)] bg-elevated p-5 transition-colors hover:border-[var(--border-hover)] hover:translate-y-[-2px]">
      <div className="flex items-start gap-4">
        <div className="flex-shrink-0 w-9 h-9 rounded-lg bg-[var(--accent)]/10 flex items-center justify-center">
          <Icon className="w-4 h-4 text-accent-base" />
        </div>
        <div className="min-w-0">
          <h3 className="text-sm font-semibold text-content mb-1">{title}</h3>
          <p className="text-sm text-content-secondary leading-relaxed">
            {description}
          </p>
        </div>
      </div>
    </div>
  );
};
