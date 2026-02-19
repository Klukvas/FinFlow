import React from 'react';
import { useTranslation } from 'react-i18next';
import { Button } from '../shared/Button';
import { GoalsPageFilters, GOAL_TYPE_I18N_MAP } from './goalsHelpers';
import type { GoalStatus, GoalType, GoalPriority } from '../../../types/goal';

interface GoalFilterBarProps {
  filters: GoalsPageFilters;
  onFiltersChange: (filters: GoalsPageFilters) => void;
  isVisible: boolean;
}

export const GoalFilterBar: React.FC<GoalFilterBarProps> = ({
  filters,
  onFiltersChange,
  isVisible,
}) => {
  const { t } = useTranslation();

  if (!isVisible) return null;

  const update = (partial: Partial<GoalsPageFilters>) => {
    onFiltersChange({ ...filters, ...partial, page: 1 });
  };

  const clearAll = () => {
    onFiltersChange({ page: 1, size: filters.size });
  };

  const hasActiveFilters =
    (filters.status && filters.status !== 'all') ||
    (filters.goal_type && filters.goal_type !== 'all') ||
    (filters.priority && filters.priority !== 'all') ||
    (filters.search && filters.search.trim() !== '');

  const inputClasses =
    'py-2 px-3 text-sm rounded-lg border theme-border theme-surface theme-text-primary focus:outline-none focus:ring-2 focus:ring-[var(--color-accent)] theme-transition';

  const goalTypes: GoalType[] = ['SAVINGS', 'DEBT_PAYOFF', 'INVESTMENT', 'EXPENSE_REDUCTION', 'INCOME_INCREASE', 'EMERGENCY_FUND'];
  const priorities: GoalPriority[] = ['LOW', 'MEDIUM', 'HIGH', 'CRITICAL'];

  return (
    <div className="theme-surface border theme-border rounded-xl p-4 animate-in fade-in slide-in-from-top-2 duration-200">
      <div className="flex flex-wrap items-end gap-3">
        <div className="flex flex-col gap-1">
          <label className="text-xs font-medium theme-text-secondary">
            {t('goalsPage.filters.status')}
          </label>
          <select
            className={inputClasses}
            value={filters.status || 'all'}
            onChange={(e) => {
              const val = e.target.value as GoalStatus | 'all';
              update({ status: val === 'all' ? undefined : val });
            }}
          >
            <option value="all">{t('goalsPage.filters.allStatuses')}</option>
            <option value="ACTIVE">{t('goalsPage.filters.active')}</option>
            <option value="COMPLETED">{t('goalsPage.filters.completed')}</option>
            <option value="PAUSED">{t('goalsPage.filters.paused')}</option>
            <option value="CANCELLED">{t('goalsPage.filters.cancelled')}</option>
          </select>
        </div>

        <div className="flex flex-col gap-1">
          <label className="text-xs font-medium theme-text-secondary">
            {t('goalsPage.filters.type')}
          </label>
          <select
            className={inputClasses}
            value={filters.goal_type || 'all'}
            onChange={(e) => {
              const val = e.target.value as GoalType | 'all';
              update({ goal_type: val === 'all' ? undefined : val });
            }}
          >
            <option value="all">{t('goalsPage.filters.allTypes')}</option>
            {goalTypes.map((gt) => (
              <option key={gt} value={gt}>
                {t(GOAL_TYPE_I18N_MAP[gt])}
              </option>
            ))}
          </select>
        </div>

        <div className="flex flex-col gap-1">
          <label className="text-xs font-medium theme-text-secondary">
            {t('goalsPage.filters.priority')}
          </label>
          <select
            className={inputClasses}
            value={filters.priority || 'all'}
            onChange={(e) => {
              const val = e.target.value as GoalPriority | 'all';
              update({ priority: val === 'all' ? undefined : val });
            }}
          >
            <option value="all">{t('goalsPage.filters.allPriorities')}</option>
            {priorities.map((p) => (
              <option key={p} value={p}>
                {t(`goalsPage.filters.${p.toLowerCase()}`)}
              </option>
            ))}
          </select>
        </div>

        <div className="flex flex-col gap-1">
          <label className="text-xs font-medium theme-text-secondary">
            {t('goalsPage.filters.search')}
          </label>
          <input
            type="text"
            className={inputClasses}
            placeholder={t('goalsPage.filters.searchPlaceholder')}
            value={filters.search || ''}
            onChange={(e) => update({ search: e.target.value })}
          />
        </div>

        {hasActiveFilters && (
          <Button variant="ghost" size="sm" onClick={clearAll}>
            {t('goalsPage.filters.clearAll')}
          </Button>
        )}
      </div>
    </div>
  );
};
