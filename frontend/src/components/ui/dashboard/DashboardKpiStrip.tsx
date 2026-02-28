import React, { useMemo } from "react";
import { useTranslation } from "react-i18next";
import { Card } from "../shared/Card";
import { Skeleton } from "../shared/Skeleton";
import { ExpenseResponse, IncomeOut, AccountSummary } from "@/types";
import { useCurrencyConversion } from "@/hooks/useCurrencyConversion";

interface DashboardKpiStripProps {
  expenses: ExpenseResponse[];
  incomes: IncomeOut[];
  accounts: AccountSummary[];
  loading: boolean;
}

export const DashboardKpiStrip: React.FC<DashboardKpiStripProps> = ({
  expenses,
  incomes,
  accounts,
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

    let thisMonthExpenses = 0;
    let prevMonthExpenses = 0;
    let thisMonthIncome = 0;
    let prevMonthIncome = 0;

    for (const exp of expenses) {
      const d = new Date(exp.date);
      const converted =
        convertToUserCurrency(exp.amount, exp.currency) ?? exp.amount;
      if (d.getMonth() === thisMonth && d.getFullYear() === thisYear) {
        thisMonthExpenses += converted;
      } else if (d.getMonth() === prevMonth && d.getFullYear() === prevYear) {
        prevMonthExpenses += converted;
      }
    }

    for (const inc of incomes) {
      const d = new Date(inc.date);
      const converted =
        convertToUserCurrency(inc.amount, inc.currency) ?? inc.amount;
      if (d.getMonth() === thisMonth && d.getFullYear() === thisYear) {
        thisMonthIncome += converted;
      } else if (d.getMonth() === prevMonth && d.getFullYear() === prevYear) {
        prevMonthIncome += converted;
      }
    }

    const totalBalance = accounts.reduce((sum, acc) => {
      const converted =
        convertToUserCurrency(acc.balance, acc.currency) ?? acc.balance;
      return sum + converted;
    }, 0);

    const incomeTrend =
      prevMonthIncome > 0
        ? ((thisMonthIncome - prevMonthIncome) / prevMonthIncome) * 100
        : 0;

    const expenseTrend =
      prevMonthExpenses > 0
        ? ((thisMonthExpenses - prevMonthExpenses) / prevMonthExpenses) * 100
        : 0;

    const netCashFlow = thisMonthIncome - thisMonthExpenses;

    return {
      thisMonthIncome,
      thisMonthExpenses,
      netCashFlow,
      totalBalance,
      incomeTrend,
      expenseTrend,
    };
  }, [expenses, incomes, accounts, convertToUserCurrency]);

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
      label: t("dashboard.kpi.totalIncome"),
      value: formatCurrency(stats.thisMonthIncome, userCurrency),
      trend: stats.incomeTrend,
      trendPositiveIsGood: true,
    },
    {
      label: t("dashboard.kpi.totalExpenses"),
      value: formatCurrency(stats.thisMonthExpenses, userCurrency),
      trend: stats.expenseTrend,
      trendPositiveIsGood: false,
    },
    {
      label: t("dashboard.kpi.netCashFlow"),
      value: formatCurrency(stats.netCashFlow, userCurrency),
      color: stats.netCashFlow >= 0 ? "text-green-500" : "text-red-500",
    },
    {
      label: t("dashboard.kpi.totalBalance"),
      value: formatCurrency(stats.totalBalance, userCurrency),
    },
  ];

  return (
    <div className="grid grid-cols-2 lg:grid-cols-4 gap-3">
      {kpiCards.map((card) => (
        <Card key={card.label}>
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
