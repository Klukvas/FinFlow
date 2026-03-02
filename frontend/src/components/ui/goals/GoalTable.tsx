import React, { useState, useMemo } from "react";
import { useTranslation } from "react-i18next";
import { Goal } from "../../../types/goal";
import { Badge } from "../shared/Badge";
import { Skeleton } from "../shared/Skeleton";
import { Pagination } from "../shared/Pagination";
import {
  getStatusBadgeVariant,
  getPriorityBadgeVariant,
  getTrackStatus,
  getTrackStatusColor,
  getTrackDotColor,
  getProgressBarColor,
  getDaysRemaining,
  getRequiredMonthlySaving,
  formatAmount,
  formatDate,
  STATUS_I18N_MAP,
  PRIORITY_I18N_MAP,
  GOAL_TYPE_I18N_MAP,
  TRACK_STATUS_I18N_MAP,
} from "./goalsHelpers";

interface GoalTableProps {
  goals: Goal[];
  loading: boolean;
  currentPage: number;
  totalPages: number;
  pageSize: number;
  totalItems: number;
  onPageChange: (page: number) => void;
  onPageSizeChange: (size: number) => void;
  onRowClick: (goal: Goal) => void;
  onUpdateProgress: (goal: Goal) => void;
  onEdit: (goal: Goal) => void;
  onDelete: (goal: Goal) => void;
  emptyMessage?: string | undefined;
}

type SortField = "name" | "progress" | "targetDate";
type SortOrder = "asc" | "desc";

export const GoalTable: React.FC<GoalTableProps> = ({
  goals,
  loading,
  currentPage,
  totalPages,
  pageSize,
  totalItems,
  onPageChange,
  onPageSizeChange,
  onRowClick,
  onUpdateProgress,
  onEdit,
  onDelete,
  emptyMessage,
}) => {
  const { t } = useTranslation();
  const [sortField, setSortField] = useState<SortField>("progress");
  const [sortOrder, setSortOrder] = useState<SortOrder>("asc");

  const sortedGoals = useMemo(() => {
    const sorted = [...goals];
    sorted.sort((a, b) => {
      let cmp = 0;
      switch (sortField) {
        case "name":
          cmp = a.title.localeCompare(b.title);
          break;
        case "progress":
          cmp = a.progress_percentage - b.progress_percentage;
          break;
        case "targetDate": {
          const aDate = a.target_date
            ? new Date(a.target_date).getTime()
            : Infinity;
          const bDate = b.target_date
            ? new Date(b.target_date).getTime()
            : Infinity;
          cmp = aDate - bDate;
          break;
        }
      }
      return sortOrder === "asc" ? cmp : -cmp;
    });
    return sorted;
  }, [goals, sortField, sortOrder]);

  const toggleSort = (field: SortField) => {
    if (sortField === field) {
      setSortOrder((prev) => (prev === "asc" ? "desc" : "asc"));
    } else {
      setSortField(field);
      setSortOrder("asc");
    }
  };

  const SortIcon = ({ field }: { field: SortField }) => (
    <svg
      className={`w-3 h-3 ml-1 inline-block ${sortField === field ? "theme-text-primary" : "theme-text-tertiary"}`}
      viewBox="0 0 12 12"
      fill="currentColor"
    >
      {sortField === field && sortOrder === "desc" ? (
        <path d="M6 9L1.5 3.5h9L6 9z" />
      ) : (
        <path d="M6 3L10.5 8.5h-9L6 3z" />
      )}
    </svg>
  );

  if (loading) {
    return (
      <div className="p-4 sm:p-6 space-y-4">
        {Array.from({ length: 5 }).map((_, i) => (
          <div key={i} className="space-y-2">
            <Skeleton variant="text" className="h-5 w-full" />
            <Skeleton variant="text" className="h-1.5 w-full" />
            <Skeleton variant="text" className="h-4 w-3/4" />
          </div>
        ))}
      </div>
    );
  }

  if (goals.length === 0) {
    return (
      <div className="p-8 sm:p-12 text-center">
        <p className="text-sm theme-text-secondary">
          {emptyMessage || t("goalsPage.table.noGoals")}
        </p>
        {!emptyMessage && (
          <p className="text-xs theme-text-tertiary mt-1">
            {t("goalsPage.table.noGoalsDescription")}
          </p>
        )}
      </div>
    );
  }

  return (
    <div>
      {/* Sort controls */}
      <div className="px-4 sm:px-6 py-3 border-b theme-border flex items-center gap-4 text-xs font-medium theme-text-secondary">
        <button
          onClick={() => toggleSort("name")}
          className="hover:theme-text-primary transition-colors"
        >
          {t("goalsPage.table.name")} <SortIcon field="name" />
        </button>
        <button
          onClick={() => toggleSort("progress")}
          className="hover:theme-text-primary transition-colors"
        >
          {t("goalsPage.table.progress")} <SortIcon field="progress" />
        </button>
        <button
          onClick={() => toggleSort("targetDate")}
          className="hover:theme-text-primary transition-colors"
        >
          {t("goalsPage.table.targetDate")} <SortIcon field="targetDate" />
        </button>
      </div>

      {/* Goal rows */}
      <div className="divide-y theme-border">
        {sortedGoals.map((goal) => {
          const trackStatus = getTrackStatus(goal);
          const daysRemaining = getDaysRemaining(goal.target_date);
          const requiredMonthly = getRequiredMonthlySaving(goal);
          const isOverdue = daysRemaining !== null && daysRemaining < 0;

          return (
            <div
              key={goal.id}
              className="px-4 sm:px-6 py-4 cursor-pointer hover:theme-surface-hover transition-colors group"
              onClick={() => onRowClick(goal)}
            >
              {/* Header line */}
              <div className="flex items-center justify-between gap-3 mb-2">
                <div className="flex items-center gap-2 min-w-0 flex-1">
                  <span className="text-sm font-medium theme-text-primary truncate">
                    {goal.title}
                  </span>
                  <Badge
                    variant={getPriorityBadgeVariant(goal.priority) as any}
                    size="sm"
                  >
                    {t(PRIORITY_I18N_MAP[goal.priority])}
                  </Badge>
                  <Badge
                    variant={getStatusBadgeVariant(goal.status) as any}
                    size="sm"
                  >
                    {t(STATUS_I18N_MAP[goal.status])}
                  </Badge>
                  <span className="text-xs theme-text-tertiary hidden sm:inline">
                    {t(GOAL_TYPE_I18N_MAP[goal.goal_type])}
                  </span>
                </div>
                <div className="flex items-center gap-2 flex-shrink-0">
                  <span className="text-sm font-semibold theme-text-primary tabular-nums">
                    {goal.progress_percentage.toFixed(1)}%
                  </span>
                  {/* Actions */}
                  <div className="flex items-center gap-1">
                    <button
                      onClick={(e) => {
                        e.stopPropagation();
                        onUpdateProgress(goal);
                      }}
                      className="p-1.5 rounded-md hover:theme-bg-secondary transition-colors theme-text-tertiary hover:theme-text-primary"
                      title={t("goalsPage.sidePanel.updateProgress")}
                    >
                      <svg
                        className="w-3.5 h-3.5"
                        fill="none"
                        viewBox="0 0 24 24"
                        stroke="currentColor"
                        strokeWidth={2}
                      >
                        <path
                          strokeLinecap="round"
                          strokeLinejoin="round"
                          d="M13 7h8m0 0v8m0-8l-8 8-4-4-6 6"
                        />
                      </svg>
                    </button>
                    <button
                      onClick={(e) => {
                        e.stopPropagation();
                        onEdit(goal);
                      }}
                      className="p-1.5 rounded-md hover:theme-bg-secondary transition-colors theme-text-tertiary hover:theme-text-primary"
                      title={t("goalsPage.sidePanel.edit")}
                    >
                      <svg
                        className="w-3.5 h-3.5"
                        fill="none"
                        viewBox="0 0 24 24"
                        stroke="currentColor"
                        strokeWidth={2}
                      >
                        <path
                          strokeLinecap="round"
                          strokeLinejoin="round"
                          d="M11 5H6a2 2 0 00-2 2v11a2 2 0 002 2h11a2 2 0 002-2v-5m-1.414-9.414a2 2 0 112.828 2.828L11.828 15H9v-2.828l8.586-8.586z"
                        />
                      </svg>
                    </button>
                    <button
                      onClick={(e) => {
                        e.stopPropagation();
                        onDelete(goal);
                      }}
                      className="p-1.5 rounded-md hover:theme-bg-secondary transition-colors text-red-500/60 hover:text-red-500"
                      title={t("goalsPage.sidePanel.delete")}
                    >
                      <svg
                        className="w-3.5 h-3.5"
                        fill="none"
                        viewBox="0 0 24 24"
                        stroke="currentColor"
                        strokeWidth={2}
                      >
                        <path
                          strokeLinecap="round"
                          strokeLinejoin="round"
                          d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16"
                        />
                      </svg>
                    </button>
                  </div>
                </div>
              </div>

              {/* Thin progress bar */}
              <div className="w-full h-1.5 rounded-full theme-bg-tertiary overflow-hidden mb-3">
                <div
                  className={`h-full rounded-full transition-all duration-500 ${getProgressBarColor(goal.progress_percentage)}`}
                  style={{
                    width: `${Math.min(goal.progress_percentage, 100)}%`,
                  }}
                />
              </div>

              {/* Compact info grid */}
              <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-6 gap-x-4 gap-y-1.5 text-xs">
                <div>
                  <span className="theme-text-tertiary">
                    {t("goalsPage.table.info.currentAmount")}
                  </span>
                  <span className="ml-1 font-medium text-green-600/80 tabular-nums">
                    {formatAmount(goal.current_amount, goal.currency)}
                  </span>
                </div>
                <div>
                  <span className="theme-text-tertiary">
                    {t("goalsPage.table.info.targetAmount")}
                  </span>
                  <span className="ml-1 font-medium theme-text-primary tabular-nums">
                    {formatAmount(goal.target_amount, goal.currency)}
                  </span>
                </div>
                <div>
                  <span className="theme-text-tertiary">
                    {t("goalsPage.table.info.requiredMonthly")}
                  </span>
                  <span className="ml-1 font-medium theme-text-primary tabular-nums">
                    {requiredMonthly !== null
                      ? formatAmount(requiredMonthly, goal.currency)
                      : "\u2014"}
                  </span>
                </div>
                <div>
                  <span className="theme-text-tertiary">
                    {t("goalsPage.table.info.targetDate")}
                  </span>
                  <span className="ml-1 font-medium theme-text-primary">
                    {formatDate(goal.target_date)}
                  </span>
                </div>
                <div>
                  <span className="theme-text-tertiary">
                    {t("goalsPage.table.info.daysRemaining")}
                  </span>
                  <span
                    className={`ml-1 font-medium tabular-nums ${isOverdue ? "text-red-500/80" : "theme-text-primary"}`}
                  >
                    {daysRemaining !== null
                      ? isOverdue
                        ? t("goalsPage.table.overdueDays", {
                            days: Math.abs(daysRemaining),
                          })
                        : t("goalsPage.table.remainingDays", {
                            days: daysRemaining,
                          })
                      : "\u2014"}
                  </span>
                </div>
                <div className="flex items-center gap-1.5">
                  <span
                    className={`w-2 h-2 rounded-full flex-shrink-0 ${getTrackDotColor(trackStatus)}`}
                  />
                  <span
                    className={`font-medium ${getTrackStatusColor(trackStatus)}`}
                  >
                    {t(TRACK_STATUS_I18N_MAP[trackStatus])}
                  </span>
                </div>
              </div>
            </div>
          );
        })}
      </div>

      {/* Pagination */}
      {totalPages > 1 && (
        <div className="border-t theme-border">
          <Pagination
            currentPage={currentPage}
            totalPages={totalPages}
            totalItems={totalItems}
            itemsPerPage={pageSize}
            onPageChange={onPageChange}
            onPageSizeChange={onPageSizeChange}
            showPageSizeSelector
          />
        </div>
      )}
    </div>
  );
};
