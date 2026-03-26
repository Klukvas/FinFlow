import React, { useState, useEffect } from "react";
import { useTranslation } from "react-i18next";
import { Link, useLocation } from "react-router-dom";
import { useAuth } from "@/contexts/AuthContext";
import { useWorkspace } from "@/contexts/WorkspaceContext";
import { useTutorial } from "@/contexts/TutorialContext";
import { Badge } from "@/components/ui/shared/Badge";
import { useApiClients } from "@/hooks/useApiClients";
import { WorkspaceSelector } from "@/components/ui/workspace";
import { FinFlowLogo, FinFlowWordmark } from "./FinFlowLogo";
import {
  LineChart,
  Folder,
  LogOut,
  X,
  User,
  DollarSign,
  RefreshCw,
  Target,
  FileText,
  Wallet,
  Users,
  Mail,
  ChevronLeft,
  ChevronRight,
  Bot,
  Receipt,
  HandCoins,
} from "lucide-react";

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
      if (res && !("error" in res)) setPlanCode(res.plan_code);
      else setPlanCode("basic");
    });
  }, [user?.id, subscriptionApi]);

  useEffect(() => {
    if (isTutorialActive && isMobile && !isOpen) {
      // Parent controls state via Layout
    }
  }, [isTutorialActive, isMobile, isOpen]);

  useEffect(() => {
    const checkMobile = () => setIsMobile(window.innerWidth < 768);
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
      icon: LineChart,
      label: t("navigation.dashboard"),
      requiresWorkspace: true,
    },
    {
      path: "/category",
      icon: Folder,
      label: t("navigation.categories"),
      requiresWorkspace: true,
    },
    {
      path: "/account",
      icon: Wallet,
      label: t("navigation.accounts"),
      requiresWorkspace: true,
    },
    {
      path: "/expense",
      icon: Receipt,
      label: t("navigation.expenses"),
      requiresWorkspace: true,
    },
    {
      path: "/income",
      icon: DollarSign,
      label: t("navigation.income"),
      requiresWorkspace: true,
    },
    {
      path: "/debts",
      icon: HandCoins,
      label: t("navigation.debts"),
      requiresWorkspace: true,
    },
    {
      path: "/recurring",
      icon: RefreshCw,
      label: t("navigation.recurring"),
      requiresWorkspace: true,
    },
    {
      path: "/goals",
      icon: Target,
      label: t("navigation.goals"),
      requiresWorkspace: true,
    },
    {
      path: "/pdf-parser",
      icon: FileText,
      label: t("navigation.pdfParser"),
      requiresWorkspace: true,
    },
    {
      path: "/ai-assistant",
      icon: Bot,
      label: t("navigation.aiAssistant"),
      requiresWorkspace: true,
    },
    {
      path: "/workspaces",
      icon: Users,
      label: t("navigation.workspaces"),
      requiresWorkspace: false,
    },
    {
      path: "/invites",
      icon: Mail,
      label: t("navigation.invites", "Invitations"),
      requiresWorkspace: false,
    },
  ];

  const navigationItems = currentWorkspaceId
    ? allNavigationItems
    : allNavigationItems.filter((item) => !item.requiresWorkspace);

  const renderSidebarContent = (expanded: boolean) => (
    <div
      data-testid="sidebar"
      className="flex flex-col h-full bg-[var(--bg-base)]"
    >
      {/* Logo + close/toggle */}
      <div className="flex-shrink-0 flex items-center gap-2.5 px-3 py-3 border-b border-[var(--border)]">
        {expanded && (
          <div className="flex items-center gap-2.5 flex-1 pl-2">
            <FinFlowLogo size={28} />
            <FinFlowWordmark />
          </div>
        )}
        {isMobile ? (
          <button
            onClick={onClose}
            className="w-7 h-7 flex items-center justify-center rounded-[var(--radius-sm)] text-[var(--text-tertiary)] hover:bg-[var(--bg-raised)] hover:text-[var(--text-primary)] transition-colors ml-auto"
          >
            <X className="w-4 h-4" strokeWidth={1.5} />
          </button>
        ) : (
          onToggle && (
            <button
              onClick={onToggle}
              className="w-7 h-7 flex items-center justify-center rounded-[var(--radius-sm)] text-[var(--text-tertiary)] hover:bg-[var(--bg-raised)] hover:text-[var(--text-primary)] transition-colors ml-auto"
              aria-label={
                expanded ? t("sidebar.collapse") : t("sidebar.expand")
              }
            >
              {expanded ? (
                <ChevronLeft className="w-4 h-4" strokeWidth={1.5} />
              ) : (
                <ChevronRight className="w-4 h-4" strokeWidth={1.5} />
              )}
            </button>
          )
        )}
      </div>

      {/* Workspace Selector */}
      {expanded && (
        <div className="flex-shrink-0 px-3 py-3 border-b border-[var(--border)]">
          <WorkspaceSelector compact />
        </div>
      )}

      {/* Navigation */}
      <nav
        className={`flex-1 overflow-y-auto ${expanded ? "px-2.5" : "px-1.5"} py-4 space-y-1`}
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
              className={`relative flex items-center gap-2.5 ${expanded ? "px-2.5" : "justify-center px-0"} py-[7px] rounded-[var(--radius-md)] text-[13px] font-medium transition-all duration-100 ${
                isActive
                  ? "bg-[var(--bg-raised)] text-[var(--text-primary)]"
                  : "text-[var(--text-secondary)] hover:bg-[var(--bg-raised)] hover:text-[var(--text-primary)]"
              }`}
            >
              {isActive && (
                <span className="absolute left-0 top-1/2 -translate-y-1/2 w-[2px] h-[18px] bg-[var(--accent)] rounded-r-sm" />
              )}
              <Icon
                className={`w-4 h-4 flex-shrink-0 ${isActive ? "opacity-100" : "opacity-65"}`}
                strokeWidth={1.5}
              />
              {expanded && <span>{item.label}</span>}
            </Link>
          );
        })}
      </nav>

      {/* User section */}
      <div
        className={`flex-shrink-0 ${expanded ? "p-3" : "p-1.5"} border-t border-[var(--border)]`}
        data-testid="user-profile-button-sidebar"
      >
        <Link
          data-testid="sidebar-profile-link"
          to="/profile"
          onClick={isMobile ? onClose : undefined}
          className={`flex items-center ${expanded ? "gap-3 px-2.5" : "justify-center"} py-2 rounded-[var(--radius-md)] hover:bg-[var(--bg-raised)] transition-colors group cursor-pointer mb-2`}
          title={
            expanded
              ? t("sidebar.goToProfile")
              : user?.email || t("header.user")
          }
        >
          <div className="w-7 h-7 bg-[var(--accent-dim)] border border-[var(--accent-border)] rounded-[6px] flex items-center justify-center flex-shrink-0">
            <User
              className="w-3.5 h-3.5 text-[var(--accent)]"
              strokeWidth={1.5}
            />
          </div>
          {expanded && (
            <div className="min-w-0 flex-1">
              <p
                className="text-[13px] font-medium text-[var(--text-primary)] truncate"
                data-testid="user-name"
              >
                {isLoading
                  ? t("common.loading")
                  : user?.email || t("header.user")}
              </p>
              {planCode && (
                <Badge
                  variant={
                    planCode === "enterprise"
                      ? "warning"
                      : planCode === "professional"
                        ? "accent"
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
          className={`w-full flex items-center ${expanded ? "gap-2.5 px-2.5" : "justify-center"} py-2 text-[13px] text-[var(--danger)] rounded-[var(--radius-md)] hover:bg-[var(--danger-dim)] transition-colors`}
        >
          <LogOut className="w-4 h-4" strokeWidth={1.5} />
          {expanded && t("navigation.logout")}
        </button>
      </div>
    </div>
  );

  if (isMobile) {
    return (
      <>
        {isOpen && (
          <div
            className="fixed inset-0 bg-[var(--bg-overlay)] z-[calc(var(--z-sidebar)-1)]"
            onClick={onClose}
          />
        )}
        <div
          className="fixed top-0 left-0 h-full z-[var(--z-sidebar)] border-r border-[var(--border)] transition-transform duration-[250ms] ease-in-out"
          style={{
            width: "var(--sidebar-width)",
            transform: isOpen ? "translateX(0)" : "translateX(-100%)",
          }}
        >
          {isOpen && (
            <div className="h-full" style={{ boxShadow: "var(--shadow-lg)" }}>
              {renderSidebarContent(true)}
            </div>
          )}
        </div>
      </>
    );
  }

  return (
    <div
      className="sticky top-0 h-screen border-r border-[var(--border)] transition-all duration-200"
      style={{
        width: isOpen
          ? "var(--sidebar-width)"
          : "var(--sidebar-collapsed-width)",
      }}
    >
      {renderSidebarContent(isOpen)}
    </div>
  );
};
