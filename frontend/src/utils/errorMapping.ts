/**
 * Utility for mapping backend error codes to translation keys
 */

export interface BackendError {
  error?: string;
  errorCode?: string;
  detail?: string;
  message?: string;
}

// Service types for type safety
export type ServiceType = 'category' | 'expense' | 'account' | 'income' | 'debt' | 'goals' | 'currency' | 'recurring' | 'user';

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
 * Maps backend error codes to translation keys for income
 */
export const getIncomeErrorTranslationKey = (error: BackendError | string): string => {
  const errorCode = typeof error === 'string' ? null : error.errorCode;
  
  if (!errorCode) {
    return 'income.errors.genericError';
  }

  const errorMap: Record<string, string> = {
    'INCOME_NOT_FOUND': 'income.errors.notFound',
    'INCOME_VALIDATION_FAILED': 'income.errors.validationFailed',
    'INCOME_AMOUNT_INVALID': 'income.errors.invalidAmount',
    'INCOME_AMOUNT_TOO_LARGE': 'income.errors.amountTooLarge',
    'INCOME_AMOUNT_NEGATIVE': 'income.errors.amountNegative',
    'INCOME_DATE_INVALID_FORMAT': 'income.errors.invalidDateFormat',
    'INCOME_DATE_FUTURE': 'income.errors.dateFuture',
    'INCOME_DESCRIPTION_TOO_LONG': 'income.errors.descriptionTooLong',
    'CATEGORY_VALIDATION_FAILED': 'income.errors.categoryValidationFailed',
    'ACCOUNT_VALIDATION_FAILED': 'income.errors.accountValidationFailed',
    'ACCOUNT_BALANCE_UPDATE_FAILED': 'income.errors.balanceUpdateFailed',
    'EXTERNAL_SERVICE_UNAVAILABLE': 'income.errors.externalServiceUnavailable',
    'VALIDATION_ERROR': 'income.errors.validationError',
  };

  return errorMap[errorCode] || 'income.errors.genericError';
};

/**
 * Maps backend error codes to translation keys for debt
 */
export const getDebtErrorTranslationKey = (error: BackendError | string): string => {
  const errorCode = typeof error === 'string' ? null : error.errorCode;
  
  if (!errorCode) {
    return 'debt.errors.genericError';
  }

  const errorMap: Record<string, string> = {
    'DEBT_NOT_FOUND': 'debt.errors.notFound',
    'CONTACT_NOT_FOUND': 'debt.errors.contactNotFound',
    'PAYMENT_NOT_FOUND': 'debt.errors.paymentNotFound',
    'DEBT_VALIDATION_FAILED': 'debt.errors.validationFailed',
    'CONTACT_VALIDATION_FAILED': 'debt.errors.contactValidationFailed',
    'PAYMENT_VALIDATION_FAILED': 'debt.errors.paymentValidationFailed',
    'INVALID_DEBT_AMOUNT': 'debt.errors.invalidAmount',
    'PAYMENT_AMOUNT_EXCEEDS_BALANCE': 'debt.errors.paymentExceedsBalance',
    'INVALID_DEBT_DATE': 'debt.errors.invalidDate',
    'EXTERNAL_SERVICE_ERROR': 'debt.errors.externalServiceError',
    'DATABASE_ERROR': 'debt.errors.databaseError',
    'CONTACT_HAS_ASSOCIATED_DEBTS': 'debt.errors.contactHasAssociatedDebts',
    'DEBT_CREATION_FAILED': 'debt.errors.creationFailed',
    'DEBT_UPDATE_FAILED': 'debt.errors.updateFailed',
    'DEBT_DELETION_FAILED': 'debt.errors.deletionFailed',
    'CONTACT_CREATION_FAILED': 'debt.errors.contactCreationFailed',
    'CONTACT_UPDATE_FAILED': 'debt.errors.contactUpdateFailed',
    'CONTACT_DELETION_FAILED': 'debt.errors.contactDeletionFailed',
    'PAYMENT_CREATION_FAILED': 'debt.errors.paymentCreationFailed',
    'INVALID_DEBT_TYPE': 'debt.errors.invalidDebtType',
    'INVALID_PAYMENT_METHOD': 'debt.errors.invalidPaymentMethod',
  };

  return errorMap[errorCode] || 'debt.errors.genericError';
};

/**
 * Maps backend error codes to translation keys for goals
 */
export const getGoalsErrorTranslationKey = (error: BackendError | string): string => {
  const errorCode = typeof error === 'string' ? null : error.errorCode;
  
  if (!errorCode) {
    return 'goals.errors.genericError';
  }

  const errorMap: Record<string, string> = {
    'GOAL_NOT_FOUND': 'goals.errors.notFound',
    'GOAL_VALIDATION_FAILED': 'goals.errors.validationFailed',
    'GOAL_ACCESS_DENIED': 'goals.errors.accessDenied',
    'MILESTONE_NOT_FOUND': 'goals.errors.milestoneNotFound',
    'MILESTONE_VALIDATION_FAILED': 'goals.errors.milestoneValidationFailed',
    'GOAL_PROGRESS_UPDATE_FAILED': 'goals.errors.progressUpdateFailed',
    'GOAL_CREATION_FAILED': 'goals.errors.creationFailed',
    'GOAL_UPDATE_FAILED': 'goals.errors.updateFailed',
    'GOAL_DELETION_FAILED': 'goals.errors.deletionFailed',
    'GOAL_RETRIEVAL_FAILED': 'goals.errors.retrievalFailed',
    'GOAL_STATISTICS_FAILED': 'goals.errors.statisticsFailed',
    'MILESTONE_CREATION_FAILED': 'goals.errors.milestoneCreationFailed',
    'MILESTONE_RETRIEVAL_FAILED': 'goals.errors.milestoneRetrievalFailed',
    'MILESTONE_PROGRESS_UPDATE_FAILED': 'goals.errors.milestoneProgressUpdateFailed',
  };

  return errorMap[errorCode] || 'goals.errors.genericError';
};

/**
 * Maps backend error codes to translation keys for currency
 */
export const getCurrencyErrorTranslationKey = (error: BackendError | string): string => {
  const errorCode = typeof error === 'string' ? null : error.errorCode;
  
  if (!errorCode) {
    return 'currency.errors.genericError';
  }

  const errorMap: Record<string, string> = {
    'UNSUPPORTED_CURRENCY': 'currency.errors.unsupportedCurrency',
    'CURRENCY_SERVICE_UNAVAILABLE': 'currency.errors.serviceUnavailable',
    'CURRENCY_CONVERSION_FAILED': 'currency.errors.conversionFailed',
    'CURRENCY_RATES_FETCH_FAILED': 'currency.errors.ratesFetchFailed',
    'CURRENCY_CACHE_ERROR': 'currency.errors.cacheError',
    'CURRENCY_VALIDATION_ERROR': 'currency.errors.validationError',
    'EXTERNAL_API_ERROR': 'currency.errors.externalApiError',
    'REDIS_CONNECTION_ERROR': 'currency.errors.redisConnectionError',
  };

  return errorMap[errorCode] || 'currency.errors.genericError';
};

/**
 * Maps backend error codes to translation keys for recurring payments
 */
export const getRecurringErrorTranslationKey = (error: BackendError | string): string => {
  const errorCode = typeof error === 'string' ? null : error.errorCode;
  
  if (!errorCode) {
    return 'recurring.errors.genericError';
  }

  const errorMap: Record<string, string> = {
    'RECURRING_PAYMENT_NOT_FOUND': 'recurring.errors.paymentNotFound',
    'INVALID_SCHEDULE_CONFIG': 'recurring.errors.invalidScheduleConfig',
    'PAYMENT_EXECUTION_FAILED': 'recurring.errors.paymentExecutionFailed',
    'CATEGORY_NOT_FOUND': 'recurring.errors.categoryNotFound',
    'INVALID_PAYMENT_STATUS': 'recurring.errors.invalidPaymentStatus',
    'PAYMENT_ALREADY_PAUSED': 'recurring.errors.paymentAlreadyPaused',
    'PAYMENT_NOT_PAUSED': 'recurring.errors.paymentNotPaused',
    'SCHEDULE_NOT_FOUND': 'recurring.errors.scheduleNotFound',
    'INVALID_SCHEDULE_STATUS': 'recurring.errors.invalidScheduleStatus',
    'SERVICE_CLIENT_ERROR': 'recurring.errors.serviceClientError',
    'DATABASE_ERROR': 'recurring.errors.databaseError',
    'VALIDATION_ERROR': 'recurring.errors.validationError',
    'INTERNAL_SERVER_ERROR': 'recurring.errors.internalServerError',
  };

  return errorMap[errorCode] || 'recurring.errors.genericError';
};

/**
 * Maps backend error codes to translation keys for user/auth
 */
export const getUserErrorTranslationKey = (error: BackendError | string): string => {
  const errorCode = typeof error === 'string' ? null : error.errorCode;
  
  if (!errorCode) {
    return 'user.errors.genericError';
  }

  const errorMap: Record<string, string> = {
    'EMAIL_ALREADY_TAKEN': 'user.errors.emailAlreadyTaken',
    'USERNAME_ALREADY_TAKEN': 'user.errors.usernameAlreadyTaken',
    'INVALID_CREDENTIALS': 'user.errors.invalidCredentials',
    'USER_NOT_FOUND': 'user.errors.notFound',
    'UNAUTHORIZED': 'user.errors.unauthorized',
    'INVALID_TOKEN': 'user.errors.invalidToken',
    'ACCOUNT_LOCKED': 'user.errors.accountLocked',
    'WEAK_PASSWORD': 'user.errors.weakPassword',
    'INVALID_USERNAME': 'user.errors.invalidUsername',
    'INVALID_EMAIL': 'user.errors.invalidEmail',
    'RATE_LIMIT_EXCEEDED': 'user.errors.rateLimitExceeded',
    'VALIDATION_ERROR': 'user.errors.validationError',
    'REGISTRATION_ERROR': 'user.errors.registrationError',
    'PASSWORD_POLICY_ERROR': 'user.errors.passwordPolicyError',
    'USERNAME_POLICY_ERROR': 'user.errors.usernamePolicyError',
    'INTERNAL_ERROR': 'user.errors.internalError',
  };

  return errorMap[errorCode] || 'user.errors.genericError';
};

/**
 * Generic error mapping function
 */
export const getErrorTranslationKey = (error: BackendError | string, service: ServiceType = 'category'): string => {
  switch (service) {
    case 'category':
      return getCategoryErrorTranslationKey(error);
    case 'expense':
      return getExpenseErrorTranslationKey(error);
    case 'account':
      return getAccountErrorTranslationKey(error);
    case 'income':
      return getIncomeErrorTranslationKey(error);
    case 'debt':
      return getDebtErrorTranslationKey(error);
    case 'goals':
      return getGoalsErrorTranslationKey(error);
    case 'currency':
      return getCurrencyErrorTranslationKey(error);
    case 'recurring':
      return getRecurringErrorTranslationKey(error);
    case 'user':
      return getUserErrorTranslationKey(error);
    default:
      return 'common.errors.genericError';
  }
};
