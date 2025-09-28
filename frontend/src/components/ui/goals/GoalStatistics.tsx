import React from 'react';
import { GoalStatistics as GoalStatisticsType } from '@/types';
import { FaBullseye, FaCheckCircle, FaPlay, FaChartPie, FaDollarSign, FaTrophy } from 'react-icons/fa';

interface GoalStatisticsProps {
  statistics: GoalStatisticsType;
}

export const GoalStatistics: React.FC<GoalStatisticsProps> = ({ statistics }) => {
  const getProgressColor = (percentage: number) => {
    if (percentage >= 80) return 'theme-success';
    if (percentage >= 60) return 'theme-accent';
    if (percentage >= 40) return 'theme-warning';
    if (percentage >= 20) return 'text-orange-600';
    return 'theme-error';
  };

  return (
    <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
      {/* Total Goals */}
      <div className="theme-surface theme-shadow rounded-lg border theme-border p-6 theme-transition">
        <div className="flex items-center">
          <div className="flex-shrink-0">
            <FaBullseye className="h-8 w-8 theme-accent" />
          </div>
          <div className="ml-4">
            <p className="text-sm font-medium theme-text-secondary">Всего целей</p>
            <p className="text-2xl font-bold theme-text-primary">{statistics.total_goals}</p>
          </div>
        </div>
      </div>

      {/* Active Goals */}
      <div className="theme-surface theme-shadow rounded-lg border theme-border p-6 theme-transition">
        <div className="flex items-center">
          <div className="flex-shrink-0">
            <FaPlay className="h-8 w-8 theme-success" />
          </div>
          <div className="ml-4">
            <p className="text-sm font-medium theme-text-secondary">Активные</p>
            <p className="text-2xl font-bold theme-text-primary">{statistics.active_goals}</p>
          </div>
        </div>
      </div>

      {/* Completed Goals */}
      <div className="theme-surface theme-shadow rounded-lg border theme-border p-6 theme-transition">
        <div className="flex items-center">
          <div className="flex-shrink-0">
            <FaCheckCircle className="h-8 w-8 theme-accent" />
          </div>
          <div className="ml-4">
            <p className="text-sm font-medium theme-text-secondary">Завершенные</p>
            <p className="text-2xl font-bold theme-text-primary">{statistics.completed_goals}</p>
          </div>
        </div>
      </div>

      {/* Overall Progress */}
      <div className="theme-surface theme-shadow rounded-lg border theme-border p-6 theme-transition">
        <div className="flex items-center">
          <div className="flex-shrink-0">
            <FaChartPie className="h-8 w-8 theme-accent" />
          </div>
          <div className="ml-4">
            <p className="text-sm font-medium theme-text-secondary">Общий прогресс</p>
            <p className={`text-2xl font-bold ${getProgressColor(statistics.overall_progress)}`}>
              {statistics.overall_progress.toFixed(1)}%
            </p>
          </div>
        </div>
      </div>

      {/* Financial Summary */}
      <div className="md:col-span-2 theme-surface theme-shadow rounded-lg border theme-border p-6 theme-transition">
        <div className="flex items-center mb-4">
          <FaDollarSign className="h-6 w-6 theme-success mr-2" />
          <h3 className="text-lg font-semibold theme-text-primary">Финансовая сводка</h3>
        </div>
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          <div>
            <p className="text-sm theme-text-secondary">Накоплено</p>
            <p className="text-xl font-bold theme-success">
              {statistics.total_current_amount.toLocaleString()} USD
            </p>
          </div>
          <div>
            <p className="text-sm theme-text-secondary">Целевая сумма</p>
            <p className="text-xl font-bold theme-text-primary">
              {statistics.total_target_amount.toLocaleString()} USD
            </p>
          </div>
        </div>
        <div className="mt-4">
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
      <div className="theme-surface theme-shadow rounded-lg border theme-border p-6 theme-transition">
        <div className="flex items-center mb-4">
          <FaTrophy className="h-6 w-6 theme-warning mr-2" />
          <h3 className="text-lg font-semibold theme-text-primary">По типам</h3>
        </div>
        <div className="space-y-2">
          {Object.entries(statistics.goals_by_type).map(([type, count]) => (
            <div key={type} className="flex justify-between items-center">
              <span className="text-sm theme-text-secondary">{type}</span>
              <span className="text-sm font-semibold theme-text-primary">{count}</span>
            </div>
          ))}
        </div>
      </div>

      {/* Goals by Priority */}
      <div className="theme-surface theme-shadow rounded-lg border theme-border p-6 theme-transition">
        <div className="flex items-center mb-4">
          <FaBullseye className="h-6 w-6 theme-error mr-2" />
          <h3 className="text-lg font-semibold theme-text-primary">По приоритету</h3>
        </div>
        <div className="space-y-2">
          {Object.entries(statistics.goals_by_priority).map(([priority, count]) => (
            <div key={priority} className="flex justify-between items-center">
              <span className="text-sm theme-text-secondary">{priority}</span>
              <span className="text-sm font-semibold theme-text-primary">{count}</span>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
};
