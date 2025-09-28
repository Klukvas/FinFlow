import React, { useState, useEffect } from 'react';
import { useAuth } from '@/contexts/AuthContext';
import { useApiClients } from '@/hooks/useApiClients';
import { 
  Goal, 
  CreateGoalRequest, 
  UpdateGoalRequest, 
  GoalProgressUpdate,
  GoalStatistics as GoalStatisticsType,
  GoalFilters,
  GoalStatus,
  GoalType,
} from '@/types';
import { 
  GoalCard, 
  GoalForm, 
  GoalProgressModal, 
  GoalStatistics as GoalStatsComponent 
} from '@/components/ui/goals';
import { Modal } from '@/components/ui/Modal';
import { Button } from '@/components/ui/Button';
import { FaPlus, FaSearch, FaFilter, FaBullseye } from 'react-icons/fa';
import { toast } from 'sonner';

export const Goals: React.FC = () => {
  const { user } = useAuth();
  const { goals: goalsApi } = useApiClients();
  const [goals, setGoals] = useState<Goal[]>([]);
  const [statistics, setStatistics] = useState<GoalStatisticsType | null>(null);
  const [loading, setLoading] = useState(true);
  const [showCreateModal, setShowCreateModal] = useState(false);
  const [showProgressModal, setShowProgressModal] = useState(false);
  const [selectedGoal, setSelectedGoal] = useState<Goal | null>(null);
  const [filters, setFilters] = useState<GoalFilters>({});
  const [currentPage, setCurrentPage] = useState(1);
  const [totalPages, setTotalPages] = useState(1);
  const [showFilters, setShowFilters] = useState(false);

  const fetchGoals = async () => {
    if (!user?.id) return;

    try {
      setLoading(true);
      const response = await goalsApi.getGoals({
        ...filters,
        page: currentPage,
        size: 10
      });
      
      if ('error' in response) {
        throw new Error(response.error);
      }
      
      setGoals(response.items);
      setTotalPages(response.pages);
    } catch (error) {
      console.error('Failed to fetch goals:', error);
      toast.error('Ошибка при загрузке целей');
    } finally {
      setLoading(false);
    }
  };

  const fetchStatistics = async () => {
    if (!user?.id) return;

    try {
      const stats = await goalsApi.getGoalStatistics();
      if ('error' in stats) {
        throw new Error(stats.error);
      }
      setStatistics(stats);
    } catch (error) {
      console.error('Failed to fetch goal statistics:', error);
    }
  };

  useEffect(() => {
    if (user?.id) {
      fetchGoals();
      fetchStatistics();
    }
  }, [user?.id, filters, currentPage]);

  const handleCreateGoal = async (goalData: CreateGoalRequest) => {
    if (!user?.id) return;

    try {
      const response = await goalsApi.createGoal(goalData);
      if ('error' in response) {
        throw new Error(response.error);
      }
      setShowCreateModal(false);
      fetchGoals();
      fetchStatistics();
      toast.success('Цель успешно создана');
    } catch (error) {
      console.error('Failed to create goal:', error);
      toast.error('Ошибка при создании цели');
    }
  };

  const handleUpdateGoal = async (goalData: UpdateGoalRequest) => {
    if (!user?.id || !selectedGoal) return;

    try {
      const response = await goalsApi.updateGoal(selectedGoal.id, goalData);
      if ('error' in response) {
        throw new Error(response.error);
      }
      setShowCreateModal(false);
      setSelectedGoal(null);
      fetchGoals();
      fetchStatistics();
      toast.success('Цель успешно обновлена');
    } catch (error) {
      console.error('Failed to update goal:', error);
      toast.error('Ошибка при обновлении цели');
    }
  };

  const handleUpdateProgress = async (goalId: number, progress: GoalProgressUpdate) => {
    if (!user?.id) return;

    try {
      const response = await goalsApi.updateGoalProgress(goalId, progress);
      if ('error' in response) {
        throw new Error(response.error);
      }
      setShowProgressModal(false);
      setSelectedGoal(null);
      fetchGoals();
      fetchStatistics();
      toast.success('Прогресс обновлен');
    } catch (error) {
      console.error('Failed to update progress:', error);
      toast.error('Ошибка при обновлении прогресса');
    }
  };

  const handleDeleteGoal = async (goalId: number) => {
    if (!user?.id) return;

    if (!confirm('Вы уверены, что хотите удалить эту цель?')) {
      return;
    }

    try {
      const response = await goalsApi.deleteGoal(goalId);
      if (response && 'error' in response) {
        throw new Error(response.error);
      }
      fetchGoals();
      fetchStatistics();
      toast.success('Цель удалена');
    } catch (error) {
      console.error('Failed to delete goal:', error);
      toast.error('Ошибка при удалении цели');
    }
  };

  const handleToggleStatus = async (goalId: number) => {
    if (!user?.id) return;

    const goal = goals.find(g => g.id === goalId);
    if (!goal) return;

    const newStatus: GoalStatus = goal.status === 'ACTIVE' ? 'PAUSED' : 'ACTIVE';

    try {
      const response = await goalsApi.updateGoal(goalId, { status: newStatus });
      if ('error' in response) {
        throw new Error(response.error);
      }
      fetchGoals();
      fetchStatistics();
      toast.success(`Цель ${newStatus === 'ACTIVE' ? 'возобновлена' : 'приостановлена'}`);
    } catch (error) {
      console.error('Failed to toggle goal status:', error);
      toast.error('Ошибка при изменении статуса цели');
    }
  };

  const handleEditGoal = (goal: Goal) => {
    setSelectedGoal(goal);
    setShowCreateModal(true);
  };

  const handleUpdateProgressClick = (goalId: number) => {
    const goal = goals.find(g => g.id === goalId);
    if (goal) {
      setSelectedGoal(goal);
      setShowProgressModal(true);
    }
  };

  const handleFilterChange = (newFilters: Partial<GoalFilters>) => {
    setFilters(prev => ({ ...prev, ...newFilters }));
    setCurrentPage(1);
  };

  const clearFilters = () => {
    setFilters({});
    setCurrentPage(1);
  };

  const filteredGoals = goals.filter(goal => {
    if (filters.search) {
      const searchLower = filters.search.toLowerCase();
      return (
        goal.title.toLowerCase().includes(searchLower) ||
        (goal.description && goal.description.toLowerCase().includes(searchLower))
      );
    }
    return true;
  });

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
        <div>
          <h1 className="text-2xl font-bold theme-text-primary">Финансовые цели</h1>
          <p className="theme-text-secondary mt-1">
            Устанавливайте и отслеживайте свои финансовые цели
          </p>
        </div>
        
        <Button
          onClick={() => setShowCreateModal(true)}
          className="flex items-center gap-2"
        >
          <FaPlus className="w-4 h-4" />
          Создать цель
        </Button>
      </div>

      {/* Statistics */}
      {statistics && <GoalStatsComponent statistics={statistics} />}

      {/* Filters */}
      <div className="theme-surface theme-shadow rounded-lg border theme-border p-4 theme-transition">
        <div className="flex items-center justify-between mb-4">
          <h3 className="text-lg font-semibold theme-text-primary">Фильтры</h3>
          <Button
            variant="secondary"
            size="sm"
            onClick={() => setShowFilters(!showFilters)}
            className="flex items-center gap-2"
          >
            <FaFilter className="w-4 h-4" />
            {showFilters ? 'Скрыть' : 'Показать'}
          </Button>
        </div>

        {showFilters && (
          <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
            <div>
              <label className="block text-sm font-medium theme-text-secondary mb-2">
                Поиск
              </label>
              <div className="relative">
                <FaSearch className="absolute left-3 top-1/2 transform -translate-y-1/2 theme-text-tertiary w-4 h-4" />
                <input
                  type="text"
                  placeholder="Поиск по названию..."
                  value={filters.search || ''}
                  onChange={(e) => handleFilterChange({ search: e.target.value })}
                  className="w-full pl-10 pr-3 py-2 theme-surface theme-border border rounded-md theme-text-primary placeholder-gray-400 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent theme-transition"
                />
              </div>
            </div>
            
            <div>
              <label className="block text-sm font-medium theme-text-secondary mb-2">
                Статус
              </label>
              <select
                value={filters.status || ''}
                onChange={(e) => handleFilterChange({ status: e.target.value as GoalStatus || undefined })}
                className="w-full px-3 py-2 theme-surface theme-border border rounded-md theme-text-primary focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent theme-transition"
              >
                <option value="">Все статусы</option>
                <option value="ACTIVE">Активные</option>
                <option value="PAUSED">Приостановленные</option>
                <option value="COMPLETED">Завершенные</option>
                <option value="CANCELLED">Отмененные</option>
              </select>
            </div>

            <div>
              <label className="block text-sm font-medium theme-text-secondary mb-2">
                Тип цели
              </label>
              <select
                value={filters.goal_type || ''}
                onChange={(e) => handleFilterChange({ goal_type: e.target.value as GoalType || undefined })}
                className="w-full px-3 py-2 theme-surface theme-border border rounded-md theme-text-primary focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent theme-transition"
              >
                <option value="">Все типы</option>
                <option value="SAVINGS">Накопления</option>
                <option value="DEBT_PAYOFF">Погашение долга</option>
                <option value="INVESTMENT">Инвестиции</option>
                <option value="EXPENSE_REDUCTION">Сокращение расходов</option>
                <option value="INCOME_INCREASE">Увеличение дохода</option>
                <option value="EMERGENCY_FUND">Резервный фонд</option>
              </select>
            </div>

            <div className="flex items-end">
              <Button
                variant="secondary"
                onClick={clearFilters}
                className="w-full"
              >
                Сбросить фильтры
              </Button>
            </div>
          </div>
        )}
      </div>

      {/* Goals List */}
      <div className="space-y-4">
        {loading ? (
          <div className="flex justify-center items-center py-8">
            <div className="animate-spin rounded-full h-8 w-8 border-b-2 theme-accent"></div>
          </div>
        ) : filteredGoals.length === 0 ? (
          <div className="text-center py-8">
            <FaBullseye className="mx-auto h-12 w-12 theme-text-tertiary mb-4" />
            <p className="theme-text-secondary text-lg">Нет целей</p>
            <p className="theme-text-tertiary">Создайте свою первую финансовую цель</p>
          </div>
        ) : (
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
            {filteredGoals.map((goal) => (
              <GoalCard
                key={goal.id}
                goal={goal}
                onEdit={handleEditGoal}
                onDelete={handleDeleteGoal}
                onUpdateProgress={handleUpdateProgressClick}
                onToggleStatus={handleToggleStatus}
              />
            ))}
          </div>
        )}
      </div>

      {/* Pagination */}
      {totalPages > 1 && (
        <div className="flex justify-center items-center space-x-2">
          <Button
            variant="secondary"
            onClick={() => setCurrentPage(prev => Math.max(1, prev - 1))}
            disabled={currentPage === 1}
          >
            Предыдущая
          </Button>
          
          <span className="px-3 py-2 theme-text-secondary">
            Страница {currentPage} из {totalPages}
          </span>
          
          <Button
            variant="secondary"
            onClick={() => setCurrentPage(prev => Math.min(totalPages, prev + 1))}
            disabled={currentPage === totalPages}
          >
            Следующая
          </Button>
        </div>
      )}

      {/* Create/Edit Goal Modal */}
      <Modal
        isOpen={showCreateModal}
        onClose={() => {
          setShowCreateModal(false);
          setSelectedGoal(null);
        }}
        title={selectedGoal ? 'Редактировать цель' : 'Создать новую цель'}
        size="lg"
      >
        <GoalForm
          {...(selectedGoal && { goal: selectedGoal })}
          onSubmit={(data) => {
            if (selectedGoal) {
              handleUpdateGoal(data as UpdateGoalRequest);
            } else {
              handleCreateGoal(data as CreateGoalRequest);
            }
          }}
          onCancel={() => {
            setShowCreateModal(false);
            setSelectedGoal(null);
          }}
        />
      </Modal>

      {/* Progress Update Modal */}
      {selectedGoal && (
        <GoalProgressModal
          goal={selectedGoal}
          isOpen={showProgressModal}
          onClose={() => {
            setShowProgressModal(false);
            setSelectedGoal(null);
          }}
          onUpdate={handleUpdateProgress}
        />
      )}
    </div>
  );
};
