export type CategoryType = 'EXPENSE' | 'INCOME';

export interface Category {
    id: number;
    name: string;
    user_id: number;
    parent_id?: number;
    type: CategoryType;
    children?: Category[];
    created_at?: string;
    updated_at?: string;
  }
  
  export interface CreateCategoryRequest {
    name: string;
    parent_id?: number;
    type: CategoryType;
  }
  
  export interface CreateCategoryResponse {
    id: number;
    name: string;
    user_id: number;
    parent_id?: number;
    type: CategoryType;
    children?: Category[];
    created_at?: string;
    updated_at?: string;
  }