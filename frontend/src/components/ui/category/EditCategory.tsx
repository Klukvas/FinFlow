import React from "react";
import { CreateCategoryRequest, Category } from "@/types";
import { useApiClients } from "@hooks";
import { useCategories } from "@/contexts/CategoriesContext";
import CategoryForm from "./CategoryForm";

interface EditCategoryProps {
 category: Category;
 onCategoryUpdated: () => void;
 onCancel: () => void;
}

export const EditCategory: React.FC<EditCategoryProps> = ({
 category,
 onCategoryUpdated,
 onCancel,
}) => {
 const { category: categoryApi } = useApiClients();

 const { refreshCategories } = useCategories();

 const handleSubmit = async (formData: CreateCategoryRequest) => {
 const response = await categoryApi.updateCategory(category.id, formData);
 if ("error" in response) {
 // Throw the error to prevent form closing - CategoryForm will handle the toast and form error
 throw response;
 }
 };

 const handleSuccess = async () => {
 // Refresh CategoriesContext after successful update
 await refreshCategories();
 onCategoryUpdated();
 };

 return (
 <CategoryForm
 mode="edit"
 initialData={category}
 onSubmit={handleSubmit}
 onCancel={onCancel}
 onSuccess={handleSuccess}
 />
 );
};

export default EditCategory;
