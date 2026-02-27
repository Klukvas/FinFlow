import React from "react";
import { useTranslation } from "react-i18next";
import { AnalysisResponse } from "@/types";
import { AnalysisSectionCard } from "./AnalysisSection";
import { FaSpinner, FaCheckCircle } from "react-icons/fa";

interface AnalysisResultPanelProps {
  result: AnalysisResponse | null;
  isLoading: boolean;
  error: string | null;
  retryAfter: number | null;
}

export const AnalysisResultPanel: React.FC<AnalysisResultPanelProps> = ({
  result,
  isLoading,
  error,
  retryAfter,
}) => {
  const { t } = useTranslation();

  if (isLoading) {
    return (
      <div className="mt-6 p-8 rounded-lg theme-surface theme-border border text-center">
        <FaSpinner className="w-8 h-8 theme-accent animate-spin mx-auto mb-3" />
        <p className="theme-text-secondary text-sm">
          {t("aiAssistant.analyzing")}
        </p>
      </div>
    );
  }

  if (error) {
    return (
      <div className="mt-6 p-6 rounded-lg theme-error-light border theme-border">
        <p className="text-sm theme-error">{error}</p>
        {retryAfter !== null && retryAfter > 0 && (
          <p className="text-xs theme-error mt-2">
            {t("aiAssistant.retryAfter", { time: formatDuration(retryAfter) })}
          </p>
        )}
      </div>
    );
  }

  if (!result) {
    return null;
  }

  return (
    <div className="mt-6">
      <div className="flex items-center gap-2 mb-4">
        <FaCheckCircle className="w-4 h-4 text-green-500" />
        <span className="text-sm theme-text-secondary">
          {result.cached
            ? t("aiAssistant.cachedResult")
            : t("aiAssistant.freshResult")}
        </span>
      </div>
      <div className="space-y-4">
        {result.sections.map((section, index) => (
          <AnalysisSectionCard
            key={`${section.title}-${index}`}
            section={section}
          />
        ))}
      </div>
    </div>
  );
};

function formatDuration(seconds: number): string {
  const hours = Math.floor(seconds / 3600);
  const minutes = Math.floor((seconds % 3600) / 60);
  if (hours >= 24) {
    const days = Math.floor(hours / 24);
    return `${days}d ${hours % 24}h`;
  }
  if (hours > 0) {
    return `${hours}h ${minutes}m`;
  }
  return `${minutes}m`;
}
