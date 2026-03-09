import React from 'react';
import { useTheme } from '@/contexts/ThemeContext';

/**
 * AnimatedBackground - Minimal ambient background
 * Only a very subtle radial gradient, no animations or particles.
 */
export const AnimatedBackground: React.FC = () => {
 const { actualTheme } = useTheme();

 return (
 <div
 className="fixed inset-0 pointer-events-none"
 style={{ zIndex: 1 }}
 aria-hidden="true"
 >
 {actualTheme === 'dark' && (
 <div
 className="absolute inset-0"
 style={{
 background:
 'radial-gradient(ellipse 80% 50% at 50% 0%, rgba(59, 130, 246, 0.04) 0%, transparent 60%)',
 }}
 />
 )}
 {actualTheme === 'light' && (
 <div
 className="absolute inset-0"
 style={{
 background:
 'radial-gradient(ellipse 80% 50% at 50% 0%, rgba(59, 130, 246, 0.02) 0%, transparent 60%)',
 }}
 />
 )}
 </div>
 );
};

export default AnimatedBackground;
