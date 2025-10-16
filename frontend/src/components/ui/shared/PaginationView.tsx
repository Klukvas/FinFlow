import React, { useCallback, useEffect, useState } from 'react';
import { Pagination } from './Pagination';

interface PaginationViewProps<T> {
  // Data fetching function
  fetchData: (page: number, pageSize: number) => Promise<{
    items: T[];
    total: number;
    pages: number;
    page: number;
  }>;
  
  // Render function for the data
  renderContent: (items: T[], loading: boolean) => React.ReactNode;
  
  // Empty state render function
  renderEmpty?: (totalItems: number) => React.ReactNode;
  
  // Pagination configuration
  initialPage?: number;
  initialPageSize?: number;
  pageSizeOptions?: number[];
  showPageSizeSelector?: boolean;
  
  // Dependencies that should trigger refetch
  dependencies?: any[];
  
  // Additional props
  className?: string;
  'data-testid'?: string;
}

export function PaginationView<T>({
  fetchData,
  renderContent,
  renderEmpty,
  initialPage = 1,
  initialPageSize = 10,
  pageSizeOptions = [5, 10, 25, 50],
  showPageSizeSelector = true,
  dependencies = [],
  className = '',
  'data-testid': dataTestId = 'pagination-view'
}: PaginationViewProps<T>) {
  // State
  const [items, setItems] = useState<T[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  
  // Pagination state
  const [currentPage, setCurrentPage] = useState(initialPage);
  const [pageSize, setPageSize] = useState(initialPageSize);
  const [totalItems, setTotalItems] = useState(0);
  const [totalPages, setTotalPages] = useState(0);

  // Fetch data function
  const loadData = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const response = await fetchData(currentPage, pageSize);
      setItems(response.items);
      setTotalPages(response.pages);
      setTotalItems(response.total);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Ошибка при загрузке данных');
      console.error('Error fetching data:', err);
    } finally {
      setLoading(false);
    }
  }, [fetchData, currentPage, pageSize, ...dependencies]);

  // Pagination handlers
  const handlePageChange = useCallback((page: number) => {
    setCurrentPage(page);
  }, []);

  const handlePageSizeChange = useCallback((size: number) => {
    setPageSize(size);
    setCurrentPage(1); // Reset to first page when changing page size
  }, []);

  // Load data when dependencies change
  useEffect(() => {
    loadData();
  }, [loadData]);

  // Render empty state
  const renderEmptyState = () => {
    if (renderEmpty) {
      return renderEmpty(totalItems);
    }
    
    return (
      <div className="text-center py-8 sm:py-12 lg:py-16">
        <div className="w-16 h-16 sm:w-20 sm:h-20 lg:w-24 lg:h-24 mx-auto mb-4 sm:mb-6 theme-bg-tertiary rounded-xl sm:rounded-2xl flex items-center justify-center">
          <svg className="w-8 h-8 sm:w-10 sm:h-10 lg:w-12 lg:h-12 theme-text-tertiary" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
          </svg>
        </div>
        <h3 className="text-base sm:text-lg font-semibold theme-text-primary mb-2">
          {totalItems === 0 ? 'Данные пока не добавлены' : 'Нет данных на этой странице'}
        </h3>
        <p className="theme-text-secondary text-xs sm:text-sm max-w-md mx-auto px-4">
          {totalItems === 0 
            ? 'Добавьте первый элемент для начала работы'
            : 'Попробуйте перейти на другую страницу или изменить фильтры'
          }
        </p>
      </div>
    );
  };

  return (
    <div className={`w-full ${className}`} data-testid={dataTestId}>
      {/* Error state */}
      {error && (
        <div className="theme-error-light border theme-border rounded-lg sm:rounded-xl p-3 sm:p-4 mb-4 sm:mb-6">
          <div className="flex items-center gap-2 sm:gap-3">
            <div className="w-4 h-4 sm:w-5 sm:h-5 text-red-500 flex-shrink-0">
              <svg fill="currentColor" viewBox="0 0 20 20">
                <path fillRule="evenodd" d="M18 10a8 8 0 11-16 0 8 8 0 0116 0zm-7 4a1 1 0 11-2 0 1 1 0 012 0zm-1-9a1 1 0 00-1 1v4a1 1 0 102 0V6a1 1 0 00-1-1z" clipRule="evenodd" />
              </svg>
            </div>
            <p className="theme-error text-xs sm:text-sm font-medium">{error}</p>
          </div>
        </div>
      )}

      {/* Content */}
      {!items || items.length === 0 ? renderEmptyState() : renderContent(items, loading)}

      {/* Pagination */}
      {!loading && totalItems > 0 && (
        <div className="mt-6 sm:mt-8">
          <Pagination
            currentPage={currentPage}
            totalPages={totalPages}
            totalItems={totalItems}
            itemsPerPage={pageSize}
            onPageChange={handlePageChange}
            onPageSizeChange={handlePageSizeChange}
            showPageSizeSelector={showPageSizeSelector}
            pageSizeOptions={pageSizeOptions}
            data-testid={`${dataTestId}-pagination`}
          />
        </div>
      )}
    </div>
  );
}

export default PaginationView;
