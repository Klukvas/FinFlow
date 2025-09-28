import React, { useState, useEffect, useCallback } from 'react';

import { CreateCategoryRequest, Category } from '@/types';
import { useApiClients } from '@hooks';

interface EditCategoryProps {
  category: Category;
  onCategoryUpdated: () => void;
  onCancel: () => void;
}

export const EditCategory: React.FC<EditCategoryProps> = ({ 
  category, 
  onCategoryUpdated, 
  onCancel 
}) => {
  const { category: categoryApi } = useApiClients();
  const [formData, setFormData] = useState<CreateCategoryRequest>(() => {
    const baseData = {
      name: category.name,
      type: category.type,
    };
    return category.parent_id ? { ...baseData, parent_id: category.parent_id } : baseData;
  });
  const [parentCategories, setParentCategories] = useState<Category[]>([]);
  const [error, setError] = useState<string | null>(null);
  const [isLoading, setIsLoading] = useState(false);

  const fetchParentCategories = useCallback(async () => {
    try {
      const res = await categoryApi.getCategories(true); // Get flat list
      if (!('error' in res)) {
        // Filter out the current category and its children to prevent circular references
        const filteredCategories = res.filter(cat => 
          cat.id !== category.id && 
          !isChildCategory(cat, category.id, res)
        );
        setParentCategories(filteredCategories);
      }
    } catch (err) {
      console.error('Error fetching parent categories:', err);
    }
  }, [categoryApi, category.id]);

  // Helper function to check if a category is a child of the current category
  const isChildCategory = (cat: Category, parentId: number, allCategories: Category[]): boolean => {
    if (cat.parent_id === parentId) return true;
    if (cat.parent_id) {
      const parent = allCategories.find(c => c.id === cat.parent_id);
      return parent ? isChildCategory(parent, parentId, allCategories) : false;
    }
    return false;
  };

  useEffect(() => {
    fetchParentCategories();
  }, [fetchParentCategories]);

  const handleChange = (e: React.ChangeEvent<HTMLInputElement | HTMLSelectElement>) => {
    const { name, value } = e.target;
    setFormData(prev => ({
      ...prev,
      [name]: name === 'parent_id' ? (value ? parseInt(value) : undefined) : value
    }));
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setIsLoading(true);
    setError(null);

    try {
      const response = await categoryApi.updateCategory(category.id, formData);
      if ('error' in response) {
        setError(response.error);
      } else {
        onCategoryUpdated();
      }
    } catch (err) {
      setError('Ошибка при обновлении категории');
      console.error('Error updating category:', err);
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="w-full">
      <form
        onSubmit={handleSubmit}
        className="space-y-4 sm:space-y-6"
      >
        <div className="space-y-4 sm:space-y-6">
          <div className="space-y-2">
            <label className="block text-sm font-semibold theme-text-primary" htmlFor="name">
              Название категории
              <span className="text-red-500 ml-1">*</span>
            </label>
            <input
              type="text"
              id="name"
              name="name"
              value={formData.name}
              onChange={handleChange}
              placeholder="Введите название категории"
              className="w-full px-3 sm:px-4 py-3 theme-surface border theme-border rounded-lg sm:rounded-xl theme-text-primary placeholder-gray-400 focus:ring-2 focus:ring-blue-500 focus:border-transparent theme-transition shadow-sm hover:shadow-md focus:shadow-lg text-sm sm:text-base min-h-[44px]"
              required
            />
          </div>

          <div className="space-y-2">
            <label className="block text-sm font-semibold theme-text-primary" htmlFor="type">
              Тип категории
              <span className="text-red-500 ml-1">*</span>
            </label>
            <select
              id="type"
              name="type"
              value={formData.type}
              onChange={handleChange}
              className="w-full px-3 sm:px-4 py-3 theme-surface border theme-border rounded-lg sm:rounded-xl theme-text-primary focus:ring-2 focus:ring-blue-500 focus:border-transparent theme-transition shadow-sm hover:shadow-md focus:shadow-lg text-sm sm:text-base min-h-[44px]"
            >
              <option value="EXPENSE">Расходы</option>
              <option value="INCOME">Доходы</option>
            </select>
          </div>

          <div className="space-y-2">
            <label className="block text-sm font-semibold theme-text-primary" htmlFor="parent_id">
              Родительская категория
              <span className="theme-text-tertiary font-normal ml-1">(необязательно)</span>
            </label>
            <select
              id="parent_id"
              name="parent_id"
              value={formData.parent_id || ''}
              onChange={handleChange}
              className="w-full px-3 sm:px-4 py-3 theme-surface border theme-border rounded-lg sm:rounded-xl theme-text-primary focus:ring-2 focus:ring-blue-500 focus:border-transparent theme-transition shadow-sm hover:shadow-md focus:shadow-lg text-sm sm:text-base min-h-[44px]"
            >
              <option value="">Без родительской категории</option>
              {parentCategories.map((cat) => (
                <option key={cat.id} value={cat.id}>
                  {cat.name}
                </option>
              ))}
            </select>
          </div>

          {error && (
            <div className="theme-error-light border theme-border rounded-lg sm:rounded-xl p-3 sm:p-4">
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
        </div>

        <div className="flex flex-col sm:flex-row gap-3 pt-4">
          <button
            type="button"
            onClick={onCancel}
            className="flex-1 theme-surface hover:theme-surface-hover theme-text-primary font-semibold py-3 px-4 sm:px-6 rounded-lg sm:rounded-xl theme-transition flex items-center justify-center gap-2 sm:gap-3 border theme-border hover:shadow-md min-h-[44px] text-sm sm:text-base"
          >
            <svg className="w-4 h-4 sm:w-5 sm:h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
            </svg>
            Отмена
          </button>
          <button
            type="submit"
            disabled={isLoading}
            className="flex-1 bg-gradient-to-r from-blue-600 to-purple-600 hover:from-blue-700 hover:to-purple-700 text-white font-semibold py-3 px-4 sm:px-6 rounded-lg sm:rounded-xl theme-transition disabled:opacity-50 disabled:cursor-not-allowed flex items-center justify-center gap-2 sm:gap-3 shadow-lg hover:shadow-xl transform hover:-translate-y-0.5 disabled:transform-none min-h-[44px] text-sm sm:text-base"
          >
            {isLoading ? (
              <>
                <div className="relative">
                  <div className="animate-spin rounded-full h-4 w-4 sm:h-5 sm:w-5 border-2 border-white/30"></div>
                  <div className="animate-spin rounded-full h-4 w-4 sm:h-5 sm:w-5 border-2 border-white border-t-transparent absolute top-0 left-0"></div>
                </div>
                Сохранение...
              </>
            ) : (
              <>
                <svg className="w-4 h-4 sm:w-5 sm:h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
                </svg>
                Сохранить изменения
              </>
            )}
          </button>
        </div>
      </form>
    </div>
  );
};

export default EditCategory;
