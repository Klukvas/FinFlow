import {
  Bar,
  BarChart,
  CartesianGrid,
  Legend,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";
import { Category, ExpenseResponse } from "@/types";
import React, { useMemo } from "react";
import { useTranslation } from "react-i18next";
import { BarChart3 } from "lucide-react";
import { CHART_COLORS, CHART_TOOLTIP_STYLE } from "./chartColors";
import { useCurrencyConversion } from "@/hooks/useCurrencyConversion";
import { getPeriodBoundaries } from "@/utils/periodUtils";

interface TopExpensesChartProps {
  expenses: ExpenseResponse[];
  categories: Category[];
  periodMonths?: number;
}

export const TopExpensesChart: React.FC<TopExpensesChartProps> = ({
  expenses,
  categories,
  periodMonths = 1,
}) => {
  const { t } = useTranslation();
  const { convertToUserCurrency, formatCurrency, userCurrency } =
    useCurrencyConversion();

  const topExpenses = useMemo(() => {
    const { periodStart } = getPeriodBoundaries(periodMonths);
    const results: Record<string, number> = {};

    for (const exp of expenses) {
      if (!exp.date || new Date(exp.date) < periodStart) continue;
      const category = categories.find((cat) => cat.id === exp.category_id);
      if (category?.name) {
        const converted =
          convertToUserCurrency(exp.amount, exp.currency ?? "") ?? exp.amount;
        results[category.name] = (results[category.name] ?? 0) + converted;
      }
    }

    return Object.entries(results)
      .sort((a, b) => b[1] - a[1])
      .slice(0, 5)
      .map(([name, amount]) => ({
        name,
        amount: Math.round(amount * 100) / 100,
      }));
  }, [expenses, categories, convertToUserCurrency, periodMonths]);

  const tooltipFormatter = (value: number) =>
    formatCurrency(value, userCurrency);

  if (topExpenses.length === 0) {
    return (
      <div className="bg-elevated p-4 rounded-lg theme-shadow border-[var(--border)] border">
        <h2 className="text-lg font-semibold mb-4 text-content">
          {t("dashboard.topSpending.title")}
        </h2>
        <div className="text-center py-8">
          <BarChart3 className="w-8 h-8 text-content-tertiary mx-auto mb-2" />
          <p className="text-sm text-content-secondary">
            {t("dashboard.noData")}
          </p>
        </div>
      </div>
    );
  }

  return (
    <div className="bg-elevated p-4 rounded-lg theme-shadow border-[var(--border)] border overflow-hidden">
      <h2 className="text-lg font-semibold mb-4 text-content">
        {t("dashboard.topSpending.title")}
      </h2>
      <div className="h-[280px] md:h-[320px]">
        <ResponsiveContainer width="100%" height="100%">
          <BarChart
            data={topExpenses}
            margin={{ left: -10, right: 8, top: 5, bottom: 5 }}
          >
            <CartesianGrid
              strokeDasharray="3 3"
              stroke="var(--border)"
              strokeOpacity={0.5}
            />
            <XAxis
              dataKey="name"
              angle={-35}
              textAnchor="end"
              height={70}
              tick={{ fill: "var(--text-primary)", fontSize: 10 }}
              axisLine={{ stroke: "var(--border)" }}
              interval={0}
            />
            <YAxis
              tick={{ fill: "var(--text-primary)", fontSize: 10 }}
              axisLine={{ stroke: "var(--border)" }}
              width={45}
              tickFormatter={(v: number) =>
                v >= 1000 ? `${(v / 1000).toFixed(0)}k` : String(v)
              }
            />
            <Tooltip
              contentStyle={CHART_TOOLTIP_STYLE}
              formatter={tooltipFormatter}
            />
            <Legend
              wrapperStyle={{ color: "var(--text-primary)", fontSize: "12px" }}
            />
            <Bar
              dataKey="amount"
              name={t("dashboard.topSpending.amount")}
              fill={CHART_COLORS[0]}
              radius={[4, 4, 0, 0]}
            />
          </BarChart>
        </ResponsiveContainer>
      </div>
    </div>
  );
};
