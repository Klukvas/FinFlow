import React, { useMemo, useState } from "react";
import { useTranslation } from "react-i18next";
import { Category } from "../../../types/category";
import { Badge } from "../shared/Badge";
import { Button } from "../shared/Button";
import { Pagination } from "../shared/Pagination";
import {
  getTypeBadgeVariant,
  getParentName,
  formatDate,
  CATEGORY_TYPE_I18N_MAP,
} from "./categoryHelpers";
import { Skeleton } from "../shared/Skeleton";

interface CategoryTableProps {
  categories: Category[];
  allCategories: Category[];
  loading: boolean;
  currentPage: number;
  totalPages: number;
  pageSize: number;
  totalItems: number;
  onPageChange: (page: number) => void;
  onPageSizeChange: (size: number) => void;
  onRowClick: (category: Category) => void;
  onEdit: (category: Category) => void;
  onDelete: (category: Category) => void;
  emptyMessage?: string | undefined;
}

type SortField = "name" | "type" | "parent" | "created";
type SortOrder = "asc" | "desc";

export const CategoryTable: React.FC<CategoryTableProps> = ({
  categories,
  allCategories,
  loading,
  currentPage,
  totalPages,
  pageSize,
  totalItems,
  onPageChange,
  onPageSizeChange,
  onRowClick,
  onEdit,
  onDelete,
  emptyMessage,
}) => {
  const { t } = useTranslation();
  const [sortField, setSortField] = useState<SortField>("name");
  const [sortOrder, setSortOrder] = useState<SortOrder>("asc");

  const hasChildren = (categoryId: number): boolean => {
    return allCategories.some((c) => c.parent_id === categoryId);
  };

  const sortedCategories = useMemo(() => {
    const sorted = [...categories].sort((a, b) => {
      let cmp = 0;
      switch (sortField) {
        case "name":
          cmp = a.name.localeCompare(b.name);
          break;
        case "type":
          cmp = a.type.localeCompare(b.type);
          break;
        case "parent": {
          const aParent = getParentName(a.parent_id, allCategories) || "";
          const bParent = getParentName(b.parent_id, allCategories) || "";
          cmp = aParent.localeCompare(bParent);
          break;
        }
        case "created":
          cmp = (a.created_at || "").localeCompare(b.created_at || "");
          break;
      }
      return sortOrder === "asc" ? cmp : -cmp;
    });
    return sorted;
  }, [categories, allCategories, sortField, sortOrder]);

  const toggleSort = (field: SortField) => {
    if (sortField === field) {
      setSortOrder((prev) => (prev === "asc" ? "desc" : "asc"));
    } else {
      setSortField(field);
      setSortOrder("asc");
    }
  };

  const SortIcon: React.FC<{ field: SortField }> = ({ field }) => {
    if (sortField !== field)
      return <span className="text-[10px] theme-text-tertiary ml-1">↕</span>;
    return (
      <span className="text-[10px] theme-accent ml-1">
        {sortOrder === "asc" ? "↑" : "↓"}
      </span>
    );
  };

  if (loading) {
    return (
      <div className="space-y-3 p-4">
        {Array.from({ length: 5 }).map((_, i) => (
          <div key={i} className="flex items-center gap-4">
            <Skeleton className="h-4 flex-[2]" />
            <Skeleton className="h-4 flex-1" />
            <Skeleton className="h-4 flex-1" />
            <Skeleton className="h-4 flex-1" />
            <Skeleton className="h-4 w-16" />
          </div>
        ))}
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
  const sortableTh = `${thClasses} cursor-pointer select-none hover:theme-text-primary transition-colors`;

  const renderRow = (category: Category) => {
    const parentName = getParentName(category.parent_id, allCategories);
    const hasCh = hasChildren(category.id);

    return (
      <tr
        key={category.id}
        className="hover:theme-surface-hover transition-colors group cursor-pointer"
        onClick={() => onRowClick(category)}
      >
        <td className="px-4 py-3">
          <span className="text-sm font-medium theme-text-primary">
            {category.name}
          </span>
        </td>
        <td className="px-4 py-3">
          <Badge variant={getTypeBadgeVariant(category.type) as any} size="sm">
            {t(CATEGORY_TYPE_I18N_MAP[category.type] || category.type)}
          </Badge>
        </td>
        <td className="px-4 py-3">
          <span className="text-sm theme-text-secondary">
            {parentName || (
              <span className="theme-text-tertiary italic">
                {t("categoryPage.table.rootCategory")}
              </span>
            )}
          </span>
        </td>
        <td className="px-4 py-3">
          <span className="text-sm theme-text-secondary">
            {formatDate(category.created_at)}
          </span>
        </td>
        <td className="px-4 py-3">
          <span className="text-sm theme-text-secondary">
            {category.created_by === "SYSTEM"
              ? t("categoryPage.sidePanel.system")
              : t("categoryPage.sidePanel.user")}
          </span>
        </td>
        <td className="px-4 py-3 text-right">
          <div className="flex items-center justify-end gap-1">
            <Button
              variant="ghost"
              size="sm"
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
              onClick={(e) => {
                e.stopPropagation();
                onDelete(category);
              }}
              className="text-red-500/60 hover:text-red-500 !p-1.5 !min-h-0"
              title={t("categoryPage.sidePanel.delete")}
              disabled={hasCh}
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
    );
  };

  const renderMobileCard = (category: Category) => {
    const parentName = getParentName(category.parent_id, allCategories);
    const hasCh = hasChildren(category.id);

    return (
      <div
        key={category.id}
        className="theme-bg-secondary rounded-lg border theme-border p-3 transition-colors cursor-pointer hover:theme-surface-hover"
        onClick={() => onRowClick(category)}
      >
        <div className="flex items-start justify-between">
          <div className="flex-1 min-w-0">
            <div className="flex items-center gap-2 mb-1">
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
            {parentName && (
              <span className="text-xs theme-text-tertiary">{parentName}</span>
            )}
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
              disabled={hasCh}
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
    );
  };

  return (
    <div className="w-full">
      {/* Mobile Cards View */}
      <div className="block lg:hidden space-y-2 p-4">
        {sortedCategories.map(renderMobileCard)}
      </div>

      {/* Desktop Table View */}
      <div className="hidden lg:block">
        <div className="overflow-x-auto">
          <table className="w-full">
            <thead className="theme-bg-secondary">
              <tr>
                <th
                  className={`${sortableTh} text-left`}
                  onClick={() => toggleSort("name")}
                >
                  {t("categoryPage.table.name")}
                  <SortIcon field="name" />
                </th>
                <th
                  className={`${sortableTh} text-left`}
                  onClick={() => toggleSort("type")}
                >
                  {t("categoryPage.table.type")}
                  <SortIcon field="type" />
                </th>
                <th
                  className={`${sortableTh} text-left`}
                  onClick={() => toggleSort("parent")}
                >
                  {t("categoryPage.table.parent")}
                  <SortIcon field="parent" />
                </th>
                <th
                  className={`${sortableTh} text-left`}
                  onClick={() => toggleSort("created")}
                >
                  {t("categoryPage.table.created")}
                  <SortIcon field="created" />
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
              {sortedCategories.map(renderRow)}
            </tbody>
          </table>
        </div>
      </div>

      {totalPages > 1 && (
        <div className="p-4 border-t theme-border">
          <Pagination
            currentPage={currentPage}
            totalPages={totalPages}
            itemsPerPage={pageSize}
            totalItems={totalItems}
            onPageChange={onPageChange}
            onPageSizeChange={onPageSizeChange}
            showPageSizeSelector
            pageSizeOptions={[10, 25, 50]}
          />
        </div>
      )}
    </div>
  );
};
