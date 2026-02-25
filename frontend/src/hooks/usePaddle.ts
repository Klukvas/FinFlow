import { useRef, useCallback } from "react";
import { config } from "@/config/env";
import { logger } from "@/utils/logger";

declare global {
  interface Window {
    Paddle?: {
      Environment: {
        set: (env: "sandbox" | "production") => void;
      };
      Initialize: (options: {
        token: string;
        eventCallback?: (event: PaddleEvent) => void;
      }) => void;
      Checkout: {
        open: (options: {
          transactionId: string;
          customer?: {
            email?: string;
            address?: {
              countryCode?: string;
            };
          };
          settings?: {
            displayMode?: "overlay" | "inline";
            theme?: "light" | "dark";
            locale?: string;
            successUrl?: string;
          };
        }) => void;
      };
      Initialized: boolean;
    };
  }
}

export interface PaddleEvent {
  name: string;
  data?: Record<string, unknown>;
}

export interface CheckoutCustomer {
  email?: string;
  countryCode?: string;
  locale?: string;
}

interface UsePaddleOptions {
  onCheckoutComplete?: (data: PaddleEvent) => void;
  onCheckoutClosed?: () => void;
}

// Module-level flag — Paddle.Initialize() can only be called once
let paddleInitialized = false;

function ensurePaddleInitialized(
  eventCallback: (event: PaddleEvent) => void,
): boolean {
  if (paddleInitialized) return true;
  if (!window.Paddle) {
    logger.error("Paddle.js script not loaded");
    return false;
  }

  const { clientToken, environment } = config.paddle;
  if (!clientToken) {
    logger.error("VITE_PADDLE_CLIENT_TOKEN is not set");
    return false;
  }

  try {
    window.Paddle.Environment.set(environment);
    window.Paddle.Initialize({
      token: clientToken,
      eventCallback,
    });
    paddleInitialized = true;
    logger.info("Paddle.js initialized successfully", { environment });
    return true;
  } catch (err) {
    logger.error("Failed to initialize Paddle.js:", err);
    return false;
  }
}

export const usePaddle = (options: UsePaddleOptions = {}) => {
  const { onCheckoutComplete, onCheckoutClosed } = options;

  const callbacksRef = useRef({ onCheckoutComplete, onCheckoutClosed });
  callbacksRef.current = { onCheckoutComplete, onCheckoutClosed };

  const openCheckout = useCallback(
    (transactionId: string, customer?: CheckoutCustomer) => {
      // Lazy init — initialize on first use, not on component mount
      const ready = ensurePaddleInitialized((event: PaddleEvent) => {
        logger.info("Paddle event:", event.name, event.data);
        if (event.name === "checkout.completed") {
          callbacksRef.current.onCheckoutComplete?.(event);
        }
        if (event.name === "checkout.closed") {
          callbacksRef.current.onCheckoutClosed?.();
        }
      });

      if (!ready) {
        logger.error("Cannot open checkout — Paddle not ready");
        return false;
      }

      logger.info(
        "Opening Paddle checkout for transaction:",
        transactionId,
        customer,
      );
      window.Paddle!.Checkout.open({
        transactionId,
        ...(customer?.email || customer?.countryCode
          ? {
              customer: {
                ...(customer.email ? { email: customer.email } : {}),
                ...(customer.countryCode
                  ? { address: { countryCode: customer.countryCode } }
                  : {}),
              },
            }
          : {}),
        ...(customer?.locale
          ? {
              settings: { locale: customer.locale },
            }
          : {}),
      });

      return true;
    },
    [],
  );

  return { openCheckout, isReady: paddleInitialized };
};
