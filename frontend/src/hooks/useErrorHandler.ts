import { useTranslation } from 'react-i18next';
import { toast } from 'sonner';
import { getErrorTranslationKey, BackendError } from '@/utils/errorMapping';

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
    service: 'category' | 'expense' | 'account' = 'category',
    showToast: boolean = true,
  ) => {
    if (logError) {
      console.error(`Error in ${service}:`, error);
    }
    let errorMessage: string;


    // its a backend error
    console.log('Error handler received:', error);
    console.log('Has errorCode:', error && typeof error === 'object' && 'errorCode' in error);
    
    if(error && typeof error === 'object' && 'errorCode' in error){
      const translationKey = getErrorTranslationKey(error, service);
      console.log('Translation key:', translationKey);
      errorMessage = t(translationKey);
      console.log('Final message:', errorMessage);
    }else{
      console.log('Using generic error');
      errorMessage = t(`${service}.errors.genericError`);
    }

    if (showToast) {
      toast.error(errorMessage, {
        testId: 'error-toast'
      });
    }

    return errorMessage;
  };

  const handleCategoryError = (error: ErrorType, showToast: boolean = true) => {
    return handleError(error, 'category', showToast);
  };

  const handleExpenseError = (error: ErrorType, showToast: boolean = true) => {
    return handleError(error, 'expense', showToast);
  };

  const handleAccountError = (error: ErrorType, showToast: boolean = true) => {
    return handleError(error, 'account', showToast);
  };

  return {
    handleError,
    handleCategoryError,
    handleExpenseError,
    handleAccountError,
  };
};
