import React, { useMemo } from "react";
import { useTranslation } from "react-i18next";
import { Link } from "react-router-dom";
import { PieChart, ArrowRight } from "lucide-react";
import { Category, ExpenseResponse } from "@/types";
import { useCurrencyConversion } from "@/hooks/useCurrencyConversion";
import { getPeriodBoundaries } from "@/utils/periodUtils";

interface BudgetProgressWidgetProps {
  expenses: ExpenseResponse[];
  categories: Category[];
  periodMonths?: number;
}

interface BudgetItem {
  categoryId: number;
  categoryName: string;
  budget: number;
  spent: number;
  percentage: number;
}

const getProgressColor = (percentage: number): string => {
  if (percentage > 100) return "bg-red-500";
  if (percentage > 80) return "bg-orange-500";
  if (percentage > 60) return "bg-yellow-500";
  return "bg-green-500";
};

export const BudgetProgressWidget: React.FC<BudgetProgressWidgetProps> = ({
  expenses,
  categories,
  periodMonths = 1,
}) => {
  const { t } = useTranslation();
  const { convertToUserCurrency, formatCurrency, userCurrency } =
    useCurrencyConversion();

  const budgetItems = useMemo(() => {
    const categoriesWithBudget = categories.filter(
      (c) => c.monthly_budget && c.monthly_budget > 0,
    );

    if (categoriesWithBudget.length === 0) return [];

    const { periodStart } = getPeriodBoundaries(periodMonths);

    const spentByCategory = new Map<number, number>();
    for (const exp of expenses) {
      if (!exp.date || new Date(exp.date) < periodStart) continue;
      const converted =
        convertToUserCurrency(exp.amount, exp.currency ?? "") ?? exp.amount;
      const catId = exp.category_id ?? 0;
      spentByCategory.set(catId, (spentByCategory.get(catId) ?? 0) + converted);
    }

    const items: BudgetItem[] = categoriesWithBudget.map((cat) => {
      const spent = spentByCategory.get(cat.id) ?? 0;
      const budget = cat.monthly_budget! * periodMonths;
      return {
        categoryId: cat.id,
        categoryName: cat.name,
        budget,
        spent,
        percentage: budget > 0 ? (spent / budget) * 100 : 0,
      };
    });

    return items.sort((a, b) => b.percentage - a.percentage).slice(0, 5);
  }, [expenses, categories, convertToUserCurrency, periodMonths]);

  return (
    <div className="theme-surface p-6 rounded-lg theme-shadow theme-border border">
      <div className="flex items-center justify-between mb-4">
        <div className="flex items-center">
          <PieChart className="h-5 w-5 theme-accent mr-2" />
          <h2 className="text-lg font-semibold theme-text-primary">
            {t("dashboard.budget.title")}
          </h2>
        </div>
        <Link
          to="/categories"
          className="theme-accent text-sm font-medium flex items-center gap-1 theme-transition"
        >
          {t("dashboard.budget.manage")}
          <ArrowRight className="w-3 h-3" />
        </Link>
      </div>

      {budgetItems.length === 0 ? (
        <div className="text-center py-6">
          <PieChart className="w-8 h-8 theme-text-tertiary mx-auto mb-2" />
          <p className="text-sm theme-text-secondary mb-2">
            {t("dashboard.budget.empty")}
          </p>
          <Link
            to="/categories"
            className="text-sm theme-accent font-medium theme-transition"
          >
            {t("dashboard.budget.setBudgets")}
          </Link>
        </div>
      ) : (
        <div className="space-y-3">
          {budgetItems.map((item) => (
            <div key={item.categoryId}>
              <div className="flex items-center justify-between mb-1">
                <span className="text-sm theme-text-primary truncate max-w-[60%]">
                  {item.categoryName}
                </span>
                <span className="text-xs theme-text-secondary">
                  {formatCurrency(item.spent, userCurrency)} /{" "}
                  {formatCurrency(item.budget, userCurrency)}
                </span>
              </div>
              <div className="w-full h-2 bg-gray-200 dark:bg-gray-700 rounded-full overflow-hidden">
                <div
                  className={`h-full rounded-full transition-all ${getProgressColor(item.percentage)}`}
                  style={{ width: `${Math.min(item.percentage, 100)}%` }}
                />
              </div>
              {item.percentage > 100 && (
                <p className="text-xs text-red-500 mt-0.5">
                  {t("dashboard.budget.overBudget", {
                    percent: Math.round(item.percentage - 100),
                  })}
                </p>
              )}
            </div>
          ))}
        </div>
      )}
    </div>
  );
};
