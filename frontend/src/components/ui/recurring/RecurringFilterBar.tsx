import React from 'react';
import { useTranslation } from 'react-i18next';
import { Button } from '../shared/Button';
import { RecurringFilters, SCHEDULE_TYPE_I18N_MAP } from './recurringHelpers';
import type { ScheduleType, RecurringStatus } from './recurringHelpers';

interface RecurringFilterBarProps {
  filters: RecurringFilters;
  onFiltersChange: (filters: RecurringFilters) => void;
  isVisible: boolean;
}

export const RecurringFilterBar: React.FC<RecurringFilterBarProps> = ({
  filters,
  onFiltersChange,
  isVisible,
}) => {
  const { t } = useTranslation();

  if (!isVisible) return null;

  const update = (partial: Partial<RecurringFilters>) => {
    onFiltersChange({ ...filters, ...partial, page: 1 });
  };

  const clearAll = () => {
    onFiltersChange({ page: 1, size: filters.size });
  };

  const hasActiveFilters =
    (filters.status && filters.status !== 'all') ||
    (filters.payment_type && filters.payment_type !== 'all') ||
    (filters.schedule_type && filters.schedule_type !== 'all');

  const inputClasses =
    'py-2 px-3 text-sm rounded-lg border theme-border theme-surface theme-text-primary focus:outline-none focus:ring-2 focus:ring-[var(--color-accent)] theme-transition';

  const scheduleTypes: ScheduleType[] = ['daily', 'weekly', 'monthly', 'yearly'];

  return (
    <div className="theme-surface border theme-border rounded-xl p-4 animate-in fade-in slide-in-from-top-2 duration-200">
      <div className="flex flex-wrap items-end gap-3">
        <div className="flex flex-col gap-1">
          <label className="text-xs font-medium theme-text-secondary">
            {t('recurringPage.filters.status')}
          </label>
          <select
            className={inputClasses}
            value={filters.status || 'all'}
            onChange={(e) => {
              const val = e.target.value as RecurringStatus | 'all';
              update({ status: val === 'all' ? undefined : val });
            }}
          >
            <option value="all">{t('recurringPage.filters.allStatuses')}</option>
            <option value="active">{t('recurringPage.status.active')}</option>
            <option value="paused">{t('recurringPage.status.paused')}</option>
            <option value="completed">{t('recurringPage.status.completed')}</option>
            <option value="cancelled">{t('recurringPage.status.cancelled')}</option>
          </select>
        </div>

        <div className="flex flex-col gap-1">
          <label className="text-xs font-medium theme-text-secondary">
            {t('recurringPage.filters.paymentType')}
          </label>
          <select
            className={inputClasses}
            value={filters.payment_type || 'all'}
            onChange={(e) => {
              const val = e.target.value as 'expense' | 'income' | 'all';
              update({ payment_type: val === 'all' ? undefined : val });
            }}
          >
            <option value="all">{t('recurringPage.filters.allTypes')}</option>
            <option value="expense">{t('recurringPage.types.expense')}</option>
            <option value="income">{t('recurringPage.types.income')}</option>
          </select>
        </div>

        <div className="flex flex-col gap-1">
          <label className="text-xs font-medium theme-text-secondary">
            {t('recurringPage.filters.frequency')}
          </label>
          <select
            className={inputClasses}
            value={filters.schedule_type || 'all'}
            onChange={(e) => {
              const val = e.target.value as ScheduleType | 'all';
              update({ schedule_type: val === 'all' ? undefined : val });
            }}
          >
            <option value="all">{t('recurringPage.filters.allFrequencies')}</option>
            {scheduleTypes.map((st) => (
              <option key={st} value={st}>
                {t(SCHEDULE_TYPE_I18N_MAP[st])}
              </option>
            ))}
          </select>
        </div>

        {hasActiveFilters && (
          <Button variant="ghost" size="sm" onClick={clearAll}>
            {t('recurringPage.filters.clearAll')}
          </Button>
        )}
      </div>
    </div>
  );
};
