import React from 'react';
import { Routes, Route, Navigate } from 'react-router-dom';
import { useAuth } from '@/contexts/AuthContext';
import { useWorkspace } from '@/contexts/WorkspaceContext';
import { Account, Category, Expense, Income, Profile, Recurring, Goals, PdfParser, Debts, Workspaces, MyInvites, Home, About, Features, Pricing, Contact, Terms, Refund } from '@/pages';
import { PaymentReturn } from '@/pages/payment/PaymentReturn';
import { PaymentHistory } from '@/pages/payment/PaymentHistory';
import { PaymentCheckoutSimple } from '@/pages/payment/PaymentCheckoutSimple';
import { Layout } from './ui/layout/Layout';
import { PublicLayout } from './ui/layout/PublicLayout';
import { ProtectedRoute } from './ProtectedRoute';

export const AppRoutes: React.FC = () => {
  const { isAuthenticated, isLoading: authLoading } = useAuth();
  const { currentWorkspaceId, isLoading: workspaceLoading } = useWorkspace();

  // Show loading spinner while checking authentication or loading workspace
  if (authLoading || (isAuthenticated && workspaceLoading)) {
    return (
      <div className="min-h-screen theme-bg flex items-center justify-center">
        <div className="theme-text-primary">Загрузка...</div>
      </div>
    );
  }

  // If authenticated but no workspace after loading, only allow workspace-independent pages.
  // This prevents API calls to services that require X-Workspace-Id header.
  if (isAuthenticated && !currentWorkspaceId && !workspaceLoading) {
    return (
      <Routes>
        <Route path="/workspaces" element={<ProtectedRoute><Layout><Workspaces /></Layout></ProtectedRoute>} />
        <Route path="/profile" element={<ProtectedRoute><Layout><Profile /></Layout></ProtectedRoute>} />
        <Route path="/invites" element={<ProtectedRoute><Layout><MyInvites /></Layout></ProtectedRoute>} />
        <Route path="/terms" element={<PublicLayout><Terms /></PublicLayout>} />
        <Route path="/refund" element={<PublicLayout><Refund /></PublicLayout>} />
        <Route path="*" element={<Navigate to="/workspaces" replace />} />
      </Routes>
    );
  }

  // If user is authenticated, show protected routes
  if (isAuthenticated) {
    return (
      <Routes>
        <Route 
          path="/account" 
          element={
            <ProtectedRoute>
              <Layout>
                <Account />
              </Layout>
            </ProtectedRoute>
          } 
        />
        <Route 
          path="/expense" 
          element={
            <ProtectedRoute>
              <Layout>
                <Expense />
              </Layout>
            </ProtectedRoute>
          } 
        />
        <Route 
          path="/income" 
          element={
            <ProtectedRoute>
              <Layout>
                <Income />
              </Layout>
            </ProtectedRoute>
          } 
        />
        <Route 
          path="/debts" 
          element={
            <ProtectedRoute>
              <Layout>
                <Debts />
              </Layout>
            </ProtectedRoute>
          } 
        />
        <Route 
          path="/recurring" 
          element={
            <ProtectedRoute>
              <Layout>
                <Recurring />
              </Layout>
            </ProtectedRoute>
          } 
        />
        <Route 
          path="/goals" 
          element={
            <ProtectedRoute>
              <Layout>
                <Goals />
              </Layout>
            </ProtectedRoute>
          } 
        />
        <Route 
          path="/category" 
          element={
            <ProtectedRoute>
              <Layout>
                <Category />
              </Layout>
            </ProtectedRoute>
          } 
        />
        <Route 
          path="/profile" 
          element={
            <ProtectedRoute>
              <Layout>
                <Profile />
              </Layout>
            </ProtectedRoute>
          } 
        />
        <Route 
          path="/pdf-parser" 
          element={
            <ProtectedRoute>
              <Layout>
                <PdfParser />
              </Layout>
            </ProtectedRoute>
          } 
        />
        <Route 
          path="/workspaces" 
          element={
            <ProtectedRoute>
              <Layout>
                <Workspaces />
              </Layout>
            </ProtectedRoute>
          } 
        />
        <Route 
          path="/invites" 
          element={
            <ProtectedRoute>
              <Layout>
                <MyInvites />
              </Layout>
            </ProtectedRoute>
          } 
        />
        <Route 
          path="/payment/checkout" 
          element={
            <ProtectedRoute>
              <PaymentCheckoutSimple />
            </ProtectedRoute>
          } 
        />
        <Route 
          path="/payment/return" 
          element={
            <ProtectedRoute>
              <PaymentReturn />
            </ProtectedRoute>
          } 
        />
        <Route 
          path="/payment/history" 
          element={
            <ProtectedRoute>
              <Layout>
                <PaymentHistory />
              </Layout>
            </ProtectedRoute>
          } 
        />
        <Route 
          path="/pricing" 
          element={
            <ProtectedRoute>
              <Layout>
                <Pricing />
              </Layout>
            </ProtectedRoute>
          } 
        />
        <Route 
          path="/terms" 
          element={
            <PublicLayout>
              <Terms />
            </PublicLayout>
          } 
        />
        <Route 
          path="/refund" 
          element={
            <PublicLayout>
              <Refund />
            </PublicLayout>
          } 
        />
        <Route path="/" element={<Navigate to={currentWorkspaceId ? "/category" : "/workspaces"} replace />} />
        <Route path="*" element={<Navigate to={currentWorkspaceId ? "/category" : "/workspaces"} replace />} />
      </Routes>
    );
  }

  // If user is not authenticated, show public routes
  return (
    <Routes>
      <Route path="/" element={
        <PublicLayout>
          <Home />
        </PublicLayout>
      } />
      <Route path="/about" element={
        <PublicLayout>
          <About />
        </PublicLayout>
      } />
      <Route path="/features" element={
        <PublicLayout>
          <Features />
        </PublicLayout>
      } />
      <Route path="/pricing" element={
        <PublicLayout>
          <Pricing />
        </PublicLayout>
      } />
      <Route path="/contact" element={
        <PublicLayout>
          <Contact />
        </PublicLayout>
      } />
      <Route path="/terms" element={
        <PublicLayout>
          <Terms />
        </PublicLayout>
      } />
      <Route path="/refund" element={
        <PublicLayout>
          <Refund />
        </PublicLayout>
      } />
      <Route path="/payment/checkout" element={<PaymentCheckoutSimple />} />
      <Route path="/payment/return" element={<PaymentReturn />} />
      <Route path="*" element={<Navigate to="/" replace />} />
    </Routes>
  );
};
