import React, { useEffect, useRef } from 'react';
import { LoadingSpinner } from '@/components/ui/shared/LoadingSpinner';
import { useTranslation } from 'react-i18next';

interface WayForPayFormAltProps {
  paymentUrl: string;
  formFields: Record<string, any>;
}

export const WayForPayFormAlt: React.FC<WayForPayFormAltProps> = ({ paymentUrl, formFields }) => {
  const { t } = useTranslation();
  const formRef = useRef<HTMLFormElement>(null);

  useEffect(() => {
    // Log form data for debugging
    console.log('WayForPay Form Data (Alternative):', {
      url: paymentUrl,
      fields: formFields,
    });

    // Auto-submit form after component mounts
    if (formRef.current) {
      console.log('Submitting form to WayForPay...');
      
      // Small delay to ensure DOM is ready
      setTimeout(() => {
        formRef.current?.submit();
      }, 100);
    }
  }, [paymentUrl, formFields]);

  return (
    <div className="min-h-screen flex items-center justify-center theme-bg-primary">
      <div className="text-center max-w-md">
        <LoadingSpinner size="lg" />
        <p className="mt-4 text-lg theme-text-secondary">
          {t('payment.redirecting')}
        </p>
        <p className="mt-2 text-sm theme-text-tertiary">
          {t('payment.doNotClose')}
        </p>

        {/* Debug info (remove in production) */}
        <details className="mt-4 text-left theme-surface p-4 rounded-lg">
          <summary className="cursor-pointer text-sm theme-text-secondary">
            Debug Info
          </summary>
          <pre className="text-xs mt-2 overflow-auto theme-text-tertiary">
            {JSON.stringify(formFields, null, 2)}
          </pre>
        </details>

        <form
          ref={formRef}
          method="POST"
          action={paymentUrl}
          acceptCharset="utf-8"
        >
          {Object.entries(formFields).map(([key, value]) => {
            if (Array.isArray(value)) {
              // WayForPay expects multiple fields with same name for arrays
              // NOT productName[0] but just productName, productName, productName
              return value.map((item, index) => (
                <input
                  key={`${key}_${index}`}
                  type="hidden"
                  name={key}
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
          
          {/* Manual submit button for debugging */}
          <button 
            type="submit" 
            style={{ display: 'none' }}
            id="wayforpay-submit"
          >
            Submit
          </button>
        </form>
      </div>
    </div>
  );
};
