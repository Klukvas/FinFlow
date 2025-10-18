import React, { useCallback, useState } from 'react';
import { useTranslation } from 'react-i18next';
import { Category } from '@types';
import { useApiClients } from '@hooks';
import { useErrorHandler } from '@/hooks/useErrorHandler';
import { DeleteButton, EditButton, PaginationView } from '@/components/ui';

interface CategoryListProps {
  key?: number;
  onEditCategory?: (category: Category) => void;
  onCategoryClick?: (category: Category) => void;
  initialPageSize?: number;
}

// Helper function to flatten categories and find parent names
const flattenCategories = (categories: Category[] | undefined, parentName?: string): Array<Category & { parentName?: string | undefined }> => {
  if (!categories || !Array.isArray(categories)) {
    return [];
  }
  
  let result: Array<Category & { parentName?: string | undefined }> = [];
  
  categories.forEach(category => {
    result.push({ ...category, parentName });
    if (category.children && category.children.length > 0) {
      result = result.concat(flattenCategories(category.children, category.name));
    }
  });
  
  return result;
};

export const CategoryList: React.FC<CategoryListProps> = ({ 
  onEditCategory, 
  onCategoryClick, 
  initialPageSize = 10 
}) => {
  const { t } = useTranslation();
  const [deletingId, setDeletingId] = useState<number | null>(null);
  const [showFlat, setShowFlat] = useState(false);
  
  const { category } = useApiClients();
  const { handleCategoryError } = useErrorHandler();

  const handleDelete = async (id: number) => {
    setDeletingId(id);
    try {
      const response = await category.deleteCategory(id);
      
      if (!response || 'error' in response) {
        // Handle API error with errorCode
        handleCategoryError(response, true);
        return; // Don't refresh data if there was an error
      }
      // The PaginationView will handle refreshing the data
    } catch (err) {
      // Handle network or other errors
      handleCategoryError(err as Error, true);
    } finally {
      setDeletingId(null);
    }
  };

  const handleToggleFlat = useCallback(() => {
    setShowFlat(!showFlat);
  }, [showFlat]);

  const handleEdit = (category: Category) => {
    if (onEditCategory) {
      onEditCategory(category);
    }
  };

  const handleCategoryClick = (category: Category) => {
    if (onCategoryClick) {
      onCategoryClick(category);
    }
  };

  // Fetch categories data for PaginationView
  const fetchCategories = useCallback(async (page: number, pageSize: number) => {
    try {
      const response = await category.getCategoriesPaginated({
        flat: showFlat,
        page,
        size: pageSize
      });
      
      if ('error' in response) {
        // Handle API error with errorCode
        handleCategoryError(response, true);
        throw new Error(response.error);
      }
      
      return {
        items: response.items,
        total: response.total,
        pages: response.pages,
        page: response.page
      };
    } catch (err) {
      // Handle network or other errors
      handleCategoryError(err as Error, true);
      throw err;
    }
  }, [category, showFlat, handleCategoryError]);

  // Render function for categories
  const renderCategories = (categories: Category[], loading: boolean) => {
    if (loading) {
      return (
        <div className="text-center py-8 sm:py-12 lg:py-16">
          <div className="w-16 h-16 sm:w-20 sm:h-20 lg:w-24 lg:h-24 mx-auto mb-4 sm:mb-6 theme-bg-tertiary rounded-xl sm:rounded-2xl flex items-center justify-center">
            <div className="animate-spin w-8 h-8 sm:w-10 sm:h-10 lg:w-12 lg:h-12 border-2 border-blue-500 border-t-transparent rounded-full"></div>
          </div>
          <h3 className="text-base sm:text-lg font-semibold theme-text-primary mb-2">{t('category.list.loading')}</h3>
          <p className="theme-text-secondary text-xs sm:text-sm max-w-md mx-auto px-4">
            {t('category.list.loadingSubtitle')}
          </p>
        </div>
      );
    }

    const flattenedCategories = flattenCategories(categories) || [];

    return (
      <div className="relative w-full">
        {/* Mobile Cards View */}
        <div className="block lg:hidden space-y-3 sm:space-y-4">
          {flattenedCategories?.map((category) => (
            <div 
              key={category.id}
              className="theme-bg-secondary rounded-lg sm:rounded-xl border theme-border p-3 sm:p-4 hover:shadow-lg hover:-translate-y-1 transition-all duration-200 cursor-pointer"
              onClick={() => handleCategoryClick(category)}
            >
              <div className="flex items-start justify-between mb-2 sm:mb-3">
                <div className="flex-1 min-w-0">
                  <h3 className="font-semibold theme-text-primary text-sm sm:text-base mb-1 truncate">
                    {category.name}
                  </h3>
                  <div className="flex items-center gap-1 sm:gap-2 mb-2">
                    <span className={`inline-flex px-2 py-1 text-xs font-medium rounded-full ${
                      category.type === 'INCOME' 
                        ? 'theme-success-light theme-success' 
                        : 'theme-error-light theme-error'
                    }`}>
                      {category.type === 'INCOME' ? t('category.income') : t('category.expense')}
                    </span>
                    <span className="text-xs theme-text-secondary">
                      #{category.id}
                    </span>
                  </div>
                  <p className="text-xs sm:text-sm theme-text-secondary truncate">
                    {category.parentName || (
                      <span className="italic">{t('category.list.rootCategory')}</span>
                    )}
                  </p>
                </div>
                <div 
                  className="flex items-center gap-1 ml-2 sm:ml-3 flex-shrink-0"
                  onClick={(e) => e.stopPropagation()}
                >
                  <EditButton
                    onEdit={() => handleEdit(category)}
                    variant="icon"
                    size="sm"
                  />
                  <DeleteButton
                    onDelete={() => handleDelete(category.id)}
                    disabled={deletingId === category.id}
                    loading={deletingId === category.id}
                    variant="icon"
                    size="sm"
                  />
                </div>
              </div>
            </div>
          ))}
        </div>

        {/* Desktop Table View */}
        <div className="hidden lg:block relative w-full">
          <div className="overflow-hidden rounded-xl border theme-border">
            <table className="w-full">
              <thead className="theme-bg-secondary">
                <tr>
                  <th className="px-6 py-4 text-left text-xs font-semibold theme-text-secondary uppercase tracking-wider">
                    {t('category.list.name')}
                  </th>
                  <th className="px-6 py-4 text-left text-xs font-semibold theme-text-secondary uppercase tracking-wider">
                    {t('category.list.type')}
                  </th>
                  <th className="px-6 py-4 text-left text-xs font-semibold theme-text-secondary uppercase tracking-wider">
                    {t('category.list.parentCategory')}
                  </th>
                  <th className="px-6 py-4 text-left text-xs font-semibold theme-text-secondary uppercase tracking-wider">
                    {t('category.list.id')}
                  </th>
                  <th className="px-6 py-4 text-right text-xs font-semibold theme-text-secondary uppercase tracking-wider">
                    {t('category.list.actions')}
                  </th>
                </tr>
              </thead>
              <tbody className="theme-surface divide-y theme-border">
                {flattenedCategories?.map((category) => (
                  <tr 
                    key={category.id}
                    data-testid={`table-category-${category.name.toLowerCase().replace(/\s+/g, '-')}`}
                    className="hover:theme-surface-hover transition-colors duration-150 cursor-pointer group"
                    onClick={() => handleCategoryClick(category)}
                  >
                    <td className="px-6 py-4">
                      <div className="flex items-center gap-3">
                        <div className={`w-2 h-2 rounded-full ${
                          category.type === 'INCOME' 
                            ? 'bg-green-500' 
                            : 'bg-red-500'
                        }`}></div>
                        <div data-testid='category-name' className="font-medium theme-text-primary">
                          {category.name}
                        </div>
                      </div>
                    </td>
                    <td className="px-6 py-4">
                      <span data-testid='category-type' className={`inline-flex px-3 py-1 text-xs font-medium rounded-full ${
                        category.type === 'INCOME' 
                          ? 'theme-success-light theme-success' 
                          : 'theme-error-light theme-error'
                      }`}>
                        {category.type === 'INCOME' ? t('category.income') : t('category.expense')}
                      </span>
                    </td>
                    <td className="px-6 py-4">
                      <div data-testid='category-parent-name' className="text-sm theme-text-secondary">
                        {category.parentName || (
                          <span className="theme-text-tertiary italic">{t('category.list.rootCategory')}</span>
                        )}
                      </div>
                    </td>
                    <td className="px-6 py-4">
                      <div data-testid='category-id' className="text-sm font-mono theme-text-secondary">
                        #{category.id}
                      </div>
                    </td>
                    <td className="px-6 py-4 text-right">
                      <div 
                        className="flex items-center justify-end gap-2 transition-opacity duration-150"
                        onClick={(e) => e.stopPropagation()}
                      >
                        <EditButton
                          dataTestId='category-edit-button'
                          onEdit={() => handleEdit(category)}
                          variant="icon"
                          size="sm"
                        />
                        <DeleteButton
                          data-testid='category-delete-button'
                          onDelete={() => handleDelete(category.id)}
                          disabled={deletingId === category.id}
                          loading={deletingId === category.id}
                          variant="icon"
                          size="sm"
                        />
                      </div>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      </div>
    );
  };

  // Render function for empty state
  const renderEmpty = (totalItems: number) => (
    <div className="text-center py-8 sm:py-12 lg:py-16">
      <div className="w-16 h-16 sm:w-20 sm:h-20 lg:w-24 lg:h-24 mx-auto mb-4 sm:mb-6 theme-bg-tertiary rounded-xl sm:rounded-2xl flex items-center justify-center">
        <svg className="w-8 h-8 sm:w-10 sm:h-10 lg:w-12 lg:h-12 theme-text-tertiary" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M19 11H5m14 0a2 2 0 012 2v6a2 2 0 01-2 2H5a2 2 0 01-2-2v-6a2 2 0 012-2m14 0V9a2 2 0 00-2-2M5 11V9a2 2 0 012-2m0 0V5a2 2 0 012-2h6a2 2 0 012 2v2M7 7h10" />
        </svg>
      </div>
      <h3 className="text-base sm:text-lg font-semibold theme-text-primary mb-2">
        {totalItems === 0 ? t('category.list.noCategoriesAtAll') : t('category.list.noCategoriesOnPage')}
      </h3>
      <p className="theme-text-secondary text-xs sm:text-sm max-w-md mx-auto px-4">
        {totalItems === 0 
          ? t('category.list.noCategoriesSubtitle')
          : t('category.list.noCategoriesOnPageSubtitle')
        }
      </p>
    </div>
  );

  return (
    <div className="w-full">
      <div className="theme-bg-secondary px-4 sm:px-6 py-3 sm:py-4 lg:px-8 lg:py-6">
        <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4">
          <div className="flex items-center gap-2 sm:gap-3">
            <div className="w-6 h-6 sm:w-8 sm:h-8 bg-gradient-to-br from-blue-500 to-purple-600 rounded-lg flex items-center justify-center">
              <svg className="w-4 h-4 sm:w-5 sm:h-5 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 11H5m14 0a2 2 0 012 2v6a2 2 0 01-2 2H5a2 2 0 01-2-2v-6a2 2 0 012-2m14 0V9a2 2 0 00-2-2M5 11V9a2 2 0 012-2m0 0V5a2 2 0 012-2h6a2 2 0 012 2v2M7 7h10" />
              </svg>
            </div>
            <h2 className="text-lg sm:text-xl lg:text-2xl font-bold theme-text-primary">{t('category.title')}</h2>
          </div>
          
          {/* View Toggle */}
          <div className="flex items-center gap-2">
            <button
              onClick={handleToggleFlat}
              className={`px-3 py-2 rounded-lg text-sm font-medium theme-transition ${
                !showFlat
                  ? 'theme-bg-primary theme-text-primary-contrast'
                  : 'theme-surface border theme-border hover:theme-surface-hover theme-text-primary'
              }`}
              data-testid="hierarchical-view-toggle"
            >
              {t('category.list.hierarchicalView')}
            </button>
            <button
              onClick={handleToggleFlat}
              className={`px-3 py-2 rounded-lg text-sm font-medium theme-transition ${
                showFlat
                  ? 'theme-bg-primary theme-text-primary-contrast'
                  : 'theme-surface border theme-border hover:theme-surface-hover theme-text-primary'
              }`}
              data-testid="flat-view-toggle"
            >
              {t('category.list.flatView')}
            </button>
          </div>
        </div>
      </div>
      
      <div className="p-4 sm:p-6 lg:p-8">
        <PaginationView
          fetchData={fetchCategories}
          renderContent={renderCategories}
          renderEmpty={renderEmpty}
          initialPageSize={initialPageSize}
          pageSizeOptions={[5, 10, 25, 50]}
          showPageSizeSelector={true}
          dependencies={[deletingId, showFlat]} // Refresh when delete operation completes or view mode changes
          data-testid="category-list"
        />
      </div>
    </div>
  );
};

export default CategoryList;
