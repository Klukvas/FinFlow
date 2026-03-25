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
import React, { useMemo } from "react";
import { CHART_COLORS, CHART_TOOLTIP_STYLE } from "./chartColors";

import { ExpenseResponse } from "@/types";

interface WeekdayExpensesChartProps {
  expenses: ExpenseResponse[];
}

export const WeekdayExpensesChart: React.FC<WeekdayExpensesChartProps> = ({
  expenses,
}) => {
  const weekdayData = useMemo(() => {
    const weekdayExpenses = expenses.reduce(
      (acc, exp) => {
        if (!exp.date) return acc;
        const date = new Date(exp.date);
        const weekday = date.toLocaleDateString("uk-UA", { weekday: "long" });
        if (!acc[weekday]) {
          acc[weekday] = { total: 0, count: 0 };
        }
        acc[weekday].total += exp.amount;
        acc[weekday].count += 1;
        return acc;
      },
      {} as Record<string, { total: number; count: number }>,
    );

    return Object.entries(weekdayExpenses).map(([weekday, data]) => ({
      weekday,
      average: data.total / data.count,
    }));
  }, [expenses]);

  return (
    <div className="bg-elevated p-4 rounded-lg theme-shadow border-[var(--border)] border overflow-hidden">
      <h2 className="text-lg font-semibold mb-4 text-content">
        Средние расходы по дням недели
      </h2>
      <div className="h-[250px] md:h-[300px]">
        <ResponsiveContainer width="100%" height="100%">
          <LineChart
            data={weekdayData}
            margin={{ left: -10, right: 8, top: 5, bottom: 5 }}
          >
            <CartesianGrid strokeDasharray="3 3" stroke="var(--border)" />
            <XAxis
              dataKey="weekday"
              tick={{ fill: "var(--text-primary)", fontSize: 10 }}
              axisLine={{ stroke: "var(--border)" }}
            />
            <YAxis
              tick={{ fill: "var(--text-primary)", fontSize: 10 }}
              axisLine={{ stroke: "var(--border)" }}
              width={45}
              tickFormatter={(v: number) =>
                v >= 1000 ? `${(v / 1000).toFixed(0)}k` : String(v)
              }
            />
            <Tooltip contentStyle={CHART_TOOLTIP_STYLE} />
            <Legend
              wrapperStyle={{ color: "var(--text-primary)", fontSize: "12px" }}
            />
            <Line
              type="monotone"
              dataKey="average"
              name="Средняя сумма"
              stroke={CHART_COLORS[1]}
              strokeWidth={2}
              dot={{ r: 3 }}
              activeDot={{ r: 5 }}
            />
          </LineChart>
        </ResponsiveContainer>
      </div>
    </div>
  );
};
