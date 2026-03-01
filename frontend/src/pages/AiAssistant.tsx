import React, { useState, useCallback, useRef, useEffect } from "react";
import { useTranslation } from "react-i18next";
import { useApiClients } from "@/hooks/useApiClients";
import { AnalysisResponse } from "@/types";
import {
  AiAssistantHeader,
  PromptBlock,
  AnalysisResultPanel,
  PROMPT_BLOCKS,
} from "@/components/ui/ai-assistant";
import type { ApiError } from "@/services/api/AuthHttpClient";
import type { AiUsageInfo } from "@/services/api/aiAssistantApiClient";

const AiAssistant: React.FC = () => {
  const { t, i18n } = useTranslation();
  const { aiAssistant } = useApiClients();

  const [activePromptId, setActivePromptId] = useState<string | null>(null);
  const [loadingPromptId, setLoadingPromptId] = useState<string | null>(null);
  const [result, setResult] = useState<AnalysisResponse | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [retryAfter, setRetryAfter] = useState<number | null>(null);
  const [usage, setUsage] = useState<AiUsageInfo | null>(null);

  const isMountedRef = useRef(true);

  useEffect(() => {
    isMountedRef.current = true;
    return () => {
      isMountedRef.current = false;
    };
  }, []);

  // Fetch usage on mount
  useEffect(() => {
    const fetchUsage = async () => {
      const resp = await aiAssistant.getUsage();
      if (!isMountedRef.current) return;
      if (!("error" in resp)) {
        setUsage(resp);
      }
    };
    fetchUsage();
  }, [aiAssistant]);

  const fetchLastResult = useCallback(
    async (promptId: string) => {
      const cached = await aiAssistant.getLastResult(
        promptId,
        i18n.language || "ru",
      );
      if (!isMountedRef.current) return;
      if (cached && !("error" in cached)) {
        setResult(cached);
      }
    },
    [aiAssistant, i18n.language],
  );

  const handlePromptClick = useCallback(
    async (promptId: string) => {
      if (loadingPromptId) return;

      setActivePromptId(promptId);
      setLoadingPromptId(promptId);
      setError(null);
      setRetryAfter(null);
      setResult(null);

      try {
        const response = await aiAssistant.analyze({
          prompt_id: promptId,
          language: i18n.language || "ru",
        });

        if (!isMountedRef.current) return;

        if ("error" in response) {
          const err = response as ApiError & { retry_after?: number };
          const status = err.status;

          if (status === 402) {
            setError(t("aiAssistant.featureUnavailable"));
            return;
          }

          if (status === 429) {
            setRetryAfter(err.retry_after ?? null);
            await fetchLastResult(promptId);
            if (!isMountedRef.current) return;
            if (!result) {
              setError(t("aiAssistant.rateLimited"));
            }
            return;
          }

          if (status === 422) {
            setError(err.error || t("aiAssistant.insufficientData"));
            return;
          }

          setError(err.error || t("aiAssistant.error"));
          return;
        }

        setResult(response as AnalysisResponse);

        // Refresh usage after successful analysis
        const updatedUsage = await aiAssistant.getUsage();
        if (isMountedRef.current && !("error" in updatedUsage)) {
          setUsage(updatedUsage);
        }
      } catch {
        if (!isMountedRef.current) return;
        setError(t("aiAssistant.error"));
      } finally {
        if (isMountedRef.current) {
          setLoadingPromptId(null);
        }
      }
    },
    [aiAssistant, i18n.language, loadingPromptId, t, fetchLastResult, result],
  );

  return (
    <div className="p-6 max-w-5xl mx-auto">
      <AiAssistantHeader />

      {usage && <UsageIndicator usage={usage} />}

      {PROMPT_BLOCKS.map((block) => (
        <PromptBlock
          key={block.block}
          block={block}
          activePromptId={activePromptId}
          loadingPromptId={loadingPromptId}
          onPromptClick={handlePromptClick}
        />
      ))}

      <AnalysisResultPanel
        result={result}
        isLoading={loadingPromptId !== null}
        error={error}
        retryAfter={retryAfter}
      />
    </div>
  );
};

const UsageIndicator: React.FC<{ usage: AiUsageInfo }> = ({ usage }) => {
  const { t } = useTranslation();
  const percentage = usage.quota > 0 ? (usage.used / usage.quota) * 100 : 0;
  const isExhausted = usage.remaining === 0;

  const daysUntilReset = Math.ceil(usage.resets_in / 86400);

  return (
    <div className="mb-6 p-4 rounded-xl theme-surface theme-border border">
      <div className="flex items-center justify-between mb-2">
        <span className="text-sm font-medium theme-text-secondary">
          {t("aiAssistant.usage.title", "Monthly usage")}
        </span>
        <span
          className={`text-sm font-semibold ${isExhausted ? "theme-error" : "theme-text-primary"}`}
        >
          {usage.used} / {usage.quota}
        </span>
      </div>
      <div className="w-full h-2 rounded-full theme-bg-tertiary overflow-hidden">
        <div
          className={`h-full rounded-full transition-all duration-300 ${
            isExhausted
              ? "bg-red-500"
              : percentage > 70
                ? "bg-orange-500"
                : "bg-blue-500"
          }`}
          style={{ width: `${Math.min(percentage, 100)}%` }}
        />
      </div>
      <div className="flex items-center justify-between mt-1.5">
        <span className="text-xs theme-text-tertiary">
          {isExhausted
            ? t("aiAssistant.usage.exhausted", "Quota exhausted")
            : t("aiAssistant.usage.remaining", "{{count}} remaining", {
                count: usage.remaining,
              })}
        </span>
        <span className="text-xs theme-text-tertiary">
          {t("aiAssistant.usage.resetsIn", "Resets in {{days}} d", {
            days: daysUntilReset,
          })}
        </span>
      </div>
    </div>
  );
};

export default AiAssistant;
