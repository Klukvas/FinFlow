import React from "react";
import { useTranslation } from "react-i18next";
import { Card } from "../shared/Card";
import { Skeleton } from "../shared/Skeleton";
import { GoalStatistics } from "../../../types/goal";
import { formatAmount, getProgressBarColor } from "./goalsHelpers";

interface GoalSummaryStripProps {
  stats: GoalStatistics | null;
  loading: boolean;
}

export const GoalSummaryStrip: React.FC<GoalSummaryStripProps> = ({
  stats,
  loading,
}) => {
  const { t } = useTranslation();

  if (loading) {
    return (
      <div className="grid grid-cols-2 lg:grid-cols-5 gap-3">
        {Array.from({ length: 5 }).map((_, i) => (
          <Card key={i}>
            <div className="p-4 space-y-2">
              <Skeleton variant="text" className="h-3 w-20" />
              <Skeleton variant="text" className="h-6 w-16" />
            </div>
          </Card>
        ))}
      </div>
    );
  }

  const currency = stats?.currency || "USD";
  const progressColor = stats?.overall_progress
    ? getProgressBarColor(stats.overall_progress)
        .replace("bg-", "text-")
        .replace("/70", "/80")
    : "text-content";

  const kpiCards = [
    {
      label: t("goalsPage.kpi.activeGoals"),
      value: String(stats?.active_goals ?? 0),
      valueClass: "text-success-base/80",
    },
    {
      label: t("goalsPage.kpi.completed"),
      value: String(stats?.completed_goals ?? 0),
      valueClass: "text-accent-base/80",
    },
    {
      label: t("goalsPage.kpi.totalSaved"),
      value: formatAmount(stats?.total_current_amount ?? 0, currency),
      valueClass: "text-content",
    },
    {
      label: t("goalsPage.kpi.totalTarget"),
      value: formatAmount(stats?.total_target_amount ?? 0, currency),
      valueClass: "text-content",
    },
    {
      label: t("goalsPage.kpi.overallProgress"),
      value: `${(stats?.overall_progress ?? 0).toFixed(1)}%`,
      valueClass: progressColor,
    },
  ];

  return (
    <div
      data-testid="goal-summary-strip"
      className="grid grid-cols-2 lg:grid-cols-5 gap-3"
    >
      {kpiCards.map((card, index) => (
        <Card key={card.label}>
          <div className="p-4" data-testid={`goal-kpi-${index}`}>
            <p className="text-xs font-medium text-content-secondary uppercase tracking-wide">
              {card.label}
            </p>
            <p
              className={`text-xl font-mono font-semibold mt-1 ${card.valueClass}`}
            >
              {card.value}
            </p>
          </div>
        </Card>
      ))}
    </div>
  );
};
