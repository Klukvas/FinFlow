import React, { useState, useEffect, useCallback, useMemo } from 'react';
import { useTranslation } from 'react-i18next';

import { CreateCategoryRequest, Category } from '@/types';
import { useApiClients } from '@hooks';
import { FormErrorHandler } from '@/utils/formErrorHandler';

interface CategoryFormProps {
  mode: 'create' | 'edit';
  initialData?: Category;
  onSubmit: (data: CreateCategoryRequest) => Promise<void>;
  onCancel?: () => void;
  onSuccess?: () => void;
}

export const CategoryForm = React.memo<CategoryFormProps>(({ 
  mode,
  initialData,
  onSubmit,
  onCancel,
  onSuccess
}) => {
  const { t } = useTranslation();
  const { category } = useApiClients();
  const [formData, setFormData] = useState<CreateCategoryRequest>(() => {
    if (mode === 'edit' && initialData) {
      const baseData = {
        name: initialData.name,
        type: initialData.type,
      };
      return initialData.parent_id ? { ...baseData, parent_id: initialData.parent_id } : baseData;
    }
    return {
      name: '',
      type: 'EXPENSE',
    };
  });
  const [parentCategories, setParentCategories] = useState<Category[]>([]);
  const [error, setError] = useState<string | null>(null);
  const [fieldErrors, setFieldErrors] = useState<Record<string, string>>({});
  const [isLoading, setIsLoading] = useState(false);

  // Helper function to check if a category is a child of the current category (for edit mode)
  const isChildCategory = (cat: Category, parentId: number, allCategories: Category[]): boolean => {
    if (cat.parent_id === parentId) return true;
    if (cat.parent_id) {
      const parent = allCategories.find(c => c.id === cat.parent_id);
      return parent ? isChildCategory(parent, parentId, allCategories) : false;
    }
    return false;
  };

  const fetchParentCategories = useCallback(async () => {
    try {
      const res = await category.getCategories(true); // Get flat list
      console.log('CategoryForm: getCategories response:', res, 'Type:', typeof res, 'IsArray:', Array.isArray(res));
      
      if (!('error' in res)) {
        const categories = res as Category[];
        console.log('CategoryForm: Setting categories:', categories);
        
        if (mode === 'edit' && initialData) {
          // Filter out the current category and its children to prevent circular references
          const filteredCategories = categories.filter(cat => 
            cat.id !== initialData.id && 
            !isChildCategory(cat, initialData.id, categories)
          );
          console.log('CategoryForm: Setting filtered categories:', filteredCategories);
          setParentCategories(filteredCategories);
        } else {
          setParentCategories(categories);
        }
      } else {
        console.error('Error fetching parent categories:', res.error);
        setParentCategories([]); // Set empty array as fallback
      }
    } catch (err) {
      console.error('Error fetching parent categories:', err);
      setParentCategories([]); // Set empty array as fallback
    }
  }, [category, mode, initialData]);

  useEffect(() => {
    fetchParentCategories();
  }, [fetchParentCategories]);

  const handleChange = useCallback((e: React.ChangeEvent<HTMLInputElement | HTMLSelectElement>) => {
    const { name, value } = e.target;
    setFormData(prev => ({
      ...prev,
      [name]: name === 'parent_id' ? (value ? parseInt(value) : undefined) : value
    }));
  }, []);

  const handleSubmit = useCallback(async (e: React.FormEvent) => {
    e.preventDefault();
    setIsLoading(true);
    setError(null);
    FormErrorHandler.clearFieldErrors(setFieldErrors);

    try {
      await onSubmit(formData);
      if (onSuccess) {
        onSuccess();
      }
    } catch (err) {
      const errorMessage = mode === 'create' ? t('category.form.createError') : t('category.form.updateError');
      setError(errorMessage);
      FormErrorHandler.handleFormError(err, errorMessage, setFieldErrors);
    } finally {
      setIsLoading(false);
    }
  }, [formData, onSubmit, onSuccess, mode]);

  const submitButtonText = useMemo(() => 
    mode === 'create' ? t('category.form.createButton') : t('category.form.updateButton'), 
    [mode, t]
  );
  
  const loadingText = useMemo(() => 
    mode === 'create' ? t('category.form.creating') : t('category.form.updating'), 
    [mode, t]
  );

  // Debug logging
  console.log('CategoryForm: parentCategories state:', parentCategories, 'Type:', typeof parentCategories, 'IsArray:', Array.isArray(parentCategories));

  return (
    <div className="w-full">
      <form
        onSubmit={handleSubmit}
        className="space-y-4 sm:space-y-6"
      >
        <div className="space-y-4 sm:space-y-6">
          <div className="space-y-2">
            <label className="block text-sm font-semibold theme-text-primary" htmlFor="name">
              {t('category.form.name')}
              <span className="text-red-500 ml-1">{t('category.form.required')}</span>
            </label>
            <input
              type="text"
              id="name"
              name="name"
              data-testid='category-name-input'
              value={formData.name}
              onChange={handleChange}
              placeholder={t('category.form.namePlaceholder')}
              className={`w-full px-3 sm:px-4 py-3 theme-surface border rounded-lg sm:rounded-xl theme-text-primary placeholder-gray-400 focus:ring-2 focus:ring-blue-500 focus:border-transparent theme-transition shadow-sm hover:shadow-md focus:shadow-lg text-sm sm:text-base min-h-[44px] ${
                FormErrorHandler.hasFieldError(fieldErrors, 'name') ? 'border-red-500' : 'theme-border'
              }`}
              required
            />
            {FormErrorHandler.hasFieldError(fieldErrors, 'name') && (
              <p className="text-sm text-red-500 mt-1">{FormErrorHandler.getFieldError(fieldErrors, 'name')}</p>
            )}
          </div>

          <div className="space-y-2">
            <label className="block text-sm font-semibold theme-text-primary" htmlFor="type">
              {t('category.form.type')}
              <span className="text-red-500 ml-1">{t('category.form.required')}</span>
            </label>
            <select
              id="type"
              data-testid='category-type-select'
              name="type"
              value={formData.type}
              onChange={handleChange}
              className={`w-full px-3 sm:px-4 py-3 theme-surface border rounded-lg sm:rounded-xl theme-text-primary focus:ring-2 focus:ring-blue-500 focus:border-transparent theme-transition shadow-sm hover:shadow-md focus:shadow-lg text-sm sm:text-base min-h-[44px] ${
                FormErrorHandler.hasFieldError(fieldErrors, 'type') ? 'border-red-500' : 'theme-border'
              }`}
            >
              <option value="EXPENSE">{t('category.expense')}</option>
              <option value="INCOME">{t('category.income')}</option>
            </select>
            {FormErrorHandler.hasFieldError(fieldErrors, 'type') && (
              <p className="text-sm text-red-500 mt-1">{FormErrorHandler.getFieldError(fieldErrors, 'type')}</p>
            )}
          </div>

          <div className="space-y-2">
            <label className="block text-sm font-semibold theme-text-primary" htmlFor="parent_id">
              {t('category.form.parentCategory')}
              <span className="theme-text-tertiary font-normal ml-1">{t('category.form.optional')}</span>
            </label>
            <select
              id="parent_id"
              data-testid='category-parent-select'
              name="parent_id"
              value={formData.parent_id || ''}
              onChange={handleChange}
              className="w-full px-3 sm:px-4 py-3 theme-surface border theme-border rounded-lg sm:rounded-xl theme-text-primary focus:ring-2 focus:ring-blue-500 focus:border-transparent theme-transition shadow-sm hover:shadow-md focus:shadow-lg text-sm sm:text-base min-h-[44px]"
            >
              <option value="">{t('category.form.noParentCategory')}</option>
              {Array.isArray(parentCategories) && parentCategories.map((cat) => (
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

        <div className={`${mode === 'edit' ? 'flex flex-col sm:flex-row gap-3 pt-4' : ''}`}>
          {mode === 'edit' && onCancel && (
            <button
              type="button"
              onClick={onCancel}
              className="flex-1 theme-surface hover:theme-surface-hover theme-text-primary font-semibold py-3 px-4 sm:px-6 rounded-lg sm:rounded-xl theme-transition flex items-center justify-center gap-2 sm:gap-3 border theme-border hover:shadow-md min-h-[44px] text-sm sm:text-base"
            >
              <svg className="w-4 h-4 sm:w-5 sm:h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
              </svg>
              {t('common.cancel')}
            </button>
          )}
          <button
            type="submit"
            data-testid='submit-category'
            disabled={isLoading}
            className={`${
              mode === 'edit' ? 'flex-1' : 'w-full'
            } bg-gradient-to-r from-blue-600 to-purple-600 hover:from-blue-700 hover:to-purple-700 text-white font-semibold py-3 sm:py-3 px-4 sm:px-6 rounded-lg sm:rounded-xl theme-transition disabled:opacity-50 disabled:cursor-not-allowed flex items-center justify-center gap-2 sm:gap-3 shadow-lg hover:shadow-xl transform hover:-translate-y-0.5 disabled:transform-none min-h-[44px] text-sm sm:text-base`}
          >
            {isLoading ? (
              <>
                <div className="relative">
                  <div className="animate-spin rounded-full h-4 w-4 sm:h-5 sm:w-5 border-2 border-white/30"></div>
                  <div className="animate-spin rounded-full h-4 w-4 sm:h-5 sm:w-5 border-2 border-white border-t-transparent absolute top-0 left-0"></div>
                </div>
                {loadingText}
              </>
            ) : (
              <>
                <svg className="w-4 h-4 sm:w-5 sm:h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  {mode === 'create' ? (
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 6v6m0 0v6m0-6h6m-6 0H6" />
                  ) : (
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
                  )}
                </svg>
                {submitButtonText}
              </>
            )}
          </button>
        </div>
      </form>
    </div>
  );
});

CategoryForm.displayName = 'CategoryForm';

export default CategoryForm;
