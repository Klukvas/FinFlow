import React from "react";
import { Lock } from "lucide-react";
import { RecurringPayment } from "@/services/api/recurringApi";
import { DeleteButton } from "@/components/ui";
import { FaPlay, FaPause, FaEdit } from "react-icons/fa";

interface RecurringPaymentCardProps {
 payment: RecurringPayment;
 onEdit: (payment: RecurringPayment) => void;
 onDelete: (paymentId: string) => void;
 onPause: (paymentId: string) => void;
 onResume: (paymentId: string) => void;
}

export const RecurringPaymentCard: React.FC<RecurringPaymentCardProps> = ({
 payment,
 onEdit,
 onDelete,
 onPause,
 onResume,
}) => {
 const formatAmount = (amount: number, currency: string) => {
 return new Intl.NumberFormat("ru-RU", {
 style: "currency",
 currency: currency,
 }).format(amount);
 };

 const formatDate = (dateString: string) => {
 return new Date(dateString).toLocaleDateString("ru-RU");
 };

 const getStatusColor = (status: string) => {
 switch (status) {
 case "active":
 return "bg-[var(--color-success-light)] text-success-base";
 case "paused":
 return "bg-[var(--color-warning-light)] text-warning-base";
 case "completed":
 return "bg-[var(--color-accent-light)] text-accent-base";
 case "cancelled":
 return "bg-[var(--color-danger-light)] text-danger-base";
 default:
 return "bg-surface-alt text-content";
 }
 };

 const getStatusText = (status: string) => {
 switch (status) {
 case "active":
 return "Активен";
 case "paused":
 return "Приостановлен";
 case "completed":
 return "Завершен";
 case "cancelled":
 return "Отменен";
 default:
 return status;
 }
 };

 const getScheduleText = () => {
 switch (payment.schedule_type) {
 case "daily":
 return "Ежедневно";
 case "weekly":
 const days = [
 "Воскресенье",
 "Понедельник",
 "Вторник",
 "Среда",
 "Четверг",
 "Пятница",
 "Суббота",
 ];
 return `Еженедельно (${days[payment.schedule_config.day_of_week || 0]})`;
 case "monthly":
 return `Ежемесячно (${payment.schedule_config.day_of_month || 1} число)`;
 case "yearly":
 const months = [
 "Январь",
 "Февраль",
 "Март",
 "Апрель",
 "Май",
 "Июнь",
 "Июль",
 "Август",
 "Сентябрь",
 "Октябрь",
 "Ноябрь",
 "Декабрь",
 ];
 return `Ежегодно (${payment.schedule_config.day || 1} ${months[(payment.schedule_config.month || 1) - 1]})`;
 default:
 return payment.schedule_type;
 }
 };

 return (
 <div className="bg-elevated rounded-lg theme-shadow p-6 border-[var(--color-border)] border">
 <div className="flex justify-between items-start mb-4">
 <div className="flex-1">
 <h3 className="text-lg font-semibold text-content mb-1 flex items-center gap-1.5">
 {payment.name}
 {payment.is_read_only && (
 <Lock className="w-4 h-4 text-warning-base flex-shrink-0" />
 )}
 </h3>
 {payment.description && (
 <p className="text-content-secondary text-sm mb-2">
 {payment.description}
 </p>
 )}
 </div>
 <span
 className={`px-2 py-1 rounded-full text-xs font-medium ${getStatusColor(payment.status)}`}
 >
 {getStatusText(payment.status)}
 </span>
 </div>

 <div className="grid grid-cols-2 gap-4 mb-4">
 <div>
 <p className="text-sm text-content-tertiary">Сумма</p>
 <p className="text-lg font-semibold text-content">
 {formatAmount(payment.amount, payment.currency)}
 </p>
 </div>
 <div>
 <p className="text-sm text-content-tertiary">Тип</p>
 <p className="text-sm font-medium text-content">
 {payment.payment_type === "expense" ? "Расход" : "Доход"}
 </p>
 </div>
 </div>

 <div className="grid grid-cols-2 gap-4 mb-4">
 <div>
 <p className="text-sm text-content-tertiary mb-1">Расписание</p>
 <p className="text-sm font-medium text-content">
 {getScheduleText()}
 </p>
 </div>

 <div>
 <p className="text-sm text-content-tertiary">Последнее выполнение</p>
 <p className="text-sm font-medium text-content">
 {payment.last_executed
 ? formatDate(payment.last_executed)
 : "Нет выполнений"}
 </p>
 </div>
 </div>

 <div className="grid grid-cols-2 gap-4 mb-4">
 <div>
 <p className="text-sm text-content-tertiary">Дата начала</p>
 <p className="text-sm font-medium text-content">
 {formatDate(payment.start_date)}
 </p>
 </div>
 <div>
 <p className="text-sm text-content-tertiary">Следующее выполнение</p>
 <p className="text-sm font-medium text-content">
 {formatDate(payment.next_execution)}
 </p>
 </div>
 </div>

 {payment.end_date && (
 <div className="mb-4">
 <p className="text-sm text-content-tertiary">Дата окончания</p>
 <p className="text-sm font-medium text-content">
 {formatDate(payment.end_date)}
 </p>
 </div>
 )}

 {payment.last_executed && (
 <div className="mb-4">
 <p className="text-sm text-content-tertiary">Последнее выполнение</p>
 <p className="text-sm font-medium text-content">
 {formatDate(payment.last_executed)}
 </p>
 </div>
 )}

 <div className="flex justify-end space-x-2">
 {payment.status === "active" && (
 <button
 onClick={() => onPause(payment.id)}
 className="p-2 text-warning-base hover:bg-[var(--color-warning-light)] rounded-md transition-colors"
 title="Приостановить"
 >
 <FaPause className="w-4 h-4" />
 </button>
 )}

 {payment.status === "paused" && (
 <button
 onClick={() => onResume(payment.id)}
 className="p-2 text-success-base hover:bg-[var(--color-success-light)] rounded-md transition-colors"
 title="Возобновить"
 >
 <FaPlay className="w-4 h-4" />
 </button>
 )}

 <button
 onClick={() => onEdit(payment)}
 disabled={payment.is_read_only}
 className={`p-2 rounded-md transition-colors ${
 payment.is_read_only
 ? "opacity-50 cursor-not-allowed text-content-tertiary"
 : "text-accent-base hover:bg-[var(--color-accent-light)]"
 }`}
 title={
 payment.is_read_only
 ? "Read-only: upgrade or delete excess records"
 : "Редактировать"
 }
 >
 <FaEdit className="w-4 h-4" />
 </button>

 <DeleteButton
 onDelete={() => onDelete(payment.id)}
 variant="icon"
 size="md"
 />
 </div>
 </div>
 );
};
