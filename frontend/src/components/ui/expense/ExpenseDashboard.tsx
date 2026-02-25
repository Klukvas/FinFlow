import { ExpenseResponse } from "@/types";
import React from "react";
import { useTranslation } from "react-i18next";
import { useCategories } from "@/contexts/CategoriesContext";
import { Skeleton } from "../shared/Skeleton";

import { CategoryExpensesChart } from "../dashboard/CategoryExpensesChart";
import { TopExpensesChart } from "../dashboard/TopExpensesChart";
import { TrendChart } from "../dashboard/TrendChart";

interface ExpenseDashboardProps {
  expenses: ExpenseResponse[];
  loading: boolean;
}

export const ExpenseDashboard: React.FC<ExpenseDashboardProps> = ({
  expenses,
  loading,
}) => {
  const { t } = useTranslation();
  const { categories } = useCategories();

  if (loading) {
    return (
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
        {Array.from({ length: 3 }).map((_, i) => (
          <div
            key={i}
            className="theme-surface rounded-lg theme-border border p-6 space-y-4"
          >
            <Skeleton className="h-5 w-32" />
            <Skeleton className="h-48 w-full rounded-lg" />
          </div>
        ))}
      </div>
    );
  }

  return (
    <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
      <TrendChart expenses={expenses} />
      <CategoryExpensesChart expenses={expenses} categories={categories} />
      <TopExpensesChart expenses={expenses} categories={categories} />
    </div>
  );
};
