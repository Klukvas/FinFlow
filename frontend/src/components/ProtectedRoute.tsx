import React from 'react';
import { Navigate } from 'react-router-dom';
import { useAuth } from '../contexts/AuthContext';
import { config } from '@/config/env';

interface ProtectedRouteProps {
  children: React.ReactNode;
}

export const ProtectedRoute: React.FC<ProtectedRouteProps> = ({ children }) => {
  const { isAuthenticated, isLoading } = useAuth();

  if (isLoading) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-gray-100">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600"></div>
      </div>
    );
  }

  if (config.debug) {
    console.log('ProtectedRoute: isAuthenticated =', isAuthenticated);
  }

  if (!isAuthenticated) {
    if (config.debug) {
      console.log('ProtectedRoute: redirecting to /login');
    }
    return <Navigate to="/login" replace />;
  }

  return <>{children}</>;
};