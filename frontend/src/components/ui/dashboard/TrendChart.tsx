import {
  CartesianGrid,
  Legend,
  Line,
  LineChart,
  ReferenceLine,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";
import React, { useMemo } from "react";
import { CHART_COLORS, CHART_TOOLTIP_STYLE } from "./chartColors";

import { ExpenseResponse } from "@/types";

interface TrendChartProps {
  expenses: ExpenseResponse[];
}

export const TrendChart: React.FC<TrendChartProps> = ({ expenses }) => {
  const trendData = useMemo(() => {
    const last6Months = Array.from({ length: 6 }, (_, i) => {
      const date = new Date();
      date.setMonth(date.getMonth() - i);
      return date;
    }).reverse();

    return last6Months.map((date) => {
      const monthExpenses = expenses.filter((exp) => {
        if (!exp.date) return false;
        const expDate = new Date(exp.date);
        return (
          expDate.getMonth() === date.getMonth() &&
          expDate.getFullYear() === date.getFullYear()
        );
      });
      const total = monthExpenses.reduce((sum, exp) => sum + exp.amount, 0);
      return {
        month: date.toLocaleDateString("uk-UA", { month: "long" }),
        amount: total,
      };
    });
  }, [expenses]);

  const averageAmount = useMemo(() => {
    return (
      trendData.reduce((sum, item) => sum + item.amount, 0) / trendData.length
    );
  }, [trendData]);

  return (
    <div className="bg-elevated p-4 rounded-lg theme-shadow border-[var(--border)] border overflow-hidden">
      <h2 className="text-lg font-semibold mb-4 text-content">
        Тренд расходов за 6 месяцев
      </h2>
      <div className="h-[250px] md:h-[300px]">
        <ResponsiveContainer width="100%" height="100%">
          <LineChart
            data={trendData}
            margin={{ left: -10, right: 8, top: 5, bottom: 5 }}
          >
            <CartesianGrid
              strokeDasharray="3 3"
              stroke="var(--border)"
              strokeOpacity={0.5}
            />
            <XAxis
              dataKey="month"
              tick={{ fill: "var(--text-primary)", fontSize: 11 }}
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
              dataKey="amount"
              name="Сумма"
              stroke={CHART_COLORS[0]}
              strokeWidth={2}
              dot={{ r: 3 }}
              activeDot={{ r: 5 }}
            />
            <ReferenceLine
              y={averageAmount}
              stroke="var(--text-tertiary)"
              strokeDasharray="3 3"
            />
          </LineChart>
        </ResponsiveContainer>
      </div>
    </div>
  );
};
