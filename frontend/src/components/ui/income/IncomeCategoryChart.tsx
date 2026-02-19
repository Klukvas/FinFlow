import React, { useMemo } from 'react';
import { useTranslation } from 'react-i18next';
import { Cell, Legend, Pie, PieChart, ResponsiveContainer, Tooltip } from 'recharts';
import { CHART_COLORS, CHART_TOOLTIP_STYLE } from '../dashboard/chartColors';
import { Category, IncomeOut } from '@/types';

interface IncomeCategoryChartProps {
  incomes: IncomeOut[];
  categories: Category[];
}

export const IncomeCategoryChart: React.FC<IncomeCategoryChartProps> = ({ incomes, categories }) => {
  const { t } = useTranslation();

  const incomesByCategory = useMemo(() => {
    return categories.map(cat => {
      const categoryIncomes = incomes.filter(inc => inc.category_id === cat.id);
      const total = categoryIncomes.reduce((sum, inc) => sum + inc.amount, 0);
      return {
        name: cat.name,
        value: total,
      };
    }).filter(item => item.value > 0);
  }, [incomes, categories]);

  return (
    <div className="theme-surface p-4 rounded-lg theme-shadow theme-border border">
      <h2 className="text-lg font-semibold mb-4 theme-text-primary">{t('incomePage.dashboard.categoryTitle')}</h2>
      <div className="h-[300px]">
        <ResponsiveContainer width="100%" height="100%">
          <PieChart>
            <Pie
              data={incomesByCategory}
              dataKey="value"
              nameKey="name"
              cx="50%"
              cy="50%"
              innerRadius={60}
              outerRadius={80}
            >
              {incomesByCategory.map((_, index) => (
                <Cell key={`cell-${index}`} fill={CHART_COLORS[index % CHART_COLORS.length]} />
              ))}
            </Pie>
            <Tooltip contentStyle={CHART_TOOLTIP_STYLE} />
            <Legend
              layout="horizontal"
              verticalAlign="bottom"
              wrapperStyle={{ color: 'var(--color-text-primary)' }}
            />
          </PieChart>
        </ResponsiveContainer>
      </div>
    </div>
  );
};
