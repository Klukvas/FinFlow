import { Bar, BarChart, CartesianGrid, Legend, ResponsiveContainer, Tooltip, XAxis, YAxis } from 'recharts';
import { Category, ExpenseResponse } from '@/types';
import React, { useMemo } from 'react';

interface CategoryComparisonChartProps {
  expenses: ExpenseResponse[];
  categories: Category[];
}

export const CategoryComparisonChart: React.FC<CategoryComparisonChartProps> = ({ expenses, categories }) => {
  const categoryComparisonData = useMemo(() => {
    const currentDate = new Date();
    const currentMonth = currentDate.getMonth();
    const currentYear = currentDate.getFullYear();
    const prevMonth = currentMonth === 0 ? 11 : currentMonth - 1;
    const prevYear = currentMonth === 0 ? currentYear - 1 : currentYear;

    const currentMonthExpenses = expenses.filter(exp => {
      const date = new Date(exp.date);
      return date.getMonth() === currentMonth && date.getFullYear() === currentYear;
    });

    const prevMonthExpenses = expenses.filter(exp => {
      const date = new Date(exp.date);
      return date.getMonth() === prevMonth && date.getFullYear() === prevYear;
    });

    return categories.map(cat => {
      const currentMonthCategoryExpenses = currentMonthExpenses.filter(exp => exp.category_id === cat.id);
      const prevMonthCategoryExpenses = prevMonthExpenses.filter(exp => exp.category_id === cat.id);
      
      const currentTotal = currentMonthCategoryExpenses.reduce((sum, exp) => sum + exp.amount, 0);
      const prevTotal = prevMonthCategoryExpenses.reduce((sum, exp) => sum + exp.amount, 0);

      return {
        name: cat.name,
        current: currentTotal,
        previous: prevTotal
      };
    }).filter(item => item.current > 0 || item.previous > 0); // Показываем только категории с расходами
  }, [expenses, categories]);

  return (
    <div className="theme-surface p-4 rounded-lg theme-shadow theme-border border">
      <h2 className="text-lg font-semibold mb-4 theme-text-primary">Сравнение категорий по месяцам</h2>
      <div className="h-[300px]">
        <ResponsiveContainer width="100%" height="100%">
          <BarChart data={categoryComparisonData}>
            <CartesianGrid strokeDasharray="3 3" stroke="var(--color-border)" />
            <XAxis 
              dataKey="name" 
              angle={-45} 
              textAnchor="end" 
              height={70}
              tick={{ fill: 'var(--color-text-primary)' }}
              axisLine={{ stroke: 'var(--color-border)' }}
            />
            <YAxis 
              tick={{ fill: 'var(--color-text-primary)' }}
              axisLine={{ stroke: 'var(--color-border)' }}
            />
            <Tooltip 
              contentStyle={{
                backgroundColor: 'var(--color-surface)',
                border: '1px solid var(--color-border)',
                borderRadius: '8px',
                color: 'var(--color-text-primary)'
              }}
            />
            <Legend 
              wrapperStyle={{
                color: 'var(--color-text-primary)'
              }}
            />
            <Bar dataKey="current" name="Текущий месяц" fill="#8884d8" />
            <Bar dataKey="previous" name="Предыдущий месяц" fill="#82ca9d" />
          </BarChart>
        </ResponsiveContainer>
      </div>
    </div>
  );
}; 