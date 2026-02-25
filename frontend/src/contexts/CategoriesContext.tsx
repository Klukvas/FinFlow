import React, {
  createContext,
  useContext,
  useEffect,
  useState,
  useCallback,
  ReactNode,
} from "react";
import { useApiClients } from "@/hooks/useApiClients";
import { useAuth } from "@/contexts/AuthContext";
import { useWorkspace } from "@/contexts/WorkspaceContext";
import { Category, CategoryListResponse } from "@/types";
import { logger } from "@/utils/logger";

interface CategoriesContextType {
  categories: Category[];
  expenseCategories: Category[];
  incomeCategories: Category[];
  parentCategories: Category[];
  childCategories: Category[];
  isLoading: boolean;
  error: string | null;
  refreshCategories: () => Promise<void>;
  getCategoryById: (id: number) => Category | undefined;
  getCategoriesByType: (type: "EXPENSE" | "INCOME") => Category[];
  getChildCategories: (parentId: number) => Category[];
}

const CategoriesContext = createContext<CategoriesContextType | undefined>(
  undefined,
);

interface CategoriesProviderProps {
  children: ReactNode;
}

export const CategoriesProvider: React.FC<CategoriesProviderProps> = ({
  children,
}) => {
  const { category } = useApiClients();
  const { isAuthenticated, isLoading: authLoading } = useAuth();
  const { currentWorkspaceId, isLoading: workspaceLoading } = useWorkspace();
  const [categories, setCategories] = useState<Category[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const fetchCategories = useCallback(async () => {
    // Don't fetch if not authenticated, auth is still loading, or workspace is not selected
    if (
      !isAuthenticated ||
      authLoading ||
      workspaceLoading ||
      !currentWorkspaceId
    ) {
      return;
    }

    try {
      setIsLoading(true);
      setError(null);

      const response = await category.getCategoriesPaginated({
        flat: true,
        page: 1,
        size: 100, // Maximum page size
      });

      if ("error" in response) {
        logger.error(
          "CategoriesContext: Failed to fetch categories:",
          response.error,
        );
        setError(response.error);
        setCategories([]);
      } else {
        const paginatedResponse = response as CategoryListResponse;
        setCategories(paginatedResponse.items || []);
      }
    } catch (err) {
      const errorMessage =
        err instanceof Error ? err.message : "Failed to fetch categories";
      logger.error("CategoriesContext: Error fetching categories:", err);
      setError(errorMessage);
      setCategories([]);
    } finally {
      setIsLoading(false);
    }
  }, [
    category,
    isAuthenticated,
    authLoading,
    workspaceLoading,
    currentWorkspaceId,
  ]);

  const refreshCategories = useCallback(async () => {
    await fetchCategories();
  }, [fetchCategories]);

  // Computed values
  const expenseCategories = categories.filter((cat) => cat.type === "EXPENSE");
  const incomeCategories = categories.filter((cat) => cat.type === "INCOME");
  const parentCategories = categories.filter((cat) => !cat.parent_id);
  const childCategories = categories.filter(
    (cat) => cat.parent_id !== null && cat.parent_id !== undefined,
  );

  // Helper methods
  const getCategoryById = useCallback(
    (id: number): Category | undefined => {
      return categories.find((cat) => cat.id === id);
    },
    [categories],
  );

  const getCategoriesByType = useCallback(
    (type: "EXPENSE" | "INCOME"): Category[] => {
      return categories.filter((cat) => cat.type === type);
    },
    [categories],
  );

  const getChildCategories = useCallback(
    (parentId: number): Category[] => {
      return categories.filter((cat) => cat.parent_id === parentId);
    },
    [categories],
  );

  // Fetch categories on mount and when user changes
  useEffect(() => {
    fetchCategories();
  }, [fetchCategories]);

  const value: CategoriesContextType = {
    categories,
    expenseCategories,
    incomeCategories,
    parentCategories,
    childCategories,
    isLoading,
    error,
    refreshCategories,
    getCategoryById,
    getCategoriesByType,
    getChildCategories,
  };

  return (
    <CategoriesContext.Provider value={value}>
      {children}
    </CategoriesContext.Provider>
  );
};

export const useCategories = (): CategoriesContextType => {
  const context = useContext(CategoriesContext);
  if (context === undefined) {
    throw new Error("useCategories must be used within a CategoriesProvider");
  }
  return context;
};
