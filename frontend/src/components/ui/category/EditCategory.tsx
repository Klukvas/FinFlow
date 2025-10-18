import React from 'react';
import { CreateCategoryRequest, Category } from '@/types';
import { useApiClients } from '@hooks';
import CategoryForm from './CategoryForm';
import { useErrorHandler } from '@/hooks/useErrorHandler';

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
  const { handleCategoryError } = useErrorHandler();
  const handleSubmit = async (formData: CreateCategoryRequest) => {
    const response = await categoryApi.updateCategory(category.id, formData);
    if ('error' in response) {
      // Throw the error to prevent form closing - CategoryForm will handle the toast and form error
      throw response;
    }
  };

  return (
    <CategoryForm
      mode="edit"
      initialData={category}
      onSubmit={handleSubmit}
      onCancel={onCancel}
      onSuccess={onCategoryUpdated}
    />
  );
};

export default EditCategory;
