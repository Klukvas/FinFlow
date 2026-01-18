import React, { useState } from 'react';
import { useTranslation } from 'react-i18next';
import { useNavigate } from 'react-router-dom';
import { Button } from '@/components/ui/shared/Button';
import { usePayment } from '@/contexts/PaymentContext';
import { useAuth } from '@/contexts/AuthContext';
import { PaymentPurpose } from '@/types/payment';
import { FaSpinner, FaCrown } from 'react-icons/fa';
import { toast } from 'sonner';

interface PaymentButtonProps {
  planCode: string;
  planName: string;
  amount: number;
  currency?: string;
  variant?: 'primary' | 'outline' | 'secondary';
  size?: 'sm' | 'md' | 'lg';
  fullWidth?: boolean;
  disabled?: boolean;
  className?: string;
}

export const PaymentButton: React.FC<PaymentButtonProps> = ({
  planCode,
  planName,
  amount,
  currency = 'UAH',
  variant = 'primary',
  size = 'lg',
  fullWidth = false,
  disabled = false,
  className = '',
}) => {
  const { t } = useTranslation();
  const navigate = useNavigate();
  const { user } = useAuth();
  const { createPayment, isProcessing } = usePayment();
  const [isCreating, setIsCreating] = useState(false);

  const handlePayment = async () => {
    if (!user?.id) {
      toast.error(t('payment.errors.notAuthenticated'));
      navigate('/login');
      return;
    }

    setIsCreating(true);

    try {
      const returnUrl = `${window.location.origin}/payment/return`;

      console.log('PaymentButton: Creating payment for user', user.id);
      
      const payment = await createPayment({
        user_id: String(user.id),
        workspace_id: user.default_workspace_id ? String(user.default_workspace_id) : undefined,
        purpose: PaymentPurpose.SUBSCRIPTION,
        plan_code: planCode,
        amount: amount,
        currency: currency,
        return_url: returnUrl,
        metadata: {
          plan_name: planName,
          user_email: user.email,
        },
      });

      console.log('PaymentButton: Payment response:', payment);

      if (!payment) {
        console.error('PaymentButton: Payment creation returned null');
        toast.error(t('payment.errors.createFailed'));
        return;
      }

      // Store payment ID in session storage for return page
      sessionStorage.setItem('pending_payment_id', payment.id);
      sessionStorage.setItem('pending_plan_code', planCode);

      // Check if we have form fields to POST
      const formFields = (payment as any).provider_form_fields;
      
      if (formFields && payment.provider_payment_url) {
        console.log('Payment created successfully:', payment);
        console.log('Form fields:', formFields);
        
        toast.success(t('payment.redirecting'));
        
        // Navigate to checkout page which will POST to WayForPay
        navigate('/payment/checkout', {
          state: {
            paymentUrl: payment.provider_payment_url,
            formFields: formFields,
          },
        });
      } else {
        console.error('PaymentButton: Missing form fields or payment URL', { formFields, url: payment.provider_payment_url });
        toast.error(t('payment.errors.noPaymentUrl'));
      }
    } catch (error) {
      console.error('Payment creation failed:', error);
      toast.error(t('payment.errors.unexpected'));
    } finally {
      setIsCreating(false);
    }
  };

  const isButtonDisabled = disabled || isCreating || isProcessing;

  return (
    <Button
      variant={variant}
      size={size}
      fullWidth={fullWidth}
      disabled={isButtonDisabled}
      onClick={handlePayment}
      className={className}
    >
      {isCreating || isProcessing ? (
        <>
          <FaSpinner className="animate-spin mr-2" />
          {t('payment.processing')}
        </>
      ) : (
        <>
          <FaCrown className="mr-2" />
          {t('payment.choosePlan')}
        </>
      )}
    </Button>
  );
};
