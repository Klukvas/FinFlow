import { useState, useCallback } from 'react';
import { useApiClients } from '@/hooks/useApiClients';
import { Payment, PaymentHistoryFilters } from '@/types/payment';

export const usePaymentHistory = () => {
  const { payment: paymentApi } = useApiClients();
  const [payments, setPayments] = useState<Payment[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [hasMore, setHasMore] = useState(true);

  const loadPayments = useCallback(
    async (filters: PaymentHistoryFilters = {}) => {
      setLoading(true);
      setError(null);

      try {
        const response = await paymentApi.listPayments(filters);

        if ('error' in response) {
          setError(response.error);
          return;
        }

        if (filters.offset === 0) {
          setPayments(response);
        } else {
          setPayments((prev) => [...prev, ...response]);
        }

        setHasMore(response.length === (filters.limit || 50));
      } catch (err) {
        setError(err instanceof Error ? err.message : 'Failed to load payments');
      } finally {
        setLoading(false);
      }
    },
    [paymentApi]
  );

  const refreshPayments = useCallback(() => {
    loadPayments({ offset: 0, limit: 50 });
  }, [loadPayments]);

  return {
    payments,
    loading,
    error,
    hasMore,
    loadPayments,
    refreshPayments,
  };
};

export const usePaymentPolling = (paymentId: string | null, onComplete?: (payment: Payment) => void) => {
  const { payment: paymentApi } = useApiClients();
  const [payment, setPayment] = useState<Payment | null>(null);
  const [polling, setPolling] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const startPolling = useCallback(async () => {
    if (!paymentId || polling) return;

    setPolling(true);
    setError(null);

    try {
      const response = await paymentApi.pollPaymentStatus(paymentId);

      if ('error' in response) {
        setError(response.error);
        setPolling(false);
        return;
      }

      setPayment(response);

      if (onComplete && ['PAID', 'FAILED', 'EXPIRED', 'CANCELED'].includes(response.status)) {
        onComplete(response);
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Polling failed');
    } finally {
      setPolling(false);
    }
  }, [paymentId, polling, onComplete, paymentApi]);

  return {
    payment,
    polling,
    error,
    startPolling,
  };
};
