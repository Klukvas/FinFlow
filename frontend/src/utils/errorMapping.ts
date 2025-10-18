/**
 * Utility for mapping backend error codes to translation keys
 */

export interface BackendError {
  error?: string;
  errorCode?: string;
  detail?: string;
  message?: string;
}

/**
 * Maps backend error codes to translation keys for categories
 */
export const getCategoryErrorTranslationKey = (error: BackendError | string): string => {
  const errorCode = typeof error === 'string' ? null : error.errorCode;
  
  if (!errorCode) {
    return 'category.errors.genericError';
  }

  const errorMap: Record<string, string> = {
    'CATEGORY_DEPTH_EXCEEDED': 'category.errors.depthExceeded',
    'CATEGORY_HAS_CHILDREN': 'category.errors.hasChildren',
    'CATEGORY_NAME_CONFLICT': 'category.errors.nameConflict',
    'CATEGORY_CIRCULAR_RELATIONSHIP': 'category.errors.circularRelationship',
    'CATEGORY_OWNERSHIP_ERROR': 'category.errors.ownershipError',
    'CATEGORY_NOT_FOUND': 'category.errors.notFound',
    'CATEGORY_VALIDATION_ERROR': 'category.errors.validationError',
  };

  return errorMap[errorCode] || 'category.errors.genericError';
};

/**
 * Maps backend error codes to translation keys for expenses
 */
export const getExpenseErrorTranslationKey = (error: BackendError | string): string => {
  const errorCode = typeof error === 'string' ? null : error.errorCode;
  
  if (!errorCode) {
    return 'expense.errors.genericError';
  }

  const errorMap: Record<string, string> = {
    'EXPENSE_CATEGORY_NOT_FOUND': 'expense.errors.invalidCategory',
    'EXPENSE_ACCOUNT_NOT_FOUND': 'expense.errors.invalidAccount',
    'EXPENSE_INVALID_AMOUNT': 'expense.errors.invalidAmount',
    'EXPENSE_VALIDATION_ERROR': 'expense.errors.validationError',
  };

  return errorMap[errorCode] || 'expense.errors.genericError';
};

/**
 * Maps backend error codes to translation keys for accounts
 */
export const getAccountErrorTranslationKey = (error: BackendError | string): string => {
  const errorCode = typeof error === 'string' ? null : error.errorCode;
  
  if (!errorCode) {
    return 'account.errors.genericError';
  }

  const errorMap: Record<string, string> = {
    'ACCOUNT_NAME_CONFLICT': 'account.errors.nameConflict',
    'ACCOUNT_VALIDATION_ERROR': 'account.errors.validationError',
    'ACCOUNT_NOT_FOUND': 'account.errors.notFound',
  };

  return errorMap[errorCode] || 'account.errors.genericError';
};

/**
 * Generic error mapping function
 */
export const getErrorTranslationKey = (error: BackendError | string, service: 'category' | 'expense' | 'account' = 'category'): string => {
  switch (service) {
    case 'category':
      return getCategoryErrorTranslationKey(error);
    case 'expense':
      return getExpenseErrorTranslationKey(error);
    case 'account':
      return getAccountErrorTranslationKey(error);
    default:
      return 'common.errors.genericError';
  }
};
