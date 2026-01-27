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
      console.log('PaymentButton: Return URL will be:', returnUrl);
      
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
      console.log('PaymentButton: Payment type:', typeof payment);
      console.log('PaymentButton: Payment keys:', payment ? Object.keys(payment) : 'null');

      if (!payment) {
        console.error('PaymentButton: Payment creation returned null');
        toast.error(t('payment.errors.createFailed'));
        return;
      }

      // Store payment ID in localStorage for return page (survives external redirects better)
      localStorage.setItem('pending_payment_id', payment.id);
      localStorage.setItem('pending_plan_code', planCode);

      // Check if we have form fields to POST
      const formFields = (payment as any).provider_form_fields;
      const paymentUrl = (payment as any).provider_payment_url || (payment as any).payment_url;
      
      console.log('PaymentButton: Extracted formFields:', formFields);
      console.log('PaymentButton: Form fields keys:', formFields ? Object.keys(formFields) : 'null');
      console.log('PaymentButton: Extracted paymentUrl:', paymentUrl);
      console.log('PaymentButton: Condition check - formFields?', !!formFields);
      console.log('PaymentButton: Condition check - paymentUrl?', !!paymentUrl);
      
      // Validate form fields
      if (!formFields || typeof formFields !== 'object') {
        console.error('❌ PaymentButton: formFields is missing or invalid');
        console.error('Full payment object:', JSON.stringify(payment, null, 2));
        toast.error('Payment data is incomplete. Please try again or contact support.');
        return;
      }

      if (!paymentUrl || typeof paymentUrl !== 'string') {
        console.error('❌ PaymentButton: paymentUrl is missing or invalid');
        console.error('Full payment object:', JSON.stringify(payment, null, 2));
        toast.error('Payment URL is missing. Please try again or contact support.');
        return;
      }

      // Validate required WayForPay fields
      const requiredFields = ['merchantAccount', 'merchantSignature', 'orderReference', 'amount', 'currency'];
      const missingFields = requiredFields.filter(field => !formFields[field]);
      
      if (missingFields.length > 0) {
        console.error('❌ PaymentButton: Missing required WayForPay fields:', missingFields);
        console.error('Available fields:', Object.keys(formFields));
        toast.error(`Payment setup incomplete: missing ${missingFields.join(', ')}`);
        return;
      }
      
      console.log('✅ PaymentButton: Payment data validated successfully');
      console.log('✅ PaymentButton: Navigating to /payment/checkout');
      
      toast.success(t('payment.redirecting'));
      
      // Navigate to checkout page which will POST to WayForPay
      navigate('/payment/checkout', {
        state: {
          paymentUrl: paymentUrl,
          formFields: formFields,
        },
      });
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
