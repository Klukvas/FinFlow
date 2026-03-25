import React from 'react';
import { useTranslation } from 'react-i18next';
import { useCategories } from '@/contexts/CategoriesContext';
import { IncomeOut } from '@/types';

import { IncomeTrendChart } from './IncomeTrendChart';
import { IncomeCategoryChart } from './IncomeCategoryChart';
import { TopIncomeChart } from './TopIncomeChart';

interface IncomeDashboardProps {
 incomes: IncomeOut[];
 loading: boolean;
}

export const IncomeDashboard: React.FC<IncomeDashboardProps> = ({ incomes, loading }) => {
 const { t } = useTranslation();
 const { categories } = useCategories();

 if (loading) {
 return (
 <div className="flex justify-center items-center py-8 sm:py-12">
 <div className="animate-spin rounded-full h-6 w-6 sm:h-8 sm:w-8 border-2 border-[var(--accent)] border-t-transparent" />
 <span className="ml-3 text-content-secondary text-sm sm:text-base">{t('incomePage.dashboard.loading')}</span>
 </div>
 );
 }

 return (
 <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
 <IncomeTrendChart incomes={incomes} />
 <IncomeCategoryChart incomes={incomes} categories={categories} />
 <TopIncomeChart incomes={incomes} categories={categories} />
 </div>
 );
};
