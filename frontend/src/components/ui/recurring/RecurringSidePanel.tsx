import React, { useEffect } from "react";
import { useTranslation } from "react-i18next";
import {
  RecurringPayment,
  PaymentSchedule,
} from "../../../services/api/recurringApi";
import { Badge } from "../shared/Badge";
import { Button } from "../shared/Button";
import {
  getStatusBadgeVariant,
  getScheduleDescription,
  formatDate,
  formatAmount,
  STATUS_I18N_MAP,
  PAYMENT_TYPE_I18N_MAP,
  SCHEDULE_TYPE_I18N_MAP,
} from "./recurringHelpers";

interface RecurringSidePanelProps {
  payment: RecurringPayment | null;
  schedules: PaymentSchedule[];
  schedulesLoading: boolean;
  isOpen: boolean;
  onClose: () => void;
  onPauseResume: () => void;
  onEdit: () => void;
  onDelete: () => void;
}

export const RecurringSidePanel: React.FC<RecurringSidePanelProps> = ({
  payment,
  schedules,
  schedulesLoading,
  isOpen,
  onClose,
  onPauseResume,
  onEdit,
  onDelete,
}) => {
  const { t } = useTranslation();

  // Close on ESC
  useEffect(() => {
    const handler = (e: KeyboardEvent) => {
      if (e.key === "Escape" && isOpen) onClose();
    };
    window.addEventListener("keydown", handler);
    return () => window.removeEventListener("keydown", handler);
  }, [isOpen, onClose]);

  // Prevent body scroll when panel is open
  useEffect(() => {
    if (isOpen) {
      document.body.style.overflow = "hidden";
    } else {
      document.body.style.overflow = "";
    }
    return () => {
      document.body.style.overflow = "";
    };
  }, [isOpen]);

  if (!payment) return null;

  const isExpense =
    payment.payment_type === "expense" ||
    payment.payment_type === ("EXPENSE" as string);
  const amountClass = isExpense
    ? "text-red-500/80 font-semibold"
    : "text-green-600/80 font-semibold";

  const overviewRows = [
    {
      label: t("recurringPage.sidePanel.amount"),
      value: `${isExpense ? "-" : "+"}${formatAmount(payment.amount, payment.currency)}`,
      valueClass: amountClass,
    },
    {
      label: t("recurringPage.sidePanel.paymentType"),
      value: t(PAYMENT_TYPE_I18N_MAP[payment.payment_type]),
      valueClass: "theme-text-primary",
    },
    {
      label: t("recurringPage.sidePanel.schedule"),
      value: getScheduleDescription(payment, t),
      valueClass: "theme-text-primary",
    },
    {
      label: t("recurringPage.sidePanel.startDate"),
      value: formatDate(payment.start_date),
      valueClass: "theme-text-primary",
    },
    {
      label: t("recurringPage.sidePanel.endDate"),
      value: formatDate(payment.end_date),
      valueClass: "theme-text-primary",
    },
    {
      label: t("recurringPage.sidePanel.nextExecution"),
      value: formatDate(payment.next_execution),
      valueClass: "theme-text-primary",
    },
    {
      label: t("recurringPage.sidePanel.lastExecuted"),
      value: formatDate(payment.last_executed),
      valueClass: "theme-text-primary",
    },
  ];

  const getScheduleStatusBadgeVariant = (status: string) => {
    switch (status) {
      case "executed":
        return "success";
      case "failed":
        return "destructive";
      case "pending":
        return "secondary";
      default:
        return "secondary";
    }
  };

  const isPaused = payment.status === "paused";
  const canToggle = payment.status === "active" || payment.status === "paused";

  return (
    <>
      {/* Backdrop */}
      <div
        className={`fixed inset-0 bg-black/30 z-30 transition-opacity duration-300 ${
          isOpen ? "opacity-100" : "opacity-0 pointer-events-none"
        }`}
        onClick={onClose}
      />

      {/* Panel */}
      <div
        className={`fixed inset-y-0 right-0 z-40 w-full sm:w-[480px] lg:w-[40%] max-w-[560px] theme-surface border-l theme-border shadow-2xl transform transition-transform duration-300 flex flex-col ${
          isOpen ? "translate-x-0" : "translate-x-full"
        }`}
      >
        {/* Header - sticky */}
        <div className="flex items-center justify-between p-4 sm:p-6 border-b theme-border flex-shrink-0">
          <div className="flex items-center gap-3 min-w-0">
            <div className="min-w-0">
              <h2 className="text-lg font-semibold theme-text-primary truncate">
                {payment.name}
              </h2>
              <div className="flex items-center gap-2 mt-0.5">
                <span className="text-xs theme-text-tertiary">
                  {t(SCHEDULE_TYPE_I18N_MAP[payment.schedule_type])}
                </span>
                <Badge
                  variant={
                    getStatusBadgeVariant(payment.status) as
                      | "success"
                      | "warning"
                      | "info"
                      | "destructive"
                  }
                  size="sm"
                >
                  {t(STATUS_I18N_MAP[payment.status])}
                </Badge>
              </div>
            </div>
          </div>
          <button
            onClick={onClose}
            className="p-2 rounded-lg hover:theme-bg-secondary transition-colors theme-text-secondary flex-shrink-0"
          >
            <svg
              className="w-5 h-5"
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
          </button>
        </div>

        {/* Scrollable content */}
        <div className="flex-1 overflow-y-auto">
          {/* Overview */}
          <div className="p-4 sm:p-6 space-y-4">
            <h3 className="text-sm font-semibold theme-text-primary uppercase tracking-wide">
              {t("recurringPage.sidePanel.overview")}
            </h3>
            <div className="space-y-3">
              {overviewRows.map((row) => (
                <div
                  key={row.label}
                  className="flex items-center justify-between"
                >
                  <span className="text-sm theme-text-secondary">
                    {row.label}
                  </span>
                  <span className={`text-sm tabular-nums ${row.valueClass}`}>
                    {row.value}
                  </span>
                </div>
              ))}
            </div>
          </div>

          {/* Divider */}
          <div className="border-t theme-border" />

          {/* Execution History */}
          <div className="p-4 sm:p-6 space-y-3">
            <div className="flex items-center justify-between">
              <h3 className="text-sm font-semibold theme-text-primary uppercase tracking-wide">
                {t("recurringPage.sidePanel.executionHistory")}
              </h3>
              {schedules.length > 0 && (
                <span className="text-xs theme-text-tertiary">
                  {t("recurringPage.sidePanel.executionsCount", {
                    count: schedules.length,
                  })}
                </span>
              )}
            </div>

            {schedulesLoading ? (
              <div className="flex justify-center py-4">
                <div className="animate-spin rounded-full h-5 w-5 border-2 border-[var(--color-accent)] border-t-transparent" />
              </div>
            ) : schedules.length === 0 ? (
              <p className="text-sm theme-text-tertiary italic py-2">
                {t("recurringPage.sidePanel.noExecutions")}
              </p>
            ) : (
              <div className="space-y-0 rounded-lg border theme-border overflow-hidden">
                <table className="w-full">
                  <thead className="theme-bg-secondary">
                    <tr>
                      <th className="px-3 py-2 text-left text-xs font-medium theme-text-secondary">
                        {t("recurringPage.sidePanel.executionDate")}
                      </th>
                      <th className="px-3 py-2 text-left text-xs font-medium theme-text-secondary">
                        {t("recurringPage.sidePanel.executionStatus")}
                      </th>
                      <th className="px-3 py-2 text-left text-xs font-medium theme-text-secondary">
                        {t("recurringPage.sidePanel.executionError")}
                      </th>
                    </tr>
                  </thead>
                  <tbody className="divide-y theme-border">
                    {schedules.map((schedule) => (
                      <tr key={schedule.id}>
                        <td className="px-3 py-2 text-sm theme-text-secondary tabular-nums">
                          {formatDate(schedule.execution_date)}
                        </td>
                        <td className="px-3 py-2">
                          <Badge
                            variant={
                              getScheduleStatusBadgeVariant(schedule.status) as
                                | "success"
                                | "destructive"
                                | "secondary"
                            }
                            size="sm"
                          >
                            {t(
                              `recurringPage.sidePanel.scheduleStatus.${schedule.status}`,
                            )}
                          </Badge>
                        </td>
                        <td className="px-3 py-2 text-sm text-red-500/80">
                          {schedule.error_message || "—"}
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            )}
          </div>

          {/* Divider */}
          <div className="border-t theme-border" />

          {/* Notes */}
          <div className="p-4 sm:p-6 space-y-2">
            <h3 className="text-sm font-semibold theme-text-primary uppercase tracking-wide">
              {t("recurringPage.sidePanel.notes")}
            </h3>
            <p
              className={`text-sm ${payment.description ? "theme-text-secondary" : "theme-text-tertiary italic"}`}
            >
              {payment.description || t("recurringPage.sidePanel.noNotes")}
            </p>
          </div>
        </div>

        {/* Action Footer - sticky */}
        <div className="border-t theme-border p-4 sm:p-6 flex-shrink-0">
          <div className="flex flex-wrap gap-2">
            {canToggle && (
              <Button
                variant={isPaused ? "primary" : "outline"}
                size="sm"
                onClick={onPauseResume}
                className="flex-1 sm:flex-none"
              >
                {isPaused
                  ? t("recurringPage.sidePanel.resume")
                  : t("recurringPage.sidePanel.pause")}
              </Button>
            )}
            <Button variant="ghost" size="sm" onClick={onEdit}>
              {t("recurringPage.sidePanel.edit")}
            </Button>
            <Button
              variant="ghost"
              size="sm"
              onClick={onDelete}
              className="text-red-500 hover:text-red-600"
            >
              {t("recurringPage.sidePanel.delete")}
            </Button>
          </div>
        </div>
      </div>
    </>
  );
};
