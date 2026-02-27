import React from "react";
import { Navigate } from "react-router-dom";
import { useAuth } from "../contexts/AuthContext";
import { config } from "@/config/env";

interface ProtectedRouteProps {
  children: React.ReactNode;
}

export const ProtectedRoute: React.FC<ProtectedRouteProps> = ({ children }) => {
  const { isAuthenticated, isLoading } = useAuth();

  if (isLoading) {
    return (
      <div className="min-h-screen flex items-center justify-center theme-bg-secondary">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 theme-accent-border"></div>
      </div>
    );
  }

  if (config.debug) {
  }

  if (!isAuthenticated) {
    if (config.debug) {
    }
    return <Navigate to="/login" replace />;
  }

  return <>{children}</>;
};
