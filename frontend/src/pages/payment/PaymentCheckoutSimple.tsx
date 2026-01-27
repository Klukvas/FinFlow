import React, { useEffect, useRef } from 'react';
import { useTranslation } from 'react-i18next';
import { useLocation, useNavigate } from 'react-router-dom';
import { FaCreditCard, FaExclamationTriangle, FaArrowRight } from 'react-icons/fa';
import { toast } from 'sonner';

export const PaymentCheckoutSimple: React.FC = () => {
  const { t } = useTranslation();
  const location = useLocation();
  const navigate = useNavigate();
  const [autoSubmitted, setAutoSubmitted] = React.useState(false);
  const [hasError, setHasError] = React.useState(false);
  const [errorMessage, setErrorMessage] = React.useState<string>('');
  const submitTimeRef = useRef<number>(0);
  const hasSubmittedRef = useRef(false);
  const isInitialRenderRef = useRef(true);

  // Get payment data from location state
  const paymentData = location.state as {
    paymentUrl: string;
    formFields: Record<string, any>;
  } | null;

  useEffect(() => {
    if (!paymentData) {
      console.error('PaymentCheckout: No payment data received in location state');
      toast.error('Payment data is missing. Please try again.');
      navigate('/pricing');
      return;
    }

    // Skip rapid redirect detection on initial render (React Strict Mode causes double render)
    if (isInitialRenderRef.current) {
      isInitialRenderRef.current = false;
      // Clear any old session data
      sessionStorage.removeItem('payment_submit_time');
      sessionStorage.removeItem('payment_order_ref');
    }

    // Validate payment data
    if (!paymentData.paymentUrl || !paymentData.formFields) {
      console.error('PaymentCheckout: Invalid payment data:', paymentData);
      setHasError(true);
      setErrorMessage('Payment URL or form fields are missing');
      toast.error('Invalid payment data. Please try again.');
      return;
    }

    // Validate required fields
    const requiredFields = ['merchantAccount', 'merchantSignature', 'orderReference', 'amount', 'currency'];
    const missingFields = requiredFields.filter(field => !paymentData.formFields[field]);
    
    if (missingFields.length > 0) {
      console.error('PaymentCheckout: Missing required fields:', missingFields);
      setHasError(true);
      setErrorMessage(`Missing required fields: ${missingFields.join(', ')}`);
      toast.error('Payment form is incomplete. Please try again.');
      return;
    }

    // Log data for debugging
    console.log('✅ PaymentCheckout: Payment data received');
    console.log('Payment URL (form action):', paymentData.paymentUrl);
    console.log('Form fields:', Object.keys(paymentData.formFields));
    console.log('Order reference:', paymentData.formFields.orderReference);
    console.log('Amount:', paymentData.formFields.amount, paymentData.formFields.currency);
    console.log('Merchant account:', paymentData.formFields.merchantAccount);
    console.log('Has signature:', !!paymentData.formFields.merchantSignature);
    console.log('Has recToken request:', paymentData.formFields.recToken);

    // Check if we've been redirected back too quickly (WayForPay rejection)
    if (hasSubmittedRef.current && submitTimeRef.current > 0) {
      const timeElapsed = Date.now() - submitTimeRef.current;
      if (timeElapsed < 3000) { // If we're back within 3 seconds
        console.warn('⚠️ Returned to checkout page within 3 seconds of submission');
        console.warn('This indicates WayForPay rejected the payment without showing the form');
        console.warn('Common causes: invalid merchant credentials, signature error, domain mismatch');
        
        // Don't auto-submit again
        return;
      }
    }

    // Auto-submit after 2 seconds to give user time to see the page
    const timer = setTimeout(() => {
      if (!autoSubmitted && !hasError && !hasSubmittedRef.current) {
        console.log('🚀 Auto-submitting form to WayForPay...');
        
        try {
          // Mark submission time
          submitTimeRef.current = Date.now();
          hasSubmittedRef.current = true;
          
          // Create a fresh form element outside React's control
          const form = document.createElement('form');
          form.method = 'POST';
          form.action = paymentData.paymentUrl;
          form.acceptCharset = 'utf-8';
          form.style.display = 'none';
          
          // Add all form fields
          Object.entries(paymentData.formFields).forEach(([key, value]) => {
            if (Array.isArray(value)) {
              // WayForPay expects array fields with [] suffix
              value.forEach((item) => {
                const input = document.createElement('input');
                input.type = 'hidden';
                input.name = `${key}[]`;
                input.value = String(item);
                form.appendChild(input);
              });
            } else {
              const input = document.createElement('input');
              input.type = 'hidden';
              input.name = key;
              input.value = String(value);
              form.appendChild(input);
            }
          });
          
          // Log form data
          console.log('Form action:', form.action);
          console.log('Form method:', form.method);
          console.log('Form fields count:', form.elements.length);
          console.log('📋 Form data to be submitted:');
          Object.entries(paymentData.formFields).forEach(([key, value]) => {
            if (key === 'merchantSignature') {
              console.log(`  ${key}: ${String(value).substring(0, 20)}...`);
            } else if (Array.isArray(value)) {
              value.forEach((item, idx) => console.log(`  ${key}[${idx}]: ${item}`));
            } else {
              console.log(`  ${key}: ${value}`);
            }
          });
          
          // Append to body, submit, then remove
          document.body.appendChild(form);
          console.log('Form appended to body, submitting now...');
          
          // Submit using native method
          form.submit();
          
          setAutoSubmitted(true);
          console.log('✅ Form submitted to WayForPay - browser should now navigate away');
          console.log('⚠️ If you see component logs again, the submission failed');
          
          // Don't remove form immediately - let browser process submission
          setTimeout(() => {
            if (document.body.contains(form)) {
              document.body.removeChild(form);
              console.log('Form removed from body');
            }
          }, 5000);
        } catch (error) {
          console.error('❌ Form submission failed:', error);
          setHasError(true);
          setErrorMessage('Failed to submit form to payment gateway');
          toast.error('Payment redirect failed. Please contact support.');
        }
      }
    }, 2000);

    return () => clearTimeout(timer);
  }, [paymentData, navigate, autoSubmitted, hasError]);

  if (!paymentData) {
    return null;
  }

  // Error state
  if (hasError) {
    return (
      <div 
        className="fixed inset-0 flex items-center justify-center px-4"
        style={{ 
          background: '#0a192f',
          zIndex: 9999,
        }}
      >
        <div 
          className="max-w-md w-full rounded-2xl p-8 text-center relative"
          style={{ 
            backgroundColor: '#112240',
            border: '2px solid #ef4444',
            boxShadow: '0 25px 50px -12px rgba(239, 68, 68, 0.3)',
            zIndex: 10000,
          }}
        >
          <div 
            className="w-16 h-16 rounded-full flex items-center justify-center mx-auto mb-6"
            style={{ backgroundColor: '#ef4444' }}
          >
            <FaExclamationTriangle className="w-8 h-8 text-white" />
          </div>
          
          <h1 className="text-2xl font-bold mb-2" style={{ color: '#e6f1ff' }}>
            Payment Setup Error
          </h1>
          <p className="mb-6" style={{ color: '#8892b0' }}>
            {errorMessage || 'There was an error setting up the payment. Please try again.'}
          </p>

          <button
            onClick={() => navigate('/pricing')}
            className="w-full py-3 px-4 rounded-lg font-semibold text-white flex items-center justify-center gap-2 transition-all hover:scale-[1.02] active:scale-[0.98]"
            style={{ 
              background: 'linear-gradient(135deg, #3b82f6 0%, #6366f1 100%)',
              boxShadow: '0 4px 15px rgba(59, 130, 246, 0.3)'
            }}
          >
            <FaArrowRight className="w-4 h-4 rotate-180" />
            Back to Pricing
          </button>
        </div>
      </div>
    );
  }

  return (
    <div 
      className="fixed inset-0 flex items-center justify-center px-4"
      style={{ 
        background: '#0a192f',
        zIndex: 9999,
      }}
    >
      <div 
        className="max-w-md w-full rounded-2xl p-8 text-center relative"
        style={{ 
          backgroundColor: '#112240',
          border: '2px solid #233554',
          boxShadow: '0 25px 50px -12px rgba(0, 0, 0, 0.8)',
          zIndex: 10000,
        }}
      >
        {/* Header */}
        <div 
          className="w-16 h-16 rounded-full flex items-center justify-center mx-auto mb-6"
          style={{ backgroundColor: '#3b82f6' }}
        >
          <FaCreditCard className="w-8 h-8 text-white" />
        </div>
        
        <h1 className="text-2xl font-bold mb-2" style={{ color: '#e6f1ff' }}>
          {t('payment.redirecting')}
        </h1>
        <p className="mb-6" style={{ color: '#8892b0' }}>
          {t('payment.doNotClose')}
        </p>

        {/* Loading Animation */}
        <div className="flex justify-center mb-6">
          <div 
            className="animate-spin rounded-full h-12 w-12"
            style={{ border: '4px solid #233554', borderTopColor: '#3b82f6' }}
          ></div>
        </div>

        {/* Payment Info */}
        <div 
          className="rounded-lg p-4 mb-4 text-left"
          style={{ backgroundColor: '#0a192f', border: '1px solid #233554' }}
        >
          <div className="flex justify-between text-sm mb-2">
            <span style={{ color: '#8892b0' }}>Amount:</span>
            <span className="text-xl font-bold" style={{ color: '#64ffda' }}>
              {paymentData.formFields.amount} {paymentData.formFields.currency}
            </span>
          </div>
          <div className="flex justify-between text-sm">
            <span style={{ color: '#8892b0' }}>Order:</span>
            <span className="font-mono text-xs" style={{ color: '#e6f1ff' }}>
              {paymentData.formFields.orderReference}
            </span>
          </div>
        </div>

        <p className="text-xs mb-4" style={{ color: '#495670' }}>
          Redirecting to WayForPay secure payment...
        </p>
        
        {/* Form will be created and submitted programmatically */}
      </div>
    </div>
  );
};
