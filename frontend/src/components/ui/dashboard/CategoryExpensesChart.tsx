import { Category, ExpenseResponse } from "@/types";
import {
  Cell,
  Legend,
  Pie,
  PieChart,
  ResponsiveContainer,
  Tooltip,
} from "recharts";
import React, { useMemo, useState, useEffect } from "react";
import { CHART_COLORS, CHART_TOOLTIP_STYLE } from "./chartColors";

interface CategoryExpensesChartProps {
  expenses: ExpenseResponse[];
  categories: Category[];
}

export const CategoryExpensesChart: React.FC<CategoryExpensesChartProps> = ({
  expenses,
  categories,
}) => {
  const [isMobile, setIsMobile] = useState(false);

  useEffect(() => {
    const mql = window.matchMedia("(max-width: 639px)");
    const handler = (e: MediaQueryListEvent | MediaQueryList) =>
      setIsMobile(e.matches);
    handler(mql);
    mql.addEventListener("change", handler);
    return () => mql.removeEventListener("change", handler);
  }, []);

  const expensesByCategory = useMemo(() => {
    return categories
      .map((cat) => {
        const categoryExpenses = expenses.filter(
          (exp) => exp.category_id === cat.id,
        );
        const total = categoryExpenses.reduce(
          (sum, exp) => sum + exp.amount,
          0,
        );

        return {
          name: cat.name,
          value: total,
        };
      })
      .filter((item) => item.value > 0);
  }, [expenses, categories]);

  return (
    <div className="bg-elevated p-4 rounded-lg theme-shadow border-[var(--border)] border overflow-hidden">
      <h2 className="text-lg font-semibold mb-4 text-content">
        Расходы по категориям
      </h2>
      <div className="h-[280px] sm:h-[300px] md:h-[320px]">
        <ResponsiveContainer width="100%" height="100%">
          <PieChart>
            <Pie
              data={expensesByCategory}
              dataKey="value"
              nameKey="name"
              cx="50%"
              cy={isMobile ? "40%" : "45%"}
              innerRadius={isMobile ? 40 : 60}
              outerRadius={isMobile ? 60 : 80}
            >
              {expensesByCategory.map((_, index) => (
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
              wrapperStyle={{
                color: "var(--text-primary)",
                fontSize: isMobile ? "10px" : "12px",
                lineHeight: "1.6",
                paddingTop: "4px",
                overflowWrap: "break-word" as const,
                wordBreak: "break-word" as const,
              }}
            />
          </PieChart>
        </ResponsiveContainer>
      </div>
    </div>
  );
};
