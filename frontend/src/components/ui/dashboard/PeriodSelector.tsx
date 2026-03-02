import React from "react";
import { useTranslation } from "react-i18next";
import { Lock } from "lucide-react";

interface PeriodOption {
  months: number;
  labelKey: string;
}

const PERIOD_OPTIONS: PeriodOption[] = [
  { months: 1, labelKey: "dashboard.period.1m" },
  { months: 3, labelKey: "dashboard.period.3m" },
  { months: 6, labelKey: "dashboard.period.6m" },
  { months: 12, labelKey: "dashboard.period.12m" },
];

const PLAN_ALLOWED_PERIODS: Record<string, number[]> = {
  basic: [1],
  professional: [1, 3, 6],
  enterprise: [1, 3, 6, 12],
};

const REQUIRED_PLAN: Record<number, string> = {
  3: "Professional",
  6: "Professional",
  12: "Enterprise",
};

interface PeriodSelectorProps {
  planCode: string;
  value: number;
  onChange: (months: number) => void;
}

export const PeriodSelector: React.FC<PeriodSelectorProps> = ({
  planCode,
  value,
  onChange,
}) => {
  const { t } = useTranslation();

  const allowedPeriods =
    PLAN_ALLOWED_PERIODS[planCode] ?? PLAN_ALLOWED_PERIODS.basic ?? [];

  return (
    <div className="flex items-center gap-1">
      {PERIOD_OPTIONS.map((option) => {
        const isAllowed = allowedPeriods.includes(option.months);
        const isActive = value === option.months;

        return (
          <button
            key={option.months}
            onClick={() => isAllowed && onChange(option.months)}
            disabled={!isAllowed}
            title={
              isAllowed
                ? undefined
                : t("dashboard.period.upgradeTooltip", {
                    plan: REQUIRED_PLAN[option.months] ?? "Pro",
                  })
            }
            className={`
              relative px-3 py-1.5 text-sm font-medium rounded-lg transition-colors
              ${
                isActive
                  ? "theme-accent-bg text-white"
                  : isAllowed
                    ? "theme-surface theme-text-secondary hover:theme-text-primary theme-border border"
                    : "theme-surface theme-text-tertiary cursor-not-allowed opacity-60 theme-border border"
              }
            `}
          >
            <span className="flex items-center gap-1">
              {t(option.labelKey)}
              {!isAllowed && <Lock className="w-3 h-3" />}
            </span>
          </button>
        );
      })}
    </div>
  );
};
