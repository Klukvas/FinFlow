import React from 'react';
import { BrowserRouter as Router } from 'react-router-dom';
import { ErrorBoundary } from './components/ErrorBoundary';
import { AuthProvider } from './contexts/AuthContext';
import { ThemeProvider } from './contexts/ThemeContext';
import { ModalProvider } from './contexts/ModalContext';
import { CurrencyProvider } from './contexts/CurrencyContext';
import { AppRoutes } from './components/AppRoutes';

function App() {
  return (
    <ErrorBoundary>
      <ThemeProvider>
        <ModalProvider>
          <AuthProvider>
            <CurrencyProvider>
              <Router>
                <AppRoutes />
              </Router>
            </CurrencyProvider>
          </AuthProvider>
        </ModalProvider>
      </ThemeProvider>
    </ErrorBoundary>
  );
}

export default App;