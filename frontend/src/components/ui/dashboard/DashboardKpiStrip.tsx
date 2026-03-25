import React, { useMemo } from "react";
import { useTranslation } from "react-i18next";
import { Skeleton } from "../shared/Skeleton";
import { ExpenseResponse, IncomeOut, AccountSummary } from "@/types";
import { useCurrencyConversion } from "@/hooks/useCurrencyConversion";
import { getPeriodBoundaries } from "@/utils/periodUtils";

interface DashboardKpiStripProps {
  expenses: ExpenseResponse[];
  incomes: IncomeOut[];
  accounts: AccountSummary[];
  periodMonths: number;
  loading: boolean;
}

export const DashboardKpiStrip: React.FC<DashboardKpiStripProps> = ({
  expenses,
  incomes,
  accounts,
  periodMonths,
  loading,
}) => {
  const { t } = useTranslation();
  const { formatCurrency, convertToUserCurrency, userCurrency } =
    useCurrencyConversion();

  const stats = useMemo(() => {
    const { periodStart, prevPeriodStart } = getPeriodBoundaries(periodMonths);

    let curExpenses = 0;
    let prevExpenses = 0;
    let curIncome = 0;
    let prevIncome = 0;

    for (const exp of expenses) {
      if (!exp.date) continue;
      const d = new Date(exp.date);
      const converted =
        convertToUserCurrency(exp.amount, exp.currency ?? "") ?? exp.amount;
      if (d >= periodStart) {
        curExpenses += converted;
      } else if (d >= prevPeriodStart) {
        prevExpenses += converted;
      }
    }

    for (const inc of incomes) {
      const d = new Date(inc.date);
      const converted =
        convertToUserCurrency(inc.amount, inc.currency ?? "") ?? inc.amount;
      if (d >= periodStart) {
        curIncome += converted;
      } else if (d >= prevPeriodStart) {
        prevIncome += converted;
      }
    }

    const totalBalance = accounts.reduce((sum, acc) => {
      const converted =
        convertToUserCurrency(acc.balance, acc.currency) ?? acc.balance;
      return sum + converted;
    }, 0);

    const incomeTrend =
      prevIncome > 0 ? ((curIncome - prevIncome) / prevIncome) * 100 : 0;
    const expenseTrend =
      prevExpenses > 0
        ? ((curExpenses - prevExpenses) / prevExpenses) * 100
        : 0;
    const netCashFlow = curIncome - curExpenses;
    const savingsRate =
      curIncome > 0 ? ((curIncome - curExpenses) / curIncome) * 100 : null;
    const prevSavingsRate =
      prevIncome > 0 ? ((prevIncome - prevExpenses) / prevIncome) * 100 : null;
    const savingsRateTrend =
      savingsRate !== null && prevSavingsRate !== null
        ? savingsRate - prevSavingsRate
        : 0;

    return {
      curIncome,
      curExpenses,
      netCashFlow,
      totalBalance,
      incomeTrend,
      expenseTrend,
      savingsRate,
      savingsRateTrend,
    };
  }, [expenses, incomes, accounts, convertToUserCurrency, periodMonths]);

  if (loading) {
    return (
      <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-5 gap-3">
        {Array.from({ length: 5 }).map((_, i) => (
          <div
            key={i}
            className="bg-[var(--bg-surface)] border border-[var(--border)] rounded-[var(--radius-lg)] p-5"
          >
            <Skeleton variant="text" className="h-3 w-20 mb-2" />
            <Skeleton variant="text" className="h-6 w-24" />
          </div>
        ))}
      </div>
    );
  }

  const kpiCards = [
    {
      id: "income",
      label: t("dashboard.kpi.totalIncome"),
      value: formatCurrency(stats.curIncome, userCurrency),
      trend: stats.incomeTrend,
      trendPositiveIsGood: true,
      valueColor: "text-[var(--success)]",
    },
    {
      id: "expenses",
      label: t("dashboard.kpi.totalExpenses"),
      value: formatCurrency(stats.curExpenses, userCurrency),
      trend: stats.expenseTrend,
      trendPositiveIsGood: false,
      valueColor: "text-[var(--danger)]",
    },
    {
      id: "cashFlow",
      label: t("dashboard.kpi.netCashFlow"),
      value: formatCurrency(stats.netCashFlow, userCurrency),
      valueColor:
        stats.netCashFlow >= 0
          ? "text-[var(--success)]"
          : "text-[var(--danger)]",
    },
    {
      id: "balance",
      label: t("dashboard.kpi.totalBalance"),
      value: formatCurrency(stats.totalBalance, userCurrency),
    },
    {
      id: "savingsRate",
      label: t("dashboard.kpi.savingsRate"),
      value:
        stats.savingsRate !== null
          ? `${stats.savingsRate.toFixed(1)}%`
          : "\u2014",
      trend: stats.savingsRateTrend,
      trendPositiveIsGood: true,
      valueColor:
        stats.savingsRate !== null
          ? stats.savingsRate >= 0
            ? "text-[var(--success)]"
            : "text-[var(--danger)]"
          : undefined,
    },
  ];

  return (
    <div
      className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-5 gap-3"
      data-testid="dashboard-kpi-strip"
    >
      {kpiCards.map((card) => (
        <div
          key={card.id}
          data-testid={`dashboard-kpi-${card.id}`}
          className="relative overflow-hidden bg-[var(--bg-surface)] border border-[var(--border)] rounded-[var(--radius-lg)] p-3 sm:p-4 md:p-5 transition-[border-color] duration-150 hover:border-[var(--border-hover)] group min-w-0"
        >
          {/* Accent top line on hover */}
          <span className="absolute top-0 left-0 right-0 h-[2px] bg-[var(--accent)] opacity-0 group-hover:opacity-100 transition-opacity duration-200" />

          <p className="text-xs font-medium text-[var(--text-secondary)] mb-2">
            {card.label}
          </p>
          <div className="flex items-baseline gap-2 min-w-0">
            <p
              className={`font-mono text-base sm:text-lg md:text-2xl font-bold tracking-[-0.02em] leading-tight truncate ${card.valueColor ?? "text-[var(--text-primary)]"}`}
            >
              {card.value}
            </p>
            {card.trend !== undefined && card.trend !== 0 && (
              <span
                className={`font-mono text-[11px] flex items-center gap-1 ${
                  card.trendPositiveIsGood
                    ? card.trend > 0
                      ? "text-[var(--success)]"
                      : "text-[var(--danger)]"
                    : card.trend > 0
                      ? "text-[var(--danger)]"
                      : "text-[var(--success)]"
                }`}
              >
                {card.trend > 0 ? "\u2191" : "\u2193"}
                {Math.abs(card.trend).toFixed(1)}%
              </span>
            )}
          </div>
        </div>
      ))}
    </div>
  );
};
