import React from "react";
import { useTranslation } from "react-i18next";
import { Card } from "../shared/Card";
import { Skeleton } from "../shared/Skeleton";
import { DebtSummary } from "../../../types/debt";
import { useCurrencyConversion } from "../../../hooks/useCurrencyConversion";

interface DebtSummaryStripProps {
  summary: DebtSummary | null;
  loading: boolean;
}

export const DebtSummaryStrip: React.FC<DebtSummaryStripProps> = ({
  summary,
  loading,
}) => {
  const { t } = useTranslation();
  const { formatCurrency, userCurrency } = useCurrencyConversion();

  if (loading) {
    return (
      <div className="grid grid-cols-2 lg:grid-cols-4 gap-3">
        {Array.from({ length: 4 }).map((_, i) => (
          <Card key={i}>
            <div className="p-4 space-y-2">
              <Skeleton variant="text" className="h-3 w-20" />
              <Skeleton variant="text" className="h-6 w-24" />
            </div>
          </Card>
        ))}
      </div>
    );
  }

  const currency = summary?.currency || userCurrency;

  const kpiCards = [
    {
      label: t("debtPage.kpi.totalOutstanding"),
      value: formatCurrency(summary?.total_debt ?? 0, currency),
      valueClass: "text-danger-base/80",
    },
    {
      label: t("debtPage.kpi.totalPaid"),
      value: formatCurrency(summary?.total_payments ?? 0, currency),
      valueClass: "text-success-base/80",
    },
    {
      label: t("debtPage.kpi.activeDebts"),
      value: String(summary?.active_debts ?? 0),
      valueClass: "text-content",
    },
    {
      label: t("debtPage.kpi.avgInterest"),
      value:
        summary?.average_interest_rate != null
          ? `${summary.average_interest_rate.toFixed(1)}%`
          : "N/A",
      valueClass: "text-content",
    },
  ];

  return (
    <div className="grid grid-cols-2 lg:grid-cols-4 gap-3">
      {kpiCards.map((card) => (
        <Card key={card.label}>
          <div className="p-4">
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
