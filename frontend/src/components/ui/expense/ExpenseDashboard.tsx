import { Category, ExpenseResponse } from '@/types';
import { useCallback, useEffect, useState } from 'react';

import { CategoryComparisonChart } from '../dashboard/CategoryComparisonChart';
import { CategoryExpensesChart } from '../dashboard/CategoryExpensesChart';
import { MonthComparisonChart } from '../dashboard/MonthComparisonChart';
import { TopExpensesChart } from '../dashboard/TopExpensesChart';
import { TrendChart } from '../dashboard/TrendChart';
import { WeekdayExpensesChart } from '../dashboard/WeekdayExpensesChart';
import { useApiClients } from '@/hooks';

export const ExpenseDashboard: React.FC = () => {
  const [expenses, setExpenses] = useState<ExpenseResponse[]>([]);
  const [categories, setCategories] = useState<Category[]>([]);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);
  const { expense, category } = useApiClients();

  const fetchData = useCallback(async () => {
    try {
      setLoading(true);
      const [expensesResponse, categoriesResponse] = await Promise.all([
        expense.getExpenses(),
        category.getCategories(true) // Запрашиваем все категории в плоском виде
      ]);

      if ('error' in expensesResponse) {
        setError(expensesResponse.error);
      } else {
        setExpenses(expensesResponse);
      }

      if ('error' in categoriesResponse) {
        setError(categoriesResponse.error);
      } else {
        setCategories(categoriesResponse);
      }
    } catch (err) {
      setError('Ошибка при загрузке данных');
      console.error('Error fetching data:', err);
    } finally {
      setLoading(false);
    }
  }, [expense, category]);

  useEffect(() => {
    fetchData();
  }, [fetchData]);

  if (loading) {
    return (
      <div className="flex justify-center items-center py-8 sm:py-12">
        <div className="relative">
          <div className="animate-spin rounded-full h-6 w-6 sm:h-8 sm:w-8 border-2 sm:border-3 theme-border"></div>
          <div className="animate-spin rounded-full h-6 w-6 sm:h-8 sm:w-8 border-2 sm:border-3 theme-error border-t-transparent absolute top-0 left-0"></div>
        </div>
        <span className="ml-3 theme-text-secondary text-sm sm:text-base">Загрузка аналитики...</span>
      </div>
    );
  }

  if (error) {
    return (
      <div className="theme-error-light theme-border border rounded-lg sm:rounded-xl p-4">
        <div className="flex items-center gap-3">
          <div className="w-5 h-5 theme-error flex-shrink-0">
            <svg fill="currentColor" viewBox="0 0 20 20">
              <path fillRule="evenodd" d="M18 10a8 8 0 11-16 0 8 8 0 0116 0zm-7 4a1 1 0 11-2 0 1 1 0 012 0zm-1-9a1 1 0 00-1 1v4a1 1 0 102 0V6a1 1 0 00-1-1z" clipRule="evenodd" />
            </svg>
          </div>
          <p className="theme-error text-sm font-medium">{error}</p>
        </div>
      </div>
    );
  }

  return (
    <div className="space-y-4 sm:space-y-6">
      <div className="grid grid-cols-1 sm:grid-cols-2 xl:grid-cols-3 gap-4 sm:gap-6">
        <CategoryExpensesChart expenses={expenses} categories={categories} />
        <MonthComparisonChart expenses={expenses} />
        <TopExpensesChart expenses={expenses} categories={categories} />
        <WeekdayExpensesChart expenses={expenses} />
        <CategoryComparisonChart expenses={expenses} categories={categories} />
        <TrendChart expenses={expenses} />
      </div>
    </div>
  );
};
