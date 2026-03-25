import React, { useState, useCallback, useMemo } from "react";
import { useTranslation } from "react-i18next";
import { CreateCategoryRequest, Category } from "@/types";
import { useCategories } from "@/contexts/CategoriesContext";
import { useErrorHandler } from "@/hooks/useErrorHandler";
import { CategorySelect } from "@/components/ui/forms";

interface CategoryFormProps {
  mode: "create" | "edit";
  initialData?: Category;
  onSubmit: (data: CreateCategoryRequest) => Promise<void>;
  onCancel?: () => void;
  onSuccess?: () => void;
}

export const CategoryForm = React.memo<CategoryFormProps>(
  ({ mode, initialData, onSubmit, onCancel, onSuccess }) => {
    const { t } = useTranslation();
    const { handleCategoryError } = useErrorHandler();
    const { categories: allCategories } = useCategories();
    const [formData, setFormData] = useState<CreateCategoryRequest>(() => {
      if (mode === "edit" && initialData) {
        const baseData = {
          name: initialData.name,
          type: initialData.type,
        };
        return initialData.parent_id
          ? { ...baseData, parent_id: initialData.parent_id }
          : baseData;
      }
      return {
        name: "",
        type: "EXPENSE",
      };
    });
    const [error, setError] = useState<string | null>(null);
    const [isLoading, setIsLoading] = useState(false);
    const [fieldErrors, setFieldErrors] = useState<Record<string, string>>({});

    // Helper function to check if a category is a child of the current category (for edit mode)
    const isChildCategory = (
      cat: Category,
      parentId: number,
      allCategories: Category[],
    ): boolean => {
      if (cat.parent_id === parentId) return true;
      if (cat.parent_id) {
        const parent = allCategories.find((c) => c.id === cat.parent_id);
        return parent
          ? isChildCategory(parent, parentId, allCategories)
          : false;
      }
      return false;
    };

    // Get parent categories filtered by type and excluding current category (for edit mode)
    const getAvailableParentCategories = useCallback(() => {
      if (mode === "edit" && initialData) {
        // Filter out the current category and its children to prevent circular references
        return allCategories.filter(
          (cat) =>
            cat.id !== initialData.id &&
            !isChildCategory(cat, initialData.id, allCategories) &&
            cat.type === formData.type,
        );
      }
      return allCategories.filter((cat) => cat.type === formData.type);
    }, [mode, initialData, allCategories, formData.type, isChildCategory]);

    const handleChange = useCallback(
      (e: React.ChangeEvent<HTMLInputElement | HTMLSelectElement>) => {
        const { name, value } = e.target;
        setFormData((prev) => ({
          ...prev,
          [name]: value,
        }));

        // Clear field error when user starts typing
        if (fieldErrors[name]) {
          setFieldErrors((prev) => {
            const newErrors = { ...prev };
            delete newErrors[name];
            return newErrors;
          });
        }
      },
      [fieldErrors],
    );

    const handleParentCategoryChange = useCallback(
      (categoryId: number | null) => {
        if (categoryId) {
          setFormData((prev) => ({ ...prev, parent_id: categoryId }));
        } else {
          setFormData((prev) => {
            const { parent_id, ...rest } = prev;
            return rest as CreateCategoryRequest;
          });
        }
      },
      [],
    );

    const handleSubmit = useCallback(
      async (e: React.FormEvent) => {
        e.preventDefault();
        setIsLoading(true);
        setError(null);
        setFieldErrors({});

        // Client-side validation for name field
        if (!formData.name || !formData.name.trim()) {
          setFieldErrors({ name: t("category.form.nameRequired") });
          setIsLoading(false);
          return;
        }

        try {
          await onSubmit(formData);
          if (onSuccess) {
            onSuccess();
          }
        } catch (err) {
          const errorMessage = handleCategoryError(err as any);
          setError(errorMessage);
        } finally {
          setIsLoading(false);
        }
      },
      [formData, onSubmit, onSuccess, mode, t, handleCategoryError],
    );

    const submitButtonText = useMemo(
      () =>
        mode === "create"
          ? t("category.form.createButton")
          : t("category.form.updateButton"),
      [mode, t],
    );

    const loadingText = useMemo(
      () =>
        mode === "create"
          ? t("category.form.creating")
          : t("category.form.updating"),
      [mode, t],
    );

    return (
      <div className="w-full">
        <form
          onSubmit={handleSubmit}
          className="space-y-4 sm:space-y-6"
          noValidate
        >
          <div className="space-y-4 sm:space-y-6">
            <div className="space-y-2">
              <label
                className="block text-sm font-semibold text-content"
                htmlFor="name"
              >
                {t("category.form.name")}
                <span className="text-danger-base ml-1">
                  {t("category.form.required")}
                </span>
              </label>
              <input
                type="text"
                id="name"
                name="name"
                data-testid="category-name-input"
                value={formData.name}
                onChange={handleChange}
                placeholder={t("category.form.namePlaceholder")}
                className={`w-full px-3 sm:px-4 py-3 bg-elevated border rounded-lg sm:rounded-xl text-content placeholder:text-content-tertiary focus:ring-2 focus:ring-[var(--accent)] focus:border-transparent transition-colors shadow-sm hover:shadow-md focus:shadow-lg text-sm sm:text-base min-h-[44px] ${
                  fieldErrors.name
                    ? "border-danger-base"
                    : "border-[var(--border)]"
                }`}
              />
              {fieldErrors.name && (
                <p
                  className="text-sm text-danger-base mt-1"
                  data-testid="category-name-error"
                >
                  {fieldErrors.name}
                </p>
              )}
            </div>

            <div className="space-y-2">
              <label
                className="block text-sm font-semibold text-content"
                htmlFor="type"
              >
                {t("category.form.type")}
                {mode === "edit" ? (
                  <span className="text-content-tertiary font-normal ml-1">
                    {t("category.form.readOnly")}
                  </span>
                ) : (
                  <span className="text-danger-base ml-1">
                    {t("category.form.required")}
                  </span>
                )}
              </label>
              <select
                id="type"
                data-testid="category-type-select"
                name="type"
                value={formData.type}
                onChange={handleChange}
                disabled={mode === "edit"}
                className={`w-full px-3 sm:px-4 py-3 bg-elevated border border-[var(--border)] rounded-lg sm:rounded-xl text-content focus:ring-2 focus:ring-[var(--accent)] focus:border-transparent transition-colors shadow-sm hover:shadow-md focus:shadow-lg text-sm sm:text-base min-h-[44px] ${
                  mode === "edit" ? "opacity-60 cursor-not-allowed" : ""
                }`}
              >
                <option value="EXPENSE">{t("category.expense")}</option>
                <option value="INCOME">{t("category.income")}</option>
              </select>
            </div>

            <CategorySelect
              key={`parent-${formData.type}`}
              value={formData.parent_id || null}
              onChange={handleParentCategoryChange}
              categoryType={formData.type as "EXPENSE" | "INCOME"}
              label={t("category.form.parentCategory")}
              optional={true}
              showEmptyOption={true}
              emptyOptionLabel={t("category.form.noParentCategory")}
              disabled={getAvailableParentCategories().length === 0}
              dataTestId="category-parent-select"
            />

            {error && (
              <div
                className="bg-[var(--danger-dim)] border border-[var(--border)] rounded-lg sm:rounded-xl p-3 sm:p-4"
                data-testid="category-form-error"
              >
                <div className="flex items-center gap-2 sm:gap-3">
                  <div className="w-4 h-4 sm:w-5 sm:h-5 text-danger-base flex-shrink-0">
                    <svg fill="currentColor" viewBox="0 0 20 20">
                      <path
                        fillRule="evenodd"
                        d="M18 10a8 8 0 11-16 0 8 8 0 0116 0zm-7 4a1 1 0 11-2 0 1 1 0 012 0zm-1-9a1 1 0 00-1 1v4a1 1 0 102 0V6a1 1 0 00-1-1z"
                        clipRule="evenodd"
                      />
                    </svg>
                  </div>
                  <p className="text-danger-base text-xs sm:text-sm font-medium">
                    {error}
                  </p>
                </div>
              </div>
            )}
          </div>

          <div
            className={`${mode === "edit" ? "flex flex-col sm:flex-row gap-3 pt-4" : ""}`}
          >
            {mode === "edit" && onCancel && (
              <button
                type="button"
                onClick={onCancel}
                className="flex-1 bg-elevated hover:bg-surface-alt text-content font-semibold py-3 px-4 sm:px-6 rounded-lg sm:rounded-xl transition-colors flex items-center justify-center gap-2 sm:gap-3 border border-[var(--border)] hover:shadow-md min-h-[44px] text-sm sm:text-base"
              >
                <svg
                  className="w-4 h-4 sm:w-5 sm:h-5"
                  fill="none"
                  stroke="currentColor"
                  viewBox="0 0 24 24"
                >
                  <path
                    strokeLinecap="round"
                    strokeLinejoin="round"
                    strokeWidth={2}
                    d="M6 18L18 6M6 6l12 12"
                  />
                </svg>
                {t("common.cancel")}
              </button>
            )}
            <button
              type="submit"
              data-testid="submit-category"
              disabled={isLoading}
              className={`${
                mode === "edit" ? "flex-1" : "w-full"
              } bg-[var(--accent)] hover:bg-[var(--accent-hover)] text-[var(--accent-text)] font-semibold py-3 px-4 sm:px-6 rounded-lg transition-colors disabled:opacity-50 disabled:cursor-not-allowed flex items-center justify-center gap-2 min-h-[44px] text-sm`}
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
                  <svg
                    className="w-4 h-4 sm:w-5 sm:h-5"
                    fill="none"
                    stroke="currentColor"
                    viewBox="0 0 24 24"
                  >
                    {mode === "create" ? (
                      <path
                        strokeLinecap="round"
                        strokeLinejoin="round"
                        strokeWidth={2}
                        d="M12 6v6m0 0v6m0-6h6m-6 0H6"
                      />
                    ) : (
                      <path
                        strokeLinecap="round"
                        strokeLinejoin="round"
                        strokeWidth={2}
                        d="M5 13l4 4L19 7"
                      />
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
  },
);

CategoryForm.displayName = "CategoryForm";

export default CategoryForm;
