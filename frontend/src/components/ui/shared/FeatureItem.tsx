import React from 'react';
import { IconType } from 'react-icons';

interface FeatureItemProps {
  icon: IconType;
  title: string;
  description: string;
}

export const FeatureItem: React.FC<FeatureItemProps> = ({
  icon: Icon,
  title,
  description
}) => {
  return (
    <div className="group rounded-xl border theme-border theme-surface p-5 theme-transition hover:theme-border-hover hover:translate-y-[-2px]">
      <div className="flex items-start gap-4">
        <div className="flex-shrink-0 w-9 h-9 rounded-lg bg-[var(--color-accent)]/10 flex items-center justify-center">
          <Icon className="w-4 h-4 theme-accent" />
        </div>
        <div className="min-w-0">
          <h3 className="text-sm font-semibold theme-text-primary mb-1">
            {title}
          </h3>
          <p className="text-sm theme-text-secondary leading-relaxed">
            {description}
          </p>
        </div>
      </div>
    </div>
  );
};
