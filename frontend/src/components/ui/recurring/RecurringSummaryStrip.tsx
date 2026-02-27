import React from "react";
import { useTranslation } from "react-i18next";
import { Card } from "../shared/Card";
import { Skeleton } from "../shared/Skeleton";
import { PaymentStatistics } from "../../../services/api/recurringApi";

interface RecurringSummaryStripProps {
  stats: PaymentStatistics | null;
  loading: boolean;
}

export const RecurringSummaryStrip: React.FC<RecurringSummaryStripProps> = ({
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

  const kpiCards = [
    {
      label: t("recurringPage.kpi.total"),
      value: String(stats?.total_payments ?? 0),
      valueClass: "theme-text-primary",
    },
    {
      label: t("recurringPage.kpi.active"),
      value: String(stats?.active_payments ?? 0),
      valueClass: "text-green-600/80",
    },
    {
      label: t("recurringPage.kpi.paused"),
      value: String(stats?.paused_payments ?? 0),
      valueClass: "text-yellow-600/80",
    },
    {
      label: t("recurringPage.kpi.executedThisMonth"),
      value: String(stats?.executed_this_month ?? 0),
      valueClass: "theme-text-primary",
    },
    {
      label: t("recurringPage.kpi.failedThisMonth"),
      value: String(stats?.failed_this_month ?? 0),
      valueClass: stats?.failed_this_month
        ? "text-red-500/80"
        : "theme-text-primary",
    },
  ];

  return (
    <div className="grid grid-cols-2 lg:grid-cols-5 gap-3">
      {kpiCards.map((card) => (
        <Card key={card.label}>
          <div className="p-4">
            <p className="text-xs font-medium theme-text-secondary uppercase tracking-wide">
              {card.label}
            </p>
            <p className={`text-xl font-semibold mt-1 ${card.valueClass}`}>
              {card.value}
            </p>
          </div>
        </Card>
      ))}
    </div>
  );
};
