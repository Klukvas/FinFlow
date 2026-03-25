import React, { useMemo, useState } from "react";
import { useTranslation } from "react-i18next";
import { RecurringPayment } from "../../../services/api/recurringApi";
import { Badge } from "../shared/Badge";
import { Button } from "../shared/Button";
import { Pagination } from "../shared/Pagination";
import {
  getStatusBadgeVariant,
  getScheduleDescription,
  formatDate,
  formatAmount,
  PAYMENT_TYPE_I18N_MAP,
  STATUS_I18N_MAP,
  RecurringStatus,
} from "./recurringHelpers";

interface RecurringTableProps {
  payments: RecurringPayment[];
  loading: boolean;
  currentPage: number;
  totalPages: number;
  pageSize: number;
  totalItems: number;
  onPageChange: (page: number) => void;
  onPageSizeChange: (size: number) => void;
  onRowClick: (payment: RecurringPayment) => void;
  onPauseResume: (payment: RecurringPayment) => void;
  onEdit: (payment: RecurringPayment) => void;
  onDelete: (payment: RecurringPayment) => void;
  emptyMessage?: string | undefined;
}

type SortField =
  | "name"
  | "amount"
  | "schedule"
  | "nextExecution"
  | "lastExecuted"
  | "status";
type SortOrder = "asc" | "desc";

export const RecurringTable: React.FC<RecurringTableProps> = ({
  payments,
  loading,
  currentPage,
  totalPages,
  pageSize,
  totalItems,
  onPageChange,
  onPageSizeChange,
  onRowClick,
  onPauseResume,
  onEdit,
  onDelete,
  emptyMessage,
}) => {
  const { t } = useTranslation();
  const [sortField, setSortField] = useState<SortField>("nextExecution");
  const [sortOrder, setSortOrder] = useState<SortOrder>("asc");

  const sortedPayments = useMemo(() => {
    const sorted = [...payments].sort((a, b) => {
      let cmp = 0;
      switch (sortField) {
        case "name":
          cmp = a.name.localeCompare(b.name);
          break;
        case "amount":
          cmp = a.amount - b.amount;
          break;
        case "schedule":
          cmp = a.schedule_type.localeCompare(b.schedule_type);
          break;
        case "nextExecution":
          cmp = (a.next_execution || "").localeCompare(b.next_execution || "");
          break;
        case "lastExecuted":
          cmp = (a.last_executed || "").localeCompare(b.last_executed || "");
          break;
        case "status":
          cmp = a.status.localeCompare(b.status);
          break;
      }
      return sortOrder === "asc" ? cmp : -cmp;
    });
    return sorted;
  }, [payments, sortField, sortOrder]);

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
      return <span className="text-[10px] text-content-tertiary ml-1">↕</span>;
    return (
      <span className="text-[10px] text-accent-base ml-1">
        {sortOrder === "asc" ? "↑" : "↓"}
      </span>
    );
  };

  const isExpense = (p: RecurringPayment) =>
    p.payment_type === "expense" || p.payment_type === ("EXPENSE" as string);

  if (loading) {
    return (
      <div className="flex justify-center items-center py-12">
        <div className="animate-spin rounded-full h-6 w-6 border-2 border-[var(--accent)] border-t-transparent" />
        <span className="ml-3 text-content-secondary text-sm">
          {t("recurringPage.table.loading")}
        </span>
      </div>
    );
  }

  if (payments.length === 0) {
    return (
      <div className="text-center py-12">
        <div className="w-16 h-16 mx-auto mb-4 bg-surface-alt rounded-xl flex items-center justify-center">
          <svg
            className="w-8 h-8 text-content-tertiary"
            fill="none"
            stroke="currentColor"
            viewBox="0 0 24 24"
          >
            <path
              strokeLinecap="round"
              strokeLinejoin="round"
              strokeWidth={1.5}
              d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15"
            />
          </svg>
        </div>
        <h3 className="text-base font-semibold text-content mb-1">
          {emptyMessage ||
            (totalItems === 0
              ? t("recurringPage.table.noPaymentsAtAll")
              : t("recurringPage.table.noPaymentsOnPage"))}
        </h3>
        <p className="text-content-secondary text-sm max-w-md mx-auto">
          {totalItems === 0
            ? t("recurringPage.table.noPaymentsSubtitle")
            : t("recurringPage.table.noPaymentsOnPageSubtitle")}
        </p>
      </div>
    );
  }

  const thClasses =
    "px-4 py-3 text-xs font-semibold text-content-secondary uppercase tracking-wider";
  const sortableTh = `${thClasses} cursor-pointer select-none hover:text-content transition-colors`;

  return (
    <div className="w-full">
      {/* Mobile Cards View */}
      <div className="block md:hidden space-y-2 p-4">
        {sortedPayments.map((payment) => {
          const status = payment.status as RecurringStatus;
          return (
            <div
              key={payment.id}
              className="bg-surface-alt rounded-lg border border-[var(--border)] p-3 transition-colors cursor-pointer hover:bg-surface-alt"
              onClick={() => onRowClick(payment)}
            >
              <div className="flex items-start justify-between">
                <div className="flex-1 min-w-0">
                  <div className="flex items-center gap-2 mb-1">
                    <span className="text-sm font-medium text-content truncate">
                      {payment.name}
                    </span>
                    <Badge
                      variant={
                        getStatusBadgeVariant(status) as
                          | "success"
                          | "warning"
                          | "info"
                          | "destructive"
                      }
                      size="sm"
                    >
                      {t(STATUS_I18N_MAP[status])}
                    </Badge>
                  </div>
                  <div className="text-xs text-content-tertiary mb-1">
                    {t(PAYMENT_TYPE_I18N_MAP[payment.payment_type] ?? "")} ·{" "}
                    {getScheduleDescription(payment, t)}
                  </div>
                  <div className="flex items-center gap-3">
                    <span
                      className={`text-sm font-mono font-semibold tabular-nums ${
                        isExpense(payment)
                          ? "text-danger-base/80"
                          : "text-success-base/80"
                      }`}
                    >
                      {isExpense(payment) ? "-" : "+"}
                      {formatAmount(payment.amount, payment.currency)}
                    </span>
                    <span className="text-xs text-content-tertiary">
                      {formatDate(payment.next_execution)}
                    </span>
                  </div>
                </div>
                <div className="flex items-center gap-1 ml-2 flex-shrink-0">
                  {(payment.status === "active" ||
                    payment.status === "paused") && (
                    <Button
                      variant="ghost"
                      size="sm"
                      onClick={(e) => {
                        e.stopPropagation();
                        onPauseResume(payment);
                      }}
                      className="text-content-secondary !p-1.5 !min-h-0"
                    >
                      {payment.status === "active" ? (
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
                            d="M10 9v6m4-6v6m7-3a9 9 0 11-18 0 9 9 0 0118 0z"
                          />
                        </svg>
                      ) : (
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
                            d="M14.752 11.168l-3.197-2.132A1 1 0 0010 9.87v4.263a1 1 0 001.555.832l3.197-2.132a1 1 0 000-1.664z"
                          />
                          <path
                            strokeLinecap="round"
                            strokeLinejoin="round"
                            strokeWidth={2}
                            d="M21 12a9 9 0 11-18 0 9 9 0 0118 0z"
                          />
                        </svg>
                      )}
                    </Button>
                  )}
                  <Button
                    variant="ghost"
                    size="sm"
                    onClick={(e) => {
                      e.stopPropagation();
                      onDelete(payment);
                    }}
                    className="text-danger-base hover:text-danger-base-hover !p-1.5 !min-h-0"
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
        })}
      </div>

      {/* Desktop Table View */}
      <div className="hidden md:block">
        <div className="overflow-x-auto">
          <table className="w-full">
            <thead className="bg-surface-alt sticky top-0 z-10">
              <tr>
                <th
                  className={`${sortableTh} text-left`}
                  onClick={() => toggleSort("name")}
                >
                  {t("recurringPage.table.name")}
                  <SortIcon field="name" />
                </th>
                <th
                  className={`${sortableTh} text-right`}
                  onClick={() => toggleSort("amount")}
                >
                  {t("recurringPage.table.amount")}
                  <SortIcon field="amount" />
                </th>
                <th
                  className={`${sortableTh} text-left`}
                  onClick={() => toggleSort("schedule")}
                >
                  {t("recurringPage.table.frequency")}
                  <SortIcon field="schedule" />
                </th>
                <th
                  className={`${sortableTh} text-left`}
                  onClick={() => toggleSort("nextExecution")}
                >
                  {t("recurringPage.table.nextExecution")}
                  <SortIcon field="nextExecution" />
                </th>
                <th
                  className={`${sortableTh} text-left`}
                  onClick={() => toggleSort("lastExecuted")}
                >
                  {t("recurringPage.table.lastExecuted")}
                  <SortIcon field="lastExecuted" />
                </th>
                <th
                  className={`${sortableTh} text-left`}
                  onClick={() => toggleSort("status")}
                >
                  {t("recurringPage.table.status")}
                  <SortIcon field="status" />
                </th>
                <th className={`${thClasses} text-right`}>
                  {t("recurringPage.table.actions")}
                </th>
              </tr>
            </thead>
            <tbody className="bg-elevated divide-y border-[var(--border)]">
              {sortedPayments.map((payment) => {
                const status = payment.status as RecurringStatus;
                return (
                  <tr
                    key={payment.id}
                    className="hover:bg-surface-alt transition-colors group cursor-pointer"
                    onClick={() => onRowClick(payment)}
                  >
                    <td className="px-4 py-3">
                      <div>
                        <span className="text-sm font-medium text-content">
                          {payment.name}
                        </span>
                        <span className="block text-xs text-content-tertiary">
                          {t(PAYMENT_TYPE_I18N_MAP[payment.payment_type] ?? "")}
                        </span>
                      </div>
                    </td>
                    <td className="px-4 py-3 text-right">
                      <span
                        className={`text-sm font-mono font-semibold tabular-nums ${
                          isExpense(payment)
                            ? "text-danger-base/80"
                            : "text-success-base/80"
                        }`}
                      >
                        {isExpense(payment) ? "-" : "+"}
                        {formatAmount(payment.amount, payment.currency)}
                      </span>
                    </td>
                    <td className="px-4 py-3">
                      <span className="text-sm text-content-secondary">
                        {getScheduleDescription(payment, t)}
                      </span>
                    </td>
                    <td className="px-4 py-3">
                      <span className="text-sm text-content-secondary">
                        {formatDate(payment.next_execution)}
                      </span>
                    </td>
                    <td className="px-4 py-3">
                      <span className="text-sm text-content-secondary">
                        {formatDate(payment.last_executed)}
                      </span>
                    </td>
                    <td className="px-4 py-3">
                      <Badge
                        variant={
                          getStatusBadgeVariant(status) as
                            | "success"
                            | "warning"
                            | "info"
                            | "destructive"
                        }
                        size="sm"
                      >
                        {t(STATUS_I18N_MAP[status])}
                      </Badge>
                    </td>
                    <td className="px-4 py-3 text-right">
                      <div className="flex items-center justify-end gap-1">
                        {(payment.status === "active" ||
                          payment.status === "paused") && (
                          <Button
                            variant="ghost"
                            size="sm"
                            onClick={(e) => {
                              e.stopPropagation();
                              onPauseResume(payment);
                            }}
                            className="text-content-secondary hover:text-content !p-1.5 !min-h-0"
                            title={
                              payment.status === "active"
                                ? t("recurringPage.sidePanel.pause")
                                : t("recurringPage.sidePanel.resume")
                            }
                          >
                            {payment.status === "active" ? (
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
                                  d="M10 9v6m4-6v6m7-3a9 9 0 11-18 0 9 9 0 0118 0z"
                                />
                              </svg>
                            ) : (
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
                                  d="M14.752 11.168l-3.197-2.132A1 1 0 0010 9.87v4.263a1 1 0 001.555.832l3.197-2.132a1 1 0 000-1.664z"
                                />
                                <path
                                  strokeLinecap="round"
                                  strokeLinejoin="round"
                                  strokeWidth={2}
                                  d="M21 12a9 9 0 11-18 0 9 9 0 0118 0z"
                                />
                              </svg>
                            )}
                          </Button>
                        )}
                        <Button
                          variant="ghost"
                          size="sm"
                          onClick={(e) => {
                            e.stopPropagation();
                            onEdit(payment);
                          }}
                          className="text-content-secondary hover:text-content !p-1.5 !min-h-0"
                          title={t("recurringPage.sidePanel.edit")}
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
                            onDelete(payment);
                          }}
                          className="text-danger-base hover:text-danger-base-hover !p-1.5 !min-h-0"
                          title={t("recurringPage.sidePanel.delete")}
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
              })}
            </tbody>
          </table>
        </div>
      </div>

      {totalPages > 1 && (
        <div className="p-4 border-t border-[var(--border)]">
          <Pagination
            currentPage={currentPage}
            totalPages={totalPages}
            itemsPerPage={pageSize}
            totalItems={totalItems}
            onPageChange={onPageChange}
            onPageSizeChange={onPageSizeChange}
            showPageSizeSelector={true}
            pageSizeOptions={[10, 25, 50]}
          />
        </div>
      )}
    </div>
  );
};
