export interface CategoryData {
    name: string;
    type?: 'expense' | 'income' | 'Доходы' | 'Расходы';
    parentCategoryName?: string;
  }