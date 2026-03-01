import React, { useMemo } from "react";
import { useTranslation } from "react-i18next";
import {
  CartesianGrid,
  Legend,
  Line,
  LineChart,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";
import { CHART_COLORS, CHART_TOOLTIP_STYLE } from "./chartColors";
import { ExpenseResponse, IncomeOut } from "@/types";
import { useCurrencyConversion } from "@/hooks/useCurrencyConversion";

interface CashFlowChartProps {
  expenses: ExpenseResponse[];
  incomes: IncomeOut[];
}

export const CashFlowChart: React.FC<CashFlowChartProps> = ({
  expenses,
  incomes,
}) => {
  const { t, i18n } = useTranslation();
  const { convertToUserCurrency } = useCurrencyConversion();

  const data = useMemo(() => {
    const last6Months = Array.from({ length: 6 }, (_, i) => {
      const date = new Date();
      date.setMonth(date.getMonth() - i);
      return date;
    }).reverse();

    return last6Months.map((date) => {
      const month = date.getMonth();
      const year = date.getFullYear();

      const monthExpenses = expenses
        .filter((e) => {
          const d = new Date(e.date);
          return d.getMonth() === month && d.getFullYear() === year;
        })
        .reduce(
          (sum, e) =>
            sum + (convertToUserCurrency(e.amount, e.currency) ?? e.amount),
          0,
        );

      const monthIncomes = incomes
        .filter((inc) => {
          const d = new Date(inc.date);
          return d.getMonth() === month && d.getFullYear() === year;
        })
        .reduce(
          (sum, inc) =>
            sum +
            (convertToUserCurrency(inc.amount, inc.currency) ?? inc.amount),
          0,
        );

      return {
        month: date.toLocaleDateString(i18n.language, { month: "short" }),
        income: Math.round(monthIncomes),
        expenses: Math.round(monthExpenses),
      };
    });
  }, [expenses, incomes, convertToUserCurrency, i18n.language]);

  return (
    <div className="theme-surface p-4 rounded-lg theme-shadow theme-border border">
      <h2 className="text-lg font-semibold mb-4 theme-text-primary">
        {t("dashboard.cashFlow.title")}
      </h2>
      <div className="h-[250px] md:h-[300px]">
        <ResponsiveContainer width="100%" height="100%">
          <LineChart data={data}>
            <CartesianGrid
              strokeDasharray="3 3"
              stroke="var(--color-border)"
              strokeOpacity={0.5}
            />
            <XAxis
              dataKey="month"
              tick={{ fill: "var(--color-text-primary)", fontSize: 12 }}
              axisLine={{ stroke: "var(--color-border)" }}
            />
            <YAxis
              tick={{ fill: "var(--color-text-primary)", fontSize: 12 }}
              axisLine={{ stroke: "var(--color-border)" }}
            />
            <Tooltip contentStyle={CHART_TOOLTIP_STYLE} />
            <Legend wrapperStyle={{ color: "var(--color-text-primary)" }} />
            <Line
              type="monotone"
              dataKey="income"
              name={t("dashboard.cashFlow.income")}
              stroke={CHART_COLORS[0]}
              strokeWidth={2}
              dot={{ r: 4 }}
              activeDot={{ r: 6 }}
            />
            <Line
              type="monotone"
              dataKey="expenses"
              name={t("dashboard.cashFlow.expenses")}
              stroke={CHART_COLORS[6]}
              strokeWidth={2}
              dot={{ r: 4 }}
              activeDot={{ r: 6 }}
            />
          </LineChart>
        </ResponsiveContainer>
      </div>
    </div>
  );
};
