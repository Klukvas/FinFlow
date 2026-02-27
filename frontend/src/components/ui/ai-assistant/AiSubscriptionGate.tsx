import React from "react";
import { useTranslation } from "react-i18next";
import { Link } from "react-router-dom";
import { FaLock } from "react-icons/fa";

export const AiSubscriptionGate: React.FC = () => {
  const { t } = useTranslation();

  return (
    <div className="flex flex-col items-center justify-center py-16 px-4 text-center">
      <div className="w-16 h-16 rounded-full theme-bg-secondary flex items-center justify-center mb-4">
        <FaLock className="w-8 h-8 theme-text-tertiary" />
      </div>
      <h2 className="text-xl font-semibold theme-text-primary mb-2">
        {t("aiAssistant.locked.title")}
      </h2>
      <p className="theme-text-secondary text-sm max-w-md mb-6">
        {t("aiAssistant.locked.description")}
      </p>
      <Link
        to="/pricing"
        className="px-6 py-2.5 rounded-lg theme-accent-bg theme-text-inverse font-medium text-sm hover:opacity-90 theme-transition"
      >
        {t("aiAssistant.locked.upgrade")}
      </Link>
    </div>
  );
};
