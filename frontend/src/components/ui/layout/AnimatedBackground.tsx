import React from 'react';
import { useTheme } from '@/contexts/ThemeContext';

/**
 * AnimatedBackground - Subtle ambient glow using accent color.
 * Matches the bg-glow pattern from the design system.
 */
export const AnimatedBackground: React.FC = () => {
  const { actualTheme } = useTheme();

  const gradient = actualTheme === 'dark'
    ? 'radial-gradient(ellipse 80% 50% at 50% 0%, rgba(34, 217, 160, 0.04) 0%, transparent 60%)'
    : 'radial-gradient(ellipse 80% 50% at 50% 0%, rgba(14, 191, 138, 0.03) 0%, transparent 60%)';

  return (
    <div
      className="fixed inset-0 pointer-events-none"
      style={{ zIndex: 1 }}
      aria-hidden="true"
    >
      <div className="absolute inset-0" style={{ background: gradient }} />
    </div>
  );
};

export default AnimatedBackground;
