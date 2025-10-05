import React from 'react';
import { GoalFilters } from '@/types';
import { Select } from '@/components/ui/Select';

interface GoalsFiltersProps {
  filters: GoalFilters;
  onFiltersChange: (filters: GoalFilters) => void;
  isVisible: boolean;
}

export const GoalsFilters = React.memo<GoalsFiltersProps>(({
  filters,
  onFiltersChange,
  isVisible,
}) => {
  if (!isVisible) return null;

  const handleFilterChange = (key: keyof GoalFilters, value: string) => {
    onFiltersChange({
      ...filters,
      [key]: value === 'all' ? undefined : value,
    });
  };

  return (
    <div className="bg-gray-50 dark:bg-gray-800 p-4 rounded-lg mb-6 space-y-4">
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        <div>
          <label className="block text-sm font-medium theme-text-primary mb-2">
            Статус
          </label>
          <Select
            value={filters.status || 'all'}
            onValueChange={(value) => handleFilterChange('status', value)}
            data-testid="goals-status-filter"
          >
            <option value="all">Все статусы</option>
            <option value="ACTIVE">Активные</option>
            <option value="COMPLETED">Завершенные</option>
            <option value="PAUSED">Приостановленные</option>
            <option value="CANCELLED">Отмененные</option>
          </Select>
        </div>

        <div>
          <label className="block text-sm font-medium theme-text-primary mb-2">
            Тип
          </label>
          <Select
            value={filters.goal_type || 'all'}
            onValueChange={(value) => handleFilterChange('goal_type', value)}
            data-testid="goals-type-filter"
          >
            <option value="all">Все типы</option>
            <option value="SAVINGS">Накопления</option>
            <option value="DEBT_PAYOFF">Погашение долга</option>
            <option value="INVESTMENT">Инвестиции</option>
            <option value="EXPENSE_REDUCTION">Сокращение расходов</option>
            <option value="INCOME_INCREASE">Увеличение дохода</option>
            <option value="EMERGENCY_FUND">Резервный фонд</option>
          </Select>
        </div>

        <div>
          <label className="block text-sm font-medium theme-text-primary mb-2">
            Приоритет
          </label>
          <Select
            value={filters.priority || 'all'}
            onValueChange={(value) => handleFilterChange('priority', value)}
            data-testid="goals-priority-filter"
          >
            <option value="all">Все приоритеты</option>
            <option value="LOW">Низкий</option>
            <option value="MEDIUM">Средний</option>
            <option value="HIGH">Высокий</option>
            <option value="CRITICAL">Критический</option>
          </Select>
        </div>

        <div>
          <label className="block text-sm font-medium theme-text-primary mb-2">
            Поиск
          </label>
          <input
            type="text"
            value={filters.search || ''}
            onChange={(e) => handleFilterChange('search', e.target.value)}
            placeholder="Поиск по названию..."
            className="w-full px-3 py-2 theme-surface border theme-border rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent theme-transition"
            data-testid="goals-search-filter"
          />
        </div>
      </div>
    </div>
  );
});

GoalsFilters.displayName = 'GoalsFilters';
