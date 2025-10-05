import { Bar, BarChart, CartesianGrid, Legend, ResponsiveContainer, Tooltip, XAxis, YAxis } from 'recharts';
import { Category, ExpenseResponse } from '@/types';
import React, { useMemo } from 'react';

interface TopExpensesChartProps {
  expenses: ExpenseResponse[];
  categories: Category[];
}

export const TopExpensesChart: React.FC<TopExpensesChartProps> = ({ expenses, categories }) => {
  const topExpenses = useMemo(() => {

    const results: { [key: string]: number } = {};
    
    for (const exp of expenses) {
      const category = categories.find(cat => cat.id === exp.category_id);
      if (category?.name) {
        if (results[category.name]) {
          results[category.name] += exp.amount;
        } else {
          results[category.name] = exp.amount;
        }
      }
    }

    const sortedResults = Object.entries(results).sort((a, b) => b[1] - a[1]);

    return sortedResults.slice(0, 5).map(([name, amount]) => ({
      name,
      amount
    }));

  }, [expenses, categories]);

  return (
    <div className="theme-surface p-4 rounded-lg theme-shadow theme-border border">
      <h2 className="text-lg font-semibold mb-4 theme-text-primary">Топ-5 крупных расходов</h2>
      <div className="h-[300px]">
        <ResponsiveContainer width="100%" height="100%">
          <BarChart data={topExpenses}>
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
              formatter={(value: number) => [`${value} ₴`, 'Сумма']}
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
            <Bar dataKey="amount" name="Сумма" fill="#ff8042" />
          </BarChart>
        </ResponsiveContainer>
      </div>
    </div>
  );
}; 