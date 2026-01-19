import React, { useEffect, useState, useRef } from 'react';
import { useTranslation } from 'react-i18next';
import { useNavigate, useSearchParams } from 'react-router-dom';
import { usePayment } from '@/contexts/PaymentContext';
import { useAuth } from '@/contexts/AuthContext';
import { Payment, PaymentStatus } from '@/types/payment';
import { 
  FaCheckCircle, 
  FaTimesCircle, 
  FaClock, 
  FaSpinner,
  FaUser,
  FaCreditCard,
  FaReceipt
} from 'react-icons/fa';
import { toast } from 'sonner';

// Status configuration for cleaner code
const STATUS_CONFIG = {
  [PaymentStatus.PAID]: {
    icon: FaCheckCircle,
    iconBg: 'bg-emerald-500',
    iconColor: 'text-white',
    titleKey: 'payment.success.title',
    messageKey: 'payment.success.message',
    gradient: 'from-emerald-500 to-teal-500',
  },
  [PaymentStatus.FAILED]: {
    icon: FaTimesCircle,
    iconBg: 'bg-red-500',
    iconColor: 'text-white',
    titleKey: 'payment.failed.title',
    messageKey: 'payment.failed.message',
    gradient: 'from-red-500 to-rose-500',
  },
  [PaymentStatus.EXPIRED]: {
    icon: FaTimesCircle,
    iconBg: 'bg-orange-500',
    iconColor: 'text-white',
    titleKey: 'payment.expired.title',
    messageKey: 'payment.expired.message',
    gradient: 'from-orange-500 to-amber-500',
  },
  [PaymentStatus.PENDING]: {
    icon: FaClock,
    iconBg: 'bg-blue-500',
    iconColor: 'text-white',
    titleKey: 'payment.pending.title',
    messageKey: 'payment.pending.detail',
    gradient: 'from-blue-500 to-indigo-500',
  },
  [PaymentStatus.CREATED]: {
    icon: FaClock,
    iconBg: 'bg-gray-500',
    iconColor: 'text-white',
    titleKey: 'payment.processing.title',
    messageKey: 'payment.processing.message',
    gradient: 'from-gray-500 to-slate-500',
  },
};

export const PaymentReturn: React.FC = () => {
  const { t } = useTranslation();
  const navigate = useNavigate();
  const [searchParams] = useSearchParams();
  const { pollPaymentStatus, getPayment, getPaymentByOrderRef } = usePayment();
  const { isAuthenticated, isLoading: authLoading } = useAuth();
  const [payment, setPayment] = useState<Payment | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  
  // Prevent double execution due to dependency changes
  const hasCheckedRef = useRef(false);
  const paymentIdRef = useRef<string | null>(null);
  const orderRefRef = useRef<string | null>(null);

  // Capture payment identifiers on mount (before they might be cleared)
  useEffect(() => {
    if (!paymentIdRef.current) {
      // Check URL params first (most reliable after redirect), then localStorage
      paymentIdRef.current = searchParams.get('paymentId') || localStorage.getItem('pending_payment_id');
    }
    if (!orderRefRef.current) {
      orderRefRef.current = searchParams.get('orderReference');
    }
  }, [searchParams]);

  useEffect(() => {
    const checkPaymentStatus = async () => {
      // Skip if already checked or still loading auth
      if (hasCheckedRef.current || authLoading) return;

      if (!isAuthenticated) {
        setError(t('payment.errors.notAuthenticated'));
        setLoading(false);
        return;
      }

      // Use captured refs, with URL params taking priority (most reliable after redirect)
      const paymentIdFromUrl = searchParams.get('paymentId');
      const paymentId = paymentIdRef.current || paymentIdFromUrl || localStorage.getItem('pending_payment_id');
      const orderRef = orderRefRef.current || searchParams.get('orderReference');
      
      console.log('PaymentReturn: paymentId from URL:', paymentIdFromUrl);
      console.log('PaymentReturn: paymentId (combined):', paymentId);
      console.log('PaymentReturn: orderRef from URL:', orderRef);
      
      if (!paymentId && !orderRef) {
        setError(t('payment.errors.noPaymentId'));
        setLoading(false);
        return;
      }

      // Mark as checked to prevent double execution
      hasCheckedRef.current = true;

      try {
        let result = null;

        // Try to get payment by ID first if available
        if (paymentId) {
          result = await pollPaymentStatus(paymentId);
          console.log('PaymentReturn: pollPaymentStatus result:', result);
        }

        // If no result from polling by ID, try to get by orderReference
        if (!result && orderRef) {
          console.log('PaymentReturn: Trying to get payment by orderReference:', orderRef);
          result = await getPaymentByOrderRef(orderRef);
          console.log('PaymentReturn: getPaymentByOrderRef result:', result);
        }

        // If still no result, try direct getPayment as last resort
        if (!result && paymentId) {
          console.log('PaymentReturn: Polling returned null, fetching payment directly...');
          result = await getPayment(paymentId);
          console.log('PaymentReturn: Direct getPayment result:', result);
        }

        if (!result) {
          setError(t('payment.errors.statusCheckFailed'));
          setLoading(false);
          return;
        }

        setPayment(result);

        // Handle status-specific actions
        if (result.status === PaymentStatus.PAID) {
          toast.success(t('payment.success.title'), {
            description: t('payment.success.message'),
          });
          localStorage.removeItem('pending_payment_id');
          localStorage.removeItem('pending_plan_code');
        } else if (result.status === PaymentStatus.FAILED) {
          toast.error(t('payment.failed.title'));
          localStorage.removeItem('pending_payment_id');
          localStorage.removeItem('pending_plan_code');
        } else if (result.status === PaymentStatus.CREATED || result.status === PaymentStatus.PENDING) {
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
  }, [pollPaymentStatus, getPayment, getPaymentByOrderRef, t, authLoading, isAuthenticated, searchParams]);

  // Loading state
  if (loading) {
    return (
      <div 
        className="fixed inset-0 flex items-center justify-center"
        style={{ background: '#0a192f' }}
      >
        <div 
          className="max-w-md w-full mx-4 rounded-2xl p-8 text-center"
          style={{ backgroundColor: '#112240', border: '1px solid #233554', boxShadow: '0 25px 50px -12px rgba(0, 0, 0, 0.5)' }}
        >
          <div className="w-20 h-20 rounded-full bg-blue-500/20 flex items-center justify-center mx-auto mb-6">
            <FaSpinner className="w-10 h-10 text-blue-400 animate-spin" />
          </div>
          <h1 className="text-2xl font-bold text-white mb-2">
            {t('payment.checkingStatus')}
          </h1>
          <p className="text-gray-400 mb-4">
            {t('payment.pleaseWait')}
          </p>
          <div className="flex justify-center gap-1">
            {[0, 1, 2].map(i => (
              <div
                key={i}
                className="w-2 h-2 rounded-full bg-blue-400 animate-bounce"
                style={{ animationDelay: `${i * 0.15}s` }}
              />
            ))}
          </div>
        </div>
      </div>
    );
  }

  // Error state
  if (error) {
    return (
      <div 
        className="fixed inset-0 flex items-center justify-center"
        style={{ background: '#0a192f' }}
      >
        <div 
          className="max-w-md w-full mx-4 rounded-2xl p-8 text-center"
          style={{ backgroundColor: '#112240', border: '1px solid #233554', boxShadow: '0 25px 50px -12px rgba(0, 0, 0, 0.5)' }}
        >
          <div className="w-20 h-20 rounded-full bg-red-500/20 flex items-center justify-center mx-auto mb-6">
            <FaTimesCircle className="w-10 h-10 text-red-400" />
          </div>
          <h1 className="text-2xl font-bold text-white mb-2">
            {t('payment.errors.title')}
          </h1>
          <p className="text-gray-400 mb-6">{error}</p>
          <button
            onClick={() => navigate('/profile')}
            className="w-full py-3 px-4 rounded-lg font-semibold text-white flex items-center justify-center gap-2 transition-all hover:scale-[1.02] active:scale-[0.98]"
            style={{ 
              background: 'linear-gradient(135deg, #3b82f6 0%, #6366f1 100%)',
              boxShadow: '0 4px 15px rgba(59, 130, 246, 0.3)'
            }}
          >
            <FaUser className="w-4 h-4" />
            {t('payment.goToProfile')}
          </button>
        </div>
      </div>
    );
  }

  if (!payment) return null;

  const config = STATUS_CONFIG[payment.status] || STATUS_CONFIG[PaymentStatus.CREATED];
  const StatusIcon = config.icon;
  const isPaid = payment.status === PaymentStatus.PAID;

  return (
    <div 
      className="fixed inset-0 flex items-center justify-center overflow-y-auto py-8"
      style={{ background: '#0a192f' }}
    >
      <div 
        className="max-w-lg w-full mx-4 rounded-2xl overflow-hidden"
        style={{ backgroundColor: '#112240', border: '1px solid #233554', boxShadow: '0 25px 50px -12px rgba(0, 0, 0, 0.5)' }}
      >
        {/* Gradient header */}
        <div className={`h-2 bg-gradient-to-r ${config.gradient}`} />
        
        <div className="p-8">
          {/* Status icon with animation */}
          <div className="text-center mb-6">
            <div 
              className={`w-20 h-20 rounded-full ${config.iconBg} flex items-center justify-center mx-auto mb-4 ${isPaid ? 'animate-bounce' : ''}`}
              style={{ animationDuration: '1s', animationIterationCount: isPaid ? 3 : 0 }}
            >
              <StatusIcon className={`w-10 h-10 ${config.iconColor}`} />
            </div>
            
            <h1 className="text-2xl font-bold text-white mb-2">
              {t(config.titleKey)}
            </h1>
            
            {/* Status badge */}
            <span 
              className={`inline-flex items-center px-3 py-1 rounded-full text-sm font-medium bg-gradient-to-r ${config.gradient} text-white`}
            >
              {payment.status}
            </span>
          </div>

          {/* Payment details card */}
          <div 
            className="rounded-xl p-5 mb-6 space-y-4"
            style={{ backgroundColor: '#0a192f', border: '1px solid #233554' }}
          >
            {/* Amount - highlighted */}
            <div className="text-center pb-4" style={{ borderBottom: '1px solid #233554' }}>
              <p className="text-gray-400 text-sm mb-1">{t('payment.amount')}</p>
              <p className="text-3xl font-bold text-white">
                {new Intl.NumberFormat('uk-UA', {
                  style: 'currency',
                  currency: payment.currency,
                }).format(payment.amount)}
              </p>
            </div>

            {/* Details grid */}
            <div className="space-y-3">
              {payment.plan_code && (
                <div className="flex items-center justify-between">
                  <span className="text-gray-400 flex items-center gap-2">
                    <FaCreditCard className="w-4 h-4" />
                    {t('payment.plan')}
                  </span>
                  <span className="text-white font-medium capitalize">
                    {payment.plan_code.replace(/-/g, ' ')}
                  </span>
                </div>
              )}

              <div className="flex items-center justify-between">
                <span className="text-gray-400 flex items-center gap-2">
                  <FaReceipt className="w-4 h-4" />
                  {t('payment.orderRef')}
                </span>
                <span className="text-gray-300 font-mono text-xs">
                  {payment.order_reference.slice(-12)}
                </span>
              </div>

              {payment.paid_at && (
                <div className="flex items-center justify-between">
                  <span className="text-gray-400">{t('payment.paidAt')}</span>
                  <span className="text-white">
                    {new Date(payment.paid_at).toLocaleString('uk-UA')}
                  </span>
                </div>
              )}
            </div>
          </div>

          {/* Failure reason */}
          {payment.failure_reason && (
            <div 
              className="rounded-lg p-4 mb-6"
              style={{ backgroundColor: 'rgba(239, 68, 68, 0.1)', border: '1px solid rgba(239, 68, 68, 0.3)' }}
            >
              <p className="text-red-400 text-sm text-center">{payment.failure_reason}</p>
            </div>
          )}

          {/* Success message */}
          {isPaid && (
            <div 
              className="rounded-lg p-4 mb-6"
              style={{ backgroundColor: 'rgba(16, 185, 129, 0.1)', border: '1px solid rgba(16, 185, 129, 0.3)' }}
            >
              <p className="text-emerald-400 text-sm text-center">
                {t(config.messageKey)}
              </p>
            </div>
          )}

          {/* Pending message */}
          {payment.status === PaymentStatus.PENDING && (
            <div 
              className="rounded-lg p-4 mb-6"
              style={{ backgroundColor: 'rgba(59, 130, 246, 0.1)', border: '1px solid rgba(59, 130, 246, 0.3)' }}
            >
              <p className="text-blue-400 text-sm text-center">
                {t(config.messageKey)}
              </p>
            </div>
          )}

          {/* Action button */}
          <button
            onClick={() => navigate('/profile')}
            className="w-full py-3 px-4 rounded-lg font-semibold text-white flex items-center justify-center gap-2 transition-all hover:scale-[1.02] active:scale-[0.98]"
            style={{ 
              background: isPaid 
                ? 'linear-gradient(135deg, #10b981 0%, #14b8a6 100%)'
                : 'linear-gradient(135deg, #3b82f6 0%, #6366f1 100%)',
              boxShadow: isPaid 
                ? '0 4px 15px rgba(16, 185, 129, 0.3)'
                : '0 4px 15px rgba(59, 130, 246, 0.3)'
            }}
          >
            <FaUser className="w-4 h-4" />
            {t('payment.goToProfile')}
          </button>
        </div>
      </div>
    </div>
  );
};
