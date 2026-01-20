import React, { useEffect, useRef } from 'react';
import { useTranslation } from 'react-i18next';
import { useLocation, useNavigate } from 'react-router-dom';
import { FaCreditCard } from 'react-icons/fa';

export const PaymentCheckoutSimple: React.FC = () => {
  const { t } = useTranslation();
  const location = useLocation();
  const navigate = useNavigate();
  const formRef = useRef<HTMLFormElement>(null);
  const [autoSubmitted, setAutoSubmitted] = React.useState(false);

  // Get payment data from location state
  const paymentData = location.state as {
    paymentUrl: string;
    formFields: Record<string, any>;
  } | null;

  useEffect(() => {
    if (!paymentData) {
      navigate('/pricing');
      return;
    }

    // Log data for debugging
    console.log('Payment Form Data:', paymentData.formFields);
    console.log('Payment URL (form action):', paymentData.paymentUrl);
    console.log('recToken in form:', paymentData.formFields.recToken);

    // Auto-submit after 1.5 seconds to give user time to see the page
    const timer = setTimeout(() => {
      if (formRef.current && !autoSubmitted) {
        console.log('Auto-submitting form to WayForPay...');
        console.log('Form action:', formRef.current.action);
        console.log('Form method:', formRef.current.method);
        console.log('Form elements count:', formRef.current.elements.length);
        
        // Log all form fields
        const formData = new FormData(formRef.current);
        console.log('Form data to be submitted:');
        for (const [key, value] of formData.entries()) {
          console.log(`  ${key}: ${value}`);
        }
        
        formRef.current.submit();
        setAutoSubmitted(true);
        console.log('✅ Form submitted successfully');
      }
    }, 1500);

    return () => clearTimeout(timer);
  }, [paymentData, navigate, autoSubmitted]);

  if (!paymentData) {
    return null;
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

        <p className="text-xs" style={{ color: '#495670' }}>
          Redirecting to WayForPay secure payment...
        </p>

        {/* Hidden form that auto-submits to WayForPay */}
        <form
          ref={formRef}
          method="POST"
          action={paymentData.paymentUrl}
          acceptCharset="utf-8"
          style={{ display: 'none' }}
        >
          {Object.entries(paymentData.formFields).map(([key, value]) => {
            if (Array.isArray(value)) {
              // WayForPay expects array fields with [] suffix
              return value.map((item, index) => (
                <input
                  key={`${key}_${index}`}
                  type="hidden"
                  name={`${key}[]`}
                  value={String(item)}
                />
              ));
            }
            return (
              <input
                key={key}
                type="hidden"
                name={key}
                value={String(value)}
              />
            );
          })}
        </form>
      </div>
    </div>
  );
};
