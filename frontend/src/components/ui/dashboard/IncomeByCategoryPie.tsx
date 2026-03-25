import React, { useMemo, useState, useEffect } from "react";
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
import { IncomeOut, Category } from "@/types";
import { useCurrencyConversion } from "@/hooks/useCurrencyConversion";
import { getPeriodBoundaries } from "@/utils/periodUtils";

interface IncomeByCategoryPieProps {
  incomes: IncomeOut[];
  categories: Category[];
  periodMonths?: number;
}

export const IncomeByCategoryPie: React.FC<IncomeByCategoryPieProps> = ({
  incomes,
  categories,
  periodMonths = 1,
}) => {
  const { t } = useTranslation();
  const { convertToUserCurrency } = useCurrencyConversion();

  const [isMobile, setIsMobile] = useState(false);

  useEffect(() => {
    const mql = window.matchMedia("(max-width: 639px)");
    const handler = (e: MediaQueryListEvent | MediaQueryList) =>
      setIsMobile(e.matches);
    handler(mql);
    mql.addEventListener("change", handler);
    return () => mql.removeEventListener("change", handler);
  }, []);

  const data = useMemo(() => {
    const { periodStart } = getPeriodBoundaries(periodMonths);

    return categories
      .map((cat) => {
        const total = incomes
          .filter(
            (inc) =>
              inc.category_id === cat.id && new Date(inc.date) >= periodStart,
          )
          .reduce(
            (sum, inc) =>
              sum +
              (convertToUserCurrency(inc.amount, inc.currency ?? "") ??
                inc.amount),
            0,
          );
        return { name: cat.name, value: total };
      })
      .filter((item) => item.value > 0);
  }, [incomes, categories, convertToUserCurrency, periodMonths]);

  if (data.length === 0) {
    return (
      <div
        className="bg-elevated p-4 rounded-lg theme-shadow border-[var(--border)] border"
        data-testid="dashboard-income-category-chart"
      >
        <h2 className="text-lg font-semibold mb-4 text-content">
          {t("dashboard.incomeByCategory")}
        </h2>
        <div className="h-[300px] flex items-center justify-center">
          <p className="text-content-tertiary">{t("dashboard.noData")}</p>
        </div>
      </div>
    );
  }

  return (
    <div
      className="bg-elevated p-4 rounded-lg theme-shadow border-[var(--border)] border overflow-hidden"
      data-testid="dashboard-income-category-chart"
    >
      <h2 className="text-lg font-semibold mb-4 text-content">
        {t("dashboard.incomeByCategory")}
      </h2>
      <div className="h-[280px] sm:h-[300px] md:h-[320px]">
        <ResponsiveContainer width="100%" height="100%">
          <PieChart>
            <Pie
              data={data}
              dataKey="value"
              nameKey="name"
              cx="50%"
              cy={isMobile ? "40%" : "45%"}
              innerRadius={isMobile ? 40 : 60}
              outerRadius={isMobile ? 60 : 80}
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
