import React, { createContext, useContext, useState, useCallback, ReactNode } from 'react';
import { useApiClients } from '@/hooks/useApiClients';
import {
  CreatePaymentRequest,
  Payment,
  PaymentUIState,
} from '@/types/payment';
import { useAuth } from './AuthContext';

interface PaymentContextType {
  state: PaymentUIState;
  createPayment: (request: CreatePaymentRequest) => Promise<Payment | null>;
  getPayment: (paymentId: string) => Promise<Payment | null>;
  getPaymentByOrderRef: (orderReference: string) => Promise<Payment | null>;
  pollPaymentStatus: (paymentId: string) => Promise<Payment | null>;
  redirectToPayment: (paymentUrl: string) => void;
  clearError: () => void;
  isProcessing: boolean;
}

const PaymentContext = createContext<PaymentContextType | undefined>(undefined);

export const PaymentProvider: React.FC<{ children: ReactNode }> = ({ children }) => {
  const { user } = useAuth();
  const { payment: paymentApi } = useApiClients();
  const [state, setState] = useState<PaymentUIState>({
    isProcessing: false,
  });

  const clearError = useCallback(() => {
    setState((prev) => ({ ...prev, error: undefined }));
  }, []);

  const createPayment = useCallback(
    async (request: CreatePaymentRequest): Promise<Payment | null> => {
      if (!user?.id) {
        setState((prev) => ({
          ...prev,
          error: 'User not authenticated',
        }));
        return null;
      }

      setState((prev) => ({ ...prev, isProcessing: true, error: undefined }));

      try {
        // Ensure user_id is a string
        const requestWithStringId = {
          ...request,
          user_id: String(request.user_id),
          workspace_id: request.workspace_id ? String(request.workspace_id) : undefined,
        };

        // Generate idempotency key
        const idempotencyKey = `${user.id}-${Date.now()}-${Math.random().toString(36).substr(2, 9)}`;

        console.log('PaymentContext: Calling API to create payment', requestWithStringId);
        const response = await paymentApi.createPayment(requestWithStringId, idempotencyKey);
        console.log('PaymentContext: API response:', response);

        if ('error' in response) {
          setState((prev) => ({
            ...prev,
            isProcessing: false,
            error: response.error,
          }));
          return null;
        }

        // Store payment info with form fields
        const payment: Payment & { provider_form_fields?: Record<string, any> } = {
          id: response.payment_id,
          order_reference: response.order_reference,
          provider: response.provider,
          amount: response.amount,
          currency: response.currency,
          status: response.status,
          provider_payment_url: response.payment_url,
          provider_form_fields: response.provider_form_fields,
          user_id: request.user_id,
          workspace_id: request.workspace_id,
          purpose: request.purpose,
          plan_code: request.plan_code,
          extra_data: request.metadata,
          created_at: response.created_at,
          updated_at: response.created_at,
        };

        setState((prev) => ({
          ...prev,
          isProcessing: false,
          currentPayment: payment,
        }));

        return payment;
      } catch (error) {
        console.error('Failed to create payment:', error);
        setState((prev) => ({
          ...prev,
          isProcessing: false,
          error: error instanceof Error ? error.message : 'Failed to create payment',
        }));
        return null;
      }
    },
    [user, paymentApi]
  );

  const getPayment = useCallback(async (paymentId: string): Promise<Payment | null> => {
    setState((prev) => ({ ...prev, isProcessing: true, error: undefined }));

    try {
      const response = await paymentApi.getPayment(paymentId);

      if ('error' in response) {
        setState((prev) => ({
          ...prev,
          isProcessing: false,
          error: response.error,
        }));
        return null;
      }

      setState((prev) => ({
        ...prev,
        isProcessing: false,
        currentPayment: response,
      }));

      return response;
    } catch (error) {
      console.error('Failed to get payment:', error);
      setState((prev) => ({
        ...prev,
        isProcessing: false,
        error: error instanceof Error ? error.message : 'Failed to get payment',
      }));
      return null;
    }
  }, [paymentApi]);

  const getPaymentByOrderRef = useCallback(async (orderReference: string): Promise<Payment | null> => {
    setState((prev) => ({ ...prev, isProcessing: true, error: undefined }));

    try {
      const response = await paymentApi.getPaymentByOrderRef(orderReference);

      if ('error' in response) {
        setState((prev) => ({
          ...prev,
          isProcessing: false,
          error: response.error,
        }));
        return null;
      }

      setState((prev) => ({
        ...prev,
        isProcessing: false,
        currentPayment: response,
      }));

      return response;
    } catch (error) {
      console.error('Failed to get payment by order ref:', error);
      setState((prev) => ({
        ...prev,
        isProcessing: false,
        error: error instanceof Error ? error.message : 'Failed to get payment',
      }));
      return null;
    }
  }, [paymentApi]);

  const pollPaymentStatus = useCallback(async (paymentId: string): Promise<Payment | null> => {
    setState((prev) => ({ ...prev, isProcessing: true, error: undefined }));

    try {
      const response = await paymentApi.pollPaymentStatus(paymentId);

      if ('error' in response) {
        setState((prev) => ({
          ...prev,
          isProcessing: false,
          error: response.error,
        }));
        return null;
      }

      setState((prev) => ({
        ...prev,
        isProcessing: false,
        currentPayment: response,
      }));

      return response;
    } catch (error) {
      console.error('Failed to poll payment status:', error);
      setState((prev) => ({
        ...prev,
        isProcessing: false,
        error: error instanceof Error ? error.message : 'Failed to poll payment status',
      }));
      return null;
    }
  }, [paymentApi]);

  const redirectToPayment = useCallback((paymentUrl: string) => {
    // Redirect to WayForPay or other payment provider
    window.location.href = paymentUrl;
  }, []);

  const value: PaymentContextType = {
    state,
    createPayment,
    getPayment,
    getPaymentByOrderRef,
    pollPaymentStatus,
    redirectToPayment,
    clearError,
    isProcessing: state.isProcessing,
  };

  return <PaymentContext.Provider value={value}>{children}</PaymentContext.Provider>;
};

export const usePayment = (): PaymentContextType => {
  const context = useContext(PaymentContext);
  if (!context) {
    throw new Error('usePayment must be used within a PaymentProvider');
  }
  return context;
};
