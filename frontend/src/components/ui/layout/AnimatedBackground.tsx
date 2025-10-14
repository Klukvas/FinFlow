import React from 'react';
import { useTheme } from '@/contexts/ThemeContext';

/**
 * AnimatedBackground - Provides layered animated background effects
 * Includes light trails and particle effects that adapt to the current theme
 */
export const AnimatedBackground: React.FC = () => {
  const { actualTheme } = useTheme();

  return (
    <div 
      className="fixed inset-0 pointer-events-none overflow-hidden"
      style={{ zIndex: 1 }}
      aria-hidden="true"
    >
      {/* Light trails - iridescent motion streaks */}
      <div className="absolute inset-0">
        {/* Trail 1 */}
        <div 
          className="light-trail"
          style={{
            top: '20%',
            left: 0,
            width: '100%',
            height: '2px'
          }}
        />
        
        {/* Trail 2 */}
        <div 
          className="light-trail"
          style={{
            top: '50%',
            left: 0,
            width: '100%',
            height: '2px'
          }}
        />
        
        {/* Trail 3 */}
        <div 
          className="light-trail"
          style={{
            top: '75%',
            left: 0,
            width: '100%',
            height: '2px'
          }}
        />
      </div>

      {/* Gradient glow overlay for depth */}
      {actualTheme === 'dark' && (
        <div className="absolute inset-0">
          <div 
            className="absolute top-0 left-1/4 w-96 h-96 rounded-full opacity-10 blur-3xl animate-float"
            style={{ 
              background: 'radial-gradient(circle, var(--color-gold) 0%, transparent 70%)',
              animationDelay: '0s',
              animationDuration: '20s'
            }}
          />
          <div 
            className="absolute bottom-1/4 right-1/4 w-96 h-96 rounded-full opacity-10 blur-3xl animate-float"
            style={{ 
              background: 'radial-gradient(circle, var(--color-accent) 0%, transparent 70%)',
              animationDelay: '5s',
              animationDuration: '25s'
            }}
          />
        </div>
      )}

      {actualTheme === 'light' && (
        <div className="absolute inset-0">
          {/* Golden sunbeam effects */}
          <div 
            className="absolute top-1/4 right-1/4 w-[500px] h-[500px] rounded-full blur-3xl animate-float"
            style={{ 
              background: 'radial-gradient(circle, rgba(203, 164, 92, 0.15) 0%, transparent 70%)',
              opacity: 0.8,
              animationDelay: '0s',
              animationDuration: '18s'
            }}
          />
          <div 
            className="absolute bottom-1/3 left-1/3 w-[400px] h-[400px] rounded-full blur-3xl animate-float"
            style={{ 
              background: 'radial-gradient(circle, rgba(92, 172, 250, 0.12) 0%, transparent 70%)',
              opacity: 0.7,
              animationDelay: '4s',
              animationDuration: '22s'
            }}
          />
          <div 
            className="absolute top-1/2 left-1/2 w-[300px] h-[300px] rounded-full blur-3xl animate-float"
            style={{ 
              background: 'radial-gradient(circle, rgba(174, 125, 251, 0.1) 0%, transparent 70%)',
              opacity: 0.6,
              animationDelay: '8s',
              animationDuration: '20s'
            }}
          />
          
          {/* Soft light rays */}
          <div 
            className="absolute inset-0 overflow-hidden"
            style={{ 
              background: `
                linear-gradient(45deg, transparent 30%, rgba(255, 248, 231, 0.05) 50%, transparent 70%),
                linear-gradient(-45deg, transparent 30%, rgba(203, 164, 92, 0.03) 50%, transparent 70%)
              `,
              animation: 'lightRays 30s linear infinite'
            }}
          />
        </div>
      )}
    </div>
  );
};

export default AnimatedBackground;

