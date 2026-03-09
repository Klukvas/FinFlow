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
import React, { useMemo } from "react";
import { useTranslation } from "react-i18next";
import { CHART_COLORS, CHART_TOOLTIP_STYLE } from "./chartColors";
import { ExpenseResponse, IncomeOut } from "@/types";
import { useCurrencyConversion } from "@/hooks/useCurrencyConversion";
import { getPeriodBoundaries } from "@/utils/periodUtils";

interface MonthComparisonChartProps {
 expenses: ExpenseResponse[];
 incomes: IncomeOut[];
 periodMonths?: number;
}

export const MonthComparisonChart: React.FC<MonthComparisonChartProps> = ({
 expenses,
 incomes,
 periodMonths = 1,
}) => {
 const { t } = useTranslation();
 const { convertToUserCurrency, formatCurrency, userCurrency } =
 useCurrencyConversion();

 const data = useMemo(() => {
 const { periodStart, prevPeriodStart } = getPeriodBoundaries(periodMonths);

 let curExp = 0;
 let prevExp = 0;
 let curInc = 0;
 let prevInc = 0;

 for (const exp of expenses) {
 if (!exp.date) continue;
 const d = new Date(exp.date);
 const converted =
 convertToUserCurrency(exp.amount, exp.currency ?? "") ?? exp.amount;
 if (d >= periodStart) {
 curExp += converted;
 } else if (d >= prevPeriodStart) {
 prevExp += converted;
 }
 }

 for (const inc of incomes) {
 const d = new Date(inc.date);
 const converted =
 convertToUserCurrency(inc.amount, inc.currency ?? "") ?? inc.amount;
 if (d >= periodStart) {
 curInc += converted;
 } else if (d >= prevPeriodStart) {
 prevInc += converted;
 }
 }

 return [
 {
 name: t("dashboard.monthComparison.current"),
 income: Math.round(curInc * 100) / 100,
 expenses: Math.round(curExp * 100) / 100,
 },
 {
 name: t("dashboard.monthComparison.previous"),
 income: Math.round(prevInc * 100) / 100,
 expenses: Math.round(prevExp * 100) / 100,
 },
 ];
 }, [expenses, incomes, convertToUserCurrency, t, periodMonths]);

 const tooltipFormatter = (value: number) =>
 formatCurrency(value, userCurrency);

 return (
 <div className="bg-elevated p-4 rounded-lg theme-shadow border-[var(--color-border)] border">
 <h2 className="text-lg font-semibold mb-4 text-content">
 {t("dashboard.monthComparison.title")}
 </h2>
 <div className="h-[250px] md:h-[300px]">
 <ResponsiveContainer width="100%" height="100%">
 <BarChart data={data}>
 <CartesianGrid strokeDasharray="3 3" stroke="var(--color-border)" />
 <XAxis
 dataKey="name"
 tick={{ fill: "var(--color-text)" }}
 axisLine={{ stroke: "var(--color-border)" }}
 />
 <YAxis
 tick={{ fill: "var(--color-text)" }}
 axisLine={{ stroke: "var(--color-border)" }}
 />
 <Tooltip
 contentStyle={CHART_TOOLTIP_STYLE}
 formatter={tooltipFormatter}
 />
 <Legend wrapperStyle={{ color: "var(--color-text)" }} />
 <Bar
 dataKey="income"
 name={t("dashboard.monthComparison.income")}
 fill={CHART_COLORS[4]}
 radius={[4, 4, 0, 0]}
 />
 <Bar
 dataKey="expenses"
 name={t("dashboard.monthComparison.expenses")}
 fill={CHART_COLORS[6]}
 radius={[4, 4, 0, 0]}
 />
 </BarChart>
 </ResponsiveContainer>
 </div>
 </div>
 );
};
