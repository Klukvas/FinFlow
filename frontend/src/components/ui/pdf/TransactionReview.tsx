import React, { useState, useEffect } from 'react';
import { useApiClients } from '@/hooks/useApiClients';
import { ParsedTransaction, TransactionValidation, PDFLimitInfo } from '@/services/api/pdfParserApiClient';
import { Category } from '@/types';
import { useTheme } from '@/contexts/ThemeContext';
import { useTranslation } from 'react-i18next';

interface TransactionReviewProps {
  transactions: ParsedTransaction[];
  limitInfo?: PDFLimitInfo;
  onTransactionsValidated: (validatedTransactions: TransactionValidation[]) => void;
  onClose: () => void;
}

export const TransactionReview: React.FC<TransactionReviewProps> = ({
  transactions,
  limitInfo,
  onTransactionsValidated,
  onClose
}) => {
  const { category, expense, income } = useApiClients();
  const { actualTheme } = useTheme();
  const { t } = useTranslation();
  const [categories, setCategories] = useState<Category[]>([]);
  const [validatedTransactions, setValidatedTransactions] = useState<TransactionValidation[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  // Two-stage validation state
  const [expenseCount, setExpenseCount] = useState<number>(0);
  const [incomeCount, setIncomeCount] = useState<number>(0);
  const [expenseLimit, setExpenseLimit] = useState<number | null>(null);
  const [incomeLimit, setIncomeLimit] = useState<number | null>(null);
  const [validationWarnings, setValidationWarnings] = useState<string[]>([]);
  const [validationResult, setValidationResult] = useState<{
    canProceed: boolean;
    stage1Pass: boolean;
    stage2Pass: boolean;
    selectedExpenses: number;
    selectedIncomes: number;
    totalSelected: number;
  }>({
    canProceed: true,
    stage1Pass: true,
    stage2Pass: true,
    selectedExpenses: 0,
    selectedIncomes: 0,
    totalSelected: 0,
  });

  useEffect(() => {
    loadCategories();
    loadCurrentLimits();
    initializeValidatedTransactions();
  }, []);

  const loadCategories = async () => {
    try {
      const response = await category.getCategories();
      if ('error' in response) {
        setError(response.error);
      } else {
        setCategories(response);
      }
    } catch (err) {
      setError('Failed to load categories');
    } finally {
      setIsLoading(false);
    }
  };

  const loadCurrentLimits = async () => {
    try {
      const [expenseData, incomeData] = await Promise.all([
        expense.getCurrentMonthCount(),
        income.getCurrentMonthCount()
      ]);

      if ('error' in expenseData) {
        console.error('Failed to load expense limits:', expenseData.error);
      } else {
        setExpenseCount(expenseData.count);
        setExpenseLimit(expenseData.limit);
      }

      if ('error' in incomeData) {
        console.error('Failed to load income limits:', incomeData.error);
      } else {
        setIncomeCount(incomeData.count);
        setIncomeLimit(incomeData.limit);
      }
    } catch (err) {
      console.error('Failed to load current month limits:', err);
    }
  };

  const initializeValidatedTransactions = () => {
    const initial: TransactionValidation[] = transactions.map((transaction, index) => {
      const validatedTransaction: TransactionValidation = {
        transaction_id: `txn_${index}`,
        amount: transaction.amount,
        description: transaction.description,
        transaction_date: transaction.transaction_date,
        transaction_type: transaction.transaction_type,
        is_valid: true
      };
      
      if (transaction.category_id !== undefined) {
        validatedTransaction.category_id = transaction.category_id;
      }
      
      return validatedTransaction;
    });
    setValidatedTransactions(initial);
  };

  const updateTransaction = (index: number, updates: Partial<TransactionValidation>) => {
    setValidatedTransactions(prev => 
      prev.map((txn, i) => 
        i === index ? { ...txn, ...updates } : txn
      )
    );
  };

  const toggleTransactionValidity = (index: number) => {
    const transaction = validatedTransactions[index];
    if (transaction) {
      updateTransaction(index, { is_valid: !transaction.is_valid });
    }
  };

  const deleteTransaction = (index: number) => {
    setValidatedTransactions(prev => prev.filter((_, i) => i !== index));
  };

  // Two-Stage Validation Function
  const performTwoStageValidation = () => {
    const warnings: string[] = [];
    const validTxns = validatedTransactions.filter(txn => txn.is_valid);

    // Count by type
    const selectedExpenses = validTxns.filter(txn => txn.transaction_type === 'expense').length;
    const selectedIncomes = validTxns.filter(txn => txn.transaction_type === 'income').length;

    // STAGE 1: Check per-type monthly quotas
    let stage1Pass = true;

    if (expenseLimit !== null) {
      const remaining = expenseLimit - expenseCount;
      if (selectedExpenses > remaining) {
        stage1Pass = false;
        warnings.push(
          `Too many expenses: ${selectedExpenses} selected but only ${remaining} remaining in your monthly quota (${expenseCount}/${expenseLimit}). Please deselect ${selectedExpenses - remaining} expense records.`
        );
      }
    }

    if (incomeLimit !== null) {
      const remaining = incomeLimit - incomeCount;
      if (selectedIncomes > remaining) {
        stage1Pass = false;
        warnings.push(
          `Too many incomes: ${selectedIncomes} selected but only ${remaining} remaining in your monthly quota (${incomeCount}/${incomeLimit}). Please deselect ${selectedIncomes - remaining} income records.`
        );
      }
    }

    // STAGE 2: Check total records per upload (only if Stage 1 passes)
    let stage2Pass = true;
    const totalSelected = selectedExpenses + selectedIncomes;

    if (stage1Pass && limitInfo?.records_per_upload !== null && limitInfo?.records_per_upload !== undefined) {
      if (totalSelected > limitInfo.records_per_upload) {
        stage2Pass = false;
        const excess = totalSelected - limitInfo.records_per_upload;
        warnings.push(
          `Upload limit exceeded: You have ${totalSelected} records selected, but your plan (${limitInfo.plan_code.toUpperCase()}) allows maximum ${limitInfo.records_per_upload} records per upload. Please deselect ${excess} more records (any type).`
        );
      }
    }

    const validationStatus = {
      canProceed: warnings.length === 0,
      stage1Pass,
      stage2Pass,
      selectedExpenses,
      selectedIncomes,
      totalSelected
    };

    setValidationWarnings(warnings);
    setValidationResult(validationStatus);

    return validationStatus;
  };

  // Run validation whenever validated transactions change
  useEffect(() => {
    if (!isLoading) {
      performTwoStageValidation();
    }
  }, [validatedTransactions, expenseCount, incomeCount, expenseLimit, incomeLimit, limitInfo]);

  const [isSubmitting, setIsSubmitting] = useState(false);
  const [deleteConfirmIndex, setDeleteConfirmIndex] = useState<number | null>(null);

  const handleSubmit = async () => {
    // Perform two-stage validation
    const validation = performTwoStageValidation();

    if (!validation.canProceed) {
      setError(t('pdfParserPage.reviewModal.errors.validationFailed'));
      return;
    }
    
    // Validate required fields
    const invalidTransactions = validatedTransactions.filter(txn => 
      txn.is_valid && (!txn.amount || !txn.transaction_date || !txn.description)
    );


    if (invalidTransactions.length > 0) {
      setError(`Please fill in all required fields for ${invalidTransactions.length} transaction(s)`);
      return;
    }

    // Validate that all valid transactions have required fields

    try {
      setIsSubmitting(true);
      setError(null);
      await onTransactionsValidated(validatedTransactions);
      onClose();
    } catch (err) {
      console.error('TransactionReview: Error in handleSubmit:', err);
      setError('Failed to create transactions. Please try again.');
    } finally {
      setIsSubmitting(false);
    }
  };

  const getValidationErrors = (transaction: TransactionValidation) => {
    const errors = [];
    if (transaction.is_valid) {
      if (!transaction.amount || transaction.amount <= 0) errors.push('Amount is required');
      if (!transaction.transaction_date) errors.push('Date is required');
      if (!transaction.description?.trim()) errors.push('Description is required');
    }
    return errors;
  };

  const validTransactions = validatedTransactions.filter(txn => txn.is_valid);
  const invalidTransactions = validatedTransactions.filter(txn => !txn.is_valid);
  
  // Calculate category_exists statistics
  const transactionsWithoutCategory = transactions.filter(txn => !txn.category_exists).length;
  const transactionsWithUserSelectedCategory = validatedTransactions.filter((txn, index) => 
    txn.category_id && !transactions[index]?.category_exists
  ).length;

  if (isLoading) {
    return (
      <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
        <div className="bg-white rounded-lg p-6">
          <p>Loading categories...</p>
        </div>
      </div>
    );
  }

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 overflow-y-auto p-2 sm:p-4">
      <div className="theme-surface rounded-xl theme-shadow-hover w-full max-w-7xl max-h-[95vh] overflow-hidden flex flex-col theme-transition mx-auto">
        {/* Header */}
        <div className={`flex flex-col sm:flex-row justify-between items-start sm:items-center p-4 sm:p-6 theme-border border-b ${
          actualTheme === 'dark' 
            ? 'bg-gradient-to-r from-slate-800 to-slate-700' 
            : 'bg-gradient-to-r from-blue-50 to-indigo-50'
        }`}>
          <div className="flex-1 min-w-0">
            <h2 className="text-xl sm:text-2xl font-bold theme-text-primary truncate">Review Parsed Transactions</h2>
            <p className="text-sm theme-text-secondary mt-1 hidden sm:block">Review and edit the transactions before creating them</p>
            <p className="text-xs theme-text-secondary mt-1 sm:hidden">Review and edit transactions</p>
          </div>
          <button
            onClick={onClose}
            className="theme-text-tertiary hover:theme-text-primary hover:theme-surface-hover rounded-full p-2 theme-transition mt-2 sm:mt-0 flex-shrink-0"
          >
            <svg className="w-5 h-5 sm:w-6 sm:h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
            </svg>
          </button>
        </div>

        {/* Error Message */}
        {error && (
          <div className="mx-4 sm:mx-6 mt-4 p-3 sm:p-4 theme-error-light border-l-4 theme-error-bg rounded-r-lg">
            <div className="flex">
              <div className="flex-shrink-0">
                <svg className="h-4 w-4 sm:h-5 sm:w-5 theme-error" viewBox="0 0 20 20" fill="currentColor">
                  <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zM8.707 7.293a1 1 0 00-1.414 1.414L8.586 10l-1.293 1.293a1 1 0 101.414 1.414L10 11.414l1.293 1.293a1 1 0 001.414-1.414L11.414 10l1.293-1.293a1 1 0 00-1.414-1.414L10 8.586 8.707 7.293z" clipRule="evenodd" />
                </svg>
              </div>
              <div className="ml-3">
                <p className="text-xs sm:text-sm theme-text-primary">{error}</p>
              </div>
            </div>
          </div>
        )}

        {/* PDF Upload Limit Info */}
        {limitInfo && (
          <div className="mx-4 sm:mx-6 mt-4 p-3 sm:p-4 theme-bg-secondary theme-border border rounded-lg">
            <div className="flex items-start">
              <div className="flex-shrink-0">
                <svg className="h-4 w-4 sm:h-5 sm:w-5 theme-accent" viewBox="0 0 20 20" fill="currentColor">
                  <path fillRule="evenodd" d="M18 10a8 8 0 11-16 0 8 8 0 0116 0zm-7-4a1 1 0 11-2 0 1 1 0 012 0zM9 9a1 1 0 000 2v3a1 1 0 001 1h1a1 1 0 100-2v-3a1 1 0 00-1-1H9z" clipRule="evenodd" />
                </svg>
              </div>
              <div className="ml-3 flex-1">
                <h3 className="text-xs sm:text-sm font-semibold theme-text-primary mb-2">{t('pdfParserPage.reviewModal.limitInfo.title')}</h3>
                <div className="grid grid-cols-1 sm:grid-cols-3 gap-2 sm:gap-4">
                  <div className="flex flex-col">
                    <span className="text-xs theme-text-secondary">{t('pdfParserPage.reviewModal.limitInfo.plan')}</span>
                    <span className="text-xs sm:text-sm font-medium theme-text-primary uppercase">{limitInfo.plan_code}</span>
                  </div>
                  <div className="flex flex-col">
                    <span className="text-xs theme-text-secondary">{t('pdfParserPage.reviewModal.limitInfo.monthlyUploads')}</span>
                    <span className="text-xs sm:text-sm font-medium theme-text-primary">
                      {limitInfo.uploads_remaining === null
                        ? t('pdfParserPage.reviewModal.limitInfo.unlimited')
                        : `${limitInfo.uploads_remaining} ${t('pdfParserPage.reviewModal.validation.remaining')} (${limitInfo.uploads_used_this_month}/${limitInfo.uploads_per_month})`}
                    </span>
                  </div>
                  <div className="flex flex-col">
                    <span className="text-xs theme-text-secondary">{t('pdfParserPage.reviewModal.limitInfo.maxPerUpload')}</span>
                    <span className="text-xs sm:text-sm font-medium theme-text-primary">
                      {limitInfo.records_per_upload === null
                        ? t('pdfParserPage.reviewModal.limitInfo.unlimited')
                        : t('pdfParserPage.reviewModal.limitInfo.recordsLimit', { limit: limitInfo.records_per_upload })}
                    </span>
                  </div>
                </div>
              </div>
            </div>
          </div>
        )}

        {/* Two-Stage Validation Warnings */}
        {validationWarnings.length > 0 && (
          <div className="mx-4 sm:mx-6 mt-4 space-y-2">
            <div className="flex items-center space-x-2 mb-2">
              <svg className="h-4 w-4 sm:h-5 sm:w-5 theme-warning" viewBox="0 0 20 20" fill="currentColor">
                <path fillRule="evenodd" d="M8.257 3.099c.765-1.36 2.722-1.36 3.486 0l5.58 9.92c.75 1.334-.213 2.98-1.742 2.98H4.42c-1.53 0-2.493-1.646-1.743-2.98l5.58-9.92zM11 13a1 1 0 11-2 0 1 1 0 012 0zm-1-8a1 1 0 00-1 1v3a1 1 0 002 0V6a1 1 0 00-1-1z" clipRule="evenodd" />
              </svg>
              <h3 className="text-xs sm:text-sm font-semibold theme-warning">Validation Issues</h3>
            </div>
            {validationWarnings.map((warning, idx) => (
              <div key={idx} className="p-3 sm:p-4 theme-warning-light border-l-4 theme-warning-bg rounded-r-lg">
                <div className="flex">
                  <div className="flex-shrink-0">
                    <svg className="h-4 w-4 sm:h-5 sm:w-5 theme-warning" viewBox="0 0 20 20" fill="currentColor">
                      <path fillRule="evenodd" d="M18 10a8 8 0 11-16 0 8 8 0 0116 0zm-7 4a1 1 0 11-2 0 1 1 0 012 0zm-1-9a1 1 0 00-1 1v4a1 1 0 102 0V6a1 1 0 00-1-1z" clipRule="evenodd" />
                    </svg>
                  </div>
                  <div className="ml-3">
                    <p className="text-xs sm:text-sm theme-text-primary">{warning}</p>
                  </div>
                </div>
              </div>
            ))}
          </div>
        )}

        {/* Statistics and Controls */}
        <div className="p-4 sm:p-6 theme-bg-secondary theme-border border-b">
          <div className="flex flex-col gap-4">
            {/* Statistics */}
            <div className="flex flex-wrap items-center gap-4 sm:gap-6">
              <div className="flex items-center space-x-2">
                <div className="w-3 h-3 theme-accent-bg rounded-full"></div>
                <span className="text-xs sm:text-sm font-medium theme-text-primary">Total: {transactions.length}</span>
              </div>
              <div className="flex items-center space-x-2">
                <div className="w-3 h-3 theme-success-bg rounded-full"></div>
                <span className="text-xs sm:text-sm font-medium theme-success">Valid: {validTransactions.length}</span>
              </div>
              <div className="flex items-center space-x-2">
                <div className="w-3 h-3 theme-error-bg rounded-full"></div>
                <span className="text-xs sm:text-sm font-medium theme-error">Invalid: {invalidTransactions.length}</span>
              </div>
              <div className="flex items-center space-x-2">
                <div className="w-3 h-3 theme-warning-bg rounded-full"></div>
                <span className="text-xs sm:text-sm font-medium theme-warning">
                  Categories Needed: {transactionsWithoutCategory - transactionsWithUserSelectedCategory}
                </span>
              </div>
            </div>

            {/* Two-Stage Validation Status */}
            {(expenseLimit !== null || incomeLimit !== null || limitInfo?.records_per_upload !== null) && (() => {
              const validation = performTwoStageValidation();
              const validExpenses = validTransactions.filter(txn => txn.transaction_type === 'expense').length;
              const validIncomes = validTransactions.filter(txn => txn.transaction_type === 'income').length;

              return (
                <div className="flex flex-col space-y-2 pt-3 border-t theme-border">
                  <div className="text-xs sm:text-sm font-semibold theme-text-secondary mb-1">{t('pdfParserPage.reviewModal.validation.title')}:</div>

                  {/* Stage 1: Per-Type Quotas */}
                  <div className="flex flex-wrap items-center gap-3 sm:gap-4">
                    <div className="flex items-center space-x-2">
                      <div className={`w-2 h-2 rounded-full ${validation.stage1Pass ? 'bg-green-500' : 'bg-red-500'}`}></div>
                      <span className="text-xs theme-text-secondary">
                        <strong>{t('pdfParserPage.reviewModal.validation.stage1')}:</strong> {t('pdfParserPage.reviewModal.validation.expenses')}: {validExpenses}/{expenseLimit === null ? '∞' : (expenseLimit - expenseCount)} | {t('pdfParserPage.reviewModal.validation.incomes')}: {validIncomes}/{incomeLimit === null ? '∞' : (incomeLimit - incomeCount)}
                      </span>
                    </div>
                  </div>

                  {/* Stage 2: Upload Limit */}
                  {limitInfo?.records_per_upload !== null && limitInfo?.records_per_upload !== undefined && (
                    <div className="flex items-center space-x-2">
                      <div className={`w-2 h-2 rounded-full ${validation.stage2Pass ? 'bg-green-500' : 'bg-red-500'}`}></div>
                      <span className="text-xs theme-text-secondary">
                        <strong>{t('pdfParserPage.reviewModal.validation.stage2')}:</strong> {t('pdfParserPage.reviewModal.validation.totalRecords')}: {validation.totalSelected}/{limitInfo.records_per_upload}
                      </span>
                    </div>
                  )}

                  {/* Overall Status */}
                  <div className={`text-xs sm:text-sm font-medium ${validation.canProceed ? 'theme-success' : 'theme-error'}`}>
                    {validation.canProceed ? `✓ ${t('pdfParserPage.reviewModal.validation.readyToCreate')}` : `✗ ${t('pdfParserPage.reviewModal.validation.adjustSelection')}`}
                  </div>
                </div>
              );
            })()}
          </div>
        </div>

        {/* Transactions List */}
        <div className="flex-1 overflow-y-auto">
          <div className="p-4 sm:p-6 space-y-3 sm:space-y-4">
            {validatedTransactions.map((transaction, index) => (
              <div
                key={transaction.transaction_id}
                className={`theme-border border rounded-xl p-4 sm:p-6 theme-transition theme-shadow hover:theme-shadow-hover ${
                  transaction.is_valid 
                    ? actualTheme === 'dark'
                      ? 'theme-success-light border-green-600'
                      : 'theme-success-light border-green-200'
                    : actualTheme === 'dark'
                      ? 'theme-error-light border-red-600'
                      : 'theme-error-light border-red-200'
                }`}
              >
                <div className="flex items-start justify-between">
                  <div className="flex-1">
                    {/* Header */}
                    <div className="flex flex-col sm:flex-row sm:items-center gap-3 sm:gap-4 mb-4">
                      <label className="flex items-center space-x-2 cursor-pointer">
                        <input
                          type="checkbox"
                          checked={transaction.is_valid}
                          onChange={() => toggleTransactionValidity(index)}
                          className="w-4 h-4 sm:w-5 sm:h-5 text-blue-600 rounded focus:ring-blue-500 focus:ring-2"
                        />
                        <span className="text-xs sm:text-sm font-medium theme-text-primary">
                          {transaction.is_valid ? 'Include' : 'Exclude'}
                        </span>
                      </label>
                      
                      <div className="flex flex-wrap items-center gap-2 sm:gap-4">
                        <span className={`inline-flex items-center px-2 sm:px-3 py-1 rounded-full text-xs font-medium ${
                          transaction.transaction_type === 'income'
                            ? actualTheme === 'dark'
                              ? 'theme-success-light theme-success'
                              : 'bg-green-100 text-green-800'
                            : actualTheme === 'dark'
                              ? 'theme-error-light theme-error'
                              : 'bg-red-100 text-red-800'
                        }`}>
                          <svg className="w-3 h-3 mr-1" fill="currentColor" viewBox="0 0 20 20">
                            {transaction.transaction_type === 'income' ? (
                              <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-9.293a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z" clipRule="evenodd" />
                            ) : (
                              <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zM8.707 7.293a1 1 0 00-1.414 1.414L8.586 10l-1.293 1.293a1 1 0 101.414 1.414L10 11.414l1.293 1.293a1 1 0 001.414-1.414L11.414 10l1.293-1.293a1 1 0 00-1.414-1.414L10 8.586 8.707 7.293z" clipRule="evenodd" />
                            )}
                          </svg>
                          {transaction.transaction_type.toUpperCase()}
                        </span>
                      
                        <div className="flex items-center space-x-1 text-xs sm:text-sm theme-text-tertiary">
                          <svg className="w-3 h-3 sm:w-4 sm:h-4" fill="currentColor" viewBox="0 0 20 20">
                            <path fillRule="evenodd" d="M6.267 3.455a3.066 3.066 0 001.745-.723 3.066 3.066 0 013.976 0 3.066 3.066 0 001.745.723 3.066 3.066 0 012.812 2.812c.051.643.304 1.254.723 1.745a3.066 3.066 0 010 3.976 3.066 3.066 0 00-.723 1.745 3.066 3.066 0 01-2.812 2.812 3.066 3.066 0 00-1.745.723 3.066 3.066 0 01-3.976 0 3.066 3.066 0 00-1.745-.723 3.066 3.066 0 01-2.812-2.812 3.066 3.066 0 00-.723-1.745 3.066 3.066 0 010-3.976 3.066 3.066 0 00.723-1.745 3.066 3.066 0 012.812-2.812zm7.44 5.252a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z" clipRule="evenodd" />
                          </svg>
                          <span className="hidden sm:inline">Confidence: {transactions[index] ? Math.round(transactions[index].confidence_score * 100) : 0}%</span>
                          <span className="sm:hidden">{transactions[index] ? Math.round(transactions[index].confidence_score * 100) : 0}%</span>
                        </div>
                        
                        
                        {/* Delete button */}
                        {deleteConfirmIndex === index ? (
                          <div className="flex items-center space-x-1 sm:space-x-2">
                            <button
                              onClick={() => {
                                deleteTransaction(index);
                                setDeleteConfirmIndex(null);
                              }}
                              className="flex items-center space-x-1 text-xs sm:text-sm theme-error hover:theme-error-light px-1.5 sm:px-2 py-1 rounded transition-colors"
                            >
                              <svg className="w-3 h-3 sm:w-4 sm:h-4" fill="currentColor" viewBox="0 0 20 20">
                                <path fillRule="evenodd" d="M16.707 5.293a1 1 0 010 1.414l-8 8a1 1 0 01-1.414 0l-4-4a1 1 0 011.414-1.414L8 12.586l7.293-7.293a1 1 0 011.414 0z" clipRule="evenodd" />
                              </svg>
                              <span className="hidden sm:inline">Confirm</span>
                              <span className="sm:hidden">✓</span>
                            </button>
                            <button
                              onClick={() => setDeleteConfirmIndex(null)}
                              className="flex items-center space-x-1 text-xs sm:text-sm theme-text-secondary hover:theme-text-primary px-1.5 sm:px-2 py-1 rounded transition-colors"
                            >
                              <svg className="w-3 h-3 sm:w-4 sm:h-4" fill="currentColor" viewBox="0 0 20 20">
                                <path fillRule="evenodd" d="M4.293 4.293a1 1 0 011.414 0L10 8.586l4.293-4.293a1 1 0 111.414 1.414L11.414 10l4.293 4.293a1 1 0 01-1.414 1.414L10 11.414l-4.293 4.293a1 1 0 01-1.414-1.414L8.586 10 4.293 5.707a1 1 0 010-1.414z" clipRule="evenodd" />
                              </svg>
                              <span className="hidden sm:inline">Cancel</span>
                              <span className="sm:hidden">✕</span>
                            </button>
                          </div>
                        ) : (
                          <button
                            onClick={() => setDeleteConfirmIndex(index)}
                            className="flex items-center space-x-1 text-xs sm:text-sm theme-error hover:theme-error-light px-1.5 sm:px-2 py-1 rounded transition-colors"
                            title="Delete transaction"
                          >
                            <svg className="w-3 h-3 sm:w-4 sm:h-4" fill="currentColor" viewBox="0 0 20 20">
                              <path fillRule="evenodd" d="M9 2a1 1 0 000 2h2a1 1 0 100-2H9z" clipRule="evenodd" />
                              <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zM8.707 7.293a1 1 0 00-1.414 1.414L8.586 10l-1.293 1.293a1 1 0 101.414 1.414L10 11.414l1.293 1.293a1 1 0 001.414-1.414L11.414 10l1.293-1.293a1 1 0 00-1.414-1.414L10 8.586 8.707 7.293z" clipRule="evenodd" />
                            </svg>
                            <span className="hidden sm:inline">Delete</span>
                            <span className="sm:hidden">Del</span>
                          </button>
                        )}
                      </div>
                    </div>

                    {/* Form Fields */}
                    <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4 sm:gap-6">
                      <div className="space-y-2">
                        <label className="block text-xs sm:text-sm font-semibold theme-text-primary">
                          Amount *
                        </label>
                        <div className="relative">
                          <div className="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none">
                            <span className="theme-text-tertiary text-xs sm:text-sm">$</span>
                          </div>
                          <input
                            type="number"
                            step="0.01"
                            value={transaction.amount}
                            onChange={(e) => {
                              const transaction = validatedTransactions[index];
                              if (transaction) {
                                updateTransaction(index, {
                                  amount: parseFloat(e.target.value) || 0
                                });
                              }
                            }}
                            className="block w-full pl-6 sm:pl-7 pr-3 py-2 sm:py-3 theme-border border rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500 theme-transition text-xs sm:text-sm theme-surface theme-text-primary"
                            placeholder="0.00"
                            required
                          />
                        </div>
                      </div>

                      <div className="space-y-2">
                        <label className="block text-xs sm:text-sm font-semibold theme-text-primary">
                          Date *
                        </label>
                        <input
                          type="date"
                          value={transaction.transaction_date}
                          onChange={(e) => {
                            const transaction = validatedTransactions[index];
                            if (transaction) {
                              updateTransaction(index, { transaction_date: e.target.value });
                            }
                          }}
                          className="block w-full px-3 py-2 sm:py-3 theme-border border rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500 theme-transition text-xs sm:text-sm theme-surface theme-text-primary"
                          required
                        />
                      </div>

                      <div className="space-y-2">
                        <label className="block text-xs sm:text-sm font-semibold theme-text-primary">
                          Type *
                        </label>
                        <select
                          value={transaction.transaction_type}
                          onChange={(e) => {
                            const transaction = validatedTransactions[index];
                            if (transaction) {
                              updateTransaction(index, {
                                transaction_type: e.target.value as 'income' | 'expense'
                              });
                            }
                          }}
                          className="block w-full px-3 py-2 sm:py-3 theme-border border rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500 theme-transition text-xs sm:text-sm theme-surface theme-text-primary"
                          required
                        >
                          <option value="expense">Expense</option>
                          <option value="income">Income</option>
                        </select>
                      </div>

                      <div className="space-y-2">
                        <label className="block text-xs sm:text-sm font-semibold theme-text-primary">
                          Category *
                        </label>
                        <select
                          value={transaction.category_id || ''}
                          onChange={(e) => {
                            const transaction = validatedTransactions[index];
                            if (transaction) {
                              const updates: Partial<TransactionValidation> = {};
                              if (e.target.value) {
                                updates.category_id = parseInt(e.target.value);
                              }
                              updateTransaction(index, updates);
                            }
                          }}
                          className="block w-full px-3 py-2 sm:py-3 theme-border border rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500 theme-transition text-xs sm:text-sm theme-surface theme-text-primary"
                        >
                          <option value="">Select Category</option>
                          {categories.map((cat) => (
                            <option key={cat.id} value={cat.id}>
                              {cat.name} {(cat as any).created_by === 'SYSTEM' ? '🤖' : ''}
                            </option>
                          ))}
                        </select>
                        
                        {/* Show MCC-based category suggestion */}
                        {transactions[index]?.mcc_code && !transactions[index]?.category_exists && !transaction.category_id && (
                          <div className="mt-2 p-2 bg-yellow-50 dark:bg-yellow-900/20 border border-yellow-200 dark:border-yellow-800 rounded-lg">
                            <div className="flex items-center text-xs text-yellow-800 dark:text-yellow-200">
                              <svg className="w-3 h-3 mr-1" fill="currentColor" viewBox="0 0 20 20">
                                <path fillRule="evenodd" d="M8.257 3.099c.765-1.36 2.722-1.36 3.486 0l5.58 9.92c.75 1.334-.213 2.98-1.742 2.98H4.42c-1.53 0-2.493-1.646-1.743-2.98l5.58-9.92zM11 13a1 1 0 11-2 0 1 1 0 012 0zm-1-8a1 1 0 00-1 1v3a1 1 0 002 0V6a1 1 0 00-1-1z" clipRule="evenodd" />
                              </svg>
                              Will auto-create: {transactions[index]?.mcc_category_translation || transactions[index]?.mcc_category_name}
                            </div>
                          </div>
                        )}
                      </div>
                    </div>

                    {/* Description */}
                    <div className="mt-4 sm:mt-6 space-y-2">
                      <label className="block text-xs sm:text-sm font-semibold theme-text-primary">
                        Description *
                      </label>
                      <textarea
                        value={transaction.description}
                        onChange={(e) => {
                          const transaction = validatedTransactions[index];
                          if (transaction) {
                            updateTransaction(index, { description: e.target.value });
                          }
                        }}
                        className="block w-full px-3 py-2 sm:py-3 theme-border border rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500 theme-transition resize-none text-xs sm:text-sm theme-surface theme-text-primary"
                        rows={2}
                        placeholder="Enter transaction description..."
                        required
                      />
                    </div>

                    {/* MCC Category Information - Enhanced Display */}
                    {transactions[index]?.mcc_code && (
                      <div className="mt-4 sm:mt-6 space-y-2">
                        <label className="block text-xs sm:text-sm font-semibold theme-text-primary">
                          Merchant Category Code (MCC) Information
                        </label>
                        
                        {/* MCC Code Badge */}
                        <div className="flex items-center gap-2 mb-2">
                          <span className="inline-flex items-center px-2 py-1 rounded-full text-xs font-medium bg-gray-100 text-gray-800 dark:bg-gray-700 dark:text-gray-200">
                            MCC: {transactions[index]?.mcc_code}
                          </span>
                          {transactions[index]?.category_exists ? (
                            <span className="inline-flex items-center px-2 py-1 rounded-full text-xs font-medium bg-green-100 text-green-800 dark:bg-green-900 dark:text-green-200">
                              ✓ Category Exists
                            </span>
                          ) : (
                            <span className="inline-flex items-center px-2 py-1 rounded-full text-xs font-medium bg-yellow-100 text-yellow-800 dark:bg-yellow-900 dark:text-yellow-200">
                              ⚡ Auto-Create
                            </span>
                          )}
                        </div>

                        {/* Category Name Display */}
                        <div className={`px-3 py-2 sm:py-3 rounded-lg border-l-4 ${
                          actualTheme === 'dark'
                            ? 'bg-blue-900/30 border-blue-400 text-blue-200'
                            : 'bg-blue-50 border-blue-400 text-blue-800'
                        }`}>
                          <div className="flex items-center justify-between">
                            <div>
                              <div className="text-sm font-semibold">
                                {transactions[index]?.mcc_category_translation || transactions[index]?.mcc_category_name || 'No category translation available'}
                              </div>
                              {transactions[index]?.mcc_category_name && transactions[index]?.mcc_category_translation && (
                                <div className="text-xs opacity-75 mt-1">
                                  Original: {transactions[index].mcc_category_name}
                                </div>
                              )}
                            </div>
                            {!transactions[index]?.category_exists && (
                              <div className="flex items-center text-xs opacity-75">
                                <svg className="w-3 h-3 mr-1" fill="currentColor" viewBox="0 0 20 20">
                                  <path fillRule="evenodd" d="M11.3 1.046A1 1 0 0112 2v5h4a1 1 0 01.82 1.573l-7 10A1 1 0 018 18v-5H4a1 1 0 01-.82-1.573l7-10a1 1 0 011.12-.38z" clipRule="evenodd" />
                                </svg>
                                Auto-created
                              </div>
                            )}
                          </div>
                        </div>

                        {/* Additional Info */}
                        {!transactions[index]?.category_exists && (
                          <div className="text-xs theme-text-secondary">
                            💡 This category will be automatically created from the MCC code if you don't select a different one.
                          </div>
                        )}
                      </div>
                    )}

                    {/* Validation errors */}
                    {transaction.is_valid && getValidationErrors(transaction).length > 0 && (
                      <div className="mt-4 p-3 theme-error-light theme-border border rounded-lg">
                        <div className="flex">
                          <svg className="w-4 h-4 theme-error mt-0.5 mr-2" fill="currentColor" viewBox="0 0 20 20">
                            <path fillRule="evenodd" d="M18 10a8 8 0 11-16 0 8 8 0 0116 0zm-7 4a1 1 0 11-2 0 1 1 0 012 0zm-1-9a1 1 0 00-1 1v4a1 1 0 102 0V6a1 1 0 00-1-1z" clipRule="evenodd" />
                          </svg>
                          <div className="text-sm theme-text-primary">
                            <strong>Validation errors:</strong> {getValidationErrors(transaction).join(', ')}
                          </div>
                        </div>
                      </div>
                    )}

                    {/* Raw text for debugging */}
                    {transactions[index]?.raw_text && (
                      <div className="mt-4">
                        <details className="group">
                          <summary className="flex items-center justify-between cursor-pointer text-sm font-medium theme-text-tertiary hover:theme-text-primary theme-transition">
                            <span>Raw Text (for reference)</span>
                            <svg className="w-4 h-4 transform group-open:rotate-180 transition-transform" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" />
                            </svg>
                          </summary>
                          <div className="mt-2 p-3 theme-bg-secondary theme-border border rounded-lg">
                            <div className="text-xs theme-text-secondary font-mono whitespace-pre-wrap">
                              {transactions[index].raw_text}
                            </div>
                          </div>
                        </details>
                      </div>
                    )}
                </div>
              </div>
            </div>
          ))}
          </div>
        </div>

        {/* Footer */}
        <div className="flex flex-col sm:flex-row justify-between items-start sm:items-center p-4 sm:p-6 theme-border border-t theme-bg-secondary gap-4">
          <div className="flex items-center space-x-4">
            {validationResult.canProceed && validTransactions.length > 0 ? (
              <div className="flex items-center space-x-2">
                <div className="w-3 h-3 theme-success-bg rounded-full"></div>
                <span className="text-xs sm:text-sm font-medium theme-success">
                  <span className="hidden sm:inline">{t('pdfParserPage.reviewModal.footer.readyToCreate')} </span>{validTransactions.length} {t('common.type').toLowerCase()}{validTransactions.length !== 1 ? 's' : ''}
                </span>
              </div>
            ) : !validationResult.canProceed ? (
              <div className="flex items-center space-x-2">
                <div className="w-3 h-3 bg-yellow-500 rounded-full"></div>
                <span className="text-xs sm:text-sm font-medium text-yellow-600 dark:text-yellow-400">
                  {t('pdfParserPage.reviewModal.validation.validationPassed')}
                </span>
              </div>
            ) : (
              <div className="flex items-center space-x-2">
                <div className="w-3 h-3 theme-error-bg rounded-full"></div>
                <span className="text-xs sm:text-sm font-medium theme-error">{t('pdfParserPage.reviewModal.footer.noValidTransactions')}</span>
              </div>
            )}
          </div>

          <div className="flex flex-col sm:flex-row space-y-2 sm:space-y-0 sm:space-x-3 w-full sm:w-auto">
            <button
              onClick={onClose}
              className="px-4 sm:px-6 py-2 sm:py-3 theme-border border theme-text-primary rounded-lg hover:theme-surface-hover theme-transition font-medium text-sm sm:text-base"
            >
              Cancel
            </button>
            <button
              onClick={handleSubmit}
              disabled={!validationResult.canProceed || isSubmitting}
              className={`px-6 sm:px-8 py-2 sm:py-3 rounded-lg font-medium flex items-center justify-center space-x-2 theme-transition text-sm sm:text-base ${
                actualTheme === 'dark'
                  ? 'bg-gradient-to-r from-blue-600 to-blue-700 hover:from-blue-700 hover:to-blue-800 disabled:from-gray-600 disabled:to-gray-700'
                  : 'bg-gradient-to-r from-blue-600 to-blue-700 hover:from-blue-700 hover:to-blue-800 disabled:from-gray-300 disabled:to-gray-400'
              } text-white disabled:cursor-not-allowed theme-shadow hover:theme-shadow-hover disabled:shadow-none`}
            >
              {isSubmitting && (
                <svg className="animate-spin -ml-1 mr-2 h-4 w-4 sm:h-5 sm:w-5 text-white" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
                  <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
                  <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
                </svg>
              )}
              <span>
                {isSubmitting
                  ? t('pdfParserPage.reviewModal.footer.creating')
                  : !validationResult.canProceed
                    ? t('pdfParserPage.reviewModal.validation.failed')
                    : validTransactions.length === 0
                      ? t('pdfParserPage.reviewModal.footer.noValidTransactions')
                      : t('pdfParserPage.reviewModal.footer.createButton', {
                          count: validTransactions.length,
                          plural: validTransactions.length !== 1 ? 's' : ''
                        })
                }
              </span>
            </button>
          </div>
        </div>
      </div>

    </div>
  );
};
