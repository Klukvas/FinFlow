import React, { useEffect } from 'react';
import { LoadingSpinner } from '@/components/ui/shared/LoadingSpinner';
import { useTranslation } from 'react-i18next';

interface WayForPayWidgetProps {
  formFields: Record<string, any>;
}

// Declare global WayForPay widget
declare global {
  interface Window {
    WayForPay: any;
  }
}

export const WayForPayWidget: React.FC<WayForPayWidgetProps> = ({ formFields }) => {
  const { t } = useTranslation();

  useEffect(() => {
    // Load WayForPay widget script
    const script = document.createElement('script');
    script.src = 'https://secure.wayforpay.com/server/pay-widget.js';
    script.id = 'widget-wfp-script';
    
    script.onload = () => {
      console.log('WayForPay widget loaded');
      console.log('Form data:', formFields);
      
      // Initialize payment widget
      if (window.WayForPay) {
        const wayforpay = new window.WayForPay();
        
        // Run widget
        wayforpay.run(
          formFields,
          (response: any) => {
            // Approved callback
            console.log('Payment approved:', response);
          },
          (response: any) => {
            // Declined callback
            console.log('Payment declined:', response);
          },
          (response: any) => {
            // Pending/In-Progress callback
            console.log('Payment pending:', response);
          }
        );
      }
    };

    script.onerror = () => {
      console.error('Failed to load WayForPay widget');
    };

    document.body.appendChild(script);

    return () => {
      // Cleanup
      const existingScript = document.getElementById('widget-wfp-script');
      if (existingScript) {
        document.body.removeChild(existingScript);
      }
    };
  }, [formFields]);

  return (
    <div className="min-h-screen flex items-center justify-center theme-bg-primary">
      <div className="text-center max-w-2xl w-full px-4">
        <LoadingSpinner size="lg" />
        <p className="mt-4 text-lg theme-text-secondary">
          {t('payment.redirecting')}
        </p>
        <p className="mt-2 text-sm theme-text-tertiary">
          {t('payment.doNotClose')}
        </p>

        {/* WayForPay widget will be injected here */}
        <div id="wayforpay-container" className="mt-8"></div>
      </div>
    </div>
  );
};
