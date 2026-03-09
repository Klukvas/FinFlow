import React from "react";
import { useTranslation } from "react-i18next";
import { Button } from "../shared/Button";
import { Badge } from "../shared/Badge";
import { useWorkspace } from "../../../contexts/WorkspaceContext";

interface CategoryPageHeaderProps {
 onAdd: () => void;
 onToggleFilters: () => void;
 filtersActive: boolean;
}

export const CategoryPageHeader: React.FC<CategoryPageHeaderProps> = ({
 onAdd,
 onToggleFilters,
 filtersActive,
}) => {
 const { t } = useTranslation();
 const { workspaces, currentWorkspace } = useWorkspace();
 const showWorkspaceBadge = workspaces.length > 1 && currentWorkspace;

 return (
 <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
 <div className="flex items-center gap-3">
 <div>
 <h1 className="text-2xl font-semibold text-content">
 {t("categoryPage.title")}
 </h1>
 <p className="text-sm text-content-secondary mt-0.5">
 {t("categoryPage.subtitle")}
 </p>
 </div>
 {showWorkspaceBadge && (
 <Badge variant="secondary" size="sm">
 {currentWorkspace.name}
 </Badge>
 )}
 </div>

 <div className="flex items-center gap-2">
 <Button
 variant="outline"
 size="sm"
 onClick={onToggleFilters}
 className={filtersActive ? "bg-[var(--color-accent-light)] text-accent-base" : ""}
 >
 <svg
 className="w-4 h-4 mr-1.5"
 fill="none"
 viewBox="0 0 24 24"
 stroke="currentColor"
 strokeWidth={2}
 >
 <path
 strokeLinecap="round"
 strokeLinejoin="round"
 d="M3 4a1 1 0 011-1h16a1 1 0 011 1v2.586a1 1 0 01-.293.707l-6.414 6.414a1 1 0 00-.293.707V17l-4 4v-6.586a1 1 0 00-.293-.707L3.293 7.293A1 1 0 013 6.586V4z"
 />
 </svg>
 {t("categoryPage.filters.toggle")}
 </Button>
 <Button
 variant="primary"
 size="sm"
 onClick={onAdd}
 data-testid="create-category-button"
 >
 <svg
 className="w-4 h-4 mr-1.5"
 fill="none"
 viewBox="0 0 24 24"
 stroke="currentColor"
 strokeWidth={2}
 >
 <path
 strokeLinecap="round"
 strokeLinejoin="round"
 d="M12 4v16m8-8H4"
 />
 </svg>
 {t("categoryPage.createButton")}
 </Button>
 </div>
 </div>
 );
};
