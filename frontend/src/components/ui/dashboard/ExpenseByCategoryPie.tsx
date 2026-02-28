import React, { useMemo } from "react";
import { useTranslation } from "react-i18next";
import {
  Cell,
  Legend,
  Pie,
  PieChart,
  ResponsiveContainer,
  Tooltip,
} from "recharts";
import { CHART_COLORS, CHART_TOOLTIP_STYLE } from "./chartColors";
import { ExpenseResponse, Category } from "@/types";
import { useCurrencyConversion } from "@/hooks/useCurrencyConversion";

interface ExpenseByCategoryPieProps {
  expenses: ExpenseResponse[];
  categories: Category[];
}

export const ExpenseByCategoryPie: React.FC<ExpenseByCategoryPieProps> = ({
  expenses,
  categories,
}) => {
  const { t } = useTranslation();
  const { convertToUserCurrency } = useCurrencyConversion();

  const data = useMemo(() => {
    const now = new Date();
    const thisMonth = now.getMonth();
    const thisYear = now.getFullYear();

    const currentMonthExpenses = expenses.filter((e) => {
      const d = new Date(e.date);
      return d.getMonth() === thisMonth && d.getFullYear() === thisYear;
    });

    return categories
      .map((cat) => {
        const total = currentMonthExpenses
          .filter((e) => e.category_id === cat.id)
          .reduce(
            (sum, e) =>
              sum + (convertToUserCurrency(e.amount, e.currency) ?? e.amount),
            0,
          );
        return { name: cat.name, value: total };
      })
      .filter((item) => item.value > 0);
  }, [expenses, categories, convertToUserCurrency]);

  if (data.length === 0) {
    return (
      <div className="theme-surface p-4 rounded-lg theme-shadow theme-border border">
        <h2 className="text-lg font-semibold mb-4 theme-text-primary">
          {t("dashboard.expensesByCategory")}
        </h2>
        <div className="h-[300px] flex items-center justify-center">
          <p className="theme-text-tertiary">{t("dashboard.noData")}</p>
        </div>
      </div>
    );
  }

  return (
    <div className="theme-surface p-4 rounded-lg theme-shadow theme-border border">
      <h2 className="text-lg font-semibold mb-4 theme-text-primary">
        {t("dashboard.expensesByCategory")}
      </h2>
      <div className="h-[300px]">
        <ResponsiveContainer width="100%" height="100%">
          <PieChart>
            <Pie
              data={data}
              dataKey="value"
              nameKey="name"
              cx="50%"
              cy="50%"
              innerRadius={60}
              outerRadius={80}
            >
              {data.map((_, index) => (
                <Cell
                  key={`cell-${index}`}
                  fill={CHART_COLORS[index % CHART_COLORS.length]}
                />
              ))}
            </Pie>
            <Tooltip contentStyle={CHART_TOOLTIP_STYLE} />
            <Legend
              layout="horizontal"
              verticalAlign="bottom"
              wrapperStyle={{ color: "var(--color-text-primary)" }}
            />
          </PieChart>
        </ResponsiveContainer>
      </div>
    </div>
  );
};
