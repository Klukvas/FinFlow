import React, { useState, useEffect } from "react";
import { Link, useLocation } from "react-router-dom";
import { useTranslation } from "react-i18next";
import { ThemeToggle } from "../shared/ThemeToggle";
import { LanguageSelector } from "../shared/LanguageSelector";
import { AuthModals } from "../auth/AuthModals";
import { useModal } from "@/contexts/ModalContext";
import { useAuth } from "@/contexts/AuthContext";
import {
  Home,
  Folder,
  DollarSign,
  LogIn,
  UserPlus,
  Menu,
  X,
  BookOpen,
  LineChart,
} from "lucide-react";
import { FinFlowLogo, FinFlowWordmark } from "./FinFlowLogo";

export const PublicHeader: React.FC = () => {
  const location = useLocation();
  const { t } = useTranslation();
  const [mobileMenuOpen, setMobileMenuOpen] = useState(false);
  const { openLoginModal, openRegisterModal } = useModal();
  const { isAuthenticated } = useAuth();

  // Close mobile menu when route changes
  useEffect(() => {
    setMobileMenuOpen(false);
  }, [location.pathname]);

  const navigationItems = [
    { path: "/", icon: Home, label: t("publicNav.howItWorks") },
    { path: "/features", icon: Folder, label: t("publicNav.features") },
    { path: "/pricing", icon: DollarSign, label: t("publicNav.pricing") },
    { path: "/blog", icon: BookOpen, label: t("publicNav.blog") },
  ];

  const toggleMobileMenu = () => {
    setMobileMenuOpen((prev) => !prev);
  };

  const closeMobileMenu = () => {
    setMobileMenuOpen(false);
  };

  return (
    <>
      {/* Mobile Header */}
      <header
        className="bg-elevated border-[var(--border)] border-b transition-colors md:hidden"
        data-testid="mobile-header"
      >
        <div className="px-4 py-3">
          <div className="flex items-center justify-between">
            <button
              onClick={toggleMobileMenu}
              data-testid="mobile-menu-toggle"
              className="p-2 rounded-md hover:bg-surface-alt transition-colors"
              aria-label={t("common.openMenu")}
            >
              <Menu className="w-5 h-5 text-content" />
            </button>

            <Link
              to="/"
              className="flex items-center gap-2"
              data-testid="app-title"
            >
              <FinFlowLogo size={24} />
              <FinFlowWordmark className="text-base" />
            </Link>

            <div className="flex items-center space-x-2">
              <LanguageSelector />
              <ThemeToggle />
              {isAuthenticated ? (
                <Link
                  to="/dashboard"
                  data-testid="go-to-dashboard-mobile"
                  className="p-2 text-accent-base hover:bg-accent-base-hover rounded-lg transition-colors"
                  title={t("header.goToDashboard")}
                >
                  <LineChart className="w-4 h-4" />
                </Link>
              ) : (
                <button
                  onClick={openLoginModal}
                  data-testid="login-modal-trigger-mobile"
                  className="p-2 text-content hover:bg-surface-alt rounded-lg transition-colors"
                  title={t("navigation.login")}
                >
                  <LogIn className="w-4 h-4" />
                </button>
              )}
            </div>
          </div>
        </div>
      </header>

      {/* Desktop Header */}
      <header
        className="bg-elevated border-[var(--border)] border-b transition-colors hidden md:block"
        data-testid="desktop-header"
      >
        <div className="px-6 py-4">
          <div className="flex items-center justify-between">
            {/* Logo and Page Title */}
            <div className="flex items-center space-x-6">
              <Link
                to="/"
                className="flex items-center gap-2.5"
                data-testid="app-title"
              >
                <FinFlowLogo size={32} />
                <FinFlowWordmark className="text-xl" />
              </Link>

              {/* Navigation Tabs */}
              <nav className="flex space-x-1" data-testid="desktop-navigation">
                {navigationItems.map((item) => {
                  const Icon = item.icon;
                  const isActive = location.pathname === item.path;

                  return (
                    <Link
                      key={item.path}
                      to={item.path}
                      data-testid={`header-${item.path.split("/")[1]}-link`}
                      className={`flex items-center px-4 py-2 rounded-lg text-sm font-medium transition-colors ${
                        isActive
                          ? "bg-[var(--accent-dim)] text-accent-base"
                          : "text-content-secondary hover:bg-surface-alt hover:text-content"
                      }`}
                    >
                      <Icon className="w-4 h-4 mr-2" />
                      {item.label}
                    </Link>
                  );
                })}
              </nav>
            </div>

            {/* Auth Buttons and Theme Toggle */}
            <div
              className="flex items-center space-x-4"
              data-testid="header-actions"
            >
              <LanguageSelector />
              <ThemeToggle />

              {isAuthenticated ? (
                <Link
                  to="/dashboard"
                  data-testid="go-to-dashboard"
                  className="flex items-center px-4 py-2 text-sm bg-accent-base text-content-inverse hover:bg-accent-base-hover rounded-lg transition-colors"
                >
                  <LineChart className="w-4 h-4 mr-2" />
                  {t("header.goToDashboard")}
                </Link>
              ) : (
                <>
                  <button
                    onClick={openLoginModal}
                    data-testid="login-modal-trigger"
                    className="flex items-center px-4 py-2 text-sm text-content hover:bg-surface-alt rounded-lg transition-colors"
                    title={t("navigation.login")}
                  >
                    <LogIn className="w-4 h-4 mr-2" />
                    {t("navigation.login")}
                  </button>

                  <button
                    onClick={openRegisterModal}
                    data-testid="register-modal-trigger"
                    className="flex items-center px-4 py-2 text-sm bg-accent-base text-content-inverse hover:bg-accent-base-hover rounded-lg transition-colors"
                    title={t("navigation.register")}
                  >
                    <UserPlus className="w-4 h-4 mr-2" />
                    {t("navigation.register")}
                  </button>
                </>
              )}
            </div>
          </div>
        </div>
      </header>

      {/* Mobile Menu Overlay */}
      {mobileMenuOpen && (
        <div
          className="mobile-overlay"
          data-testid="mobile-menu-overlay"
          onClick={closeMobileMenu}
        />
      )}

      {/* Mobile Menu */}
      <div
        className={`mobile-menu bg-elevated theme-shadow ${mobileMenuOpen ? "open" : ""}`}
        data-testid="mobile-menu"
      >
        <div className="flex items-center justify-between p-4 border-[var(--border)] border-b">
          <h2 className="text-lg font-bold text-content">{t("common.menu")}</h2>
          <button
            onClick={closeMobileMenu}
            data-testid="mobile-menu-close"
            className="p-2 rounded-md hover:bg-surface-alt transition-colors"
          >
            <X className="w-5 h-5 text-content" />
          </button>
        </div>

        <nav className="p-4 space-y-2" data-testid="mobile-navigation">
          {navigationItems.map((item) => {
            const Icon = item.icon;
            const isActive = location.pathname === item.path;

            return (
              <Link
                key={item.path}
                to={item.path}
                onClick={closeMobileMenu}
                data-testid={`mobile-${item.path.split("/")[1]}-link`}
                className={`flex items-center px-4 py-3 rounded-lg transition-colors ${
                  isActive
                    ? "bg-[var(--accent-dim)] text-accent-base font-medium"
                    : "text-content-secondary hover:bg-surface-alt hover:text-content"
                }`}
              >
                <Icon className="w-5 h-5 mr-3" />
                {item.label}
              </Link>
            );
          })}
        </nav>

        <div
          className="p-4 border-[var(--border)] border-t space-y-2"
          data-testid="mobile-auth-section"
        >
          {/* Language Selector and Theme Toggle */}
          <div className="flex items-center justify-center space-x-4 px-4 py-3">
            <LanguageSelector />
            <ThemeToggle />
          </div>

          {isAuthenticated ? (
            <Link
              to="/dashboard"
              onClick={closeMobileMenu}
              data-testid="mobile-go-to-dashboard"
              className="w-full flex items-center justify-center px-4 py-3 text-sm bg-accent-base text-content-inverse hover:bg-accent-base-hover rounded-lg transition-colors"
            >
              <LineChart className="w-4 h-4 mr-2" />
              {t("header.goToDashboard")}
            </Link>
          ) : (
            <>
              <button
                onClick={() => {
                  openLoginModal();
                  closeMobileMenu();
                }}
                data-testid="mobile-login-button"
                className="w-full flex items-center justify-center px-4 py-3 text-sm text-content hover:bg-surface-alt rounded-lg transition-colors border-[var(--border)] border"
              >
                <LogIn className="w-4 h-4 mr-2" />
                {t("navigation.login")}
              </button>
              <button
                onClick={() => {
                  openRegisterModal();
                  closeMobileMenu();
                }}
                data-testid="mobile-register-button"
                className="w-full flex items-center justify-center px-4 py-3 text-sm bg-accent-base text-content-inverse hover:bg-accent-base-hover rounded-lg transition-colors"
              >
                <UserPlus className="w-4 h-4 mr-2" />
                {t("navigation.register")}
              </button>
            </>
          )}
        </div>
      </div>

      {/* Auth Modals */}
      <AuthModals />
    </>
  );
};
