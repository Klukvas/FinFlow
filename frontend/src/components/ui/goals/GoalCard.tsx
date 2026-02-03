import React from 'react';
import { useTranslation } from 'react-i18next';
import { Goal, GoalType, GoalStatus, GoalPriority, GOAL_PRIORITY_COLORS, GOAL_STATUS_COLORS } from '@/types';
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
  const { t } = useTranslation();

  const getTypeLabel = (type: GoalType): string => {
    const typeMap: Record<GoalType, string> = {
      SAVINGS: t('goalsPage.filters.savings'),
      DEBT_PAYOFF: t('goalsPage.filters.debtPayoff'),
      INVESTMENT: t('goalsPage.filters.investment'),
      EXPENSE_REDUCTION: t('goalsPage.filters.expenseReduction'),
      INCOME_INCREASE: t('goalsPage.filters.incomeIncrease'),
      EMERGENCY_FUND: t('goalsPage.filters.emergencyFund')
    };
    return typeMap[type];
  };

  const getStatusLabel = (status: GoalStatus): string => {
    const statusMap: Record<GoalStatus, string> = {
      ACTIVE: t('goalsPage.filters.active'),
      COMPLETED: t('goalsPage.filters.completed'),
      PAUSED: t('goalsPage.filters.paused'),
      CANCELLED: t('goalsPage.filters.cancelled')
    };
    return statusMap[status];
  };

  const getPriorityLabel = (priority: GoalPriority): string => {
    const priorityMap: Record<GoalPriority, string> = {
      LOW: t('goalsPage.filters.low'),
      MEDIUM: t('goalsPage.filters.medium'),
      HIGH: t('goalsPage.filters.high'),
      CRITICAL: t('goalsPage.filters.critical')
    };
    return priorityMap[priority];
  };

  const getProgressColor = (percentage: number) => {
    if (percentage >= 100) return 'theme-success-bg';
    if (percentage >= 75) return 'theme-accent-bg';
    if (percentage >= 50) return 'theme-warning-bg';
    if (percentage >= 25) return 'theme-warning-bg';
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
    <div className="theme-surface theme-shadow rounded-lg border theme-border p-4 sm:p-6 hover:theme-shadow-hover theme-transition">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:justify-between sm:items-start gap-3 sm:gap-4 mb-4">
        <div className="flex-1 min-w-0">
          <h3 className="text-base sm:text-lg font-semibold theme-text-primary mb-1 sm:mb-2 truncate">{goal.title}</h3>
          <div className="flex flex-wrap items-center gap-2 sm:gap-4 text-sm theme-text-secondary">
            <span className={`px-2 py-1 rounded-full text-xs font-medium ${GOAL_PRIORITY_COLORS[goal.priority]} theme-bg-tertiary whitespace-nowrap`}>
              {getPriorityLabel(goal.priority)}
            </span>
            <span className={`px-2 py-1 rounded-full text-xs font-medium ${GOAL_STATUS_COLORS[goal.status]} theme-bg-tertiary whitespace-nowrap`}>
              {getStatusLabel(goal.status)}
            </span>
            <span className="theme-text-tertiary text-xs sm:text-sm truncate">
              {getTypeLabel(goal.goal_type)}
            </span>
          </div>
        </div>
        
        <div className="flex items-center justify-end gap-1 sm:gap-2">
          <button
            onClick={() => onEdit(goal)}
            className="p-2 sm:p-2 theme-text-tertiary hover:theme-accent theme-transition min-h-[44px] min-w-[44px] flex items-center justify-center touch-manipulation"
            title={t('common.edit')}
          >
            <FaEdit className="w-4 h-4" />
          </button>
          <button
            onClick={() => onToggleStatus(goal.id)}
            className="p-2 sm:p-2 theme-text-tertiary hover:theme-success theme-transition min-h-[44px] min-w-[44px] flex items-center justify-center touch-manipulation"
            title={goal.status === 'ACTIVE' ? t('goalsPage.card.pause') : t('goalsPage.card.resume')}
          >
            {goal.status === 'ACTIVE' ? <FaPause className="w-4 h-4" /> : <FaPlay className="w-4 h-4" />}
          </button>
          <button
            onClick={() => onDelete(goal.id)}
            className="p-2 sm:p-2 theme-text-tertiary hover:theme-error theme-transition min-h-[44px] min-w-[44px] flex items-center justify-center touch-manipulation"
            title={t('common.delete')}
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
          <span className="text-sm font-medium theme-text-secondary">{t('goalsPage.card.progress')}</span>
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
      <div className="grid grid-cols-1 sm:grid-cols-2 gap-3 sm:gap-4 mb-4">
        <div className="flex items-center gap-2">
          <FaDollarSign className="w-4 h-4 theme-text-tertiary flex-shrink-0" />
          <div className="min-w-0 flex-1">
            <p className="text-xs theme-text-tertiary">{t('goalsPage.progressModal.currentAmount')}</p>
            <p className="text-sm font-semibold theme-text-primary truncate">
              {goal.current_amount.toLocaleString()} {goal.currency}
            </p>
          </div>
        </div>
        <div className="flex items-center gap-2">
          <FaBullseye className="w-4 h-4 theme-text-tertiary flex-shrink-0" />
          <div className="min-w-0 flex-1">
            <p className="text-xs theme-text-tertiary">{t('goalsPage.progressModal.targetAmount')}</p>
            <p className="text-sm font-semibold theme-text-primary truncate">
              {goal.target_amount.toLocaleString()} {goal.currency}
            </p>
          </div>
        </div>
      </div>

      {/* Timeline */}
      {goal.target_date && (
        <div className="flex items-center gap-2 mb-4">
          <FaCalendarAlt className="w-4 h-4 theme-text-tertiary flex-shrink-0" />
          <div className="min-w-0 flex-1">
            <p className="text-xs theme-text-tertiary">{t('goalsPage.card.targetDate')}</p>
            <p className={`text-sm font-semibold ${isOverdue ? 'theme-error' : 'theme-text-primary'}`}>
              <span className="block sm:inline">{new Date(goal.target_date).toLocaleDateString()}</span>
              {daysRemaining !== null && (
                <span className={`block sm:inline sm:ml-2 text-xs ${isOverdue ? 'theme-error' : 'theme-text-tertiary'}`}>
                  ({isOverdue 
                    ? t('goalsPage.card.overdueDays', { days: Math.abs(daysRemaining) })
                    : t('goalsPage.card.remainingDays', { days: daysRemaining })
                  })
                </span>
              )}
            </p>
          </div>
        </div>
      )}

      {/* Actions */}
      <div className="flex flex-col sm:flex-row gap-2">
        <button
          onClick={() => onUpdateProgress(goal.id)}
          className="flex-1 theme-accent-bg theme-text-inverse px-4 py-3 sm:py-2 rounded-md hover:theme-accent-hover theme-transition text-sm font-medium min-h-[44px] touch-manipulation"
        >
          {t('goalsPage.progressModal.updateProgress')}
        </button>
        {goal.is_milestone_based && (
          <button
            className="px-4 py-3 sm:py-2 border theme-border theme-text-secondary rounded-md hover:theme-surface-hover theme-transition text-sm font-medium min-h-[44px] touch-manipulation"
          >
            {t('goalsPage.card.milestones')}
          </button>
        )}
      </div>
    </div>
  );
};
