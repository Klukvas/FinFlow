import React from 'react';
import { Button } from '@/components/ui/shared/Button';
import { FaPlus, FaSearch, FaFilter } from 'react-icons/fa';

interface GoalsHeaderProps {
  onShowCreateModal: () => void;
  onToggleFilters: () => void;
  showFilters: boolean;
  searchTerm: string;
  onSearchChange: (value: string) => void;
}

export const GoalsHeader = React.memo<GoalsHeaderProps>(({
  onShowCreateModal,
  onToggleFilters,
  showFilters,
  searchTerm,
  onSearchChange,
}) => {
  return (
    <div className="flex flex-col sm:flex-row gap-4 mb-6">
      <div className="flex-1">
        <div className="relative">
          <FaSearch className="absolute left-3 top-1/2 transform -translate-y-1/2 text-gray-400" />
          <input
            type="text"
            placeholder="Поиск целей..."
            value={searchTerm}
            onChange={(e) => onSearchChange(e.target.value)}
            className="w-full pl-10 pr-4 py-2 theme-surface border theme-border rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent theme-transition"
            data-testid="goals-search"
          />
        </div>
      </div>
      
      <div className="flex gap-2">
        <Button
          variant="outline"
          onClick={onToggleFilters}
          className="flex items-center gap-2"
          data-testid="goals-filter-toggle"
        >
          <FaFilter />
          Фильтры
        </Button>
        
        <Button
          onClick={onShowCreateModal}
          className="flex items-center gap-2"
          data-testid="goals-create-button"
        >
          <FaPlus />
          Создать цель
        </Button>
      </div>
    </div>
  );
});

GoalsHeader.displayName = 'GoalsHeader';
