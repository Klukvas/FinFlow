import React from 'react';

interface PaginationProps {
 currentPage: number;
 totalPages: number;
 totalItems: number;
 itemsPerPage: number;
 onPageChange: (page: number) => void;
 onPageSizeChange?: (size: number) => void;
 showPageSizeSelector?: boolean;
 pageSizeOptions?: number[];
 className?: string;
 'data-testid'?: string;
}

export const Pagination: React.FC<PaginationProps> = ({
 currentPage,
 totalPages,
 totalItems,
 itemsPerPage,
 onPageChange,
 onPageSizeChange,
 showPageSizeSelector = false,
 pageSizeOptions = [10, 25, 50, 100],
 className = '',
 'data-testid': dataTestId = 'pagination'
}) => {
 const startItem = (currentPage - 1) * itemsPerPage + 1;
 const endItem = Math.min(currentPage * itemsPerPage, totalItems);

 const getVisiblePages = () => {
 const delta = 2;
 const range = [];
 const rangeWithDots = [];

 for (let i = Math.max(2, currentPage - delta); i <= Math.min(totalPages - 1, currentPage + delta); i++) {
 range.push(i);
 }

 if (currentPage - delta > 2) {
 rangeWithDots.push(1, '...');
 } else {
 rangeWithDots.push(1);
 }

 rangeWithDots.push(...range);

 if (currentPage + delta < totalPages - 1) {
 rangeWithDots.push('...', totalPages);
 } else if (totalPages > 1) {
 rangeWithDots.push(totalPages);
 }

 return rangeWithDots;
 };

 if (totalPages <= 1) {
 return null;
 }

 const visiblePages = getVisiblePages();

 return (
 <div className={`flex flex-col sm:flex-row items-center justify-between gap-4 ${className}`} data-testid={dataTestId}>
 {/* Items info */}
 <div className="flex items-center gap-2 text-sm text-content-secondary">
 <span>
 Показано {startItem}-{endItem} из {totalItems}
 </span>
 {showPageSizeSelector && onPageSizeChange && (
 <div className="flex items-center gap-2">
 <span>на странице:</span>
 <select
 value={itemsPerPage}
 onChange={(e) => onPageSizeChange(Number(e.target.value))}
 className="px-2 py-1 bg-elevated border border-[var(--border)] rounded text-sm focus:outline-none focus:ring-2 focus:ring-[var(--accent)]"
 data-testid="page-size-selector"
 >
 {pageSizeOptions.map(size => (
 <option key={size} value={size}>{size}</option>
 ))}
 </select>
 </div>
 )}
 </div>

 {/* Pagination controls */}
 <div className="flex items-center gap-1">
 {/* Previous button */}
 <button
 onClick={() => onPageChange(currentPage - 1)}
 disabled={currentPage === 1}
 className="px-3 py-2 bg-elevated border border-[var(--border)] rounded-lg disabled:opacity-50 disabled:cursor-not-allowed hover:bg-surface-alt transition-colors flex items-center gap-1 text-sm"
 data-testid="pagination-prev"
 >
 <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
 <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 19l-7-7 7-7" />
 </svg>
 Назад
 </button>

 {/* Page numbers */}
 <div className="flex items-center gap-1">
 {visiblePages.map((page, index) => (
 <React.Fragment key={index}>
 {page === '...' ? (
 <span className="px-3 py-2 text-content-secondary">...</span>
 ) : (
 <button
 onClick={() => onPageChange(page as number)}
 className={`px-3 py-2 rounded-lg text-sm font-medium transition-colors ${
 currentPage === page
 ? 'bg-accent-base text-white'
 : 'bg-elevated border border-[var(--border)] hover:bg-surface-alt text-content'
 }`}
 data-testid={`pagination-page-${page}`}
 >
 {page}
 </button>
 )}
 </React.Fragment>
 ))}
 </div>

 {/* Next button */}
 <button
 onClick={() => onPageChange(currentPage + 1)}
 disabled={currentPage === totalPages}
 className="px-3 py-2 bg-elevated border border-[var(--border)] rounded-lg disabled:opacity-50 disabled:cursor-not-allowed hover:bg-surface-alt transition-colors flex items-center gap-1 text-sm"
 data-testid="pagination-next"
 >
 Вперед
 <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
 <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5l7 7-7 7" />
 </svg>
 </button>
 </div>
 </div>
 );
};

export default Pagination;
