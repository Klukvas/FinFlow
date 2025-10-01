import React from 'react';
import { Routes, Route, Navigate } from 'react-router-dom';
import { useAuth } from '@/contexts/AuthContext';
import { Account, Category, CategoryDetail, Expense, Income, Profile, Recurring, Goals, PdfParser, Debts, Home, About, Features, Pricing, Contact } from '@/pages';
import { Layout } from './ui/Layout';
import { PublicLayout } from './ui/PublicLayout';
import { ProtectedRoute } from './ProtectedRoute';

export const AppRoutes: React.FC = () => {
  const { isAuthenticated, isLoading } = useAuth();

  // Show loading spinner while checking authentication
  if (isLoading) {
    return (
      <div className="min-h-screen theme-bg flex items-center justify-center">
        <div className="theme-text-primary">Загрузка...</div>
      </div>
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
          path="/category/:id" 
          element={
            <ProtectedRoute>
              <Layout>
                <CategoryDetail />
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
        <Route path="/" element={<Navigate to="/category" replace />} />
        <Route path="*" element={<Navigate to="/category" replace />} />
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
      <Route path="*" element={<Navigate to="/" replace />} />
    </Routes>
  );
};
