import React, { useMemo } from 'react';
import { useTranslation } from 'react-i18next';
import { Bar, BarChart, CartesianGrid, ResponsiveContainer, Tooltip, XAxis, YAxis } from 'recharts';
import { CHART_COLORS, CHART_TOOLTIP_STYLE } from '../dashboard/chartColors';
import { Category, IncomeOut } from '@/types';

interface TopIncomeChartProps {
 incomes: IncomeOut[];
 categories: Category[];
}

export const TopIncomeChart: React.FC<TopIncomeChartProps> = ({ incomes, categories }) => {
 const { t } = useTranslation();

 const topData = useMemo(() => {
 const categoryTotals = categories.map(cat => {
 const total = incomes
 .filter(inc => inc.category_id === cat.id)
 .reduce((sum, inc) => sum + inc.amount, 0);
 return { name: cat.name, amount: total };
 });

 return categoryTotals
 .filter(item => item.amount > 0)
 .sort((a, b) => b.amount - a.amount)
 .slice(0, 5);
 }, [incomes, categories]);

 return (
 <div className="bg-elevated p-4 rounded-lg theme-shadow border-[var(--border)] border">
 <h2 className="text-lg font-semibold mb-4 text-content">{t('incomePage.dashboard.topTitle')}</h2>
 <div className="h-[300px]">
 <ResponsiveContainer width="100%" height="100%">
 <BarChart data={topData} layout="vertical">
 <CartesianGrid strokeDasharray="3 3" stroke="var(--border)" strokeOpacity={0.5} />
 <XAxis type="number" tick={{ fill: 'var(--text-primary)', fontSize: 12 }} axisLine={{ stroke: 'var(--border)' }} />
 <YAxis dataKey="name" type="category" width={100} tick={{ fill: 'var(--text-primary)', fontSize: 12 }} axisLine={{ stroke: 'var(--border)' }} />
 <Tooltip contentStyle={CHART_TOOLTIP_STYLE} />
 <Bar dataKey="amount" name={t('incomePage.list.amount')} fill={CHART_COLORS[4]} radius={[0, 4, 4, 0]} />
 </BarChart>
 </ResponsiveContainer>
 </div>
 </div>
 );
};
