import React, { useState, useLayoutEffect, useEffect } from "react";
import { useLocation } from "react-router-dom";
import { useTranslation } from "react-i18next";
import { Sidebar } from "./Sidebar";
import { AppHeader } from "./MobileHeader";
import { AnimatedBackground } from "./AnimatedBackground";
import { useTutorial } from "@/contexts/TutorialContext";
import { SupportButton } from "@/components/ui/support/SupportButton";

interface LayoutProps {
  children: React.ReactNode;
}

const MOBILE_BREAKPOINT = 768;

export const Layout: React.FC<LayoutProps> = ({ children }) => {
  const [sidebarOpen, setSidebarOpen] = useState(false);
  const [isMobile, setIsMobile] = useState(false);
  const location = useLocation();
  const { t } = useTranslation();
  const { isActive: isTutorialActive } = useTutorial();

  useLayoutEffect(() => {
    const checkMobile = () => {
      const mobile = window.innerWidth < MOBILE_BREAKPOINT;
      setIsMobile(mobile);
      if (!mobile) {
        setSidebarOpen(true);
      }
    };

    checkMobile();
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
    document.title = getPageTitle();
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

  const handleSidebarToggle = () => setSidebarOpen(!sidebarOpen);
  const handleSidebarClose = () => setSidebarOpen(false);

  return (
    <div className="min-h-screen bg-[var(--bg-base)] transition-colors relative">
      {/* Animated background layers */}
      <AnimatedBackground />

      {/* App shell */}
      <div className="flex min-h-screen relative" style={{ zIndex: 10 }}>
        {/* Sidebar */}
        <Sidebar
          isOpen={sidebarOpen}
          onClose={handleSidebarClose}
          onToggle={handleSidebarToggle}
        />

        {/* Main content area */}
        <div className="flex-1 flex flex-col min-h-screen overflow-x-hidden">
          {/* Header */}
          <AppHeader
            onMenuClick={handleSidebarToggle}
            title={getPageTitle()}
            isMobile={isMobile}
          />

          {/* Page content */}
          <main className="flex-1">
            <div className="p-4 sm:p-6 lg:p-8 max-w-[1280px] w-full mx-auto min-h-[calc(100vh-var(--header-height)-4rem)]">
              {children}
            </div>
          </main>
        </div>
      </div>

      {/* Floating support button */}
      <SupportButton />
    </div>
  );
};
