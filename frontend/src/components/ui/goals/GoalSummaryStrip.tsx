import React from 'react';
import { useTranslation } from 'react-i18next';
import { Card } from '../shared/Card';
import { Skeleton } from '../shared/Skeleton';
import { GoalStatistics } from '../../../types/goal';
import { formatAmount, getProgressBarColor } from './goalsHelpers';

interface GoalSummaryStripProps {
  stats: GoalStatistics | null;
  loading: boolean;
}

export const GoalSummaryStrip: React.FC<GoalSummaryStripProps> = ({
  stats,
  loading,
}) => {
  const { t } = useTranslation();

  if (loading) {
    return (
      <div className="grid grid-cols-2 lg:grid-cols-5 gap-3">
        {Array.from({ length: 5 }).map((_, i) => (
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

  const currency = stats?.currency || 'USD';
  const progressColor = stats?.overall_progress
    ? getProgressBarColor(stats.overall_progress).replace('bg-', 'text-').replace('/70', '/80')
    : 'theme-text-primary';

  const kpiCards = [
    {
      label: t('goalsPage.kpi.activeGoals'),
      value: String(stats?.active_goals ?? 0),
      valueClass: 'text-green-600/80 dark:text-green-400/70',
    },
    {
      label: t('goalsPage.kpi.completed'),
      value: String(stats?.completed_goals ?? 0),
      valueClass: 'text-blue-600/80 dark:text-blue-400/70',
    },
    {
      label: t('goalsPage.kpi.totalSaved'),
      value: formatAmount(stats?.total_current_amount ?? 0, currency),
      valueClass: 'theme-text-primary',
    },
    {
      label: t('goalsPage.kpi.totalTarget'),
      value: formatAmount(stats?.total_target_amount ?? 0, currency),
      valueClass: 'theme-text-primary',
    },
    {
      label: t('goalsPage.kpi.overallProgress'),
      value: `${(stats?.overall_progress ?? 0).toFixed(1)}%`,
      valueClass: progressColor,
    },
  ];

  return (
    <div className="grid grid-cols-2 lg:grid-cols-5 gap-3">
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
