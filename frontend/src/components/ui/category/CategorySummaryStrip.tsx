import React from 'react';
import { useTranslation } from 'react-i18next';
import { Card } from '../shared/Card';
import { Skeleton } from '../shared/Skeleton';
import { CategoryStatisticsResponse } from '../../../types/category';

interface CategorySummaryStripProps {
  stats: CategoryStatisticsResponse | null;
  loading: boolean;
}

export const CategorySummaryStrip: React.FC<CategorySummaryStripProps> = ({
  stats,
  loading,
}) => {
  const { t } = useTranslation();

  if (loading) {
    return (
      <div className="grid grid-cols-2 lg:grid-cols-4 gap-3">
        {Array.from({ length: 4 }).map((_, i) => (
          <Card key={i}>
            <div className="p-4 space-y-2">
              <Skeleton variant="text" className="h-3 w-20" />
              <Skeleton variant="text" className="h-6 w-16" />
            </div>
          </Card>
        ))}
      </div>
    );
  }

  const kpiCards = [
    {
      label: t('categoryPage.kpi.totalCategories'),
      value: String(stats?.total_categories ?? 0),
      valueClass: 'theme-text-primary',
    },
    {
      label: t('categoryPage.kpi.expenseCategories'),
      value: String(stats?.expense_categories ?? 0),
      valueClass: 'text-red-500/80 dark:text-red-400/70',
    },
    {
      label: t('categoryPage.kpi.incomeCategories'),
      value: String(stats?.income_categories ?? 0),
      valueClass: 'text-green-600/80 dark:text-green-400/70',
    },
    {
      label: t('categoryPage.kpi.withChildren'),
      value: String(stats?.parent_categories ?? 0),
      valueClass: 'theme-text-primary',
    },
  ];

  return (
    <div className="grid grid-cols-2 lg:grid-cols-4 gap-3">
      {kpiCards.map((card) => (
        <Card key={card.label}>
          <div className="p-4">
            <p className="text-xs font-medium theme-text-secondary uppercase tracking-wide">
              {card.label}
            </p>
            <p className={`text-xl font-semibold mt-1 ${card.valueClass}`}>
              {card.value}
            </p>
          </div>
        </Card>
      ))}
    </div>
  );
};
