import React, { useState, useEffect, useCallback } from 'react';

import { CreateCategoryRequest, Category } from '@/types';
import { useApiClients } from '@hooks';

interface CreateCategoryProps {
  onCategoryCreated: () => void;
}

export const CreateCategory: React.FC<CreateCategoryProps> = ({ onCategoryCreated }) => {
  const { category } = useApiClients();
  const [formData, setFormData] = useState<CreateCategoryRequest>({
    name: '',
    type: 'EXPENSE',
  });
  const [parentCategories, setParentCategories] = useState<Category[]>([]);
  const [error, setError] = useState<string | null>(null);
  const [isLoading, setIsLoading] = useState(false);

  const fetchParentCategories = useCallback(async () => {
    try {
      const res = await category.getCategories(true); // Get flat list
      if (!('error' in res)) {
        setParentCategories(res);
      }
    } catch (err) {
      console.error('Error fetching parent categories:', err);
    }
  }, [category]);

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
      const response = await category.createCategory(formData);
      if ('error' in response) {
        setError(response.error);
      } else {
        setFormData({ name: '', type: 'EXPENSE' });
        // Refresh parent categories dropdown
        await fetchParentCategories();
        onCategoryCreated();
      }
    } catch (err) {
      setError('Ошибка при создании категории');
      console.error('Error creating category:', err);
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

        <button
          type="submit"
          disabled={isLoading}
          className="w-full bg-gradient-to-r from-blue-600 to-purple-600 hover:from-blue-700 hover:to-purple-700 text-white font-semibold py-3 sm:py-3 px-4 sm:px-6 rounded-lg sm:rounded-xl theme-transition disabled:opacity-50 disabled:cursor-not-allowed flex items-center justify-center gap-2 sm:gap-3 shadow-lg hover:shadow-xl transform hover:-translate-y-0.5 disabled:transform-none min-h-[44px] text-sm sm:text-base"
        >
          {isLoading ? (
            <>
              <div className="relative">
                <div className="animate-spin rounded-full h-4 w-4 sm:h-5 sm:w-5 border-2 border-white/30"></div>
                <div className="animate-spin rounded-full h-4 w-4 sm:h-5 sm:w-5 border-2 border-white border-t-transparent absolute top-0 left-0"></div>
              </div>
              Создание...
            </>
          ) : (
            <>
              <svg className="w-4 h-4 sm:w-5 sm:h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 6v6m0 0v6m0-6h6m-6 0H6" />
              </svg>
              Создать категорию
            </>
          )}
        </button>
      </form>
    </div>
  );
};

export default CreateCategory;
