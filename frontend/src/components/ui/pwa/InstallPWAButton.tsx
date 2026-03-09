import React, { useState } from "react";
import { useTranslation } from "react-i18next";
import { FaDownload } from "react-icons/fa";
import { usePWAInstallContext } from "@/contexts/PWAInstallContext";
import { InstallPWAModal } from "./InstallPWAModal";

export const InstallPWAButton: React.FC = () => {
  const { t } = useTranslation();
  const { isInstallable, isInstalled, platform, install } =
    usePWAInstallContext();
  const [showModal, setShowModal] = useState(false);

  if (isInstalled) return null;
  if (!isInstallable && platform !== "ios") return null;

  const handleClick = () => {
    if (platform === "ios") {
      setShowModal(true);
    } else {
      install();
    }
  };

  return (
    <>
      <button
        onClick={handleClick}
        data-testid="pwa-install-button"
        aria-label={t("pwa.headerButton")}
        className="flex items-center px-3 py-2 text-sm text-accent-base hover:bg-surface-alt rounded-lg transition-colors"
      >
        <FaDownload className="w-4 h-4 mr-1.5" />
        <span className="hidden sm:inline">{t("pwa.headerButton")}</span>
      </button>

      <InstallPWAModal
        isOpen={showModal}
        onClose={() => setShowModal(false)}
        platform={platform}
        onInstall={install}
      />
    </>
  );
};
