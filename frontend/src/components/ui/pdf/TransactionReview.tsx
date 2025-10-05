import React, { useState, useEffect } from 'react';
import { useApiClients } from '@/hooks/useApiClients';
import { ParsedTransaction, TransactionValidation } from '@/services/api/pdfParserApiClient';
import { Category } from '@/types';
import { useTheme } from '@/contexts/ThemeContext';

interface TransactionReviewProps {
  transactions: ParsedTransaction[];
  onTransactionsValidated: (validatedTransactions: TransactionValidation[]) => void;
  onClose: () => void;
}

export const TransactionReview: React.FC<TransactionReviewProps> = ({
  transactions,
  onTransactionsValidated,
  onClose
}) => {
  const { category } = useApiClients();
  const { actualTheme } = useTheme();
  const [categories, setCategories] = useState<Category[]>([]);
  const [validatedTransactions, setValidatedTransactions] = useState<TransactionValidation[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    loadCategories();
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

  const initializeValidatedTransactions = () => {
    const initial = transactions.map((transaction, index) => ({
      transaction_id: `txn_${index}`,
      amount: transaction.amount,
      description: transaction.description,
      transaction_date: transaction.transaction_date,
      transaction_type: transaction.transaction_type,
      is_valid: true
    }));
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

  const [isSubmitting, setIsSubmitting] = useState(false);
  const [deleteConfirmIndex, setDeleteConfirmIndex] = useState<number | null>(null);
  const [showBulkDeleteConfirm, setShowBulkDeleteConfirm] = useState(false);

  const handleSubmit = async () => {
    
    // Validate required fields
    const invalidTransactions = validatedTransactions.filter(txn => 
      txn.is_valid && (!txn.amount || !txn.transaction_date || !txn.description)
    );


    if (invalidTransactions.length > 0) {
      setError(`Please fill in all required fields for ${invalidTransactions.length} transaction(s)`);
      return;
    }

    // Validate that all valid transactions have categories
    const validTransactions = validatedTransactions.filter(txn => txn.is_valid);
    const transactionsWithoutCategory = validTransactions.filter(txn => !txn.category_id);


    if (transactionsWithoutCategory.length > 0) {
      setError(`Please select a category for ${transactionsWithoutCategory.length} transaction(s)`);
      return;
    }

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
      if (!transaction.category_id) errors.push('Category is required');
    }
    return errors;
  };

  const validTransactions = validatedTransactions.filter(txn => txn.is_valid);
  const invalidTransactions = validatedTransactions.filter(txn => !txn.is_valid);

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

        {/* Statistics and Controls */}
        <div className="p-4 sm:p-6 theme-bg-secondary theme-border border-b">
          <div className="flex flex-col lg:flex-row lg:items-center lg:justify-between gap-4">
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
            </div>

            {/* Bulk Actions */}
            <div className="flex flex-wrap gap-1.5 sm:gap-2">
              <button
                onClick={() => setValidatedTransactions(prev =>
                  prev.map(txn => ({ ...txn, is_valid: true }))
                )}
                className="inline-flex items-center px-2 sm:px-3 py-1 sm:py-1.5 text-xs font-medium theme-success theme-success-light rounded-md hover:theme-surface-hover theme-transition"
              >
                <svg className="w-3 h-3 mr-1" fill="currentColor" viewBox="0 0 20 20">
                  <path fillRule="evenodd" d="M16.707 5.293a1 1 0 010 1.414l-8 8a1 1 0 01-1.414 0l-4-4a1 1 0 011.414-1.414L8 12.586l7.293-7.293a1 1 0 011.414 0z" clipRule="evenodd" />
                </svg>
                <span className="hidden sm:inline">Mark All Valid</span>
                <span className="sm:hidden">All Valid</span>
              </button>
              <button
                onClick={() => setValidatedTransactions(prev =>
                  prev.map(txn => ({ ...txn, is_valid: false }))
                )}
                className="inline-flex items-center px-2 sm:px-3 py-1 sm:py-1.5 text-xs font-medium theme-error theme-error-light rounded-md hover:theme-surface-hover theme-transition"
              >
                <svg className="w-3 h-3 mr-1" fill="currentColor" viewBox="0 0 20 20">
                  <path fillRule="evenodd" d="M4.293 4.293a1 1 0 011.414 0L10 8.586l4.293-4.293a1 1 0 111.414 1.414L11.414 10l4.293 4.293a1 1 0 01-1.414 1.414L10 11.414l-4.293 4.293a1 1 0 01-1.414-1.414L8.586 10 4.293 5.707a1 1 0 010-1.414z" clipRule="evenodd" />
                </svg>
                <span className="hidden sm:inline">Mark All Invalid</span>
                <span className="sm:hidden">All Invalid</span>
              </button>
            </div>
          </div>
          
          {/* Quick Actions */}
          <div className="mt-4 flex flex-wrap gap-1.5 sm:gap-2">
            <button
              onClick={() => setValidatedTransactions(prev =>
                prev.map(txn => ({ ...txn, transaction_type: 'expense' }))
              )}
              className="inline-flex items-center px-2 sm:px-3 py-1 sm:py-1.5 text-xs font-medium theme-warning theme-warning-light rounded-md hover:theme-surface-hover theme-transition"
            >
              <svg className="w-3 h-3 mr-1" fill="currentColor" viewBox="0 0 20 20">
                <path fillRule="evenodd" d="M3 3a1 1 0 000 2v8a2 2 0 002 2h2.586l-1.293 1.293a1 1 0 101.414 1.414L10 15.414l2.293 2.293a1 1 0 001.414-1.414L12.414 15H15a2 2 0 002-2V5a1 1 0 100-2H3zm11.707 4.707a1 1 0 00-1.414-1.414L10 9.586 8.707 8.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z" clipRule="evenodd" />
              </svg>
              <span className="hidden sm:inline">Set All as Expenses</span>
              <span className="sm:hidden">All Expenses</span>
            </button>
            <button
              onClick={() => setValidatedTransactions(prev =>
                prev.map(txn => ({ ...txn, transaction_type: 'income' }))
              )}
              className="inline-flex items-center px-2 sm:px-3 py-1 sm:py-1.5 text-xs font-medium theme-accent theme-accent-light rounded-md hover:theme-surface-hover theme-transition"
            >
              <svg className="w-3 h-3 mr-1" fill="currentColor" viewBox="0 0 20 20">
                <path fillRule="evenodd" d="M3 3a1 1 0 000 2v8a2 2 0 002 2h2.586l-1.293 1.293a1 1 0 101.414 1.414L10 15.414l2.293 2.293a1 1 0 001.414-1.414L12.414 15H15a2 2 0 002-2V5a1 1 0 100-2H3zm11.707 4.707a1 1 0 00-1.414-1.414L10 9.586 8.707 8.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z" clipRule="evenodd" />
              </svg>
              <span className="hidden sm:inline">Set All as Income</span>
              <span className="sm:hidden">All Income</span>
            </button>
            <button
              onClick={() => setValidatedTransactions(prev =>
                prev.map(txn => {
                  const { category_id, ...rest } = txn;
                  return rest;
                })
              )}
              className="inline-flex items-center px-2 sm:px-3 py-1 sm:py-1.5 text-xs font-medium theme-text-secondary theme-bg-tertiary rounded-md hover:theme-surface-hover theme-transition"
            >
              <svg className="w-3 h-3 mr-1" fill="currentColor" viewBox="0 0 20 20">
                <path fillRule="evenodd" d="M4.293 4.293a1 1 0 011.414 0L10 8.586l4.293-4.293a1 1 0 111.414 1.414L11.414 10l4.293 4.293a1 1 0 01-1.414 1.414L10 11.414l-4.293 4.293a1 1 0 01-1.414-1.414L8.586 10 4.293 5.707a1 1 0 010-1.414z" clipRule="evenodd" />
              </svg>
              <span className="hidden sm:inline">Clear All Categories</span>
              <span className="sm:hidden">Clear Categories</span>
            </button>
            <button
              onClick={() => setShowBulkDeleteConfirm(true)}
              className="inline-flex items-center px-2 sm:px-3 py-1 sm:py-1.5 text-xs font-medium theme-error theme-error-light rounded-md hover:theme-surface-hover theme-transition"
            >
              <svg className="w-3 h-3 mr-1" fill="currentColor" viewBox="0 0 20 20">
                <path fillRule="evenodd" d="M9 2a1 1 0 000 2h2a1 1 0 100-2H9z" clipRule="evenodd" />
                <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zM8.707 7.293a1 1 0 00-1.414 1.414L8.586 10l-1.293 1.293a1 1 0 101.414 1.414L10 11.414l1.293 1.293a1 1 0 001.414-1.414L11.414 10l1.293-1.293a1 1 0 00-1.414-1.414L10 8.586 8.707 7.293z" clipRule="evenodd" />
              </svg>
              <span className="hidden sm:inline">Delete All Valid</span>
              <span className="sm:hidden">Delete Valid</span>
            </button>
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
                    ? !transaction.category_id
                      ? actualTheme === 'dark'
                        ? 'theme-warning-light border-yellow-600'
                        : 'theme-warning-light border-yellow-200'
                      : actualTheme === 'dark'
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
                        
                        {/* Category warning */}
                        {transaction.is_valid && !transaction.category_id && (
                          <div className="flex items-center space-x-1 text-xs sm:text-sm theme-warning">
                            <svg className="w-3 h-3 sm:w-4 sm:h-4" fill="currentColor" viewBox="0 0 20 20">
                              <path fillRule="evenodd" d="M8.257 3.099c.765-1.36 2.722-1.36 3.486 0l5.58 9.92c.75 1.334-.213 2.98-1.742 2.98H4.42c-1.53 0-2.493-1.646-1.743-2.98l5.58-9.92zM11 13a1 1 0 11-2 0 1 1 0 012 0zm-1-8a1 1 0 00-1 1v3a1 1 0 002 0V6a1 1 0 00-1-1z" clipRule="evenodd" />
                            </svg>
                            <span className="hidden sm:inline">Category required</span>
                            <span className="sm:hidden">Category</span>
                          </div>
                        )}
                        
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
                              {cat.name}
                            </option>
                          ))}
                        </select>
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
            {validTransactions.length > 0 ? (
              <div className="flex items-center space-x-2">
                <div className="w-3 h-3 theme-success-bg rounded-full"></div>
                <span className="text-xs sm:text-sm font-medium theme-success">
                  <span className="hidden sm:inline">Ready to create </span>{validTransactions.length} transaction{validTransactions.length !== 1 ? 's' : ''}
                </span>
              </div>
            ) : (
              <div className="flex items-center space-x-2">
                <div className="w-3 h-3 theme-error-bg rounded-full"></div>
                <span className="text-xs sm:text-sm font-medium theme-error">No valid transactions to create</span>
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
              disabled={validTransactions.length === 0 || isSubmitting}
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
                  ? 'Creating...'
                  : validTransactions.length === 0
                    ? 'No Valid Transactions' 
                    : `Create ${validTransactions.length} Transaction${validTransactions.length !== 1 ? 's' : ''}`
                }
              </span>
            </button>
          </div>
        </div>
      </div>

      {/* Bulk Delete Confirmation Modal */}
      {showBulkDeleteConfirm && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-60 p-4">
          <div className="theme-surface rounded-xl theme-shadow-hover p-4 sm:p-6 max-w-md w-full mx-auto">
            <div className="flex items-start space-x-3 mb-4">
              <div className="flex-shrink-0">
                <svg className="w-6 h-6 sm:w-8 sm:h-8 theme-error" fill="currentColor" viewBox="0 0 20 20">
                  <path fillRule="evenodd" d="M8.257 3.099c.765-1.36 2.722-1.36 3.486 0l5.58 9.92c.75 1.334-.213 2.98-1.742 2.98H4.42c-1.53 0-2.493-1.646-1.743-2.98l5.58-9.92zM11 13a1 1 0 11-2 0 1 1 0 012 0zm-1-8a1 1 0 00-1 1v3a1 1 0 002 0V6a1 1 0 00-1-1z" clipRule="evenodd" />
                </svg>
              </div>
              <div className="flex-1 min-w-0">
                <h3 className="text-base sm:text-lg font-semibold theme-text-primary">Delete All Valid Transactions</h3>
                <p className="text-xs sm:text-sm theme-text-secondary mt-1">
                  This will permanently delete {validTransactions.length} valid transaction{validTransactions.length !== 1 ? 's' : ''}. This action cannot be undone.
                </p>
              </div>
            </div>
            
            <div className="flex flex-col sm:flex-row justify-end space-y-2 sm:space-y-0 sm:space-x-3">
              <button
                onClick={() => setShowBulkDeleteConfirm(false)}
                className="px-4 py-2 theme-border border theme-text-primary rounded-lg hover:theme-surface-hover theme-transition font-medium text-sm sm:text-base"
              >
                Cancel
              </button>
              <button
                onClick={() => {
                  setValidatedTransactions(prev => prev.filter(txn => !txn.is_valid));
                  setShowBulkDeleteConfirm(false);
                }}
                className="px-4 py-2 theme-error theme-error-light rounded-lg hover:theme-surface-hover theme-transition font-medium text-sm sm:text-base"
              >
                Delete All
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};
