import React from 'react';
import { useTranslation } from 'react-i18next';
import { Button } from '../shared/Button';
import { CategoryPageFilters, CATEGORY_TYPES, CATEGORY_TYPE_I18N_MAP } from './categoryHelpers';

interface CategoryFilterBarProps {
  filters: CategoryPageFilters;
  onFiltersChange: (filters: CategoryPageFilters) => void;
  isVisible: boolean;
}

export const CategoryFilterBar: React.FC<CategoryFilterBarProps> = ({
  filters,
  onFiltersChange,
  isVisible,
}) => {
  const { t } = useTranslation();

  if (!isVisible) return null;

  const update = (partial: Partial<CategoryPageFilters>) => {
    onFiltersChange({ ...filters, ...partial, page: 1 });
  };

  const clearAll = () => {
    onFiltersChange({ page: 1, size: filters.size, viewMode: filters.viewMode });
  };

  const hasActiveFilters =
    (filters.type && filters.type !== 'all') ||
    (filters.search && filters.search.trim() !== '');

  const inputClasses =
    'py-2 px-3 text-sm rounded-lg border theme-border theme-surface theme-text-primary focus:outline-none focus:ring-2 focus:ring-[var(--color-accent)] theme-transition';

  return (
    <div className="theme-surface border theme-border rounded-xl p-4 animate-in fade-in slide-in-from-top-2 duration-200">
      <div className="flex flex-wrap items-end gap-3">
        <div className="flex flex-col gap-1">
          <label className="text-xs font-medium theme-text-secondary">
            {t('categoryPage.filters.type')}
          </label>
          <select
            className={inputClasses}
            value={filters.type || 'all'}
            onChange={(e) => {
              const val = e.target.value;
              update({ type: val === 'all' ? undefined : (val as 'EXPENSE' | 'INCOME') });
            }}
          >
            <option value="all">{t('categoryPage.filters.allTypes')}</option>
            {CATEGORY_TYPES.map((type) => (
              <option key={type} value={type}>
                {t(CATEGORY_TYPE_I18N_MAP[type])}
              </option>
            ))}
          </select>
        </div>

        <div className="flex flex-col gap-1">
          <label className="text-xs font-medium theme-text-secondary">
            {t('categoryPage.filters.search')}
          </label>
          <input
            type="text"
            className={inputClasses}
            placeholder={t('categoryPage.filters.searchPlaceholder')}
            value={filters.search || ''}
            onChange={(e) => update({ search: e.target.value })}
          />
        </div>

        {/* View Mode Toggle */}
        <div className="flex flex-col gap-1">
          <label className="text-xs font-medium theme-text-secondary">&nbsp;</label>
          <div className="flex items-center rounded-lg border theme-border overflow-hidden">
            <button
              onClick={() => update({ viewMode: 'tree' })}
              className={`px-3 py-2 text-sm font-medium theme-transition ${
                filters.viewMode === 'tree'
                  ? 'theme-bg-primary theme-text-primary-contrast'
                  : 'theme-surface hover:theme-surface-hover theme-text-primary'
              }`}
            >
              {t('categoryPage.filters.viewTree')}
            </button>
            <button
              onClick={() => update({ viewMode: 'table' })}
              className={`px-3 py-2 text-sm font-medium theme-transition ${
                filters.viewMode === 'table'
                  ? 'theme-bg-primary theme-text-primary-contrast'
                  : 'theme-surface hover:theme-surface-hover theme-text-primary'
              }`}
            >
              {t('categoryPage.filters.viewTable')}
            </button>
          </div>
        </div>

        {hasActiveFilters && (
          <Button variant="ghost" size="sm" onClick={clearAll}>
            {t('categoryPage.filters.clearAll')}
          </Button>
        )}
      </div>
    </div>
  );
};
