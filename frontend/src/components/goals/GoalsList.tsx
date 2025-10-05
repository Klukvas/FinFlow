import React from 'react';
import { Goal } from '@/types';
import { GoalCard } from '@/components/ui/goals';
import { LoadingState } from '@/components/ui/LoadingState';

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
  if (loading) {
    return <LoadingState isLoading={true} data-testid="goals-list-loading"><div>Загрузка целей...</div></LoadingState>;
  }

  if (goals.length === 0) {
    return (
      <div className="text-center py-12" data-testid="goals-empty-state">
        <div className="text-gray-400 text-6xl mb-4">🎯</div>
        <h3 className="text-lg font-medium theme-text-primary mb-2">
          Нет целей
        </h3>
        <p className="theme-text-tertiary">
          Создайте свою первую цель для начала планирования
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
              Назад
            </button>
            
            <span className="px-3 py-2 theme-text-primary">
              {currentPage} из {totalPages}
            </span>
            
            <button
              onClick={() => onPageChange(currentPage + 1)}
              disabled={currentPage === totalPages}
              className="px-3 py-2 theme-surface border theme-border rounded-lg disabled:opacity-50 disabled:cursor-not-allowed hover:theme-surface-hover theme-transition"
              data-testid="goals-next-page"
            >
              Вперед
            </button>
          </div>
        </div>
      )}
    </div>
  );
});

GoalsList.displayName = 'GoalsList';
