import React, { useState } from 'react';
import { useLocation, useNavigate } from 'react-router-dom';
import { Button } from '@/components/ui/shared/Button';
import { FaCheckCircle, FaTimesCircle, FaCreditCard } from 'react-icons/fa';

/**
 * Mock WayForPay page for testing integration without real credentials
 * This simulates WayForPay behavior for development
 */
export const MockPaymentPage: React.FC = () => {
  const location = useLocation();
  const navigate = useNavigate();
  const [processing, setProcessing] = useState(false);

  const paymentData = location.state as {
    formFields: Record<string, any>;
  } | null;

  if (!paymentData) {
    return (
      <div className="min-h-screen flex items-center justify-center px-4" style={{ background: 'linear-gradient(135deg, #1e3a5f 0%, #0f172a 100%)' }}>
        <div className="text-center rounded-2xl p-8" style={{ backgroundColor: '#1e293b', border: '1px solid #334155', boxShadow: '0 25px 50px -12px rgba(0, 0, 0, 0.5)' }}>
          <p className="text-red-400 mb-4">No payment data</p>
          <Button onClick={() => navigate('/pricing')} variant="primary">
            Back to Pricing
          </Button>
        </div>
      </div>
    );
  }

  const handleApprove = async () => {
    setProcessing(true);
    
    // Simulate payment processing
    await new Promise(resolve => setTimeout(resolve, 2000));
    
    // Simulate webhook call to backend
    const orderRef = paymentData.formFields.orderReference;
    const amount = paymentData.formFields.amount;
    const currency = paymentData.formFields.currency;
    
    try {
      // Call webhook endpoint (mock)
      await fetch('http://localhost:8013/v1/webhooks/wayforpay', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          merchantAccount: paymentData.formFields.merchantAccount,
          orderReference: orderRef,
          merchantSignature: paymentData.formFields.merchantSignature,
          amount: parseFloat(amount),
          currency: currency,
          authCode: '123456',
          cardPan: '411111******1111',
          transactionStatus: 'Approved',
          reasonCode: 1100,
          createdDate: Math.floor(Date.now() / 1000),
          processingDate: Math.floor(Date.now() / 1000),
          fee: 0.20,
          paymentSystem: 'card',
        }),
      });
    } catch (error) {
      console.error('Webhook call failed:', error);
    }
    
    // Redirect back to app
    const returnUrl = paymentData.formFields.returnUrl || 'http://localhost:5173/payment/return';
    window.location.href = returnUrl;
  };

  const handleDecline = async () => {
    setProcessing(true);
    
    await new Promise(resolve => setTimeout(resolve, 1000));
    
    // Simulate failed payment webhook
    const orderRef = paymentData.formFields.orderReference;
    
    try {
      await fetch('http://localhost:8013/v1/webhooks/wayforpay', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          merchantAccount: paymentData.formFields.merchantAccount,
          orderReference: orderRef,
          merchantSignature: paymentData.formFields.merchantSignature,
          amount: parseFloat(paymentData.formFields.amount),
          currency: paymentData.formFields.currency,
          transactionStatus: 'Declined',
          reasonCode: 1101,
          reason: 'Insufficient funds',
          createdDate: Math.floor(Date.now() / 1000),
        }),
      });
    } catch (error) {
      console.error('Webhook call failed:', error);
    }
    
    const returnUrl = paymentData.formFields.returnUrl || 'http://localhost:5173/payment/return';
    window.location.href = returnUrl;
  };

  return (
    <div className="min-h-screen flex items-center justify-center px-4" style={{ background: 'linear-gradient(135deg, #1e3a5f 0%, #0f172a 100%)' }}>
      <div className="max-w-md w-full rounded-2xl p-8 relative z-50" style={{ backgroundColor: '#1e293b', border: '1px solid #334155', boxShadow: '0 25px 50px -12px rgba(0, 0, 0, 0.5)' }}>
        {/* Mock WayForPay Header */}
        <div className="text-center mb-8">
          <div className="w-16 h-16 bg-blue-500 rounded-full flex items-center justify-center mx-auto mb-4">
            <FaCreditCard className="w-8 h-8 text-white" />
          </div>
          <h1 className="text-2xl font-bold text-white mb-2">
            Mock Payment Gateway
          </h1>
          <p className="text-sm text-gray-400">
            (Testing Mode - No real payment)
          </p>
        </div>

        {/* Payment Details */}
        <div className="rounded-lg p-4 mb-6" style={{ backgroundColor: '#0f172a', border: '1px solid #334155' }}>
          <div className="space-y-3 text-sm">
            <div className="flex justify-between">
              <span className="text-gray-400">Merchant:</span>
              <span className="text-white font-medium">
                {paymentData.formFields.merchantAccount}
              </span>
            </div>
            <div className="flex justify-between">
              <span className="text-gray-400">Order:</span>
              <span className="text-white font-mono text-xs">
                {paymentData.formFields.orderReference}
              </span>
            </div>
            <div className="flex justify-between items-center">
              <span className="text-gray-400">Amount:</span>
              <span className="text-2xl font-bold text-blue-400">
                {paymentData.formFields.amount} {paymentData.formFields.currency}
              </span>
            </div>
            <div className="flex justify-between">
              <span className="text-gray-400">Product:</span>
              <span className="text-white text-xs">
                {paymentData.formFields.productName?.[0]}
              </span>
            </div>
          </div>
        </div>

        {/* Test Buttons */}
        <div className="space-y-3">
          <button
            onClick={handleApprove}
            disabled={processing}
            className="w-full py-3 px-4 rounded-lg font-semibold text-white flex items-center justify-center transition-colors disabled:opacity-50"
            style={{ backgroundColor: '#22c55e' }}
          >
            {processing ? (
              'Processing...'
            ) : (
              <>
                <FaCheckCircle className="mr-2" />
                Simulate Success
              </>
            )}
          </button>

          <button
            onClick={handleDecline}
            disabled={processing}
            className="w-full py-3 px-4 rounded-lg font-semibold flex items-center justify-center transition-colors disabled:opacity-50"
            style={{ backgroundColor: 'transparent', border: '1px solid #ef4444', color: '#ef4444' }}
          >
            <FaTimesCircle className="mr-2" />
            Simulate Failure
          </button>
        </div>

        {/* Info */}
        <div className="mt-6 rounded-lg p-4" style={{ backgroundColor: '#1e40af20', border: '1px solid #1e40af' }}>
          <p className="text-xs text-center text-gray-300">
            <strong className="text-white">Mock Payment Page:</strong> This simulates WayForPay behavior.
            Click "Simulate Success" to test successful payment flow.
          </p>
        </div>
      </div>
    </div>
  );
};
