import React from 'react';
import { useTranslation } from 'react-i18next';
import { Goal } from '@/types';
import { GoalCard } from '@/components/ui/goals';
import { LoadingState } from '@/components/ui/shared/LoadingState';

interface GoalsListProps {
  goals: Goal[];
  loading: boolean;
  onEditGoal: (goal: Goal) => void;
  onUpdateProgress: (goal: Goal) => void;
  onDeleteGoal: (goalId: number) => void;
  onToggleStatus: (goalId: number) => void;
  currentPage: number;
  totalPages: number;
  onPageChange: (page: number) => void;
}

export const GoalsList = React.memo<GoalsListProps>(({
  goals,
  loading,
  onEditGoal,
  onUpdateProgress,
  onDeleteGoal,
  onToggleStatus,
  currentPage,
  totalPages,
  onPageChange,
}) => {
  const { t } = useTranslation();

  if (loading) {
    return <LoadingState isLoading={true} data-testid="goals-list-loading"><div>{t('goalsPage.loadingGoals')}</div></LoadingState>;
  }

  if (goals.length === 0) {
    return (
      <div className="text-center py-12" data-testid="goals-empty-state">
        <div className="theme-text-tertiary text-6xl mb-4">🎯</div>
        <h3 className="text-lg font-medium theme-text-primary mb-2">
          {t('goalsPage.noGoals')}
        </h3>
        <p className="theme-text-tertiary">
          {t('goalsPage.createFirstGoal')}
        </p>
      </div>
    );
  }

  return (
    <div className="space-y-4">
      <div className="grid gap-4" data-testid="goals-list">
        {goals.map((goal) => (
          <GoalCard
            key={goal.id}
            goal={goal}
            onEdit={() => onEditGoal(goal)}
            onUpdateProgress={() => onUpdateProgress(goal)}
            onDelete={() => onDeleteGoal(goal.id)}
            onToggleStatus={() => onToggleStatus(goal.id)}
          />
        ))}
      </div>

      {totalPages > 1 && (
        <div className="flex justify-center mt-8" data-testid="goals-pagination">
          <div className="flex gap-2">
            <button
              onClick={() => onPageChange(currentPage - 1)}
              disabled={currentPage === 1}
              className="px-3 py-2 theme-surface border theme-border rounded-lg disabled:opacity-50 disabled:cursor-not-allowed hover:theme-surface-hover theme-transition"
              data-testid="goals-prev-page"
            >
              {t('goalsPage.pagination.previous')}
            </button>
            
            <span className="px-3 py-2 theme-text-primary">
              {currentPage} {t('goalsPage.pagination.of')} {totalPages}
            </span>
            
            <button
              onClick={() => onPageChange(currentPage + 1)}
              disabled={currentPage === totalPages}
              className="px-3 py-2 theme-surface border theme-border rounded-lg disabled:opacity-50 disabled:cursor-not-allowed hover:theme-surface-hover theme-transition"
              data-testid="goals-next-page"
            >
              {t('goalsPage.pagination.next')}
            </button>
          </div>
        </div>
      )}
    </div>
  );
});

GoalsList.displayName = 'GoalsList';
