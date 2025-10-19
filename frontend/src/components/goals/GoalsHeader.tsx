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
    <div className="flex flex-col gap-3 sm:gap-4 mb-4 sm:mb-6">
      {/* Search Input */}
      <div className="w-full">
        <div className="relative">
          <FaSearch className="absolute left-3 top-1/2 transform -translate-y-1/2 text-gray-400 w-4 h-4" />
          <input
            type="text"
            placeholder="Поиск целей..."
            value={searchTerm}
            onChange={(e) => onSearchChange(e.target.value)}
            className="w-full pl-10 pr-4 py-3 sm:py-2 text-base sm:text-sm theme-surface border theme-border rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent theme-transition touch-manipulation"
            data-testid="goals-search"
          />
        </div>
      </div>
      
      {/* Action Buttons */}
      <div className="flex flex-col sm:flex-row gap-2 sm:gap-3">
        <Button
          variant="outline"
          onClick={onToggleFilters}
          className="flex items-center justify-center gap-2 py-3 sm:py-2 min-h-[44px] touch-manipulation"
          data-testid="goals-filter-toggle"
        >
          <FaFilter className="w-4 h-4" />
          <span className="hidden xs:inline">Фильтры</span>
          <span className="xs:hidden">Фильтры</span>
        </Button>
        
        <Button
          onClick={onShowCreateModal}
          className="flex items-center justify-center gap-2 py-3 sm:py-2 min-h-[44px] touch-manipulation"
          data-testid="goals-create-button"
        >
          <FaPlus className="w-4 h-4" />
          <span className="hidden xs:inline">Создать цель</span>
          <span className="xs:hidden">Создать</span>
        </Button>
      </div>
    </div>
  );
});

GoalsHeader.displayName = 'GoalsHeader';
