import React from "react";
import { useTranslation } from "react-i18next";
import { Category } from "../../../types/category";
import { Badge } from "../shared/Badge";
import { Button } from "../shared/Button";
import { getTypeBadgeVariant, CATEGORY_TYPE_I18N_MAP } from "./categoryHelpers";

interface CategoryTreeProps {
  categories: Category[];
  loading: boolean;
  onRowClick: (category: Category) => void;
  onEdit: (category: Category) => void;
  onDelete: (category: Category) => void;
  expandedNodes: Set<number>;
  onToggleExpand: (id: number) => void;
  emptyMessage?: string;
}

export const CategoryTree: React.FC<CategoryTreeProps> = ({
  categories,
  loading,
  onRowClick,
  onEdit,
  onDelete,
  expandedNodes,
  onToggleExpand,
  emptyMessage,
}) => {
  const { t } = useTranslation();

  if (loading) {
    return (
      <div className="flex justify-center items-center py-12">
        <div className="animate-spin rounded-full h-6 w-6 border-2 border-[var(--color-accent)] border-t-transparent" />
      </div>
    );
  }

  if (categories.length === 0) {
    return (
      <div className="text-center py-12">
        <div className="w-16 h-16 mx-auto mb-4 theme-bg-tertiary rounded-xl flex items-center justify-center">
          <svg
            className="w-8 h-8 theme-text-tertiary"
            fill="none"
            stroke="currentColor"
            viewBox="0 0 24 24"
          >
            <path
              strokeLinecap="round"
              strokeLinejoin="round"
              strokeWidth={1.5}
              d="M19 11H5m14 0a2 2 0 012 2v6a2 2 0 01-2 2H5a2 2 0 01-2-2v-6a2 2 0 012-2m14 0V9a2 2 0 00-2-2M5 11V9a2 2 0 012-2m0 0V5a2 2 0 012-2h6a2 2 0 012 2v2M7 7h10"
            />
          </svg>
        </div>
        <h3 className="text-base font-semibold theme-text-primary mb-1">
          {emptyMessage || t("categoryPage.table.noCategories")}
        </h3>
        <p className="theme-text-secondary text-sm max-w-md mx-auto">
          {!emptyMessage && t("categoryPage.table.noCategoriesDescription")}
        </p>
      </div>
    );
  }

  const thClasses =
    "px-4 py-3 text-xs font-semibold theme-text-secondary uppercase tracking-wider";

  const renderDesktopTreeNode = (category: Category, depth: number) => {
    const hasChildren = category.children && category.children.length > 0;
    const isExpanded = expandedNodes.has(category.id);
    const indentPx = depth * 24;

    const nameSlug = category.name.toLowerCase().replace(/\s+/g, "-");
    const parentName =
      depth > 0
        ? categories.find((c) =>
            c.children?.some((ch) => ch.id === category.id),
          )?.name
        : undefined;

    return (
      <React.Fragment key={category.id}>
        <tr
          data-testid={`table-category-${nameSlug}`}
          className="hover:theme-surface-hover transition-colors group cursor-pointer"
          onClick={() => onRowClick(category)}
        >
          <td className="px-4 py-3">
            <div
              className="flex items-center gap-1.5"
              style={{ paddingLeft: `${indentPx}px` }}
            >
              {hasChildren ? (
                <button
                  className="p-0.5 rounded hover:theme-bg-secondary transition-colors flex-shrink-0"
                  onClick={(e) => {
                    e.stopPropagation();
                    onToggleExpand(category.id);
                  }}
                  title={
                    isExpanded
                      ? t("categoryPage.tree.collapse")
                      : t("categoryPage.tree.expand")
                  }
                >
                  <svg
                    className={`w-4 h-4 theme-text-secondary transition-transform duration-150 ${isExpanded ? "rotate-90" : ""}`}
                    fill="none"
                    stroke="currentColor"
                    viewBox="0 0 24 24"
                  >
                    <path
                      strokeLinecap="round"
                      strokeLinejoin="round"
                      strokeWidth={2}
                      d="M9 5l7 7-7 7"
                    />
                  </svg>
                </button>
              ) : (
                <span className="w-5 flex-shrink-0" />
              )}
              {depth > 0 && (
                <span className="w-2 h-px theme-bg-tertiary flex-shrink-0" />
              )}
              <span
                data-testid="category-name"
                className="text-sm font-medium theme-text-primary"
              >
                {category.name}
              </span>
              {hasChildren && (
                <span className="text-xs theme-text-tertiary ml-1">
                  ({category.children!.length})
                </span>
              )}
            </div>
          </td>
          <td className="px-4 py-3">
            <span data-testid="category-type">
              <Badge
                variant={getTypeBadgeVariant(category.type) as any}
                size="sm"
              >
                {t(CATEGORY_TYPE_I18N_MAP[category.type] || category.type)}
              </Badge>
            </span>
          </td>
          <td className="px-4 py-3">
            <span className="text-sm theme-text-secondary">
              {category.created_by === "SYSTEM"
                ? t("categoryPage.sidePanel.system")
                : t("categoryPage.sidePanel.user")}
            </span>
            <span data-testid="category-parent-name" className="sr-only">
              {parentName || t("category.list.rootCategory")}
            </span>
            <span data-testid="category-id" className="sr-only">
              #{category.id}
            </span>
          </td>
          <td className="px-4 py-3 text-right">
            <div
              className="flex items-center justify-end gap-1"
              onClick={(e) => e.stopPropagation()}
            >
              <Button
                variant="ghost"
                size="sm"
                data-testid="category-edit-button"
                onClick={(e) => {
                  e.stopPropagation();
                  onEdit(category);
                }}
                className="theme-text-secondary hover:theme-text-primary !p-1.5 !min-h-0"
                title={t("categoryPage.sidePanel.edit")}
              >
                <svg
                  className="w-4 h-4"
                  fill="none"
                  stroke="currentColor"
                  viewBox="0 0 24 24"
                >
                  <path
                    strokeLinecap="round"
                    strokeLinejoin="round"
                    strokeWidth={2}
                    d="M11 5H6a2 2 0 00-2 2v11a2 2 0 002 2h11a2 2 0 002-2v-5m-1.414-9.414a2 2 0 112.828 2.828L11.828 15H9v-2.828l8.586-8.586z"
                  />
                </svg>
              </Button>
              <Button
                variant="ghost"
                size="sm"
                data-testid="category-delete-button"
                onClick={(e) => {
                  e.stopPropagation();
                  onDelete(category);
                }}
                className="text-red-500/60 hover:text-red-500 !p-1.5 !min-h-0"
                title={t("categoryPage.sidePanel.delete")}
                disabled={hasChildren}
              >
                <svg
                  className="w-4 h-4"
                  fill="none"
                  stroke="currentColor"
                  viewBox="0 0 24 24"
                >
                  <path
                    strokeLinecap="round"
                    strokeLinejoin="round"
                    strokeWidth={2}
                    d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16"
                  />
                </svg>
              </Button>
            </div>
          </td>
        </tr>
        {isExpanded &&
          hasChildren &&
          category.children!.map((child) =>
            renderDesktopTreeNode(child, depth + 1),
          )}
      </React.Fragment>
    );
  };

  const renderMobileTreeNode = (category: Category, depth: number) => {
    const hasChildren = category.children && category.children.length > 0;
    const isExpanded = expandedNodes.has(category.id);
    const indentClass = depth === 0 ? "" : depth === 1 ? "ml-4" : "ml-8";

    return (
      <React.Fragment key={category.id}>
        <div
          className={`${indentClass} theme-bg-secondary rounded-lg border theme-border p-3 transition-colors cursor-pointer hover:theme-surface-hover`}
          onClick={() => onRowClick(category)}
        >
          <div className="flex items-start justify-between">
            <div className="flex items-center gap-2 flex-1 min-w-0">
              {hasChildren && (
                <button
                  className="p-0.5 rounded hover:theme-bg-secondary transition-colors flex-shrink-0"
                  onClick={(e) => {
                    e.stopPropagation();
                    onToggleExpand(category.id);
                  }}
                >
                  <svg
                    className={`w-4 h-4 theme-text-secondary transition-transform duration-150 ${isExpanded ? "rotate-90" : ""}`}
                    fill="none"
                    stroke="currentColor"
                    viewBox="0 0 24 24"
                  >
                    <path
                      strokeLinecap="round"
                      strokeLinejoin="round"
                      strokeWidth={2}
                      d="M9 5l7 7-7 7"
                    />
                  </svg>
                </button>
              )}
              <div className="min-w-0">
                <div className="flex items-center gap-2 mb-0.5">
                  <span className="text-sm font-medium theme-text-primary truncate">
                    {category.name}
                  </span>
                  <Badge
                    variant={getTypeBadgeVariant(category.type) as any}
                    size="sm"
                  >
                    {t(CATEGORY_TYPE_I18N_MAP[category.type] || category.type)}
                  </Badge>
                </div>
                {hasChildren && (
                  <span className="text-xs theme-text-tertiary">
                    {t("categoryPage.tree.childCount", {
                      count: category.children!.length,
                    })}
                  </span>
                )}
              </div>
            </div>
            <div
              className="flex items-center gap-1 ml-2 flex-shrink-0"
              onClick={(e) => e.stopPropagation()}
            >
              <Button
                variant="ghost"
                size="sm"
                onClick={() => onEdit(category)}
                className="theme-text-secondary !p-1.5 !min-h-0"
              >
                <svg
                  className="w-4 h-4"
                  fill="none"
                  stroke="currentColor"
                  viewBox="0 0 24 24"
                >
                  <path
                    strokeLinecap="round"
                    strokeLinejoin="round"
                    strokeWidth={2}
                    d="M11 5H6a2 2 0 00-2 2v11a2 2 0 002 2h11a2 2 0 002-2v-5m-1.414-9.414a2 2 0 112.828 2.828L11.828 15H9v-2.828l8.586-8.586z"
                  />
                </svg>
              </Button>
              <Button
                variant="ghost"
                size="sm"
                onClick={() => onDelete(category)}
                className="text-red-500/60 hover:text-red-500 !p-1.5 !min-h-0"
                disabled={hasChildren}
              >
                <svg
                  className="w-4 h-4"
                  fill="none"
                  stroke="currentColor"
                  viewBox="0 0 24 24"
                >
                  <path
                    strokeLinecap="round"
                    strokeLinejoin="round"
                    strokeWidth={2}
                    d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16"
                  />
                </svg>
              </Button>
            </div>
          </div>
        </div>
        {isExpanded &&
          hasChildren &&
          category.children!.map((child) =>
            renderMobileTreeNode(child, depth + 1),
          )}
      </React.Fragment>
    );
  };

  return (
    <div className="w-full">
      {/* Mobile Cards View */}
      <div className="block lg:hidden space-y-2 p-4">
        {categories.map((cat) => renderMobileTreeNode(cat, 0))}
      </div>

      {/* Desktop Table View */}
      <div className="hidden lg:block">
        <div className="overflow-x-auto">
          <table className="w-full">
            <thead className="theme-bg-secondary">
              <tr>
                <th className={`${thClasses} text-left`}>
                  {t("categoryPage.table.name")}
                </th>
                <th className={`${thClasses} text-left`}>
                  {t("categoryPage.table.type")}
                </th>
                <th className={`${thClasses} text-left`}>
                  {t("categoryPage.table.source")}
                </th>
                <th className={`${thClasses} text-right`}>
                  {t("categoryPage.table.actions")}
                </th>
              </tr>
            </thead>
            <tbody className="theme-surface divide-y theme-border">
              {categories.map((cat) => renderDesktopTreeNode(cat, 0))}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
};
