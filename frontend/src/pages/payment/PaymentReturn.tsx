import React, { useEffect, useState } from 'react';
import { useTranslation } from 'react-i18next';
import { useNavigate } from 'react-router-dom';
import { usePayment } from '@/contexts/PaymentContext';
import { useAuth } from '@/contexts/AuthContext';
import { Payment, PaymentStatus } from '@/types/payment';
import { LoadingSpinner } from '@/components/ui/shared/LoadingSpinner';
import { PaymentStatusBadge } from '@/components/payment/PaymentStatus';
import { Button } from '@/components/ui/shared/Button';
import { FaCheckCircle, FaTimesCircle, FaClock } from 'react-icons/fa';
import { toast } from 'sonner';

export const PaymentReturn: React.FC = () => {
  const { t } = useTranslation();
  const navigate = useNavigate();
  const { pollPaymentStatus } = usePayment();
  const { isAuthenticated, isLoading: authLoading } = useAuth();
  const [payment, setPayment] = useState<Payment | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const checkPaymentStatus = async () => {
      // Wait for auth to load
      if (authLoading) {
        return;
      }

      // Check if user is authenticated
      if (!isAuthenticated) {
        console.warn('User not authenticated on payment return');
        setError('Please log in to view payment status');
        setLoading(false);
        return;
      }

      // Get payment ID from session storage
      const paymentId = sessionStorage.getItem('pending_payment_id');
      const planCode = sessionStorage.getItem('pending_plan_code');

      if (!paymentId) {
        setError(t('payment.errors.noPaymentId'));
        setLoading(false);
        return;
      }

      try {
        // Poll payment status (WayForPay webhook might take a moment)
        const result = await pollPaymentStatus(paymentId);

        if (!result) {
          setError(t('payment.errors.statusCheckFailed'));
          setLoading(false);
          return;
        }

        setPayment(result);

        // Show appropriate toast based on status
        if (result.status === PaymentStatus.PAID) {
          toast.success(t('payment.success.title'));
          // Clear pending payment from storage
          sessionStorage.removeItem('pending_payment_id');
          sessionStorage.removeItem('pending_plan_code');
        } else if (result.status === PaymentStatus.FAILED) {
          toast.error(t('payment.errors.failed'));
        } else if (result.status === PaymentStatus.PENDING) {
          toast.info(t('payment.pending.message'));
        }
      } catch (err) {
        console.error('Failed to check payment status:', err);
        setError(t('payment.errors.unexpected'));
      } finally {
        setLoading(false);
      }
    };

    checkPaymentStatus();
  }, [pollPaymentStatus, t, authLoading, isAuthenticated]);

  const handleContinue = () => {
    if (payment?.status === PaymentStatus.PAID) {
      navigate('/profile');
    } else {
      navigate('/pricing');
    }
  };

  if (loading) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-gray-100 dark:bg-gray-900">
        <div className="text-center bg-white dark:bg-gray-800 rounded-2xl p-8 shadow-xl">
          <LoadingSpinner size="lg" />
          <p className="mt-4 text-lg text-gray-600 dark:text-gray-300">
            {t('payment.checkingStatus')}
          </p>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-gray-100 dark:bg-gray-900 px-4">
        <div className="max-w-md w-full bg-white dark:bg-gray-800 border border-gray-200 dark:border-gray-700 rounded-2xl p-8 text-center shadow-xl">
          <div className="w-16 h-16 bg-red-100 dark:bg-red-900/30 rounded-full flex items-center justify-center mx-auto mb-4">
            <FaTimesCircle className="w-8 h-8 text-red-500" />
          </div>
          <h1 className="text-2xl font-bold text-gray-900 dark:text-white mb-4">
            {t('payment.errors.title')}
          </h1>
          <p className="text-gray-600 dark:text-gray-400 mb-6">{error}</p>
          <Button onClick={() => navigate('/pricing')} variant="primary" fullWidth>
            {t('payment.backToPricing')}
          </Button>
        </div>
      </div>
    );
  }

  if (!payment) {
    return null;
  }

  const isPaid = payment.status === PaymentStatus.PAID;
  const isFailed = payment.status === PaymentStatus.FAILED || payment.status === PaymentStatus.EXPIRED;
  const isPending = payment.status === PaymentStatus.PENDING;

  return (
    <div className="min-h-screen flex items-center justify-center bg-gray-100 dark:bg-gray-900 px-4">
      <div className="max-w-md w-full bg-white dark:bg-gray-800 border border-gray-200 dark:border-gray-700 rounded-2xl p-8 shadow-xl">
        <div className="text-center mb-6">
          {isPaid && (
            <div className="w-16 h-16 bg-green-100 dark:bg-green-900/30 rounded-full flex items-center justify-center mx-auto mb-4">
              <FaCheckCircle className="w-8 h-8 text-green-500" />
            </div>
          )}
          {isFailed && (
            <div className="w-16 h-16 bg-red-100 dark:bg-red-900/30 rounded-full flex items-center justify-center mx-auto mb-4">
              <FaTimesCircle className="w-8 h-8 text-red-500" />
            </div>
          )}
          {isPending && (
            <div className="w-16 h-16 bg-blue-100 dark:bg-blue-900/30 rounded-full flex items-center justify-center mx-auto mb-4">
              <FaClock className="w-8 h-8 text-blue-500" />
            </div>
          )}

          <h1 className="text-2xl font-bold text-gray-900 dark:text-white mb-2">
            {isPaid && t('payment.success.title')}
            {isFailed && t('payment.failed.title')}
            {isPending && t('payment.pending.title')}
          </h1>

          <PaymentStatusBadge status={payment.status} size="lg" className="mx-auto" />
        </div>

        <div className="space-y-4 mb-6 bg-gray-50 dark:bg-gray-900/50 rounded-lg p-4">
          <div className="flex justify-between text-sm">
            <span className="text-gray-600 dark:text-gray-400">{t('payment.amount')}:</span>
            <span className="font-medium text-gray-900 dark:text-white">
              {new Intl.NumberFormat(undefined, {
                style: 'currency',
                currency: payment.currency,
              }).format(payment.amount)}
            </span>
          </div>

          {payment.plan_code && (
            <div className="flex justify-between text-sm">
              <span className="text-gray-600 dark:text-gray-400">{t('payment.plan')}:</span>
              <span className="font-medium text-gray-900 dark:text-white">{payment.plan_code}</span>
            </div>
          )}

          <div className="flex justify-between text-sm">
            <span className="text-gray-600 dark:text-gray-400">{t('payment.orderRef')}:</span>
            <span className="font-mono text-xs text-gray-500 dark:text-gray-400">
              {payment.order_reference}
            </span>
          </div>

          {payment.paid_at && (
            <div className="flex justify-between text-sm">
              <span className="text-gray-600 dark:text-gray-400">{t('payment.paidAt')}:</span>
              <span className="text-gray-900 dark:text-white">
                {new Date(payment.paid_at).toLocaleString()}
              </span>
            </div>
          )}
        </div>

        {payment.failure_reason && (
          <div className="bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-800 rounded-lg p-3 mb-6">
            <p className="text-sm text-red-600 dark:text-red-400">{payment.failure_reason}</p>
          </div>
        )}

        <div className="space-y-3">
          <Button onClick={handleContinue} variant="primary" fullWidth size="lg">
            {isPaid ? t('payment.goToProfile') : t('payment.tryAgain')}
          </Button>

          {!isPaid && (
            <Button onClick={() => navigate('/')} variant="outline" fullWidth>
              {t('payment.backToHome')}
            </Button>
          )}
        </div>

        {isPaid && (
          <div className="mt-6 bg-green-50 dark:bg-green-900/20 border border-green-200 dark:border-green-800 rounded-lg p-4">
            <p className="text-sm text-green-600 dark:text-green-400 text-center">
              {t('payment.success.message')}
            </p>
          </div>
        )}

        {isPending && (
          <div className="mt-6 bg-blue-50 dark:bg-blue-900/20 border border-blue-200 dark:border-blue-800 rounded-lg p-4">
            <p className="text-sm text-blue-600 dark:text-blue-400 text-center">
              {t('payment.pending.detail')}
            </p>
          </div>
        )}
      </div>
    </div>
  );
};
