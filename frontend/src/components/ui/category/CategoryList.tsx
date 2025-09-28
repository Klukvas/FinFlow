import React, { useCallback, useEffect, useState } from 'react';
import { Category } from '@types';
import { useApiClients } from '@hooks';
import { DeleteButton, EditButton } from '@/components/ui';

interface CategoryListProps {
  key?: number;
  onEditCategory?: (category: Category) => void;
  onCategoryClick?: (category: Category) => void;
}

// Helper function to flatten categories and find parent names
const flattenCategories = (categories: Category[], parentName?: string): Array<Category & { parentName?: string | undefined }> => {
  let result: Array<Category & { parentName?: string | undefined }> = [];
  
  categories.forEach(category => {
    result.push({ ...category, parentName });
    if (category.children && category.children.length > 0) {
      result = result.concat(flattenCategories(category.children, category.name));
    }
  });
  
  return result;
};

export const CategoryList: React.FC<CategoryListProps> = ({ onEditCategory, onCategoryClick }) => {
  const [categories, setCategories] = useState<Category[]>([]);
  const [error, setError] = useState<string | null>(null);
  const [deletingId, setDeletingId] = useState<number | null>(null);
  const { category } = useApiClients();

  const fetchCategories = useCallback(async () => {
    try {
      const res = await category.getCategories();
      if ('error' in res) {
        setError(res.error);
      } else {
        setCategories(res);
      }
    } catch (err) {
      setError('Ошибка при загрузке категорий');
      console.error('Error fetching categories:', err);
    }
  }, [category]);

  const handleDelete = async (id: number) => {
    setDeletingId(id);
    try {
      const response = await category.deleteCategory(id);
      if (!response || 'error' in response) {
        setError(response?.error || 'Ошибка при удалении категории');
      } else {
        // Recursively remove category and its children from the tree
        const removeCategory = (cats: Category[]): Category[] => {
          return cats.filter(cat => {
            if (cat.id === id) return false;
            if (cat.children) {
              cat.children = removeCategory(cat.children);
            }
            return true;
          });
        };
        setCategories(prev => removeCategory(prev));
      }
    } catch (err) {
      setError('Ошибка при удалении категории');
      console.error('Error deleting category:', err);
    } finally {
      setDeletingId(null);
    }
  };

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

  useEffect(() => {
    fetchCategories();
  }, [fetchCategories]);

  const flattenedCategories = flattenCategories(categories);

  return (
    <div className="w-full">
      <div className="theme-bg-secondary px-4 sm:px-6 py-3 sm:py-4 lg:px-8 lg:py-6">
        <div className="flex items-center gap-2 sm:gap-3">
          <div className="w-6 h-6 sm:w-8 sm:h-8 bg-gradient-to-br from-blue-500 to-purple-600 rounded-lg flex items-center justify-center">
            <svg className="w-4 h-4 sm:w-5 sm:h-5 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 11H5m14 0a2 2 0 012 2v6a2 2 0 01-2 2H5a2 2 0 01-2-2v-6a2 2 0 012-2m14 0V9a2 2 0 00-2-2M5 11V9a2 2 0 012-2m0 0V5a2 2 0 012-2h6a2 2 0 012 2v2M7 7h10" />
            </svg>
          </div>
          <h2 className="text-lg sm:text-xl lg:text-2xl font-bold theme-text-primary">Категории</h2>
          <span className="theme-surface theme-text-secondary text-xs sm:text-sm font-medium px-2 sm:px-3 py-1 rounded-full">
            {categories.length}
          </span>
        </div>
      </div>
      
      <div className="p-4 sm:p-6 lg:p-8">
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
        
        {categories.length === 0 ? (
          <div className="text-center py-8 sm:py-12 lg:py-16">
            <div className="w-16 h-16 sm:w-20 sm:h-20 lg:w-24 lg:h-24 mx-auto mb-4 sm:mb-6 theme-bg-tertiary rounded-xl sm:rounded-2xl flex items-center justify-center">
              <svg className="w-8 h-8 sm:w-10 sm:h-10 lg:w-12 lg:h-12 theme-text-tertiary" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M19 11H5m14 0a2 2 0 012 2v6a2 2 0 01-2 2H5a2 2 0 01-2-2v-6a2 2 0 012-2m14 0V9a2 2 0 00-2-2M5 11V9a2 2 0 012-2m0 0V5a2 2 0 012-2h6a2 2 0 012 2v2M7 7h10" />
              </svg>
            </div>
            <h3 className="text-base sm:text-lg font-semibold theme-text-primary mb-2">Категории пока не созданы</h3>
            <p className="theme-text-secondary text-xs sm:text-sm max-w-md mx-auto px-4">
              Создайте первую категорию для организации ваших доходов и расходов
            </p>
          </div>
        ) : (
          <div className="relative w-full">
            {/* Mobile Cards View */}
            <div className="block lg:hidden space-y-3 sm:space-y-4">
              {flattenedCategories.map((category) => (
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
                          {category.type === 'INCOME' ? 'Доходы' : 'Расходы'}
                        </span>
                        <span className="text-xs theme-text-secondary">
                          #{category.id}
                        </span>
                      </div>
                      <p className="text-xs sm:text-sm theme-text-secondary truncate">
                        {category.parentName || (
                          <span className="italic">Корневая категория</span>
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
                        Название
                      </th>
                      <th className="px-6 py-4 text-left text-xs font-semibold theme-text-secondary uppercase tracking-wider">
                        Тип
                      </th>
                      <th className="px-6 py-4 text-left text-xs font-semibold theme-text-secondary uppercase tracking-wider">
                        Родительская категория
                      </th>
                      <th className="px-6 py-4 text-left text-xs font-semibold theme-text-secondary uppercase tracking-wider">
                        ID
                      </th>
                      <th className="px-6 py-4 text-right text-xs font-semibold theme-text-secondary uppercase tracking-wider">
                        Действия
                      </th>
                    </tr>
                  </thead>
                  <tbody className="theme-surface divide-y theme-border">
                    {flattenedCategories.map((category) => (
                      <tr 
                        key={category.id} 
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
                            <div className="font-medium theme-text-primary">
                              {category.name}
                            </div>
                          </div>
                        </td>
                        <td className="px-6 py-4">
                          <span className={`inline-flex px-3 py-1 text-xs font-medium rounded-full ${
                            category.type === 'INCOME' 
                              ? 'theme-success-light theme-success' 
                              : 'theme-error-light theme-error'
                          }`}>
                            {category.type === 'INCOME' ? 'Доходы' : 'Расходы'}
                          </span>
                        </td>
                        <td className="px-6 py-4">
                          <div className="text-sm theme-text-secondary">
                            {category.parentName || (
                              <span className="theme-text-tertiary italic">Корневая категория</span>
                            )}
                          </div>
                        </td>
                        <td className="px-6 py-4">
                          <div className="text-sm font-mono theme-text-secondary">
                            #{category.id}
                          </div>
                        </td>
                        <td className="px-6 py-4 text-right">
                          <div 
                            className="flex items-center justify-end gap-2 opacity-0 group-hover:opacity-100 transition-opacity duration-150"
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
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </div>
          </div>
        )}
      </div>
    </div>
  );
};

export default CategoryList;
