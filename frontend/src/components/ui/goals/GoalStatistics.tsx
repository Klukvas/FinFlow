import React from 'react';
import { useTranslation } from 'react-i18next';
import { GoalStatistics as GoalStatisticsType } from '@/types';
import { useAuth } from '@/contexts/AuthContext';
import { useCurrencyConversion } from '@/hooks/useCurrencyConversion';
import { FaBullseye, FaCheckCircle, FaPlay, FaChartPie, FaDollarSign, FaTrophy } from 'react-icons/fa';

interface GoalStatisticsProps {
  statistics: GoalStatisticsType;
}

export const GoalStatistics: React.FC<GoalStatisticsProps> = ({ statistics }) => {
  const { t } = useTranslation();
  const { user } = useAuth();
  const { formatCurrency } = useCurrencyConversion();
  
  // Get currency from statistics or fallback to user's base currency
  const displayCurrency = statistics.currency || user?.base_currency || 'USD';
  
  const getProgressColor = (percentage: number) => {
    if (percentage >= 80) return 'theme-success';
    if (percentage >= 60) return 'theme-accent';
    if (percentage >= 40) return 'theme-warning';
    if (percentage >= 20) return 'text-orange-600';
    return 'theme-error';
  };

  return (
    <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4 sm:gap-6">
      {/* Total Goals */}
      <div className="theme-surface theme-shadow rounded-lg border theme-border p-4 sm:p-6 theme-transition">
        <div className="flex items-center">
          <div className="flex-shrink-0">
            <FaBullseye className="h-6 w-6 sm:h-8 sm:w-8 theme-accent" />
          </div>
          <div className="ml-3 sm:ml-4 min-w-0 flex-1">
            <p className="text-xs sm:text-sm font-medium theme-text-secondary truncate">{t('goalsPage.statistics.totalGoals')}</p>
            <p className="text-xl sm:text-2xl font-bold theme-text-primary">{statistics.total_goals}</p>
          </div>
        </div>
      </div>

      {/* Active Goals */}
      <div className="theme-surface theme-shadow rounded-lg border theme-border p-4 sm:p-6 theme-transition">
        <div className="flex items-center">
          <div className="flex-shrink-0">
            <FaPlay className="h-6 w-6 sm:h-8 sm:w-8 theme-success" />
          </div>
          <div className="ml-3 sm:ml-4 min-w-0 flex-1">
            <p className="text-xs sm:text-sm font-medium theme-text-secondary truncate">{t('goalsPage.statistics.activeGoals')}</p>
            <p className="text-xl sm:text-2xl font-bold theme-text-primary">{statistics.active_goals}</p>
          </div>
        </div>
      </div>

      {/* Completed Goals */}
      <div className="theme-surface theme-shadow rounded-lg border theme-border p-4 sm:p-6 theme-transition">
        <div className="flex items-center">
          <div className="flex-shrink-0">
            <FaCheckCircle className="h-6 w-6 sm:h-8 sm:w-8 theme-accent" />
          </div>
          <div className="ml-3 sm:ml-4 min-w-0 flex-1">
            <p className="text-xs sm:text-sm font-medium theme-text-secondary truncate">{t('goalsPage.statistics.completedGoals')}</p>
            <p className="text-xl sm:text-2xl font-bold theme-text-primary">{statistics.completed_goals}</p>
          </div>
        </div>
      </div>

      {/* Overall Progress */}
      <div className="theme-surface theme-shadow rounded-lg border theme-border p-4 sm:p-6 theme-transition">
        <div className="flex items-center">
          <div className="flex-shrink-0">
            <FaChartPie className="h-6 w-6 sm:h-8 sm:w-8 theme-accent" />
          </div>
          <div className="ml-3 sm:ml-4 min-w-0 flex-1">
            <p className="text-xs sm:text-sm font-medium theme-text-secondary truncate">{t('goalsPage.statistics.overallProgress')}</p>
            <p className={`text-xl sm:text-2xl font-bold ${getProgressColor(statistics.overall_progress)}`}>
              {statistics.overall_progress.toFixed(1)}%
            </p>
          </div>
        </div>
      </div>

      {/* Financial Summary */}
      <div className="sm:col-span-2 lg:col-span-2 theme-surface theme-shadow rounded-lg border theme-border p-4 sm:p-6 theme-transition">
        <div className="flex items-center mb-3 sm:mb-4">
          <FaDollarSign className="h-5 w-5 sm:h-6 sm:w-6 theme-success mr-2 flex-shrink-0" />
          <h3 className="text-base sm:text-lg font-semibold theme-text-primary truncate">{t('goalsPage.statistics.financialSummary')}</h3>
        </div>
        <div className="grid grid-cols-1 sm:grid-cols-2 gap-3 sm:gap-4">
          <div>
            <p className="text-xs sm:text-sm theme-text-secondary">{t('goalsPage.statistics.totalSaved')}</p>
            <p className="text-lg sm:text-xl font-bold theme-success truncate">
              {formatCurrency(statistics.total_current_amount, displayCurrency)}
            </p>
          </div>
          <div>
            <p className="text-xs sm:text-sm theme-text-secondary">{t('goalsPage.statistics.targetAmount')}</p>
            <p className="text-lg sm:text-xl font-bold theme-text-primary truncate">
              {formatCurrency(statistics.total_target_amount, displayCurrency)}
            </p>
          </div>
        </div>
        <div className="mt-3 sm:mt-4">
          <div className="w-full theme-bg-tertiary rounded-full h-2">
            <div
              className={`h-2 rounded-full transition-all duration-300 ${
                statistics.overall_progress >= 80 ? 'theme-success-bg' :
                statistics.overall_progress >= 60 ? 'theme-accent-bg' :
                statistics.overall_progress >= 40 ? 'theme-warning-bg' :
                statistics.overall_progress >= 20 ? 'bg-orange-500' : 'theme-error-bg'
              }`}
              style={{ width: `${Math.min(statistics.overall_progress, 100)}%` }}
            />
          </div>
        </div>
      </div>

      {/* Goals by Type */}
      <div className="theme-surface theme-shadow rounded-lg border theme-border p-4 sm:p-6 theme-transition">
        <div className="flex items-center mb-3 sm:mb-4">
          <FaTrophy className="h-5 w-5 sm:h-6 sm:w-6 theme-warning mr-2 flex-shrink-0" />
          <h3 className="text-base sm:text-lg font-semibold theme-text-primary truncate">{t('goalsPage.statistics.byType')}</h3>
        </div>
        <div className="space-y-2">
          {Object.entries(statistics.goals_by_type).map(([type, count]) => (
            <div key={type} className="flex justify-between items-center">
              <span className="text-xs sm:text-sm theme-text-secondary truncate">{type}</span>
              <span className="text-xs sm:text-sm font-semibold theme-text-primary ml-2">{count}</span>
            </div>
          ))}
        </div>
      </div>

      {/* Goals by Priority */}
      <div className="theme-surface theme-shadow rounded-lg border theme-border p-4 sm:p-6 theme-transition">
        <div className="flex items-center mb-3 sm:mb-4">
          <FaBullseye className="h-5 w-5 sm:h-6 sm:w-6 theme-error mr-2 flex-shrink-0" />
          <h3 className="text-base sm:text-lg font-semibold theme-text-primary truncate">{t('goalsPage.statistics.byPriority')}</h3>
        </div>
        <div className="space-y-2">
          {Object.entries(statistics.goals_by_priority).map(([priority, count]) => (
            <div key={priority} className="flex justify-between items-center">
              <span className="text-xs sm:text-sm theme-text-secondary truncate">{priority}</span>
              <span className="text-xs sm:text-sm font-semibold theme-text-primary ml-2">{count}</span>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
};
