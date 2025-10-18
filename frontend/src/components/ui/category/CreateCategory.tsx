import React from 'react';
import { CreateCategoryRequest } from '@/types';
import { useApiClients } from '@hooks';
import CategoryForm from './CategoryForm';

interface CreateCategoryProps {
  onCategoryCreated: () => void;
}

export const CreateCategory: React.FC<CreateCategoryProps> = ({ onCategoryCreated }) => {
  const { category } = useApiClients();

  const handleSubmit = async (formData: CreateCategoryRequest) => {
    const response = await category.createCategory(formData);
    if ('error' in response) {
      throw response; // Throw the entire error response object instead of just the message
    }
  };

  const handleSuccess = async () => {
    onCategoryCreated();
  };

  return (
    <CategoryForm
      mode="create"
      onSubmit={handleSubmit}
      onSuccess={handleSuccess}
    />
  );
};

export default CreateCategory;
