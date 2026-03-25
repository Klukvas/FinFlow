import React, { useMemo } from "react";
import { useTranslation } from "react-i18next";
import { Card } from "../shared/Card";
import { Skeleton } from "../shared/Skeleton";
import { IncomeOut } from "../../../types/income";
import { useCurrencyConversion } from "../../../hooks/useCurrencyConversion";

interface IncomeSummaryStripProps {
  incomes: IncomeOut[];
  loading: boolean;
}

export const IncomeSummaryStrip: React.FC<IncomeSummaryStripProps> = ({
  incomes,
  loading,
}) => {
  const { t } = useTranslation();
  const { formatCurrency, convertToUserCurrency, userCurrency } =
    useCurrencyConversion();

  const stats = useMemo(() => {
    const now = new Date();
    const thisMonth = now.getMonth();
    const thisYear = now.getFullYear();
    const prevMonth = thisMonth === 0 ? 11 : thisMonth - 1;
    const prevYear = thisMonth === 0 ? thisYear - 1 : thisYear;

    let thisMonthTotal = 0;
    let prevMonthTotal = 0;
    const categorySet = new Set<number>();
    let thisMonthCount = 0;

    for (const income of incomes) {
      const d = new Date(income.date);
      const m = d.getMonth();
      const y = d.getFullYear();
      const converted =
        convertToUserCurrency(income.amount, income.currency ?? "") ??
        income.amount;

      if (m === thisMonth && y === thisYear) {
        thisMonthTotal += converted;
        thisMonthCount++;
        if (income.category_id) {
          categorySet.add(income.category_id);
        }
      } else if (m === prevMonth && y === prevYear) {
        prevMonthTotal += converted;
      }
    }

    const daysInMonth = new Date(thisYear, thisMonth + 1, 0).getDate();
    const currentDay = Math.min(now.getDate(), daysInMonth);
    const avgPerDay = currentDay > 0 ? thisMonthTotal / currentDay : 0;

    const trend =
      prevMonthTotal > 0
        ? ((thisMonthTotal - prevMonthTotal) / prevMonthTotal) * 100
        : 0;

    return {
      thisMonthTotal,
      prevMonthTotal,
      avgPerDay,
      sources: categorySet.size,
      trend,
    };
  }, [incomes, convertToUserCurrency]);

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

  const kpiCards = [
    {
      label: t("incomePage.kpi.thisMonth"),
      value: formatCurrency(stats.thisMonthTotal, userCurrency),
      trend: stats.trend,
    },
    {
      label: t("incomePage.kpi.prevMonth"),
      value: formatCurrency(stats.prevMonthTotal, userCurrency),
    },
    {
      label: t("incomePage.kpi.avgPerDay"),
      value: formatCurrency(stats.avgPerDay, userCurrency),
    },
    {
      label: t("incomePage.kpi.sources"),
      value: String(stats.sources),
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
            <div className="flex items-baseline gap-2 mt-1">
              <p className="text-xl font-mono font-semibold text-content">
                {card.value}
              </p>
              {card.trend !== undefined && card.trend !== 0 && (
                <span
                  className={`text-xs font-mono font-medium ${
                    card.trend > 0 ? "text-success-base" : "text-danger-base"
                  }`}
                >
                  {card.trend > 0 ? "+" : ""}
                  {card.trend.toFixed(1)}%
                </span>
              )}
            </div>
          </div>
        </Card>
      ))}
    </div>
  );
};
