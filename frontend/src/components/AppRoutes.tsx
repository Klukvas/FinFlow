import React, { Suspense } from "react";
import { Routes, Route, Navigate } from "react-router-dom";
import { useTranslation } from "react-i18next";
import { useAuth } from "@/contexts/AuthContext";
import { useWorkspace } from "@/contexts/WorkspaceContext";

// Public pages — eagerly loaded for SEO / fast initial render
import {
 Home,
 About,
 Features,
 Pricing,
 Contact,
 Terms,
 Refund,
 PrivacyPolicy,
 NotFound,
 Blog,
 BlogPost,
} from "@/pages";

// Protected pages — lazy loaded (behind auth, not needed on initial load)
const Dashboard = React.lazy(() => import("@/pages/Dashboard"));
const Account = React.lazy(() => import("@/pages/Account"));
const Category = React.lazy(() => import("@/pages/Category"));
const CategoryDetail = React.lazy(() => import("@/pages/CategoryDetail"));
const Expense = React.lazy(() => import("@/pages/Expense"));
const Income = React.lazy(() => import("@/pages/Income"));
const Profile = React.lazy(() => import("@/pages/Profile"));
const Recurring = React.lazy(() => import("@/pages/Recurring"));
const Goals = React.lazy(() => import("@/pages/Goals"));
const PdfParser = React.lazy(() => import("@/pages/PdfParser"));
const Debts = React.lazy(() => import("@/pages/Debts"));
const Workspaces = React.lazy(() => import("@/pages/Workspaces"));
const MyInvites = React.lazy(() => import("@/pages/MyInvites"));
const PaymentReturn = React.lazy(() => import("@/pages/payment/PaymentReturn"));
const AiAssistant = React.lazy(() => import("@/pages/AiAssistant"));
// Bank Sync — hidden until feature is ready for production
// const BankSync = React.lazy(() => import("@/pages/BankSync"));
const PaymentHistory = React.lazy(
 () => import("@/pages/payment/PaymentHistory"),
);
const SubscriptionTermsPage = React.lazy(
 () => import("@/pages/legal/SubscriptionTermsPage"),
);
const CancelHelpPage = React.lazy(() => import("@/pages/legal/CancelHelpPage"));

import { Layout } from "./ui/layout/Layout";
import { PublicLayout } from "./ui/layout/PublicLayout";
import { ProtectedRoute } from "./ProtectedRoute";

export const AppRoutes: React.FC = () => {
 const { t } = useTranslation();
 const { isAuthenticated, isLoading: authLoading } = useAuth();
 const { currentWorkspaceId, isLoading: workspaceLoading } = useWorkspace();

 const lazyFallback = (
 <div className="min-h-screen bg-surface flex items-center justify-center">
 <div className="text-content">{t("common.loading")}</div>
 </div>
 );

 // Show loading spinner while checking authentication or loading workspace
 if (authLoading || (isAuthenticated && workspaceLoading)) {
 return lazyFallback;
 }

 // If authenticated but no workspace after loading, only allow workspace-independent pages.
 // This prevents API calls to services that require X-Workspace-Id header.
 if (isAuthenticated && !currentWorkspaceId && !workspaceLoading) {
 return (
 <Suspense fallback={lazyFallback}>
 <Routes>
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
 <Route
 path="/privacy"
 element={
 <PublicLayout>
 <PrivacyPolicy />
 </PublicLayout>
 }
 />
 <Route
 path="/subscription-terms"
 element={
 <PublicLayout>
 <SubscriptionTermsPage />
 </PublicLayout>
 }
 />
 <Route
 path="/cancel-subscription"
 element={
 <PublicLayout>
 <CancelHelpPage />
 </PublicLayout>
 }
 />
 <Route
 path="/blog"
 element={
 <PublicLayout>
 <Blog />
 </PublicLayout>
 }
 />
 <Route
 path="/blog/:slug"
 element={
 <PublicLayout>
 <BlogPost />
 </PublicLayout>
 }
 />
 <Route path="*" element={<Navigate to="/workspaces" replace />} />
 </Routes>
 </Suspense>
 );
 }

 // If user is authenticated, show protected routes
 if (isAuthenticated) {
 return (
 <Suspense fallback={lazyFallback}>
 <Routes>
 <Route
 path="/dashboard"
 element={
 <ProtectedRoute>
 <Layout>
 <Dashboard />
 </Layout>
 </ProtectedRoute>
 }
 />
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
 <Route
 path="/ai-assistant"
 element={
 <ProtectedRoute>
 <Layout>
 <AiAssistant />
 </Layout>
 </ProtectedRoute>
 }
 />
 {/* Bank Sync — hidden until feature is ready for production */}
 {/* <Route
 path="/bank-sync"
 element={
 <ProtectedRoute>
 <Layout>
 <BankSync />
 </Layout>
 </ProtectedRoute>
 }
 /> */}
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
 <Route
 path="/privacy"
 element={
 <PublicLayout>
 <PrivacyPolicy />
 </PublicLayout>
 }
 />
 <Route
 path="/subscription-terms"
 element={
 <PublicLayout>
 <SubscriptionTermsPage />
 </PublicLayout>
 }
 />
 <Route
 path="/cancel-subscription"
 element={
 <PublicLayout>
 <CancelHelpPage />
 </PublicLayout>
 }
 />
 <Route
 path="/blog"
 element={
 <PublicLayout>
 <Blog />
 </PublicLayout>
 }
 />
 <Route
 path="/blog/:slug"
 element={
 <PublicLayout>
 <BlogPost />
 </PublicLayout>
 }
 />
 <Route
 path="/"
 element={
 <Navigate
 to={currentWorkspaceId ? "/dashboard" : "/workspaces"}
 replace
 />
 }
 />
 <Route
 path="*"
 element={
 <Navigate
 to={currentWorkspaceId ? "/dashboard" : "/workspaces"}
 replace
 />
 }
 />
 </Routes>
 </Suspense>
 );
 }

 // If user is not authenticated, show public routes
 return (
 <Suspense fallback={lazyFallback}>
 <Routes>
 <Route
 path="/"
 element={
 <PublicLayout>
 <Home />
 </PublicLayout>
 }
 />
 <Route
 path="/about"
 element={
 <PublicLayout>
 <About />
 </PublicLayout>
 }
 />
 <Route
 path="/features"
 element={
 <PublicLayout>
 <Features />
 </PublicLayout>
 }
 />
 <Route
 path="/pricing"
 element={
 <PublicLayout>
 <Pricing />
 </PublicLayout>
 }
 />
 <Route
 path="/contact"
 element={
 <PublicLayout>
 <Contact />
 </PublicLayout>
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
 <Route
 path="/privacy"
 element={
 <PublicLayout>
 <PrivacyPolicy />
 </PublicLayout>
 }
 />
 <Route
 path="/subscription-terms"
 element={
 <PublicLayout>
 <SubscriptionTermsPage />
 </PublicLayout>
 }
 />
 <Route
 path="/cancel-subscription"
 element={
 <PublicLayout>
 <CancelHelpPage />
 </PublicLayout>
 }
 />
 <Route
 path="/blog"
 element={
 <PublicLayout>
 <Blog />
 </PublicLayout>
 }
 />
 <Route
 path="/blog/:slug"
 element={
 <PublicLayout>
 <BlogPost />
 </PublicLayout>
 }
 />
 <Route path="/payment/return" element={<PaymentReturn />} />
 <Route
 path="*"
 element={
 <PublicLayout>
 <NotFound />
 </PublicLayout>
 }
 />
 </Routes>
 </Suspense>
 );
};
