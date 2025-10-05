import React from 'react';
import { CreateCategoryRequest, Category } from '@/types';
import { useApiClients } from '@hooks';
import CategoryForm from './CategoryForm';

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

  const handleSubmit = async (formData: CreateCategoryRequest) => {
    const response = await categoryApi.updateCategory(category.id, formData);
    if ('error' in response) {
      throw new Error(response.error);
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
