import React from "react";
import { Routes, Route, Navigate } from "react-router-dom";
import { AuthProvider } from "@/contexts/AuthContext";
import { ProtectedRoute } from "@/components/ProtectedRoute";
import { Layout } from "@/components/Layout";
import { Login } from "@/pages/Login";
import { AccessDenied } from "@/pages/AccessDenied";
import { Dashboard } from "@/pages/Dashboard";
import { Users } from "@/pages/Users";
import { UserDetail } from "@/pages/UserDetail";
import { Subscriptions } from "@/pages/Subscriptions";
import { Payments } from "@/pages/Payments";
import { Subscription } from "@/pages/Subscription";
import { SystemHealth } from "@/pages/SystemHealth";

const ProtectedPage: React.FC<{ children: React.ReactNode }> = ({
  children,
}) => (
  <ProtectedRoute>
    <Layout>{children}</Layout>
  </ProtectedRoute>
);

const App: React.FC = () => {
  return (
    <AuthProvider>
      <Routes>
        {/* Public routes */}
        <Route path="/" element={<Login />} />
        <Route path="/403" element={<AccessDenied />} />

        {/* Protected admin routes */}
        <Route
          path="/dashboard"
          element={
            <ProtectedPage>
              <Dashboard />
            </ProtectedPage>
          }
        />
        <Route
          path="/users"
          element={
            <ProtectedPage>
              <Users />
            </ProtectedPage>
          }
        />
        <Route
          path="/users/:userId"
          element={
            <ProtectedPage>
              <UserDetail />
            </ProtectedPage>
          }
        />
        <Route
          path="/subscriptions"
          element={
            <ProtectedPage>
              <Subscriptions />
            </ProtectedPage>
          }
        />
        <Route
          path="/payments"
          element={
            <ProtectedPage>
              <Payments />
            </ProtectedPage>
          }
        />
        <Route
          path="/plans"
          element={
            <ProtectedPage>
              <Subscription />
            </ProtectedPage>
          }
        />
        <Route
          path="/system"
          element={
            <ProtectedPage>
              <SystemHealth />
            </ProtectedPage>
          }
        />

        {/* Legacy route redirect */}
        <Route path="/subscription" element={<Navigate to="/plans" replace />} />

        {/* Catch all */}
        <Route path="*" element={<Navigate to="/dashboard" replace />} />
      </Routes>
    </AuthProvider>
  );
};

export default App;
