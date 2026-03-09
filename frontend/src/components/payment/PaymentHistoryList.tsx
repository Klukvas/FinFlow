import React, { useEffect } from "react";
import { useTranslation } from "react-i18next";
import { usePaymentHistory } from "@/hooks/usePayment";
import { Card } from "@/components/ui/shared/Card";
import { Skeleton } from "@/components/ui/shared/Skeleton";
import { PaymentStatusBadge } from "./PaymentStatus";
import { PaymentStatus } from "@/types/payment";
import { FaReceipt } from "react-icons/fa";

interface PaymentHistoryListProps {
 className?: string;
 limit?: number;
}

export const PaymentHistoryList: React.FC<PaymentHistoryListProps> = ({
 className = "",
 limit = 10,
}) => {
 const { t } = useTranslation();
 const { payments, loading, error, loadPayments } = usePaymentHistory();

 useEffect(() => {
 loadPayments({ limit, offset: 0 });
 }, [loadPayments, limit]);

 const formatDate = (dateString: string) => {
 return new Date(dateString).toLocaleDateString(undefined, {
 year: "numeric",
 month: "short",
 day: "numeric",
 hour: "2-digit",
 minute: "2-digit",
 });
 };

 const formatAmount = (amount: number | string, currency: string) => {
 return new Intl.NumberFormat(undefined, {
 style: "currency",
 currency: currency,
 }).format(Number(amount));
 };

 if (loading && payments.length === 0) {
 return (
 <Card className={`p-6 ${className}`}>
 <Skeleton className="h-6 w-40 mb-6" />
 <div className="space-y-4">
 {Array.from({ length: 3 }).map((_, i) => (
 <div
 key={i}
 className="border border-[var(--color-border)] rounded-lg p-4 space-y-3"
 >
 <div className="flex items-start justify-between">
 <div className="space-y-2 flex-1">
 <div className="flex items-center gap-2">
 <Skeleton className="h-4 w-24" />
 <Skeleton className="h-5 w-14 rounded-full" />
 </div>
 <Skeleton className="h-3 w-36" />
 </div>
 <Skeleton className="h-6 w-20" />
 </div>
 <Skeleton className="h-3 w-48" />
 </div>
 ))}
 </div>
 </Card>
 );
 }

 if (error) {
 return (
 <Card className={`p-6 ${className}`}>
 <div className="text-center py-8">
 <p className="text-danger-base">{error}</p>
 </div>
 </Card>
 );
 }

 if (payments.length === 0) {
 return (
 <Card className={`p-6 ${className}`}>
 <div className="text-center py-8">
 <FaReceipt className="w-12 h-12 text-content-tertiary mx-auto mb-4" />
 <p className="text-content-secondary">{t("payment.noPayments")}</p>
 </div>
 </Card>
 );
 }

 return (
 <Card className={`p-6 ${className}`}>
 <div className="flex items-center justify-between mb-6">
 <h3 className="text-lg font-semibold text-content">
 {t("payment.history")}
 </h3>
 </div>

 <div className="space-y-4">
 {payments.map((payment) => (
 <div
 key={payment.id}
 className="bg-elevated border-[var(--color-border)] border rounded-lg p-4 hover:theme-shadow-hover transition-shadow"
 >
 <div className="flex items-start justify-between mb-3">
 <div className="flex-1">
 <div className="flex items-center gap-2 mb-1">
 <h4 className="font-medium text-content">
 {payment.plan_code || t("payment.oneTime")}
 </h4>
 <PaymentStatusBadge status={payment.status} size="sm" />
 </div>
 <p className="text-sm text-content-secondary">
 {formatDate(payment.created_at)}
 </p>
 </div>
 <div className="text-right">
 <p className="font-semibold text-content text-lg">
 {formatAmount(payment.amount, payment.currency)}
 </p>
 </div>
 </div>

 <div className="flex items-center justify-between text-sm">
 <div className="text-content-tertiary">
 {t("payment.orderRef")}: {payment.order_reference}
 </div>
 {payment.status === PaymentStatus.PAID && payment.paid_at && (
 <div className="text-success-base">
 {t("payment.paidAt")}: {formatDate(payment.paid_at)}
 </div>
 )}
 {payment.status === PaymentStatus.FAILED &&
 payment.failure_reason && (
 <div className="text-danger-base text-xs">
 {payment.failure_reason}
 </div>
 )}
 </div>
 </div>
 ))}
 </div>

 {loading && (
 <div className="flex items-center justify-center mt-4">
 <Skeleton className="h-4 w-4 rounded-full" />
 </div>
 )}
 </Card>
 );
};
