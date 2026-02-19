import { RecurringPayment } from '@/services/api/recurringApi';

export type RecurringStatus = 'active' | 'paused' | 'completed' | 'cancelled';
export type ScheduleType = 'daily' | 'weekly' | 'monthly' | 'yearly';

export interface RecurringFilters {
  page: number;
  size: number;
  status?: RecurringStatus | 'all';
  payment_type?: 'expense' | 'income' | 'all';
  schedule_type?: ScheduleType | 'all';
}

export const getStatusBadgeVariant = (status: RecurringStatus): string => {
  switch (status) {
    case 'active':
      return 'success';
    case 'paused':
      return 'warning';
    case 'completed':
      return 'info';
    case 'cancelled':
      return 'destructive';
  }
};

export const STATUS_I18N_MAP: Record<RecurringStatus, string> = {
  active: 'recurringPage.status.active',
  paused: 'recurringPage.status.paused',
  completed: 'recurringPage.status.completed',
  cancelled: 'recurringPage.status.cancelled',
};

export const PAYMENT_TYPE_I18N_MAP: Record<string, string> = {
  expense: 'recurringPage.types.expense',
  income: 'recurringPage.types.income',
  EXPENSE: 'recurringPage.types.expense',
  INCOME: 'recurringPage.types.income',
};

export const SCHEDULE_TYPE_I18N_MAP: Record<ScheduleType, string> = {
  daily: 'recurringPage.schedule.daily',
  weekly: 'recurringPage.schedule.weekly',
  monthly: 'recurringPage.schedule.monthly',
  yearly: 'recurringPage.schedule.yearly',
};

export const getScheduleDescription = (
  payment: RecurringPayment,
  t: (key: string) => string,
): string => {
  const base = t(SCHEDULE_TYPE_I18N_MAP[payment.schedule_type]);
  switch (payment.schedule_type) {
    case 'daily':
      return base;
    case 'weekly': {
      const days = ['sunday', 'monday', 'tuesday', 'wednesday', 'thursday', 'friday', 'saturday'];
      const dayKey = `common.weekDays.${days[payment.schedule_config.day_of_week || 0]}`;
      return `${base} (${t(dayKey)})`;
    }
    case 'monthly':
      return `${base} (${payment.schedule_config.day_of_month || 1})`;
    case 'yearly': {
      const month = payment.schedule_config.month || 1;
      const day = payment.schedule_config.day || 1;
      const monthName = new Date(2024, month - 1, 1).toLocaleDateString(undefined, { month: 'long' });
      return `${base} (${day} ${monthName})`;
    }
    default:
      return base;
  }
};

export const getUpcomingExecutions = (
  payments: RecurringPayment[],
  limit: number = 5,
): RecurringPayment[] => {
  return payments
    .filter((p) => p.status === 'active' && p.next_execution)
    .sort((a, b) => new Date(a.next_execution).getTime() - new Date(b.next_execution).getTime())
    .slice(0, limit);
};

export const formatDate = (dateString: string | null | undefined): string => {
  if (!dateString) return '\u2014';
  return new Date(dateString).toLocaleDateString('uk-UA');
};

export const formatAmount = (amount: number, currency: string): string => {
  return (
    new Intl.NumberFormat('uk-UA', {
      minimumFractionDigits: 2,
      maximumFractionDigits: 2,
    }).format(amount) + ' ' + currency
  );
};
