import React, { useState, useEffect } from 'react';
import { useAuth } from '@/contexts/AuthContext';
import { Goal, GoalStatistics as GoalStatisticsType } from '@/types';
import { FaBullseye, FaCheckCircle, FaPlay, FaChartPie, FaDollarSign, FaArrowRight } from 'react-icons/fa';
import { Link } from 'react-router-dom';

export const GoalsOverview: React.FC = () => {
  const { user, goalsApi } = useAuth();
  const [goals, setGoals] = useState<Goal[]>([]);
  const [statistics, setStatistics] = useState<GoalStatisticsType | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const fetchData = async () => {
      if (!user?.id) return;

      try {
        setLoading(true);
        const [goalsResponse, statsResponse] = await Promise.all([
          goalsApi.getGoals({ page: 1, size: 3 }),
          goalsApi.getGoalStatistics()
        ]);
        
        if ('error' in goalsResponse) {
          throw new Error(goalsResponse.error);
        }
        if ('error' in statsResponse) {
          throw new Error(statsResponse.error);
        }
        
        setGoals(goalsResponse.items);
        setStatistics(statsResponse);
      } catch (error) {
        console.error('Failed to fetch goals data:', error);
      } finally {
        setLoading(false);
      }
    };

    fetchData();
  }, [user?.id]);

  const getProgressColor = (percentage: number) => {
    if (percentage >= 80) return 'bg-green-500';
    if (percentage >= 60) return 'bg-blue-500';
    if (percentage >= 40) return 'bg-yellow-500';
    if (percentage >= 20) return 'bg-orange-500';
    return 'bg-red-500';
  };

  const getDaysRemaining = (targetDate: string) => {
    const target = new Date(targetDate);
    const today = new Date();
    const diffTime = target.getTime() - today.getTime();
    const diffDays = Math.ceil(diffTime / (1000 * 60 * 60 * 24));
    return diffDays;
  };

  if (loading) {
    return (
      <div className="theme-surface rounded-lg theme-shadow theme-border border p-6">
        <div className="animate-pulse">
          <div className="h-4 theme-bg-tertiary rounded w-1/4 mb-4"></div>
          <div className="space-y-3">
            <div className="h-3 theme-bg-tertiary rounded"></div>
            <div className="h-3 theme-bg-tertiary rounded w-5/6"></div>
          </div>
        </div>
      </div>
    );
  }

  if (!statistics || statistics.total_goals === 0) {
    return (
      <div className="theme-surface rounded-lg theme-shadow theme-border border p-6">
        <div className="text-center">
          <FaBullseye className="mx-auto h-12 w-12 theme-text-tertiary mb-4" />
          <h3 className="text-lg font-semibold theme-text-primary mb-2">Нет финансовых целей</h3>
          <p className="theme-text-secondary mb-4">Создайте свою первую финансовую цель для отслеживания прогресса</p>
          <Link
            to="/goals"
            className="inline-flex items-center px-4 py-2 theme-accent-bg theme-text-inverse rounded-md hover:theme-accent-hover theme-transition"
          >
            Создать цель
            <FaArrowRight className="ml-2 w-4 h-4" />
          </Link>
        </div>
      </div>
    );
  }

  return (
    <div className="theme-surface rounded-lg theme-shadow theme-border border p-6">
      {/* Header */}
      <div className="flex items-center justify-between mb-6">
        <div className="flex items-center">
          <FaBullseye className="h-6 w-6 theme-accent mr-2" />
          <h3 className="text-lg font-semibold theme-text-primary">Финансовые цели</h3>
        </div>
        <Link
          to="/goals"
          className="theme-accent hover:theme-accent text-sm font-medium flex items-center theme-transition"
        >
          Все цели
          <FaArrowRight className="ml-1 w-3 h-3" />
        </Link>
      </div>

      {/* Statistics */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-6">
        <div className="text-center">
          <div className="flex items-center justify-center mb-2">
            <FaBullseye className="h-5 w-5 theme-accent" />
          </div>
          <p className="text-2xl font-bold theme-text-primary">{statistics.total_goals}</p>
          <p className="text-xs theme-text-tertiary">Всего целей</p>
        </div>
        
        <div className="text-center">
          <div className="flex items-center justify-center mb-2">
            <FaPlay className="h-5 w-5 theme-success" />
          </div>
          <p className="text-2xl font-bold theme-text-primary">{statistics.active_goals}</p>
          <p className="text-xs theme-text-tertiary">Активные</p>
        </div>
        
        <div className="text-center">
          <div className="flex items-center justify-center mb-2">
            <FaCheckCircle className="h-5 w-5 theme-accent" />
          </div>
          <p className="text-2xl font-bold theme-text-primary">{statistics.completed_goals}</p>
          <p className="text-xs theme-text-tertiary">Завершенные</p>
        </div>
        
        <div className="text-center">
          <div className="flex items-center justify-center mb-2">
            <FaChartPie className="h-5 w-5 theme-accent" />
          </div>
          <p className="text-2xl font-bold theme-text-primary">{statistics.overall_progress.toFixed(0)}%</p>
          <p className="text-xs theme-text-tertiary">Общий прогресс</p>
        </div>
      </div>

      {/* Financial Summary */}
      <div className="theme-bg-secondary rounded-lg p-4 mb-6">
        <div className="flex items-center mb-3">
          <FaDollarSign className="h-5 w-5 theme-success mr-2" />
          <h4 className="font-semibold theme-text-primary">Финансовая сводка</h4>
        </div>
        <div className="grid grid-cols-2 gap-4">
          <div>
            <p className="text-sm theme-text-tertiary">Накоплено</p>
            <p className="text-lg font-bold theme-success">
              {statistics.total_current_amount.toLocaleString()} USD
            </p>
          </div>
          <div>
            <p className="text-sm theme-text-tertiary">Целевая сумма</p>
            <p className="text-lg font-bold theme-text-primary">
              {statistics.total_target_amount.toLocaleString()} USD
            </p>
          </div>
        </div>
        <div className="mt-3">
          <div className="w-full theme-bg-tertiary rounded-full h-2">
            <div
              className={`h-2 rounded-full transition-all duration-300 ${getProgressColor(statistics.overall_progress)}`}
              style={{ width: `${Math.min(statistics.overall_progress, 100)}%` }}
            />
          </div>
        </div>
      </div>

      {/* Recent Goals */}
      {goals.length > 0 && (
        <div>
          <h4 className="font-semibold theme-text-primary mb-4">Последние цели</h4>
          <div className="space-y-3">
            {goals.map((goal) => {
              const daysRemaining = goal.target_date ? getDaysRemaining(goal.target_date) : null;
              const isOverdue = daysRemaining !== null && daysRemaining < 0;

              return (
                <div key={goal.id} className="flex items-center justify-between p-3 bg-gray-50 rounded-lg">
                  <div className="flex-1">
                    <h5 className="font-medium text-gray-900 text-sm">{goal.title}</h5>
                    <div className="flex items-center mt-1">
                      <div className="w-16 bg-gray-200 rounded-full h-1.5 mr-3">
                        <div
                          className={`h-1.5 rounded-full ${getProgressColor(goal.progress_percentage)}`}
                          style={{ width: `${Math.min(goal.progress_percentage, 100)}%` }}
                        />
                      </div>
                      <span className="text-xs text-gray-500">
                        {goal.progress_percentage.toFixed(0)}%
                      </span>
                    </div>
                  </div>
                  <div className="text-right">
                    <p className="text-sm font-medium text-gray-900">
                      {goal.current_amount.toLocaleString()} / {goal.target_amount.toLocaleString()}
                    </p>
                    {goal.target_date && (
                      <p className={`text-xs ${isOverdue ? 'text-red-500' : 'text-gray-500'}`}>
                        {isOverdue ? `Просрочено на ${Math.abs(daysRemaining!)} дн.` : `Осталось ${daysRemaining} дн.`}
                      </p>
                    )}
                  </div>
                </div>
              );
            })}
          </div>
        </div>
      )}
    </div>
  );
};
