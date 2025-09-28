import { Bar, BarChart, CartesianGrid, Legend, ResponsiveContainer, Tooltip, XAxis, YAxis } from 'recharts';
import React, { useMemo } from 'react';

import { ExpenseResponse } from '@/types';

interface MonthComparisonChartProps {
  expenses: ExpenseResponse[];
}

export const MonthComparisonChart: React.FC<MonthComparisonChartProps> = ({ expenses }) => {
  const monthComparisonData = useMemo(() => {
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

    const currentMonthTotal = currentMonthExpenses.reduce((sum, exp) => sum + exp.amount, 0);
    const prevMonthTotal = prevMonthExpenses.reduce((sum, exp) => sum + exp.amount, 0);

    return [
      {
        name: 'Текущий месяц',
        amount: currentMonthTotal
      },
      {
        name: 'Предыдущий месяц',
        amount: prevMonthTotal
      }
    ];
  }, [expenses]);

  return (
    <div className="theme-surface p-4 rounded-lg theme-shadow theme-border border">
      <h2 className="text-lg font-semibold mb-4 theme-text-primary">Сравнение месяцев</h2>
      <div className="h-[300px]">
        <ResponsiveContainer width="100%" height="100%">
          <BarChart data={monthComparisonData}>
            <CartesianGrid strokeDasharray="3 3" stroke="var(--color-border)" />
            <XAxis 
              dataKey="name" 
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
            <Bar dataKey="amount" name="Сумма" fill="#82ca9d" />
          </BarChart>
        </ResponsiveContainer>
      </div>
    </div>
  );
}; 