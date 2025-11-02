import React from 'react';
import { useTranslation } from 'react-i18next';
import { useCategories } from '@/contexts/CategoriesContext';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from './Select';
import { Label } from './Label';

interface CategorySelectProps {
  value?: number | null;
  onChange: (categoryId: number | null) => void;
  categoryType?: 'EXPENSE' | 'INCOME';
  showLabel?: boolean;
  label?: string;
  labelKey?: string;
  required?: boolean;
  optional?: boolean;
  className?: string;
  placeholder?: string;
  placeholderKey?: string;
  showEmptyOption?: boolean;
  emptyOptionLabel?: string;
  emptyOptionLabelKey?: string;
  disabled?: boolean;
}

export const CategorySelect: React.FC<CategorySelectProps> = ({
  value,
  onChange,
  categoryType,
  showLabel = true,
  label,
  labelKey = 'common.category',
  required = false,
  optional = false,
  className = '',
  placeholder,
  placeholderKey,
  showEmptyOption = true,
  emptyOptionLabel,
  emptyOptionLabelKey = 'common.noCategory',
  disabled = false
}) => {
  const { t } = useTranslation();
  const { categories, expenseCategories, incomeCategories, isLoading, getCategoryById } = useCategories();

  // Выбираем категории в зависимости от типа
  const displayCategories = categoryType === 'EXPENSE' 
    ? expenseCategories 
    : categoryType === 'INCOME' 
    ? incomeCategories 
    : categories;

  // Получаем выбранную категорию
  const selectedCategory = value ? getCategoryById(value) : null;

  const handleValueChange = (newValue: string) => {
    if (newValue === 'none' || newValue === '') {
      onChange(null);
    } else {
      onChange(parseInt(newValue, 10));
    }
  };

  return (
    <div className={`space-y-2 ${className}`}>
      {showLabel && (
        <Label htmlFor="category-select">
          {label || t(labelKey || 'common.category')}
          {required && <span className="text-red-500 ml-1">*</span>}
          {!required && optional && <span className="theme-text-tertiary font-normal ml-1">{t('common.optional')}</span>}
        </Label>
      )}
      
      <Select
        value={value?.toString() || 'none'}
        onValueChange={handleValueChange}
      >
        <SelectTrigger 
          className="w-full" 
          disabled={disabled || isLoading}
        >
          <SelectValue placeholder={
            placeholder || 
            t(placeholderKey || 'common.selectCategory')
          }>
            <span className="block truncate">
              {selectedCategory?.name || emptyOptionLabel || t(emptyOptionLabelKey || 'common.noCategory')}
            </span>
          </SelectValue>
        </SelectTrigger>
        
        <SelectContent>
          {showEmptyOption && (
            <SelectItem value="none" data-testid="category-none">
              <span className="min-w-0 flex-1 truncate">
                {emptyOptionLabel || t(emptyOptionLabelKey || 'common.noCategory')}
              </span>
            </SelectItem>
          )}
          
          {isLoading ? (
            <SelectItem value="loading" disabled>
              <span className="truncate">{t('common.loading')}</span>
            </SelectItem>
          ) : displayCategories.length === 0 ? (
            <SelectItem value="empty" disabled>
              <span className="truncate">{t('category.noCategories')}</span>
            </SelectItem>
          ) : (
            displayCategories.map((category) => (
              <SelectItem 
                key={category.id} 
                value={category.id.toString()}
                data-testid={`category-${category.id}`}
              >
                <span className="min-w-0 flex-1 truncate" title={category.name}>
                  {category.name}
                </span>
              </SelectItem>
            ))
          )}
        </SelectContent>
      </Select>
    </div>
  );
};

