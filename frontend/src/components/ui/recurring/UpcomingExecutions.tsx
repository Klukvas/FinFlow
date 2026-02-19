import React from 'react';
import { useTranslation } from 'react-i18next';
import { Card } from '../shared/Card';
import { RecurringPayment } from '../../../services/api/recurringApi';
import { getUpcomingExecutions, getScheduleDescription, formatDate, formatAmount } from './recurringHelpers';

interface UpcomingExecutionsProps {
  payments: RecurringPayment[];
  loading: boolean;
  onPaymentClick: (payment: RecurringPayment) => void;
}

export const UpcomingExecutions: React.FC<UpcomingExecutionsProps> = ({
  payments,
  loading,
  onPaymentClick,
}) => {
  const { t } = useTranslation();

  const upcoming = getUpcomingExecutions(payments, 5);

  if (loading) {
    return (
      <Card>
        <div className="p-4 sm:p-6">
          <div className="flex justify-center py-4">
            <div className="animate-spin rounded-full h-5 w-5 border-2 border-[var(--color-accent)] border-t-transparent" />
          </div>
        </div>
      </Card>
    );
  }

  if (upcoming.length === 0) return null;

  return (
    <Card>
      <div className="p-4 sm:p-6">
        <h3 className="text-sm font-semibold theme-text-primary uppercase tracking-wide mb-3">
          {t('recurringPage.upcoming.title')}
        </h3>
        <div className="space-y-0">
          {upcoming.map((payment, index) => (
            <div
              key={payment.id}
              className={`flex items-center justify-between py-2.5 cursor-pointer hover:theme-surface-hover transition-colors rounded-lg px-2 -mx-2 ${
                index < upcoming.length - 1 ? 'border-b theme-border' : ''
              }`}
              onClick={() => onPaymentClick(payment)}
            >
              <div className="min-w-0 flex-1">
                <span className="text-sm font-medium theme-text-primary block truncate">
                  {payment.name}
                </span>
                <span className="text-xs theme-text-tertiary">
                  {getScheduleDescription(payment, t)}
                </span>
              </div>
              <div className="text-right ml-4 flex-shrink-0">
                <span
                  className={`text-sm font-semibold tabular-nums block ${
                    payment.payment_type === 'expense' || payment.payment_type === ('EXPENSE' as string)
                      ? 'text-red-500/80 dark:text-red-400/70'
                      : 'text-green-600/80 dark:text-green-400/70'
                  }`}
                >
                  {payment.payment_type === 'expense' || payment.payment_type === ('EXPENSE' as string)
                    ? '-'
                    : '+'}
                  {formatAmount(payment.amount, payment.currency)}
                </span>
                <span className="text-xs theme-text-tertiary">
                  {formatDate(payment.next_execution)}
                </span>
              </div>
            </div>
          ))}
        </div>
      </div>
    </Card>
  );
};
