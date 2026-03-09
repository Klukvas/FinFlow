import React, { useMemo, useCallback } from "react";
import { Link, useLocation } from "react-router-dom";
import { useTranslation } from "react-i18next";
import { useAuth } from "@/contexts/AuthContext";
import { ThemeToggle } from "../shared/ThemeToggle";
import { LanguageSelector } from "../shared/LanguageSelector";
import { WorkspaceSelector } from "../workspace/WorkspaceSelector";
import {
 FaHome,
 FaFolder,
 FaSignOutAlt,
 FaUser,
 FaDollarSign,
 FaRedo,
} from "react-icons/fa";

export const DesktopHeader = React.memo(() => {
 const { logout, user, isLoading } = useAuth();
 const { t } = useTranslation();
 const location = useLocation();

 const handleLogout = useCallback(() => {
 logout();
 }, [logout]);

 const navigationItems = useMemo(
 () => [
 { path: "/category", icon: FaFolder, label: t("navigation.categories") },
 { path: "/expense", icon: FaHome, label: t("navigation.expenses") },
 { path: "/income", icon: FaDollarSign, label: t("navigation.income") },
 { path: "/recurring", icon: FaRedo, label: t("navigation.recurring") },
 ],
 [t],
 );

 return (
 <header
 className="bg-elevated border-[var(--color-border)] border-b theme-shadow transition-colors"
 data-testid="desktop-header"
 >
 <div className="px-6 py-4">
 <div className="flex items-center justify-between">
 {/* Logo and Page Title */}
 <div className="flex items-center space-x-6">
 <h1
 className="text-2xl font-bold text-content"
 data-testid="app-title"
 >
 {t("header.appTitle")}
 </h1>

 {/* Navigation Tabs */}
 <nav className="flex space-x-1" data-testid="desktop-navigation">
 {navigationItems.map((item) => {
 const Icon = item.icon;
 const isActive = location.pathname === item.path;

 return (
 <Link
 key={item.path}
 to={item.path}
 data-testid={`sidebar-${item.path.split("/")[1]}-link`}
 className={`flex items-center px-4 py-2 rounded-lg text-sm font-medium transition-colors ${
 isActive
 ? "bg-[var(--color-accent-light)] text-accent-base"
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

 {/* User Menu and Theme Toggle */}
 <div
 className="flex items-center space-x-4"
 data-testid="header-actions"
 >
 <WorkspaceSelector />
 <div className="w-px h-6 bg-surface-alt" />
 <ThemeToggle />
 <LanguageSelector />

 <Link
 to="/profile"
 data-testid="user-profile-button"
 className="flex items-center space-x-2 hover:bg-surface-alt rounded-lg px-3 py-2 transition-colors group cursor-pointer"
 title={t("header.goToProfile")}
 >
 <div className="w-8 h-8 bg-[var(--color-accent-light)] rounded-full flex items-center justify-center group-hover:bg-accent-base-hover transition-colors">
 <FaUser className="w-4 h-4 text-accent-base" />
 </div>
 <span className="text-sm font-medium text-content-secondary group-hover:text-content">
 {isLoading
 ? t("common.loading")
 : user?.email || t("header.user")}
 </span>
 </Link>

 <button
 onClick={handleLogout}
 data-testid="logout-button"
 className="flex items-center px-3 py-2 text-sm text-danger-base hover:bg-[var(--color-danger-light)] rounded-lg transition-colors"
 title={t("navigation.logout")}
 >
 <FaSignOutAlt className="w-4 h-4 mr-2" />
 {t("navigation.logout")}
 </button>
 </div>
 </div>
 </div>
 </header>
 );
});

DesktopHeader.displayName = "DesktopHeader";
