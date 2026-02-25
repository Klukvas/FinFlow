import React, {
  createContext,
  useContext,
  useState,
  useCallback,
  ReactNode,
} from "react";
import { useApiClients } from "@/hooks/useApiClients";
import {
  CreatePaymentRequest,
  ChangePlanRequest,
  ChangePlanResponse,
  Payment,
  PaymentUIState,
} from "@/types/payment";
import { useAuth } from "./AuthContext";
import { logger } from "@/utils/logger";

interface PaymentContextType {
  state: PaymentUIState;
  createPayment: (request: CreatePaymentRequest) => Promise<Payment | null>;
  changePlan: (
    request: ChangePlanRequest,
  ) => Promise<ChangePlanResponse | null>;
  getPayment: (paymentId: string) => Promise<Payment | null>;
  getPaymentByOrderRef: (orderReference: string) => Promise<Payment | null>;
  pollPaymentStatus: (paymentId: string) => Promise<Payment | null>;
  redirectToPayment: (paymentUrl: string) => void;
  clearError: () => void;
  isProcessing: boolean;
}

const PaymentContext = createContext<PaymentContextType | undefined>(undefined);

export const PaymentProvider: React.FC<{ children: ReactNode }> = ({
  children,
}) => {
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
          error: "User not authenticated",
        }));
        return null;
      }

      setState((prev) => ({ ...prev, isProcessing: true, error: undefined }));

      try {
        // Ensure user_id is a string
        const requestWithStringId = {
          ...request,
          user_id: String(request.user_id),
          workspace_id: request.workspace_id
            ? String(request.workspace_id)
            : undefined,
        };

        // Deterministic idempotency key: same key for same user+plan within a 5-min window
        // This ensures server-side dedup works if the user double-clicks or retries quickly
        const IDEMPOTENCY_WINDOW_MS = 5 * 60 * 1000;
        const timeWindow = Math.floor(Date.now() / IDEMPOTENCY_WINDOW_MS);
        const idempotencyKey = `${user.id}-${requestWithStringId.plan_code}-${timeWindow}`;

        const response = await paymentApi.createPayment(
          requestWithStringId,
          idempotencyKey,
        );

        if ("error" in response) {
          setState((prev) => ({
            ...prev,
            isProcessing: false,
            error: response.error,
          }));
          return null;
        }

        // Store payment info
        const payment: Payment = {
          id: response.payment_id,
          order_reference: response.order_reference,
          provider: response.provider,
          amount: response.amount,
          currency: response.currency,
          status: response.status,
          provider_payment_url: response.payment_url,
          checkout_url: response.checkout_url,
          transaction_id: response.transaction_id,
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
        logger.error("Failed to create payment:", error);
        setState((prev) => ({
          ...prev,
          isProcessing: false,
          error:
            error instanceof Error ? error.message : "Failed to create payment",
        }));
        return null;
      }
    },
    [user, paymentApi],
  );

  const changePlan = useCallback(
    async (request: ChangePlanRequest): Promise<ChangePlanResponse | null> => {
      if (!user?.id) {
        setState((prev) => ({
          ...prev,
          error: "User not authenticated",
        }));
        return null;
      }

      setState((prev) => ({ ...prev, isProcessing: true, error: undefined }));

      try {
        const response = await paymentApi.changePlan(request);

        if ("error" in response) {
          setState((prev) => ({
            ...prev,
            isProcessing: false,
            error: response.error,
          }));
          return null;
        }

        setState((prev) => ({ ...prev, isProcessing: false }));
        return response;
      } catch (error) {
        logger.error("Failed to change plan:", error);
        setState((prev) => ({
          ...prev,
          isProcessing: false,
          error:
            error instanceof Error ? error.message : "Failed to change plan",
        }));
        return null;
      }
    },
    [user, paymentApi],
  );

  const getPayment = useCallback(
    async (paymentId: string): Promise<Payment | null> => {
      setState((prev) => ({ ...prev, isProcessing: true, error: undefined }));

      try {
        const response = await paymentApi.getPayment(paymentId);

        if ("error" in response) {
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
        logger.error("Failed to get payment:", error);
        setState((prev) => ({
          ...prev,
          isProcessing: false,
          error:
            error instanceof Error ? error.message : "Failed to get payment",
        }));
        return null;
      }
    },
    [paymentApi],
  );

  const getPaymentByOrderRef = useCallback(
    async (orderReference: string): Promise<Payment | null> => {
      setState((prev) => ({ ...prev, isProcessing: true, error: undefined }));

      try {
        const response = await paymentApi.getPaymentByOrderRef(orderReference);

        if ("error" in response) {
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
        logger.error("Failed to get payment by order ref:", error);
        setState((prev) => ({
          ...prev,
          isProcessing: false,
          error:
            error instanceof Error ? error.message : "Failed to get payment",
        }));
        return null;
      }
    },
    [paymentApi],
  );

  const pollPaymentStatus = useCallback(
    async (paymentId: string): Promise<Payment | null> => {
      setState((prev) => ({ ...prev, isProcessing: true, error: undefined }));

      try {
        const response = await paymentApi.pollPaymentStatus(paymentId);

        if ("error" in response) {
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
        logger.error("Failed to poll payment status:", error);
        setState((prev) => ({
          ...prev,
          isProcessing: false,
          error:
            error instanceof Error
              ? error.message
              : "Failed to poll payment status",
        }));
        return null;
      }
    },
    [paymentApi],
  );

  const redirectToPayment = useCallback((paymentUrl: string) => {
    // Redirect to payment provider checkout
    window.location.href = paymentUrl;
  }, []);

  const value: PaymentContextType = {
    state,
    createPayment,
    changePlan,
    getPayment,
    getPaymentByOrderRef,
    pollPaymentStatus,
    redirectToPayment,
    clearError,
    isProcessing: state.isProcessing,
  };

  return (
    <PaymentContext.Provider value={value}>{children}</PaymentContext.Provider>
  );
};

export const usePayment = (): PaymentContextType => {
  const context = useContext(PaymentContext);
  if (!context) {
    throw new Error("usePayment must be used within a PaymentProvider");
  }
  return context;
};
