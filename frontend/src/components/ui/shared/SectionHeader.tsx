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
}) => (
  <div className={`mb-12 ${className}`}>
    {label && (
      <span className="inline-block font-mono text-[11px] font-medium uppercase tracking-[0.12em] text-[var(--accent)] mb-3">
        {label}
      </span>
    )}
    <h2 className="text-2xl sm:text-[32px] font-bold tracking-[-0.03em] text-[var(--text-primary)] mb-2">
      {title}
    </h2>
    {description && (
      <p className="text-base text-[var(--text-secondary)] max-w-[540px] leading-relaxed">
        {description}
      </p>
    )}
  </div>
);
