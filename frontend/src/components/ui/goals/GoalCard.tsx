import React from 'react';
import { Goal, GOAL_TYPE_LABELS, GOAL_STATUS_LABELS, GOAL_PRIORITY_LABELS, GOAL_PRIORITY_COLORS, GOAL_STATUS_COLORS } from '@/types';
import { FaEdit, FaTrash, FaPlay, FaPause, FaBullseye, FaCalendarAlt, FaDollarSign } from 'react-icons/fa';

interface GoalCardProps {
  goal: Goal;
  onEdit: (goal: Goal) => void;
  onDelete: (goalId: number) => void;
  onUpdateProgress: (goalId: number) => void;
  onToggleStatus: (goalId: number) => void;
}

export const GoalCard: React.FC<GoalCardProps> = ({
  goal,
  onEdit,
  onDelete,
  onUpdateProgress,
  onToggleStatus
}) => {
  const getProgressColor = (percentage: number) => {
    if (percentage >= 100) return 'theme-success-bg';
    if (percentage >= 75) return 'theme-accent-bg';
    if (percentage >= 50) return 'theme-warning-bg';
    if (percentage >= 25) return 'bg-orange-500';
    return 'theme-error-bg';
  };

  const getDaysRemaining = () => {
    if (!goal.target_date) return null;
    const targetDate = new Date(goal.target_date);
    const today = new Date();
    const diffTime = targetDate.getTime() - today.getTime();
    const diffDays = Math.ceil(diffTime / (1000 * 60 * 60 * 24));
    return diffDays;
  };

  const daysRemaining = getDaysRemaining();
  const isOverdue = daysRemaining !== null && daysRemaining < 0;

  return (
    <div className="theme-surface theme-shadow rounded-lg border theme-border p-6 hover:theme-shadow-hover theme-transition">
      {/* Header */}
      <div className="flex justify-between items-start mb-4">
        <div className="flex-1">
          <h3 className="text-lg font-semibold theme-text-primary mb-1">{goal.title}</h3>
          <div className="flex items-center gap-4 text-sm theme-text-secondary">
            <span className={`px-2 py-1 rounded-full text-xs font-medium ${GOAL_PRIORITY_COLORS[goal.priority]} theme-bg-tertiary`}>
              {GOAL_PRIORITY_LABELS[goal.priority]}
            </span>
            <span className={`px-2 py-1 rounded-full text-xs font-medium ${GOAL_STATUS_COLORS[goal.status]} theme-bg-tertiary`}>
              {GOAL_STATUS_LABELS[goal.status]}
            </span>
            <span className="theme-text-tertiary">
              {GOAL_TYPE_LABELS[goal.goal_type]}
            </span>
          </div>
        </div>
        
        <div className="flex items-center gap-2">
          <button
            onClick={() => onEdit(goal)}
            className="p-2 theme-text-tertiary hover:theme-accent theme-transition"
            title="Редактировать"
          >
            <FaEdit className="w-4 h-4" />
          </button>
          <button
            onClick={() => onToggleStatus(goal.id)}
            className="p-2 theme-text-tertiary hover:theme-success theme-transition"
            title={goal.status === 'ACTIVE' ? 'Приостановить' : 'Возобновить'}
          >
            {goal.status === 'ACTIVE' ? <FaPause className="w-4 h-4" /> : <FaPlay className="w-4 h-4" />}
          </button>
          <button
            onClick={() => onDelete(goal.id)}
            className="p-2 theme-text-tertiary hover:theme-error theme-transition"
            title="Удалить"
          >
            <FaTrash className="w-4 h-4" />
          </button>
        </div>
      </div>

      {/* Description */}
      {goal.description && (
        <p className="theme-text-secondary text-sm mb-4">{goal.description}</p>
      )}

      {/* Progress */}
      <div className="mb-4">
        <div className="flex justify-between items-center mb-2">
          <span className="text-sm font-medium theme-text-secondary">Прогресс</span>
          <span className="text-sm font-bold theme-text-primary">
            {goal.progress_percentage.toFixed(1)}%
          </span>
        </div>
        <div className="w-full theme-bg-tertiary rounded-full h-2">
          <div
            className={`h-2 rounded-full transition-all duration-300 ${getProgressColor(goal.progress_percentage)}`}
            style={{ width: `${Math.min(goal.progress_percentage, 100)}%` }}
          />
        </div>
      </div>

      {/* Financial Info */}
      <div className="grid grid-cols-2 gap-4 mb-4">
        <div className="flex items-center gap-2">
          <FaDollarSign className="w-4 h-4 theme-text-tertiary" />
          <div>
            <p className="text-xs theme-text-tertiary">Текущая сумма</p>
            <p className="text-sm font-semibold theme-text-primary">
              {goal.current_amount.toLocaleString()} {goal.currency}
            </p>
          </div>
        </div>
        <div className="flex items-center gap-2">
          <FaBullseye className="w-4 h-4 theme-text-tertiary" />
          <div>
            <p className="text-xs theme-text-tertiary">Целевая сумма</p>
            <p className="text-sm font-semibold theme-text-primary">
              {goal.target_amount.toLocaleString()} {goal.currency}
            </p>
          </div>
        </div>
      </div>

      {/* Timeline */}
      {goal.target_date && (
        <div className="flex items-center gap-2 mb-4">
          <FaCalendarAlt className="w-4 h-4 theme-text-tertiary" />
          <div>
            <p className="text-xs theme-text-tertiary">Целевая дата</p>
            <p className={`text-sm font-semibold ${isOverdue ? 'theme-error' : 'theme-text-primary'}`}>
              {new Date(goal.target_date).toLocaleDateString('ru-RU')}
              {daysRemaining !== null && (
                <span className={`ml-2 text-xs ${isOverdue ? 'theme-error' : 'theme-text-tertiary'}`}>
                  ({isOverdue ? `Просрочено на ${Math.abs(daysRemaining)} дн.` : `Осталось ${daysRemaining} дн.`})
                </span>
              )}
            </p>
          </div>
        </div>
      )}

      {/* Actions */}
      <div className="flex gap-2">
        <button
          onClick={() => onUpdateProgress(goal.id)}
          className="flex-1 theme-accent-bg theme-text-inverse px-4 py-2 rounded-md hover:theme-accent-hover theme-transition text-sm font-medium"
        >
          Обновить прогресс
        </button>
        {goal.is_milestone_based && (
          <button
            className="px-4 py-2 border theme-border theme-text-secondary rounded-md hover:theme-surface-hover theme-transition text-sm font-medium"
          >
            Вехи
          </button>
        )}
      </div>
    </div>
  );
};
