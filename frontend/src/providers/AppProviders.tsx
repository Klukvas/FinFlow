import React from 'react';
import { BrowserRouter as Router } from 'react-router-dom';
import { HelmetProvider } from 'react-helmet-async';
import { ErrorBoundary } from '@/components/ErrorBoundary';
import { AuthProvider } from '@/contexts/AuthContext';
import { CategoriesProvider } from '@/contexts/CategoriesContext';
import { ThemeProvider } from '@/contexts/ThemeContext';
import { ModalProvider } from '@/contexts/ModalContext';
import { CurrencyProvider } from '@/contexts/CurrencyContext';
import { WorkspaceProvider } from '@/contexts/WorkspaceContext';
import { TutorialProvider } from '@/contexts/TutorialContext';
import { AppRoutes } from '@/components/AppRoutes';
import { TutorialOverlay } from '@/components/ui/tutorial';
import '@/i18n';

interface AppProvidersProps {
  children?: React.ReactNode;
}

export const AppProviders: React.FC<AppProvidersProps> = ({ children }) => {
  return (
    <ErrorBoundary>
      <HelmetProvider>
        <ThemeProvider>
          <ModalProvider>
            <AuthProvider>
              <WorkspaceProvider>
                <CategoriesProvider>
                  <CurrencyProvider>
                    <TutorialProvider>
                      <Router>
                        {children || <AppRoutes />}
                        <TutorialOverlay />
                      </Router>
                    </TutorialProvider>
                  </CurrencyProvider>
                </CategoriesProvider>
              </WorkspaceProvider>
            </AuthProvider>
          </ModalProvider>
        </ThemeProvider>
      </HelmetProvider>
    </ErrorBoundary>
  );
};
