import React, { useState, useLayoutEffect, useEffect } from "react";
import { useLocation } from "react-router-dom";
import { useTranslation } from "react-i18next";
import { Sidebar } from "./Sidebar";
import { AppHeader } from "./MobileHeader";
import { PublicFooter } from "./PublicFooter";
import { AnimatedBackground } from "./AnimatedBackground";
import { useTutorial } from "@/contexts/TutorialContext";
import { usePWAInstallContext } from "@/contexts/PWAInstallContext";
import { InstallPWAModal } from "../pwa/InstallPWAModal";
import {
  getPWADismissed,
  getPWAPromptShown,
  setPWAPromptShown,
} from "@/hooks/usePWAInstall";

interface LayoutProps {
  children: React.ReactNode;
}

export const Layout: React.FC<LayoutProps> = ({ children }) => {
  const [sidebarOpen, setSidebarOpen] = useState(false);
  const [isMobile, setIsMobile] = useState(false);
  const location = useLocation();
  const { t } = useTranslation();
  const { isActive: isTutorialActive } = useTutorial();
  const { isInstallable, isInstalled, platform, install } =
    usePWAInstallContext();
  const [showPWAModal, setShowPWAModal] = useState(false);

  // Show PWA install modal after dashboard loads (once per session)
  useEffect(() => {
    if (getPWAPromptShown()) return;
    if (isInstalled) return;
    if (!isInstallable && platform !== "ios") return;
    if (getPWADismissed()) return;

    setPWAPromptShown();
    const timer = setTimeout(() => setShowPWAModal(true), 2000);
    return () => clearTimeout(timer);
  }, [isInstallable, isInstalled, platform]);

  useLayoutEffect(() => {
    const checkMobile = () => {
      const width = window.innerWidth;
      const mobile = width < 1024;
      setIsMobile(mobile);
      if (!mobile) {
        setSidebarOpen(true); // Show sidebar on desktop by default
      }
    };

    // Check immediately on mount
    checkMobile();

    // Add event listener for resize
    window.addEventListener("resize", checkMobile);
    return () => window.removeEventListener("resize", checkMobile);
  }, []);

  // Open sidebar when tutorial is active on mobile
  useEffect(() => {
    if (isTutorialActive && isMobile && !sidebarOpen) {
      setSidebarOpen(true);
    }
  }, [isTutorialActive, isMobile, sidebarOpen]);

  // Update document title when location or language changes
  useEffect(() => {
    const pageTitle = getPageTitle();
    document.title = pageTitle;
  }, [location.pathname, t]);

  const getPageTitle = () => {
    switch (location.pathname) {
      case "/category":
        return t("navigation.categories");
      case "/account":
        return t("navigation.accounts");
      case "/expense":
        return t("navigation.expenses");
      case "/income":
        return t("navigation.income");
      case "/recurring":
        return t("navigation.recurring");
      case "/goals":
        return t("navigation.goals");
      case "/profile":
        return t("navigation.profile");
      default:
        return t("header.appTitle");
    }
  };

  const handleSidebarToggle = () => {
    setSidebarOpen(!sidebarOpen);
  };

  const handleSidebarClose = () => {
    setSidebarOpen(false);
  };

  return (
    <div className="min-h-screen bg-surface transition-colors relative">
      {/* Animated background layers */}
      <AnimatedBackground />

      <div className="flex min-h-screen relative" style={{ zIndex: 10 }}>
        {/* Sidebar - Full height, starts from top */}
        <Sidebar
          isOpen={sidebarOpen}
          onClose={handleSidebarClose}
          onToggle={handleSidebarToggle}
        />

        {/* Main Content Area with Header */}
        <div className="flex-1 flex flex-col min-h-screen">
          {/* App Header - Only above content, not sidebar */}
          <AppHeader
            onMenuClick={handleSidebarToggle}
            title={getPageTitle()}
            isMobile={isMobile}
          />

          {/* Page Content */}
          <main className="flex-1">
            <div className="p-4 sm:p-6 lg:p-6 min-h-[calc(100vh-8rem)] main-content">
              {children}
            </div>
          </main>

          {/* Footer */}
          <PublicFooter />
        </div>
      </div>

      {/* PWA Install Modal */}
      <InstallPWAModal
        isOpen={showPWAModal}
        onClose={() => setShowPWAModal(false)}
        platform={platform}
        onInstall={install}
      />
    </div>
  );
};
