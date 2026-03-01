import React, { useMemo } from "react";
import { useTranslation } from "react-i18next";
import { Card } from "../shared/Card";
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
      const d = new Date(exp.date);
      const converted =
        convertToUserCurrency(exp.amount, exp.currency) ?? exp.amount;
      if (d >= periodStart) {
        curExpenses += converted;
      } else if (d >= prevPeriodStart) {
        prevExpenses += converted;
      }
    }

    for (const inc of incomes) {
      const d = new Date(inc.date);
      const converted =
        convertToUserCurrency(inc.amount, inc.currency) ?? inc.amount;
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
      id: "income",
      label: t("dashboard.kpi.totalIncome"),
      value: formatCurrency(stats.curIncome, userCurrency),
      trend: stats.incomeTrend,
      trendPositiveIsGood: true,
    },
    {
      id: "expenses",
      label: t("dashboard.kpi.totalExpenses"),
      value: formatCurrency(stats.curExpenses, userCurrency),
      trend: stats.expenseTrend,
      trendPositiveIsGood: false,
    },
    {
      id: "cashFlow",
      label: t("dashboard.kpi.netCashFlow"),
      value: formatCurrency(stats.netCashFlow, userCurrency),
      color: stats.netCashFlow >= 0 ? "text-green-500" : "text-red-500",
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
        stats.savingsRate !== null ? `${stats.savingsRate.toFixed(1)}%` : "—",
      trend: stats.savingsRateTrend,
      trendPositiveIsGood: true,
      color:
        stats.savingsRate !== null
          ? stats.savingsRate >= 0
            ? "text-green-500"
            : "text-red-500"
          : undefined,
    },
  ];

  return (
    <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-5 gap-3">
      {kpiCards.map((card) => (
        <Card key={card.id}>
          <div className="p-4">
            <p className="text-xs font-medium theme-text-secondary uppercase tracking-wide">
              {card.label}
            </p>
            <div className="flex items-baseline gap-2 mt-1">
              <p
                className={`text-xl font-semibold ${card.color ?? "theme-text-primary"}`}
              >
                {card.value}
              </p>
              {card.trend !== undefined && card.trend !== 0 && (
                <span
                  className={`text-xs font-medium ${
                    card.trendPositiveIsGood
                      ? card.trend > 0
                        ? "text-green-500"
                        : "text-red-500"
                      : card.trend > 0
                        ? "text-red-500"
                        : "text-green-500"
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
