import React, { useEffect } from "react";
import { useTranslation } from "react-i18next";
import { DebtResponse, DebtPaymentResponse } from "../../../types/debt";
import { Badge } from "../shared/Badge";
import { Button } from "../shared/Button";
import {
 getProgressPercentage,
 getDebtStatus,
 getStatusBadgeVariant,
 DEBT_TYPE_I18N_MAP,
} from "./debtHelpers";

interface DebtSidePanelProps {
 debt: DebtResponse | null;
 payments: DebtPaymentResponse[];
 paymentsLoading: boolean;
 isOpen: boolean;
 onClose: () => void;
 onMakePayment: () => void;
 onMarkAsPaid: () => void;
 onEdit: () => void;
 onDelete: () => void;
}

export const DebtSidePanel: React.FC<DebtSidePanelProps> = ({
 debt,
 payments,
 paymentsLoading,
 isOpen,
 onClose,
 onMakePayment,
 onMarkAsPaid,
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

 const formatDate = (dateString: string | null | undefined) => {
 if (!dateString) return "—";
 return new Date(dateString).toLocaleDateString("uk-UA");
 };

 if (!debt) return null;

 const status = getDebtStatus(debt);
 const progress = getProgressPercentage(debt);

 const overviewRows = [
 {
 label: t("debtPage.sidePanel.balance"),
 value: `${Math.abs(debt.current_balance).toLocaleString("uk-UA", { minimumFractionDigits: 2 })} ${debt.currency}`,
 valueClass: "text-danger-base/80 font-semibold",
 },
 {
 label: t("debtPage.sidePanel.initialAmount"),
 value: `${Math.abs(debt.initial_amount).toLocaleString("uk-UA", { minimumFractionDigits: 2 })} ${debt.currency}`,
 valueClass: "text-content",
 },
 {
 label: t("debtPage.sidePanel.interestRate"),
 value: debt.interest_rate != null ? `${debt.interest_rate}%` : "—",
 valueClass: "text-content",
 },
 {
 label: t("debtPage.sidePanel.minimumPayment"),
 value:
 debt.minimum_payment != null
 ? `${debt.minimum_payment.toLocaleString("uk-UA", { minimumFractionDigits: 2 })} ${debt.currency}`
 : "—",
 valueClass: "text-content",
 },
 {
 label: t("debtPage.sidePanel.dueDate"),
 value: formatDate(debt.due_date),
 valueClass: "text-content",
 },
 {
 label: t("debtPage.sidePanel.startDate"),
 value: formatDate(debt.start_date),
 valueClass: "text-content",
 },
 {
 label: t("debtPage.sidePanel.lastPayment"),
 value: formatDate(debt.last_payment_date),
 valueClass: "text-content",
 },
 ];

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
 className={`fixed inset-y-0 right-0 z-40 w-full sm:w-[480px] lg:w-[40%] max-w-[560px] bg-elevated border-l border-[var(--color-border)] shadow-2xl transform transition-transform duration-300 flex flex-col ${
 isOpen ? "translate-x-0" : "translate-x-full"
 }`}
 >
 {/* Header - sticky */}
 <div className="flex items-center justify-between p-4 sm:p-6 border-b border-[var(--color-border)] flex-shrink-0">
 <div className="flex items-center gap-3 min-w-0">
 <div className="min-w-0">
 <h2 className="text-lg font-semibold text-content truncate">
 {debt.name}
 </h2>
 <div className="flex items-center gap-2 mt-0.5">
 <span className="text-xs text-content-tertiary">
 {t(DEBT_TYPE_I18N_MAP[debt.debt_type])}
 </span>
 <Badge
 variant={
 getStatusBadgeVariant(status) as
 | "success"
 | "info"
 | "secondary"
 }
 size="sm"
 >
 {t(
 `debtPage.status.${status === "paid_off" ? "paidOff" : status}`,
 )}
 </Badge>
 </div>
 </div>
 </div>
 <button
 onClick={onClose}
 className="p-2 rounded-lg hover:bg-surface-alt transition-colors text-content-secondary flex-shrink-0"
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
 <h3 className="text-sm font-semibold text-content uppercase tracking-wide">
 {t("debtPage.sidePanel.overview")}
 </h3>
 <div className="space-y-3">
 {overviewRows.map((row) => (
 <div
 key={row.label}
 className="flex items-center justify-between"
 >
 <span className="text-sm text-content-secondary">
 {row.label}
 </span>
 <span className={`text-sm tabular-nums ${row.valueClass}`}>
 {row.value}
 </span>
 </div>
 ))}
 </div>

 {/* Progress bar */}
 <div>
 <div className="flex items-center justify-between mb-1.5">
 <span className="text-sm text-content-secondary">
 {t("debtPage.sidePanel.progress")}
 </span>
 <span className="text-sm font-medium text-content tabular-nums">
 {Math.round(progress)}%
 </span>
 </div>
 <div className="w-full h-2 rounded-full bg-surface-alt overflow-hidden">
 <div
 className="h-full rounded-full bg-success-base/70 transition-all duration-500"
 style={{ width: `${progress}%` }}
 />
 </div>
 </div>
 </div>

 {/* Divider */}
 <div className="border-t border-[var(--color-border)]" />

 {/* Payment History */}
 <div className="p-4 sm:p-6 space-y-3">
 <div className="flex items-center justify-between">
 <h3 className="text-sm font-semibold text-content uppercase tracking-wide">
 {t("debtPage.sidePanel.paymentHistory")}
 </h3>
 {payments.length > 0 && (
 <span className="text-xs text-content-tertiary">
 {t("debtPage.sidePanel.paymentsCount", {
 count: payments.length,
 })}
 </span>
 )}
 </div>

 {paymentsLoading ? (
 <div className="flex justify-center py-4">
 <div className="animate-spin rounded-full h-5 w-5 border-2 border-[var(--color-accent)] border-t-transparent" />
 </div>
 ) : payments.length === 0 ? (
 <p className="text-sm text-content-tertiary italic py-2">
 {t("debtPage.sidePanel.noPayments")}
 </p>
 ) : (
 <div className="space-y-0 rounded-lg border border-[var(--color-border)] overflow-x-auto">
 <table className="w-full">
 <thead className="bg-surface-alt">
 <tr>
 <th className="px-3 py-2 text-left text-xs font-medium text-content-secondary">
 {t("debtPage.sidePanel.paymentDate")}
 </th>
 <th className="px-3 py-2 text-right text-xs font-medium text-content-secondary">
 {t("debtPage.sidePanel.paymentAmount")}
 </th>
 <th className="px-3 py-2 text-left text-xs font-medium text-content-secondary">
 {t("debtPage.sidePanel.paymentMethod")}
 </th>
 </tr>
 </thead>
 <tbody className="divide-y border-[var(--color-border)]">
 {payments.map((p) => (
 <tr key={p.id}>
 <td className="px-3 py-2 text-sm text-content-secondary">
 {formatDate(p.payment_date)}
 </td>
 <td className="px-3 py-2 text-sm text-right text-success-base/80 font-medium tabular-nums">
 +
 {p.amount.toLocaleString("uk-UA", {
 minimumFractionDigits: 2,
 })}
 </td>
 <td className="px-3 py-2 text-sm text-content-tertiary">
 {p.payment_method || "—"}
 </td>
 </tr>
 ))}
 </tbody>
 </table>
 </div>
 )}
 </div>

 {/* Divider */}
 <div className="border-t border-[var(--color-border)]" />

 {/* Notes */}
 <div className="p-4 sm:p-6 space-y-2">
 <h3 className="text-sm font-semibold text-content uppercase tracking-wide">
 {t("debtPage.sidePanel.notes")}
 </h3>
 <p
 className={`text-sm ${debt.description ? "text-content-secondary" : "text-content-tertiary italic"}`}
 >
 {debt.description || t("debtPage.sidePanel.noNotes")}
 </p>
 </div>

 {/* Contact (conditional) */}
 {debt.contact && (
 <>
 <div className="border-t border-[var(--color-border)]" />
 <div className="p-4 sm:p-6 space-y-2">
 <h3 className="text-sm font-semibold text-content uppercase tracking-wide">
 {t("debtPage.sidePanel.contact")}
 </h3>
 <div className="space-y-1.5">
 <p className="text-sm font-medium text-content">
 {debt.contact.name}
 </p>
 {debt.contact.email && (
 <p className="text-sm text-content-secondary">
 <a
 href={`mailto:${debt.contact.email}`}
 className="hover:text-accent-base transition-colors"
 >
 {debt.contact.email}
 </a>
 </p>
 )}
 {debt.contact.company && (
 <p className="text-sm text-content-tertiary">
 {debt.contact.company}
 </p>
 )}
 {debt.contact.phone && (
 <p className="text-sm text-content-tertiary">
 {debt.contact.phone}
 </p>
 )}
 </div>
 </div>
 </>
 )}
 </div>

 {/* Action Footer - sticky */}
 <div className="border-t border-[var(--color-border)] p-4 sm:p-6 flex-shrink-0">
 <div className="flex flex-wrap gap-2">
 {!debt.is_paid_off && (
 <>
 <Button
 variant="primary"
 size="sm"
 onClick={onMakePayment}
 className="flex-1 sm:flex-none"
 >
 {t("debtPage.sidePanel.makePayment")}
 </Button>
 <Button
 variant="outline"
 size="sm"
 onClick={onMarkAsPaid}
 className="flex-1 sm:flex-none"
 >
 {t("debtPage.sidePanel.markAsPaid")}
 </Button>
 </>
 )}
 <Button variant="ghost" size="sm" onClick={onEdit}>
 {t("debtPage.sidePanel.edit")}
 </Button>
 <Button
 variant="ghost"
 size="sm"
 onClick={onDelete}
 className="text-danger-base hover:text-danger-base-hover"
 >
 {t("debtPage.sidePanel.delete")}
 </Button>
 </div>
 </div>
 </div>
 </>
 );
};
