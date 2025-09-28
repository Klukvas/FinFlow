import { CartesianGrid, Legend, Line, LineChart, ReferenceLine, ResponsiveContainer, Tooltip, XAxis, YAxis } from 'recharts';
import React, { useMemo } from 'react';

import { ExpenseResponse } from '@/types';

interface TrendChartProps {
  expenses: ExpenseResponse[];
}

export const TrendChart: React.FC<TrendChartProps> = ({ expenses }) => {
  const trendData = useMemo(() => {
    const last6Months = Array.from({ length: 6 }, (_, i) => {
      const date = new Date();
      date.setMonth(date.getMonth() - i);
      return date;
    }).reverse();

    return last6Months.map(date => {
      const monthExpenses = expenses.filter(exp => {
        const expDate = new Date(exp.date);
        return expDate.getMonth() === date.getMonth() && expDate.getFullYear() === date.getFullYear();
      });
      const total = monthExpenses.reduce((sum, exp) => sum + exp.amount, 0);
      return {
        month: date.toLocaleDateString('uk-UA', { month: 'long' }),
        amount: total
      };
    });
  }, [expenses]);

  const averageAmount = useMemo(() => {
    return trendData.reduce((sum, item) => sum + item.amount, 0) / trendData.length;
  }, [trendData]);

  return (
    <div className="theme-surface p-4 rounded-lg theme-shadow theme-border border">
      <h2 className="text-lg font-semibold mb-4 theme-text-primary">Тренд расходов за 6 месяцев</h2>
      <div className="h-[300px]">
        <ResponsiveContainer width="100%" height="100%">
          <LineChart data={trendData}>
            <CartesianGrid strokeDasharray="3 3" stroke="var(--color-border)" />
            <XAxis 
              dataKey="month" 
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
              dataKey="amount" 
              name="Сумма" 
              stroke="#8884d8" 
              strokeWidth={2}
              dot={{ r: 4 }}
              activeDot={{ r: 6 }}
            />
            <ReferenceLine y={averageAmount} stroke="red" strokeDasharray="3 3" />
          </LineChart>
        </ResponsiveContainer>
      </div>
    </div>
  );
}; 