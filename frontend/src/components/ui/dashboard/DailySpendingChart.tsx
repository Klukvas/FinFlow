import React, { useMemo } from "react";
import { useTranslation } from "react-i18next";
import {
  Area,
  AreaChart,
  CartesianGrid,
  ReferenceLine,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
  Legend,
} from "recharts";
import { CHART_COLORS, CHART_TOOLTIP_STYLE } from "./chartColors";
import { ExpenseResponse } from "@/types";
import { useCurrencyConversion } from "@/hooks/useCurrencyConversion";
import { TrendingUp } from "lucide-react";

interface DailySpendingChartProps {
  expenses: ExpenseResponse[];
  periodMonths?: number;
}

export const DailySpendingChart: React.FC<DailySpendingChartProps> = ({
  expenses,
  periodMonths = 1,
}) => {
  const { t } = useTranslation();
  const { convertToUserCurrency, formatCurrency, userCurrency } =
    useCurrencyConversion();

  const data = useMemo(() => {
    if (periodMonths > 1) return [];

    const now = new Date();
    const curMonth = now.getMonth();
    const curYear = now.getFullYear();
    const prevMonth = curMonth === 0 ? 11 : curMonth - 1;
    const prevYear = curMonth === 0 ? curYear - 1 : curYear;

    const daysInMonth = new Date(curYear, curMonth + 1, 0).getDate();
    const daysInPrevMonth = new Date(prevYear, prevMonth + 1, 0).getDate();
    const maxDays = Math.max(daysInMonth, daysInPrevMonth);

    const curDaily: number[] = new Array(maxDays).fill(0);
    const prevDaily: number[] = new Array(maxDays).fill(0);

    for (const exp of expenses) {
      if (!exp.date) continue;
      const d = new Date(exp.date);
      const converted =
        convertToUserCurrency(exp.amount, exp.currency ?? "") ?? exp.amount;
      const day = d.getDate() - 1;

      if (
        day >= 0 &&
        day < maxDays &&
        d.getMonth() === curMonth &&
        d.getFullYear() === curYear
      ) {
        curDaily[day] = (curDaily[day] ?? 0) + converted;
      } else if (
        day >= 0 &&
        day < maxDays &&
        d.getMonth() === prevMonth &&
        d.getFullYear() === prevYear
      ) {
        prevDaily[day] = (prevDaily[day] ?? 0) + converted;
      }
    }

    const today = now.getDate();
    let curCum = 0;
    let prevCum = 0;

    return Array.from({ length: maxDays }, (_, i) => {
      curCum += curDaily[i] ?? 0;
      prevCum += prevDaily[i] ?? 0;
      return {
        day: i + 1,
        current: i < today ? Math.round(curCum * 100) / 100 : null,
        previous: Math.round(prevCum * 100) / 100,
      };
    });
  }, [expenses, convertToUserCurrency, periodMonths]);

  const tooltipFormatter = (value: number) =>
    formatCurrency(value, userCurrency);

  if (periodMonths > 1) {
    return (
      <div className="bg-elevated p-4 rounded-lg theme-shadow border-[var(--border)] border">
        <h2 className="text-lg font-semibold mb-4 text-content">
          {t("dashboard.dailySpending.title")}
        </h2>
        <div className="text-center py-8">
          <TrendingUp className="w-8 h-8 text-content-tertiary mx-auto mb-2" />
          <p className="text-sm text-content-secondary">
            {t("dashboard.dailySpending.multiMonthHint")}
          </p>
        </div>
      </div>
    );
  }

  const today = new Date().getDate();

  return (
    <div className="bg-elevated p-4 rounded-lg theme-shadow border-[var(--border)] border overflow-hidden">
      <h2 className="text-lg font-semibold mb-4 text-content">
        {t("dashboard.dailySpending.title")}
      </h2>
      <div className="h-[250px] md:h-[300px]">
        <ResponsiveContainer width="100%" height="100%">
          <AreaChart
            data={data}
            margin={{ left: -10, right: 8, top: 5, bottom: 5 }}
          >
            <CartesianGrid strokeDasharray="3 3" stroke="var(--border)" />
            <XAxis
              dataKey="day"
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
            <Tooltip
              contentStyle={CHART_TOOLTIP_STYLE}
              formatter={tooltipFormatter}
            />
            <Legend
              wrapperStyle={{ color: "var(--text-primary)", fontSize: "12px" }}
            />
            <ReferenceLine
              x={today}
              stroke="var(--text-secondary)"
              strokeDasharray="3 3"
              label={{
                value: t("dashboard.dailySpending.today"),
                position: "top",
                fill: "var(--text-secondary)",
                fontSize: 11,
              }}
            />
            <Area
              type="monotone"
              dataKey="current"
              name={t("dashboard.dailySpending.currentMonth")}
              stroke={CHART_COLORS[0]}
              fill={CHART_COLORS[0]}
              fillOpacity={0.15}
              strokeWidth={2}
            />
            <Area
              type="monotone"
              dataKey="previous"
              name={t("dashboard.dailySpending.previousMonth")}
              stroke={CHART_COLORS[7]}
              fill="none"
              strokeDasharray="5 5"
              strokeWidth={1.5}
            />
          </AreaChart>
        </ResponsiveContainer>
      </div>
    </div>
  );
};
