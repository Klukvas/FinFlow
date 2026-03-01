import React, { useState, useEffect } from "react";
import { useTranslation } from "react-i18next";
import { Link } from "react-router-dom";
import { AlertTriangle, Sparkles, ArrowRight } from "lucide-react";
import { useApiClients } from "@/hooks/useApiClients";
import { AnalysisResponse } from "@/types";
import { AiUsageInfo } from "@/services/api/aiAssistantApiClient";

export const AiInsightsWidget: React.FC = () => {
  const { t, i18n } = useTranslation();
  const { aiAssistant } = useApiClients();

  const [result, setResult] = useState<AnalysisResponse | null>(null);
  const [usage, setUsage] = useState<AiUsageInfo | null>(null);
  const [loading, setLoading] = useState(true);
  const [hasError, setHasError] = useState(false);

  useEffect(() => {
    const fetchData = async () => {
      setLoading(true);
      setHasError(false);
      try {
        const [resultRes, usageRes] = await Promise.all([
          aiAssistant.getLastResult("expenses_reduce_spending", i18n.language),
          aiAssistant.getUsage(),
        ]);

        if (resultRes && !("error" in resultRes)) {
          setResult(resultRes);
        } else {
          setResult(null);
        }
        if (usageRes && !("error" in usageRes)) setUsage(usageRes);
      } catch {
        setHasError(true);
      } finally {
        setLoading(false);
      }
    };

    fetchData();
  }, [aiAssistant, i18n.language]);

  const renderContent = () => {
    if (loading) {
      return (
        <div className="space-y-2">
          <div className="h-4 bg-gray-200 dark:bg-gray-700 rounded animate-pulse w-full" />
          <div className="h-4 bg-gray-200 dark:bg-gray-700 rounded animate-pulse w-3/4" />
          <div className="h-4 bg-gray-200 dark:bg-gray-700 rounded animate-pulse w-1/2" />
        </div>
      );
    }

    if (hasError) {
      return (
        <div className="text-center py-6">
          <AlertTriangle className="w-8 h-8 text-yellow-500 mx-auto mb-2" />
          <p className="text-sm theme-text-secondary">
            {t("dashboard.aiInsights.error")}
          </p>
        </div>
      );
    }

    if (result && result.sections.length > 0) {
      return (
        <div className="space-y-3">
          {result.sections.slice(0, 3).map((section) => (
            <div key={section.title} className="flex gap-2">
              <span
                className={`mt-1 flex-shrink-0 w-2 h-2 rounded-full ${
                  section.priority === "high"
                    ? "bg-red-500"
                    : section.priority === "medium"
                      ? "bg-yellow-500"
                      : "bg-green-500"
                }`}
              />
              <div className="min-w-0">
                <p className="text-sm font-medium theme-text-primary">
                  {section.title}
                </p>
                <p className="text-xs theme-text-secondary line-clamp-2">
                  {section.content}
                </p>
              </div>
            </div>
          ))}

          {usage && (
            <p className="text-xs theme-text-secondary mt-2 pt-2 border-t border-gray-200 dark:border-gray-700">
              {t("dashboard.aiInsights.usage", {
                used: usage.used,
                quota: usage.quota,
              })}
            </p>
          )}
        </div>
      );
    }

    return (
      <div className="text-center py-6">
        <Sparkles className="w-8 h-8 theme-text-secondary mx-auto mb-2" />
        <p className="text-sm theme-text-secondary mb-3">
          {t("dashboard.aiInsights.empty")}
        </p>
        <Link
          to="/ai-assistant"
          className="px-3 py-1.5 text-sm font-medium text-white bg-indigo-600 hover:bg-indigo-700 rounded-lg transition-colors"
        >
          {t("dashboard.aiInsights.runFirst")}
        </Link>
      </div>
    );
  };

  return (
    <div className="theme-surface p-6 rounded-lg theme-shadow theme-border border">
      <div className="flex items-center justify-between mb-4">
        <div className="flex items-center">
          <Sparkles className="h-5 w-5 theme-accent mr-2" />
          <h2 className="text-lg font-semibold theme-text-primary">
            {t("dashboard.aiInsights.title")}
          </h2>
        </div>
        <Link
          to="/ai-assistant"
          className="theme-accent text-sm font-medium flex items-center gap-1 theme-transition"
        >
          {t("dashboard.aiInsights.viewAll")}
          <ArrowRight className="w-3 h-3" />
        </Link>
      </div>
      {renderContent()}
    </div>
  );
};
