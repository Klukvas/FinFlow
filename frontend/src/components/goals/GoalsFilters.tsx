import React from 'react';
import { useTranslation } from 'react-i18next';
import { GoalFilters } from '@/types';
import { Select } from '@/components/ui/forms/Select';

interface GoalsFiltersProps {
 filters: GoalFilters;
 onFiltersChange: (filters: GoalFilters) => void;
 isVisible: boolean;
}

const STATUS_OPTIONS = ['all', 'ACTIVE', 'COMPLETED', 'PAUSED', 'CANCELLED'] as const;
const TYPE_OPTIONS = ['all', 'SAVINGS', 'DEBT_PAYOFF', 'INVESTMENT', 'EXPENSE_REDUCTION', 'INCOME_INCREASE', 'EMERGENCY_FUND'] as const;
const PRIORITY_OPTIONS = ['all', 'LOW', 'MEDIUM', 'HIGH', 'CRITICAL'] as const;

export const GoalsFilters = React.memo<GoalsFiltersProps>(({
 filters,
 onFiltersChange,
 isVisible,
}) => {
 const { t } = useTranslation();
 
 if (!isVisible) return null;

 const handleFilterChange = (key: keyof GoalFilters, value: string) => {
 onFiltersChange({
 ...filters,
 [key]: value === 'all' ? undefined : value,
 });
 };

 return (
 <div className="bg-surface-alt p-3 sm:p-4 rounded-lg mb-4 sm:mb-6 space-y-3 sm:space-y-4">
 <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-3 sm:gap-4">
 <div>
 <label className="block text-sm font-medium text-content mb-1 sm:mb-2">
 {t('goalsPage.filters.status')}
 </label>
 <Select
 value={filters.status || 'all'}
 onValueChange={(value) => handleFilterChange('status', value)}
 data-testid="goals-status-filter"
 >
 {STATUS_OPTIONS.map((status) => {
 const statusKey = status === 'all' ? 'allStatuses' : status.toLowerCase();
 return (
 <option key={status} value={status}>{t(`goalsPage.filters.${statusKey}`)}</option>
 );
 })}
 </Select>
 </div>

 <div>
 <label className="block text-sm font-medium text-content mb-1 sm:mb-2">
 {t('goalsPage.filters.type')}
 </label>
 <Select
 value={filters.goal_type || 'all'}
 onValueChange={(value) => handleFilterChange('goal_type', value)}
 data-testid="goals-type-filter"
 >
 {TYPE_OPTIONS.map((type) => {
 const typeKey = type === 'all' ? 'allTypes' : type.toLowerCase().replace(/_/g, '');
 return (
 <option key={type} value={type}>{t(`goalsPage.filters.${typeKey}`)}</option>
 );
 })}
 </Select>
 </div>

 <div>
 <label className="block text-sm font-medium text-content mb-1 sm:mb-2">
 {t('goalsPage.filters.priority')}
 </label>
 <Select
 value={filters.priority || 'all'}
 onValueChange={(value) => handleFilterChange('priority', value)}
 data-testid="goals-priority-filter"
 >
 {PRIORITY_OPTIONS.map((priority) => {
 const priorityKey = priority === 'all' ? 'allPriorities' : priority.toLowerCase();
 return (
 <option key={priority} value={priority}>{t(`goalsPage.filters.${priorityKey}`)}</option>
 );
 })}
 </Select>
 </div>

 <div>
 <label className="block text-sm font-medium text-content mb-1 sm:mb-2">
 {t('goalsPage.filters.search')}
 </label>
 <input
 type="text"
 value={filters.search || ''}
 onChange={(e) => handleFilterChange('search', e.target.value)}
 placeholder={t('goalsPage.filters.searchPlaceholder')}
 className="w-full px-3 py-2 text-base sm:text-sm bg-elevated border border-[var(--color-border)] rounded-lg focus:ring-2 focus:ring-[var(--color-ring)] focus:border-transparent transition-colors touch-manipulation"
 data-testid="goals-search-filter"
 />
 </div>
 </div>
 </div>
 );
});

GoalsFilters.displayName = 'GoalsFilters';
