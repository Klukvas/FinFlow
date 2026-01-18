import React, { useEffect, useRef } from 'react';
import { LoadingSpinner } from '@/components/ui/shared/LoadingSpinner';
import { useTranslation } from 'react-i18next';

interface WayForPayFormProps {
  paymentUrl: string;
  formFields: Record<string, any>;
}

export const WayForPayForm: React.FC<WayForPayFormProps> = ({ paymentUrl, formFields }) => {
  const { t } = useTranslation();
  const formRef = useRef<HTMLFormElement>(null);

  useEffect(() => {
    // Log form data for debugging
    console.log('WayForPay Form Data:', {
      url: paymentUrl,
      fields: formFields,
    });

    // Auto-submit form after component mounts
    if (formRef.current) {
      console.log('Submitting form to WayForPay...');
      formRef.current.submit();
    }
  }, [paymentUrl, formFields]);

  const renderFormField = (key: string, value: any) => {
    // Handle arrays (like productName, productCount, productPrice)
    if (Array.isArray(value)) {
      return value.map((item, index) => (
        <input
          key={`${key}_${index}`}
          type="hidden"
          name={`${key}[${index}]`}
          value={String(item)}
        />
      ));
    }

    // Handle regular values
    return (
      <input
        key={key}
        type="hidden"
        name={key}
        value={String(value)}
      />
    );
  };

  return (
    <div className="min-h-screen flex items-center justify-center theme-bg-primary">
      <div className="text-center">
        <LoadingSpinner size="lg" />
        <p className="mt-4 text-lg theme-text-secondary">
          {t('payment.redirecting')}
        </p>
        <p className="mt-2 text-sm theme-text-tertiary">
          {t('payment.doNotClose')}
        </p>

        <form
          ref={formRef}
          method="POST"
          action={paymentUrl}
          className="hidden"
        >
          {Object.entries(formFields).map(([key, value]) =>
            renderFormField(key, value)
          )}
        </form>
      </div>
    </div>
  );
};
