import { Category, ExpenseResponse } from '@/types';
import { Cell, Legend, Pie, PieChart, ResponsiveContainer, Tooltip } from 'recharts';
import React, { useMemo } from 'react';

const COLORS = ['#0088FE', '#00C49F', '#FFBB28', '#FF8042', '#8884d8', '#82ca9d', '#ffc658', '#ff8042'];

interface CategoryExpensesChartProps {
  expenses: ExpenseResponse[];
  categories: Category[];
}

export const CategoryExpensesChart: React.FC<CategoryExpensesChartProps> = ({ expenses, categories }) => {
  const expensesByCategory = useMemo(() => {
    return categories.map(cat => {
      const categoryExpenses = expenses.filter(exp => exp.category_id === cat.id);
      const total = categoryExpenses.reduce((sum, exp) => sum + exp.amount, 0);
      
      return {
        name: cat.name,
        value: total
      };
    }).filter(item => item.value > 0); // Показываем только категории с расходами
  }, [expenses, categories]);

  return (
    <div className="theme-surface p-4 rounded-lg theme-shadow theme-border border">
      <h2 className="text-lg font-semibold mb-4 theme-text-primary">Расходы по категориям</h2>
      <div className="h-[300px]">
        <ResponsiveContainer width="100%" height="100%">
          <PieChart>
            <Pie
              data={expensesByCategory}
              dataKey="value"
              nameKey="name"
              cx="50%"
              cy="50%"
              outerRadius={80}
              label
            >
              {expensesByCategory.map((_, index) => (
                <Cell key={`cell-${index}`} fill={COLORS[index % COLORS.length]} />
              ))}
            </Pie>
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
          </PieChart>
        </ResponsiveContainer>
      </div>
    </div>
  );
}; 