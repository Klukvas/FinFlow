import { CartesianGrid, Legend, Line, LineChart, ResponsiveContainer, Tooltip, XAxis, YAxis } from 'recharts';
import React, { useMemo } from 'react';

import { ExpenseResponse } from '@/types';

interface WeekdayExpensesChartProps {
  expenses: ExpenseResponse[];
}

export const WeekdayExpensesChart: React.FC<WeekdayExpensesChartProps> = ({ expenses }) => {
  const weekdayData = useMemo(() => {
    const weekdayExpenses = expenses.reduce((acc, exp) => {
      const date = new Date(exp.date);
      const weekday = date.toLocaleDateString('uk-UA', { weekday: 'long' });
      if (!acc[weekday]) {
        acc[weekday] = { total: 0, count: 0 };
      }
      acc[weekday].total += exp.amount;
      acc[weekday].count += 1;
      return acc;
    }, {} as Record<string, { total: number; count: number }>);

    return Object.entries(weekdayExpenses).map(([weekday, data]) => ({
      weekday,
      average: data.total / data.count
    }));
  }, [expenses]);

  return (
    <div className="theme-surface p-4 rounded-lg theme-shadow theme-border border">
      <h2 className="text-lg font-semibold mb-4 theme-text-primary">Средние расходы по дням недели</h2>
      <div className="h-[300px]">
        <ResponsiveContainer width="100%" height="100%">
          <LineChart data={weekdayData}>
            <CartesianGrid strokeDasharray="3 3" stroke="var(--color-border)" />
            <XAxis 
              dataKey="weekday" 
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
            <Line 
              type="monotone" 
              dataKey="average" 
              name="Средняя сумма" 
              stroke="#8884d8" 
              strokeWidth={2}
              dot={{ r: 4 }}
              activeDot={{ r: 6 }}
            />
          </LineChart>
        </ResponsiveContainer>
      </div>
    </div>
  );
}; 