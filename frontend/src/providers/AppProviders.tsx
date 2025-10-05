import React from 'react';
import { BrowserRouter as Router } from 'react-router-dom';
import { ErrorBoundary } from '@/components/ErrorBoundary';
import { AuthProvider } from '@/contexts/AuthContext';
import { ThemeProvider } from '@/contexts/ThemeContext';
import { ModalProvider } from '@/contexts/ModalContext';
import { CurrencyProvider } from '@/contexts/CurrencyContext';
import { AppRoutes } from '@/components/AppRoutes';
import '@/i18n';

interface AppProvidersProps {
  children?: React.ReactNode;
}

export const AppProviders: React.FC<AppProvidersProps> = ({ children }) => {
  return (
    <ErrorBoundary>
      <ThemeProvider>
        <ModalProvider>
          <AuthProvider>
            <CurrencyProvider>
              <Router>
                {children || <AppRoutes />}
              </Router>
            </CurrencyProvider>
          </AuthProvider>
        </ModalProvider>
      </ThemeProvider>
    </ErrorBoundary>
  );
};
