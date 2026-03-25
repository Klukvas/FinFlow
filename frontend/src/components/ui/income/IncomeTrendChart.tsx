import React, { useMemo } from 'react';
import { useTranslation } from 'react-i18next';
import { CartesianGrid, Legend, Line, LineChart, ReferenceLine, ResponsiveContainer, Tooltip, XAxis, YAxis } from 'recharts';
import { CHART_COLORS, CHART_TOOLTIP_STYLE } from '../dashboard/chartColors';
import { IncomeOut } from '@/types';

interface IncomeTrendChartProps {
 incomes: IncomeOut[];
}

export const IncomeTrendChart: React.FC<IncomeTrendChartProps> = ({ incomes }) => {
 const { t } = useTranslation();

 const trendData = useMemo(() => {
 const last6Months = Array.from({ length: 6 }, (_, i) => {
 const date = new Date();
 date.setMonth(date.getMonth() - i);
 return date;
 }).reverse();

 return last6Months.map(date => {
 const monthIncomes = incomes.filter(inc => {
 const incDate = new Date(inc.date);
 return incDate.getMonth() === date.getMonth() && incDate.getFullYear() === date.getFullYear();
 });
 const total = monthIncomes.reduce((sum, inc) => sum + inc.amount, 0);
 return {
 month: date.toLocaleDateString('uk-UA', { month: 'long' }),
 amount: total,
 };
 });
 }, [incomes]);

 const averageAmount = useMemo(() => {
 const nonZero = trendData.filter(d => d.amount > 0);
 return nonZero.length > 0 ? nonZero.reduce((sum, item) => sum + item.amount, 0) / nonZero.length : 0;
 }, [trendData]);

 return (
 <div className="bg-elevated p-4 rounded-lg theme-shadow border-[var(--border)] border">
 <h2 className="text-lg font-semibold mb-4 text-content">{t('incomePage.dashboard.trendTitle')}</h2>
 <div className="h-[300px]">
 <ResponsiveContainer width="100%" height="100%">
 <LineChart data={trendData}>
 <CartesianGrid strokeDasharray="3 3" stroke="var(--border)" strokeOpacity={0.5} />
 <XAxis dataKey="month" tick={{ fill: 'var(--text-primary)', fontSize: 12 }} axisLine={{ stroke: 'var(--border)' }} />
 <YAxis tick={{ fill: 'var(--text-primary)', fontSize: 12 }} axisLine={{ stroke: 'var(--border)' }} />
 <Tooltip contentStyle={CHART_TOOLTIP_STYLE} />
 <Legend wrapperStyle={{ color: 'var(--text-primary)' }} />
 <Line type="monotone" dataKey="amount" name={t('incomePage.list.amount')} stroke={CHART_COLORS[4]} strokeWidth={2} dot={{ r: 4 }} activeDot={{ r: 6 }} />
 {averageAmount > 0 && (
 <ReferenceLine y={averageAmount} stroke="var(--text-tertiary)" strokeDasharray="3 3" />
 )}
 </LineChart>
 </ResponsiveContainer>
 </div>
 </div>
 );
};
