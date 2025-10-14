import React from 'react';
import { PublicHeader } from './PublicHeader';
import { PublicFooter } from './PublicFooter';
import { AnimatedBackground } from './AnimatedBackground';

interface PublicLayoutProps {
  children: React.ReactNode;
}

export const PublicLayout: React.FC<PublicLayoutProps> = ({ children }) => {
  return (
    <div className="min-h-screen theme-bg theme-transition flex flex-col relative">
      {/* Animated background layers */}
      <AnimatedBackground />
      
      {/* Public Header */}
      <PublicHeader />

      {/* Main Content */}
      <main className="flex-1 relative" style={{ zIndex: 10 }}>
        {children}
      </main>

      {/* Public Footer */}
      <PublicFooter />
    </div>
  );
};
