import React from 'react';
import { useTranslation } from 'react-i18next';
import { Button } from '../shared/Button';
import { Badge } from '../shared/Badge';
import { useWorkspace } from '../../../contexts/WorkspaceContext';

interface RecurringPageHeaderProps {
  onAdd: () => void;
  onToggleFilters: () => void;
  onExportCsv: () => void;
  filtersActive: boolean;
}

export const RecurringPageHeader: React.FC<RecurringPageHeaderProps> = ({
  onAdd,
  onToggleFilters,
  onExportCsv,
  filtersActive,
}) => {
  const { t } = useTranslation();
  const { workspaces, currentWorkspace } = useWorkspace();
  const showWorkspaceBadge = workspaces.length > 1 && currentWorkspace;

  return (
    <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
      <div className="flex items-center gap-3">
        <div>
          <h1 className="text-2xl font-semibold theme-text-primary">
            {t('recurringPage.title')}
          </h1>
          <p className="text-sm theme-text-secondary mt-0.5">
            {t('recurringPage.subtitle')}
          </p>
        </div>
        {showWorkspaceBadge && (
          <Badge variant="secondary" size="sm">
            {currentWorkspace.name}
          </Badge>
        )}
      </div>

      <div className="flex items-center gap-2">
        <Button
          variant="outline"
          size="sm"
          onClick={onToggleFilters}
          className={filtersActive ? 'theme-accent-light theme-accent' : ''}
        >
          <svg className="w-4 h-4 mr-1.5" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
            <path strokeLinecap="round" strokeLinejoin="round" d="M3 4a1 1 0 011-1h16a1 1 0 011 1v2.586a1 1 0 01-.293.707l-6.414 6.414a1 1 0 00-.293.707V17l-4 4v-6.586a1 1 0 00-.293-.707L3.293 7.293A1 1 0 013 6.586V4z" />
          </svg>
          {t('recurringPage.filters.toggle')}
        </Button>
        <Button variant="outline" size="sm" onClick={onExportCsv}>
          <svg className="w-4 h-4 mr-1.5" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
            <path strokeLinecap="round" strokeLinejoin="round" d="M4 16v1a3 3 0 003 3h10a3 3 0 003-3v-1m-4-4l-4 4m0 0l-4-4m4 4V4" />
          </svg>
          {t('recurringPage.exportButton')}
        </Button>
        <Button variant="primary" size="sm" onClick={onAdd}>
          <svg className="w-4 h-4 mr-1.5" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
            <path strokeLinecap="round" strokeLinejoin="round" d="M12 4v16m8-8H4" />
          </svg>
          {t('recurringPage.addButton')}
        </Button>
      </div>
    </div>
  );
};
