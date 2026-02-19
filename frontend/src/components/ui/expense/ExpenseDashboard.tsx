import { ExpenseResponse } from '@/types';
import React from 'react';
import { useTranslation } from 'react-i18next';
import { useCategories } from '@/contexts/CategoriesContext';

import { CategoryExpensesChart } from '../dashboard/CategoryExpensesChart';
import { TopExpensesChart } from '../dashboard/TopExpensesChart';
import { TrendChart } from '../dashboard/TrendChart';

interface ExpenseDashboardProps {
  expenses: ExpenseResponse[];
  loading: boolean;
}

export const ExpenseDashboard: React.FC<ExpenseDashboardProps> = ({ expenses, loading }) => {
  const { t } = useTranslation();
  const { categories } = useCategories();

  if (loading) {
    return (
      <div className="flex justify-center items-center py-8 sm:py-12">
        <div className="animate-spin rounded-full h-6 w-6 sm:h-8 sm:w-8 border-2 border-[var(--color-accent)] border-t-transparent" />
        <span className="ml-3 theme-text-secondary text-sm sm:text-base">{t('expense.dashboard.loading')}</span>
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
