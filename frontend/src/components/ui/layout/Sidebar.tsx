import React, { useState, useEffect } from "react";
import { useTranslation } from "react-i18next";
import { Link, useLocation } from "react-router-dom";
import { useAuth } from "@/contexts/AuthContext";
import { useWorkspace } from "@/contexts/WorkspaceContext";
import { useTutorial } from "@/contexts/TutorialContext";
import { Badge } from "@/components/ui/shared/Badge";
import { useApiClients } from "@/hooks/useApiClients";
import { WorkspaceSelector } from "@/components/ui/workspace";
import {
 FaChartLine,
 FaFolder,
 FaSignOutAlt,
 FaTimes,
 FaUser,
 FaDollarSign,
 FaRedo,
 FaBullseye,
 FaFilePdf,
 FaWallet,
 FaUsers,
 FaEnvelope,
 FaChevronLeft,
 FaChevronRight,
 FaRobot,
 FaReceipt,
 FaHandHoldingUsd,
 // FaUniversity, // Bank Sync — disabled
} from "react-icons/fa";

interface SidebarProps {
 isOpen: boolean;
 onClose: () => void;
 onToggle?: () => void;
}

export const Sidebar: React.FC<SidebarProps> = ({
 isOpen,
 onClose,
 onToggle,
}) => {
 const { logout, user, isLoading } = useAuth();
 const { currentWorkspaceId } = useWorkspace();
 const { isActive: isTutorialActive } = useTutorial();
 const { subscription: subscriptionApi } = useApiClients();
 const location = useLocation();
 const [isMobile, setIsMobile] = useState(false);
 const [planCode, setPlanCode] = useState<string | null>(null);
 const { t } = useTranslation();

 useEffect(() => {
 if (!user?.id) return;
 subscriptionApi.getUserSubscription(user.id).then((res) => {
 if (!("error" in res)) setPlanCode(res.plan_code);
 });
 }, [user?.id, subscriptionApi]);

 // Force sidebar open on mobile when tutorial is active
 useEffect(() => {
 if (isTutorialActive && isMobile && !isOpen) {
 // We don't directly open here as parent controls state
 // But the tutorial will handle opening the sidebar via Layout
 }
 }, [isTutorialActive, isMobile, isOpen]);

 useEffect(() => {
 const checkMobile = () => {
 const mobile = window.innerWidth < 1024;
 setIsMobile(mobile);
 };

 checkMobile();
 window.addEventListener("resize", checkMobile);
 return () => window.removeEventListener("resize", checkMobile);
 }, []);

 const handleLogout = () => {
 logout();
 onClose();
 };

 const allNavigationItems = [
 {
 path: "/dashboard",
 icon: FaChartLine,
 label: t("navigation.dashboard"),
 requiresWorkspace: true,
 },
 {
 path: "/category",
 icon: FaFolder,
 label: t("navigation.categories"),
 requiresWorkspace: true,
 },
 {
 path: "/account",
 icon: FaWallet,
 label: t("navigation.accounts"),
 requiresWorkspace: true,
 },
 {
 path: "/expense",
 icon: FaReceipt,
 label: t("navigation.expenses"),
 requiresWorkspace: true,
 },
 {
 path: "/income",
 icon: FaDollarSign,
 label: t("navigation.income"),
 requiresWorkspace: true,
 },
 {
 path: "/debts",
 icon: FaHandHoldingUsd,
 label: t("navigation.debts"),
 requiresWorkspace: true,
 },
 {
 path: "/recurring",
 icon: FaRedo,
 label: t("navigation.recurring"),
 requiresWorkspace: true,
 },
 {
 path: "/goals",
 icon: FaBullseye,
 label: t("navigation.goals"),
 requiresWorkspace: true,
 },
 {
 path: "/pdf-parser",
 icon: FaFilePdf,
 label: t("navigation.pdfParser"),
 requiresWorkspace: true,
 },
 {
 path: "/ai-assistant",
 icon: FaRobot,
 label: t("navigation.aiAssistant"),
 requiresWorkspace: true,
 },
 // Bank Sync — hidden until feature is ready for production
 // {
 // path: "/bank-sync",
 // icon: FaUniversity,
 // label: t("navigation.bankSync"),
 // requiresWorkspace: true,
 // },
 {
 path: "/workspaces",
 icon: FaUsers,
 label: t("navigation.workspaces"),
 requiresWorkspace: false,
 },
 {
 path: "/invites",
 icon: FaEnvelope,
 label: t("navigation.invites", "Invitations"),
 requiresWorkspace: false,
 },
 ];

 // Hide workspace-dependent items when no workspace is selected
 const navigationItems = currentWorkspaceId
 ? allNavigationItems
 : allNavigationItems.filter((item) => !item.requiresWorkspace);

 // Render sidebar content with expanded/collapsed state
 const renderSidebarContent = (expanded: boolean) => (
 <div
 data-testid="sidebar"
 className="flex flex-col h-full bg-elevated transition-colors"
 >
 {/* Header */}
 <div
 className={`flex-shrink-0 flex items-center ${expanded ? "justify-between" : "justify-center"} p-4 border-[var(--color-border)] border-b`}
 >
 {expanded && (
 <h1 className="text-lg font-bold text-content">
 {t("header.appTitle")}
 </h1>
 )}
 {isMobile ? (
 <button
 onClick={onClose}
 className="p-2 rounded-md hover:bg-surface-alt transition-colors"
 >
 <FaTimes className="w-5 h-5 text-content" />
 </button>
 ) : (
 onToggle && (
 <button
 onClick={onToggle}
 className="p-2 rounded-md hover:bg-surface-alt transition-colors"
 aria-label={
 expanded ? t("sidebar.collapse") : t("sidebar.expand")
 }
 >
 {expanded ? (
 <FaChevronLeft className="w-4 h-4 text-content-secondary" />
 ) : (
 <FaChevronRight className="w-4 h-4 text-content-secondary" />
 )}
 </button>
 )
 )}
 </div>

 {/* Workspace Selector */}
 {expanded && (
 <div className="flex-shrink-0 px-4 py-3 border-[var(--color-border)] border-b">
 <WorkspaceSelector compact />
 </div>
 )}

 {/* Navigation - scrollable if needed */}
 <nav
 className={`flex-1 overflow-y-auto ${expanded ? "px-4" : "px-2"} py-6 space-y-2`}
 >
 {navigationItems.map((item) => {
 const Icon = item.icon;
 const isActive = location.pathname === item.path;

 return (
 <Link
 key={item.path}
 to={item.path}
 data-testid={`sidebar-${item.path.split("/")[1]}-link`}
 onClick={isMobile ? onClose : undefined}
 title={!expanded ? item.label : undefined}
 className={`flex items-center ${expanded ? "px-4" : "justify-center px-2"} py-3 rounded-lg transition-colors ${
 isActive
 ? "bg-[var(--color-accent-light)] text-accent-base font-medium"
 : "text-content-secondary hover:bg-surface-alt hover:text-content"
 }`}
 >
 <Icon className={`w-5 h-5 ${expanded ? "mr-3" : ""}`} />
 {expanded && <span className="text-sm">{item.label}</span>}
 </Link>
 );
 })}
 </nav>

 {/* User Section - always at bottom */}
 <div
 className={`flex-shrink-0 ${expanded ? "p-4" : "p-2"} border-[var(--color-border)] border-t`}
 data-testid="user-profile-button-sidebar"
 >
 <Link
 data-testid="sidebar-profile-link"
 to="/profile"
 onClick={isMobile ? onClose : undefined}
 className={`flex items-center ${expanded ? "mb-4" : "mb-2 justify-center"} hover:bg-surface-alt rounded-lg p-2 ${expanded ? "-m-2" : ""} transition-colors group cursor-pointer`}
 title={
 expanded
 ? t("sidebar.goToProfile")
 : user?.email || t("header.user")
 }
 >
 <div className="w-8 h-8 bg-[var(--color-accent-light)] rounded-full flex items-center justify-center group-hover:bg-accent-base-hover transition-colors">
 <FaUser className="w-4 h-4 text-accent-base" />
 </div>
 {expanded && (
 <div className="ml-3 min-w-0 flex-1">
 <p
 className="text-sm font-medium text-content group-hover:text-content-secondary truncate"
 data-testid="user-name"
 >
 {isLoading
 ? t("common.loading")
 : user?.email || t("header.user")}
 </p>
 {planCode && (
 <Badge
 size="sm"
 variant={
 planCode === "enterprise"
 ? "warning"
 : planCode === "professional"
 ? "default"
 : "secondary"
 }
 data-testid="subscription-badge"
 >
 {t(
 `homepage.plans.${planCode}.name`,
 planCode.charAt(0).toUpperCase() + planCode.slice(1),
 )}
 </Badge>
 )}
 </div>
 )}
 </Link>

 <button
 data-testid="logout-button"
 onClick={handleLogout}
 title={!expanded ? t("navigation.logout") : undefined}
 className={`w-full flex items-center ${expanded ? "px-4" : "justify-center px-2"} py-2 text-sm text-danger-base hover:bg-[var(--color-danger-light)] rounded-lg transition-colors`}
 >
 <FaSignOutAlt className={`w-4 h-4 ${expanded ? "mr-3" : ""}`} />
 {expanded && t("navigation.logout")}
 </button>
 </div>
 </div>
 );

 if (isMobile) {
 return (
 <>
 {/* Mobile Overlay */}
 {isOpen && (
 <div
 className="fixed inset-0 bg-black/50 bg-opacity-50 z-40"
 onClick={onClose}
 />
 )}

 {/* Mobile Sidebar - always expanded when open */}
 <div
 className={`fixed top-0 left-0 h-full w-64 z-50 transform transition-transform duration-300 ease-in-out ${
 isOpen ? "translate-x-0" : "-translate-x-full"
 }`}
 >
 {renderSidebarContent(true)}
 </div>
 </>
 );
 }

 // Desktop Sidebar - Collapsible & Sticky (full height)
 // When collapsed: show only icons (w-16), when expanded: full width (w-64)
 return (
 <div
 className={`sticky top-0 h-screen bg-elevated border-[var(--color-border)] border-r transition-colors transition-all duration-300 ${
 isOpen ? "w-64" : "w-16"
 }`}
 >
 {renderSidebarContent(isOpen)}
 </div>
 );
};
