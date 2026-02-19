import React from 'react';

interface SectionHeaderProps {
  label?: string;
  title: string;
  description?: string;
  className?: string;
}

export const SectionHeader: React.FC<SectionHeaderProps> = ({
  label,
  title,
  description,
  className = ''
}) => {
  return (
    <div className={`mb-12 ${className}`}>
      {label && (
        <span className="inline-block text-xs font-semibold uppercase tracking-widest theme-accent mb-3">
          {label}
        </span>
      )}
      <h2 className="text-2xl sm:text-3xl font-bold theme-text-primary mb-3">
        {title}
      </h2>
      {description && (
        <p className="text-base theme-text-secondary max-w-2xl leading-relaxed">
          {description}
        </p>
      )}
    </div>
  );
};
