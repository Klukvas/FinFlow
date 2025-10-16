export interface CategoryData {
    name: string;
    type: 'EXPENSE' | 'INCOME';
    parentCategoryName?: string;
}

export type CreateCategoryFailureData = CategoryData & {
  toastErrorMessage?: string;
  formErrorMessage?: string;
  nameError?: string;
}