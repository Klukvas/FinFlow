import { useTranslation } from "react-i18next";
import { toast } from "sonner";
import {
  getErrorTranslationKey,
  BackendError,
  ServiceType,
} from "@/utils/errorMapping";
import { logger } from "@/utils/logger";

interface UseErrorHandlerOptions {
  showToast?: boolean;
  logError?: boolean;
}

type ErrorType = BackendError | string | Error | void;

export const useErrorHandler = (options: UseErrorHandlerOptions = {}) => {
  const { logError = true } = options;
  const { t } = useTranslation();

  const handleError = (
    error: ErrorType,
    service: ServiceType = "category",
    showToast: boolean = true,
  ) => {
    if (logError) {
      logger.error(`Error in ${service}:`, error);
    }
    let errorMessage: string;

    if (error && typeof error === "object" && "errorCode" in error) {
      const translationKey = getErrorTranslationKey(error, service);
      errorMessage = t(translationKey);
    } else {
      errorMessage = t(`${service}.errors.genericError`);
    }

    if (showToast) {
      toast.error(errorMessage, {
        testId: "error-toast",
      });
    }

    return errorMessage;
  };

  const handleCategoryError = (error: ErrorType, showToast: boolean = true) => {
    return handleError(error, "category", showToast);
  };

  const handleExpenseError = (error: ErrorType, showToast: boolean = true) => {
    return handleError(error, "expense", showToast);
  };

  const handleAccountError = (error: ErrorType, showToast: boolean = true) => {
    return handleError(error, "account", showToast);
  };

  const handleIncomeError = (error: ErrorType, showToast: boolean = true) => {
    return handleError(error, "income", showToast);
  };

  const handleDebtError = (error: ErrorType, showToast: boolean = true) => {
    return handleError(error, "debt", showToast);
  };

  const handleGoalsError = (error: ErrorType, showToast: boolean = true) => {
    return handleError(error, "goals", showToast);
  };

  const handleCurrencyError = (error: ErrorType, showToast: boolean = true) => {
    return handleError(error, "currency", showToast);
  };

  const handleRecurringError = (
    error: ErrorType,
    showToast: boolean = true,
  ) => {
    return handleError(error, "recurring", showToast);
  };

  const handleUserError = (error: ErrorType, showToast: boolean = true) => {
    return handleError(error, "user", showToast);
  };

  return {
    handleError,
    handleCategoryError,
    handleExpenseError,
    handleAccountError,
    handleIncomeError,
    handleDebtError,
    handleGoalsError,
    handleCurrencyError,
    handleRecurringError,
    handleUserError,
  };
};
