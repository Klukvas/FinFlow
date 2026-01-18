import React, { useEffect, useState } from 'react';
import { useTranslation } from 'react-i18next';
import { useLocation, useNavigate } from 'react-router-dom';
import { Button } from '@/components/ui/shared/Button';
import { FaArrowRight, FaCopy, FaCheckCircle } from 'react-icons/fa';

export const PaymentCheckout: React.FC = () => {
  const { t } = useTranslation();
  const location = useLocation();
  const navigate = useNavigate();
  const [copied, setCopied] = useState(false);

  // Get payment data from location state
  const paymentData = location.state as {
    paymentUrl: string;
    formFields: Record<string, any>;
  } | null;

  useEffect(() => {
    if (!paymentData) {
      // No payment data, redirect to pricing
      navigate('/pricing');
    }
  }, [paymentData, navigate]);

  if (!paymentData) {
    return null;
  }

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    // Submit form
    const form = document.getElementById('wayforpay-form') as HTMLFormElement;
    form.submit();
  };

  const copyToClipboard = () => {
    navigator.clipboard.writeText(JSON.stringify(paymentData.formFields, null, 2));
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  return (
    <div className="min-h-screen bg-gray-50 dark:bg-gray-900 py-8 px-4">
      <div className="max-w-4xl mx-auto">
        <div className="bg-white dark:bg-gray-800 rounded-lg shadow-lg p-8 border border-gray-200 dark:border-gray-700">
          <h1 className="text-2xl font-bold text-gray-900 dark:text-white mb-6">
            🔍 Payment Checkout - Debug Mode
          </h1>

          <div className="space-y-6">
            {/* Payment Info */}
            <div className="bg-blue-50 dark:bg-blue-900/20 rounded-lg p-4 border border-blue-200 dark:border-blue-800">
              <h2 className="font-semibold text-gray-900 dark:text-white mb-3">Payment Information:</h2>
              <div className="space-y-2 text-sm">
                <div className="flex justify-between">
                  <span className="text-gray-600 dark:text-gray-400">Amount:</span>
                  <span className="text-gray-900 dark:text-white font-medium">
                    {paymentData.formFields.amount} {paymentData.formFields.currency}
                  </span>
                </div>
                <div className="flex justify-between">
                  <span className="text-gray-600 dark:text-gray-400">Order Reference:</span>
                  <span className="text-gray-900 dark:text-white font-mono text-xs">
                    {paymentData.formFields.orderReference}
                  </span>
                </div>
                <div className="flex justify-between">
                  <span className="text-gray-600 dark:text-gray-400">Merchant:</span>
                  <span className="text-gray-900 dark:text-white">
                    {paymentData.formFields.merchantAccount}
                  </span>
                </div>
                <div className="flex justify-between">
                  <span className="text-gray-600 dark:text-gray-400">Domain:</span>
                  <span className="text-gray-900 dark:text-white">
                    {paymentData.formFields.merchantDomainName}
                  </span>
                </div>
              </div>
            </div>

            {/* Full Form Data */}
            <div className="bg-gray-50 dark:bg-gray-900/50 rounded-lg p-4 border border-gray-200 dark:border-gray-700">
              <div className="flex items-center justify-between mb-3">
                <h2 className="font-semibold text-gray-900 dark:text-white">Full Form Data:</h2>
                <Button
                  variant="outline"
                  size="sm"
                  onClick={copyToClipboard}
                >
                  {copied ? <FaCheckCircle className="mr-1" /> : <FaCopy className="mr-1" />}
                  {copied ? 'Copied!' : 'Copy JSON'}
                </Button>
              </div>
              <pre className="text-xs text-gray-700 dark:text-gray-300 overflow-auto p-4 bg-white dark:bg-gray-800 rounded border border-gray-200 dark:border-gray-600 max-h-96">
                {JSON.stringify(paymentData.formFields, null, 2)}
              </pre>
            </div>

            {/* Hidden Form */}
            <form
              id="wayforpay-form"
              method="POST"
              action={paymentData.paymentUrl}
              className="hidden"
            >
              {Object.entries(paymentData.formFields).map(([key, value]) => {
                if (Array.isArray(value)) {
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
            </form>

            {/* Action Buttons */}
            <div className="flex gap-4">
              <Button
                variant="primary"
                size="lg"
                fullWidth
                onClick={handleSubmit}
              >
                <FaArrowRight className="mr-2" />
                Proceed to WayForPay
              </Button>
              <Button
                variant="outline"
                onClick={() => navigate('/pricing')}
              >
                Cancel
              </Button>
            </div>

            {/* Instructions */}
            <div className="bg-yellow-50 dark:bg-yellow-900/20 rounded-lg p-4 border border-yellow-200 dark:border-yellow-800">
              <p className="text-sm text-gray-700 dark:text-gray-300">
                <strong className="text-gray-900 dark:text-white">Debug Mode:</strong> Check the form data above. 
                Click "Proceed to WayForPay" when ready to submit.
              </p>
              <p className="text-sm text-gray-600 dark:text-gray-400 mt-2">
                If you see "Bad Request" after submit, the credentials or signature might be incorrect.
              </p>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};
