import React, { useState } from 'react';
import { useApiClients } from '@/hooks/useApiClients';
import { PdfUploader, TransactionReview } from '@/components/ui/pdf';
import { ParsedTransaction, TransactionValidation } from '@/services/api/pdfParserApiClient';
import { useTheme } from '@/contexts/ThemeContext';
import i18n from '@/i18n';
import { MccBatchResponse } from '@/services/api/categoryApiClient';

export const PdfParser: React.FC = () => {
  const { income, expense, category } = useApiClients();
  const { actualTheme } = useTheme();
  const [showUploader, setShowUploader] = useState(false);
  const [showReview, setShowReview] = useState(false);
  const [parsedTransactions, setParsedTransactions] = useState<ParsedTransaction[]>([]);
  const [isCreating, setIsCreating] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [success, setSuccess] = useState<string | null>(null);
  
  // MCC processing states
  const [mccProcessingStatus, setMccProcessingStatus] = useState<string>('');
  const [mccProcessingProgress, setMccProcessingProgress] = useState<{
    total: number;
    processed: number;
    successful: number;
    failed: number;
  }>({ total: 0, processed: 0, successful: 0, failed: 0 });
  const [failedMccCodes, setFailedMccCodes] = useState<Array<{
    mcc_code: number;
    error: string;
    category_name?: string;
  }>>([]);

  // Translate error codes to user-friendly messages
  const translateErrorCode = (errorCode: string): string => {
    const errorTranslations: Record<string, string> = {
      'CATEGORY_LIMIT_EXCEEDED': 'Category limit exceeded. Please upgrade your plan or delete some existing categories.',
      'CATEGORY_ALREADY_EXISTS': 'Category already exists for this MCC code.',
      'MCC_CODE_NOT_FOUND': 'MCC code not found in the system.',
      'VALIDATION_ERROR': 'Invalid category data provided.',
      'SUBSCRIPTION_ERROR': 'Subscription service error. Please try again later.',
      'DATABASE_ERROR': 'Database error. Please try again later.',
      'UNAUTHORIZED': 'You are not authorized to perform this action.',
      'FORBIDDEN': 'Access denied. Please check your permissions.',
      'NOT_FOUND': 'Requested resource not found.',
      'INTERNAL_ERROR': 'Internal server error. Please try again later.'
    };
    
    return errorTranslations[errorCode] || 'An unexpected error occurred. Please try again.';
  };

  // Extract user-friendly error message from API response
  const getUserFriendlyError = (error: string): string => {
    try {
      // Try to parse as JSON to extract errorCode
      const errorObj = JSON.parse(error);
      if (errorObj.errorCode) {
        return translateErrorCode(errorObj.errorCode);
      }
      return errorObj.error || error;
    } catch {
      // If not JSON, check if it contains error codes
      if (error.includes('CATEGORY_LIMIT_EXCEEDED')) {
        return translateErrorCode('CATEGORY_LIMIT_EXCEEDED');
      }
      if (error.includes('CATEGORY_ALREADY_EXISTS')) {
        return translateErrorCode('CATEGORY_ALREADY_EXISTS');
      }
      if (error.includes('MCC_CODE_NOT_FOUND')) {
        return translateErrorCode('MCC_CODE_NOT_FOUND');
      }
      return error;
    }
  };


  const handleTransactionsParsed = (transactions: ParsedTransaction[]) => {
    setParsedTransactions(transactions);
    setShowUploader(false);
    setShowReview(true);
  };

  const retryFailedMccCodes = async () => {
    if (failedMccCodes.length === 0) return;
    
    try {
      setIsCreating(true);
      setMccProcessingStatus('Retrying failed MCC category creations...');
      
      const retryCategories = failedMccCodes.map(failed => ({
        mcc_code: failed.mcc_code,
        type: 'EXPENSE' as const // Default to expense, could be improved
      }));
      
      const batchResponse = await category.createCategoriesFromMccBatch(retryCategories, i18n.language);
      
      if ('error' in batchResponse) {
        setMccProcessingStatus(`Retry failed: ${batchResponse.error}`);
        return;
      }
      
      const response = batchResponse as MccBatchResponse;
      const newFailedCodes: Array<{mcc_code: number; error: string; category_name?: string}> = [];
      const mccCodeToCategoryId = new Map<number, number>();
      
      response.results.forEach((result) => {
        if (result.success && result.category_id && result.error === null) {
          mccCodeToCategoryId.set(result.mcc_code, result.category_id);
        } else {
          newFailedCodes.push({
            mcc_code: result.mcc_code,
            error: getUserFriendlyError(result.error || 'Unknown error'),
            ...(result.category_name && { category_name: result.category_name })
          });
        }
      });
      
      setFailedMccCodes(newFailedCodes);
      
      // Show detailed error information
      if (response.failed > 0) {
        const errorDetails = response.results
          .filter(result => !result.success)
          .map(result => `MCC ${result.mcc_code}: ${getUserFriendlyError(result.error || 'Unknown error')}`)
          .join(', ');
        setMccProcessingStatus(`Retry failed - Errors: ${errorDetails}`);
      } else {
        setMccProcessingStatus(`Retry completed: ${response.successful} successful, ${response.failed} still failed`);
      }
      
    } catch (err) {
      console.error('Error retrying MCC codes:', err);
      setMccProcessingStatus(`Retry error: ${err}`);
    } finally {
      setIsCreating(false);
    }
  };

  const handleTransactionsValidated = async (validatedTransactions: TransactionValidation[]) => {
    try {
      setIsCreating(true);
      setError(null);
      setSuccess(null);

      const validTransactions = validatedTransactions.filter(txn => txn.is_valid);
      
      if (validTransactions.length === 0) {
        setError('No valid transactions to create');
        return;
      }

      // Get current language
      const currentLanguage = i18n.language || 'ru';

      let incomeCount = 0;
      let expenseCount = 0;
      let debtCount = 0;
      const errors: string[] = [];

      // Count transaction types first
      validTransactions.forEach(transaction => {
        if (transaction.transaction_type === 'income') {
          incomeCount++;
        } else if (transaction.transaction_type === 'expense' && transaction.description?.toLowerCase().includes('debt')) {
          debtCount++;
        } else {
          expenseCount++;
        }
      });

      // Step 1: Collect unique MCC codes that need categories created
      const mccCodeToCategoryId = new Map<number, number>();
      const uniqueMccCodes = new Set<number>();

      // Process transactions to identify which MCC categories need to be created
      const transactionsWithCategories = validTransactions.map((transaction, index) => {
        const originalTransaction = parsedTransactions[index];
        let categoryId = transaction.category_id;

        // If user didn't select a category, check if we need to create one from MCC
        if (!categoryId && originalTransaction) {
          if (originalTransaction.mcc_code && originalTransaction.mcc_category_name) {
            // Add unique MCC code to our set
            uniqueMccCodes.add(originalTransaction.mcc_code);
          } else {
            // No MCC data available, force user to select category
            errors.push(`Transaction "${transaction.description}" requires a category selection (no MCC data available)`);
            return null; // Skip this transaction
          }
        }

        return {
          transaction,
          originalTransaction,
          categoryId
        };
      }).filter((item): item is { transaction: TransactionValidation; originalTransaction: ParsedTransaction | undefined; categoryId: number | undefined } => item !== null);

      // Create batch request with unique MCC codes
      const mccCategoriesToCreate: Array<{
        mcc_code: number;
        custom_name?: string;
        parent_id?: number;
        type?: 'EXPENSE' | 'INCOME';
      }> = [];

      // For each unique MCC code, determine the most appropriate type
      uniqueMccCodes.forEach(mccCode => {
        // Find the first transaction with this MCC code to determine type
        const transactionWithMcc = transactionsWithCategories.find(({ originalTransaction }) => 
          originalTransaction?.mcc_code === mccCode
        );
        
        if (transactionWithMcc) {
          mccCategoriesToCreate.push({
            mcc_code: mccCode,
            type: transactionWithMcc.transaction.transaction_type === 'income' ? 'INCOME' : 'EXPENSE'
          });
        }
      });

      // Step 2: Create categories from MCC codes in batch
      if (mccCategoriesToCreate.length > 0) {
        try {
          // Set up progress tracking
          setMccProcessingStatus(`Creating ${mccCategoriesToCreate.length} categories from MCC codes...`);
          setMccProcessingProgress({
            total: mccCategoriesToCreate.length,
            processed: 0,
            successful: 0,
            failed: 0
          });
          setFailedMccCodes([]);
          
          console.log(`Creating ${mccCategoriesToCreate.length} unique categories from MCC codes in batch:`, mccCategoriesToCreate.map(c => c.mcc_code));
          const batchResponse = await category.createCategoriesFromMccBatch(mccCategoriesToCreate, currentLanguage);
          
          if ('error' in batchResponse) {
            console.error('Failed to create categories from MCC batch:', batchResponse.error);
            setMccProcessingStatus(`Failed to create categories: ${batchResponse.error}`);
            errors.push(`Failed to create categories from MCC batch: ${batchResponse.error}`);
            return;
          } else {
            const response = batchResponse as MccBatchResponse;
            
            // Process results and update progress
            const failedMccCodes: Array<{mcc_code: number; error: string; category_name?: string}> = [];
            const successfulMccCodes: number[] = [];
            
            response.results.forEach((result) => {
              if (result.success && result.category_id && result.error === null) {
                mccCodeToCategoryId.set(result.mcc_code, result.category_id);
                successfulMccCodes.push(result.mcc_code);
                console.log(`✅ Mapped MCC ${result.mcc_code} to category ID ${result.category_id} (${result.category_name})`);
              } else {
                failedMccCodes.push({
                  mcc_code: result.mcc_code,
                  error: getUserFriendlyError(result.error || 'Unknown error'),
                  ...(result.category_name && { category_name: result.category_name })
                });
                console.error(`❌ Failed to create category for MCC ${result.mcc_code}: ${result.error}`);
              }
            });
            
            // Update progress state
            setMccProcessingProgress({
              total: response.total_requested,
              processed: response.total_requested,
              successful: response.successful,
              failed: response.failed
            });
            setFailedMccCodes(failedMccCodes);
            
            console.log(`Batch result: ${response.successful} successful, ${response.failed} failed out of ${response.total_requested} requested`);
            
            // If all MCC codes failed, we should stop processing
            if (response.failed === response.total_requested) {
              console.error('All MCC category creations failed. Cannot proceed with transaction creation.');
              setMccProcessingStatus('All MCC category creations failed. Please select categories manually.');
              errors.push('All MCC category creations failed. Please select categories manually for transactions.');
              return;
            }
            
            // Update status based on results
            if (response.failed > 0) {
              setMccProcessingStatus(`${response.successful} categories created successfully, ${response.failed} failed. Continuing with successful ones.`);
              console.warn(`${response.failed} MCC codes failed to create categories. Continuing with ${response.successful} successful ones.`);
            } else {
              setMccProcessingStatus(`Successfully created ${response.successful} categories from MCC codes!`);
            }
          }
        } catch (err) {
          console.error('Error creating categories from MCC batch:', err);
          setMccProcessingStatus(`Error creating categories: ${err}`);
          errors.push(`Error creating categories from MCC batch: ${err}`);
          return;
        }
      }

      // Step 3: Create transactions with proper category IDs
      console.log(`Creating ${transactionsWithCategories.length} transactions with categories from batch creation`);
      let successfulIncomeCount = 0;
      let successfulExpenseCount = 0;
      let successfulDebtCount = 0;

      const createPromises = transactionsWithCategories.map(async ({ transaction, originalTransaction, categoryId }) => {
        try {
          // If we don't have a category ID yet, get it from our MCC mapping
          if (!categoryId && originalTransaction?.mcc_code) {
            categoryId = mccCodeToCategoryId.get(originalTransaction.mcc_code);
            if (categoryId) {
              console.log(`Using created category ID ${categoryId} for MCC ${originalTransaction.mcc_code} in transaction: ${transaction.description}`);
            } else {
              console.error(`No category ID found for MCC ${originalTransaction.mcc_code}. Skipping transaction: ${transaction.description}`);
              errors.push(`Transaction "${transaction.description}" requires a category selection (MCC ${originalTransaction.mcc_code} category creation failed)`);
              return; // Skip this transaction
            }
          }

          // Create the transaction with the category
          if (transaction.transaction_type === 'income') {
            const incomeData = {
              amount: transaction.amount,
              description: transaction.description,
              date: transaction.transaction_date,
              ...(categoryId && { category_id: categoryId })
            };
            const response = await income.createIncome(incomeData);
            
            if ('error' in response) {
              console.error('PdfParser: Income creation failed:', response.error);
              errors.push(`Income creation failed: ${response.error}`);
            } else {
              successfulIncomeCount++;
            }
          } else if (transaction.transaction_type === 'expense' && transaction.description?.toLowerCase().includes('debt')) {
            // For debt transactions, create a debt payment
            if (!categoryId) {
              console.warn('PdfParser: Skipping debt transaction without category_id');
              errors.push(`Debt transaction requires a category: ${transaction.description}`);
            } else {
              const expenseData = {
                amount: transaction.amount,
                description: `[DEBT] ${transaction.description}`,
                date: transaction.transaction_date,
                category_id: categoryId
              };
              const response = await expense.createExpense(expenseData);
              
              if ('error' in response) {
                console.error('PdfParser: Debt expense creation failed:', response.error);
                errors.push(`Debt expense creation failed: ${response.error}`);
              } else {
                successfulDebtCount++;
              }
            }
          } else {
            // Default to expense for any other transaction type
            const expenseData = {
              amount: transaction.amount,
              description: transaction.description,
              date: transaction.transaction_date,
              ...(categoryId && { category_id: categoryId })
            };
            const response = await expense.createExpense(expenseData);
            
            if ('error' in response) {
              console.error('PdfParser: Expense creation failed:', response.error);
              errors.push(`Expense creation failed: ${response.error}`);
            } else {
              successfulExpenseCount++;
            }
          }
        } catch (err) {
          console.error(`PdfParser: Failed to create ${transaction.transaction_type}:`, err);
          errors.push(`Failed to create ${transaction.transaction_type}: ${err}`);
        }
      });

      await Promise.all(createPromises);

      if (errors.length > 0) {
        console.error('PdfParser: Errors occurred:', errors);
        setError(`Some transactions failed to create: ${errors.join(', ')}`);
      }

      const totalSuccessful = successfulIncomeCount + successfulExpenseCount + successfulDebtCount;
      const totalAttempted = incomeCount + expenseCount + debtCount;
      
      let successMessage = `Successfully created ${totalSuccessful} out of ${totalAttempted} transactions: `;
      const parts = [];
      if (successfulIncomeCount > 0) parts.push(`${successfulIncomeCount} income`);
      if (successfulExpenseCount > 0) parts.push(`${successfulExpenseCount} expense`);
      if (successfulDebtCount > 0) parts.push(`${successfulDebtCount} debt`);
      successMessage += parts.join(', ');
      
      setSuccess(successMessage);
      setShowReview(false);
      setParsedTransactions([]);

    } catch (err) {
      console.error('PdfParser: Error in handleTransactionsValidated:', err);
      setError('Failed to create transactions');
    } finally {
      setIsCreating(false);
    }
  };

  const handleClose = () => {
    setShowUploader(false);
    setShowReview(false);
    setParsedTransactions([]);
    setError(null);
    setSuccess(null);
  };

  const handleUploaderClose = () => {
    setShowUploader(false);
    setError(null);
    setSuccess(null);
    // Don't reset parsedTransactions or showReview here
  };

  return (
    <div className="container mx-auto px-4 py-8">
      <div className="max-w-4xl mx-auto">
        <div className="mb-8">
          <h1 className="text-3xl font-bold theme-text-primary mb-4">PDF Parser</h1>
          <p className="theme-text-secondary">
            Upload bank PDF statements to automatically extract and import transactions.
          </p>
        </div>

        {error && (
          <div className="mb-6 p-4 theme-error-light theme-border border theme-error-bg rounded-lg">
            <div className="flex">
              <div className="flex-shrink-0">
                <svg className="h-5 w-5 theme-error" viewBox="0 0 20 20" fill="currentColor">
                  <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zM8.707 7.293a1 1 0 00-1.414 1.414L8.586 10l-1.293 1.293a1 1 0 101.414 1.414L10 11.414l1.293 1.293a1 1 0 001.414-1.414L11.414 10l1.293-1.293a1 1 0 00-1.414-1.414L10 8.586 8.707 7.293z" clipRule="evenodd" />
                </svg>
              </div>
              <div className="ml-3">
                <p className="text-sm theme-text-primary">{error}</p>
              </div>
            </div>
          </div>
        )}

        {success && (
          <div className="mb-6 p-4 theme-success-light theme-border border theme-success-bg rounded-lg">
            <div className="flex">
              <div className="flex-shrink-0">
                <svg className="h-5 w-5 theme-success" viewBox="0 0 20 20" fill="currentColor">
                  <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-9.293a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z" clipRule="evenodd" />
                </svg>
              </div>
              <div className="ml-3">
                <p className="text-sm theme-text-primary">{success}</p>
              </div>
            </div>
          </div>
        )}

        {/* MCC Processing Status */}
        {mccProcessingStatus && (
          <div className="mb-6 p-4 theme-info-light theme-border border theme-info-bg rounded-lg">
            <div className="flex items-center justify-between">
              <div className="flex items-center">
                <div className="flex-shrink-0">
                  {isCreating ? (
                    <svg className="animate-spin h-5 w-5 theme-info" viewBox="0 0 24 24">
                      <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" fill="none" />
                      <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z" />
                    </svg>
                  ) : (
                    <svg className="h-5 w-5 theme-info" viewBox="0 0 20 20" fill="currentColor">
                      <path fillRule="evenodd" d="M18 10a8 8 0 11-16 0 8 8 0 0116 0zm-7-4a1 1 0 11-2 0 1 1 0 012 0zM9 9a1 1 0 000 2v3a1 1 0 001 1h1a1 1 0 100-2v-3a1 1 0 00-1-1H9z" clipRule="evenodd" />
                    </svg>
                  )}
                </div>
                <div className="ml-3">
                  <p className="text-sm theme-text-primary font-medium">{mccProcessingStatus}</p>
                  {mccProcessingProgress.total > 0 && (
                    <div className="mt-2">
                      <div className="flex justify-between text-xs theme-text-secondary mb-1">
                        <span>Progress: {mccProcessingProgress.processed}/{mccProcessingProgress.total}</span>
                        <span>{mccProcessingProgress.successful} successful, {mccProcessingProgress.failed} failed</span>
                      </div>
                      <div className="w-full bg-gray-200 rounded-full h-2">
                        <div 
                          className="bg-blue-600 h-2 rounded-full transition-all duration-300" 
                          style={{ width: `${(mccProcessingProgress.processed / mccProcessingProgress.total) * 100}%` }}
                        ></div>
                      </div>
                    </div>
                  )}
                </div>
              </div>
              {failedMccCodes.length > 0 && !isCreating && (
                <button
                  onClick={retryFailedMccCodes}
                  className="px-3 py-1 text-xs theme-button-primary rounded-md hover:opacity-80 transition-opacity"
                >
                  Retry Failed ({failedMccCodes.length})
                </button>
              )}
            </div>
            
            {/* Failed MCC Codes Details */}
            {failedMccCodes.length > 0 && (
              <div className="mt-3 pt-3 border-t theme-border">
                <p className="text-xs theme-text-secondary mb-2">Failed MCC codes:</p>
                <div className="space-y-1">
                  {failedMccCodes.map((failed, index) => (
                    <div key={index} className="flex items-center justify-between text-xs">
                      <span className="theme-text-primary">
                        MCC {failed.mcc_code} {failed.category_name && `(${failed.category_name})`}
                      </span>
                      <span className="theme-error">{failed.error}</span>
                    </div>
                  ))}
                </div>
              </div>
            )}
          </div>
        )}

        <div className="theme-surface rounded-lg theme-shadow p-6">
          <div className="text-center">
            <div className="mb-4">
              <svg
                className="mx-auto h-12 w-12 theme-text-tertiary"
                fill="none"
                viewBox="0 0 24 24"
                stroke="currentColor"
              >
                <path
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  strokeWidth={2}
                  d="M7 21h10a2 2 0 002-2V9.414a1 1 0 00-.293-.707l-5.414-5.414A1 1 0 0012.586 3H7a2 2 0 00-2 2v14a2 2 0 002 2z"
                />
              </svg>
            </div>
            <h3 className="text-lg font-medium theme-text-primary mb-2">
              Upload Bank PDF
            </h3>
            <p className="theme-text-secondary mb-6">
              Upload a PDF statement from your bank to automatically extract transactions.
              Currently supported: Monobank (Ukrainian and English).
            </p>
            <button
              onClick={() => setShowUploader(true)}
              disabled={isCreating}
              className={`px-6 py-3 rounded-lg font-medium transition-colors ${
                actualTheme === 'dark'
                  ? 'bg-gradient-to-r from-blue-600 to-blue-700 hover:from-blue-700 hover:to-blue-800 disabled:from-gray-600 disabled:to-gray-700'
                  : 'bg-gradient-to-r from-blue-600 to-blue-700 hover:from-blue-700 hover:to-blue-800 disabled:from-gray-300 disabled:to-gray-400'
              } text-white disabled:cursor-not-allowed theme-shadow hover:theme-shadow-hover disabled:shadow-none`}
            >
              {isCreating ? 'Creating Transactions...' : 'Upload PDF'}
            </button>
          </div>
        </div>

        <div className="mt-8 grid grid-cols-1 md:grid-cols-3 gap-6">
          <div className="theme-surface rounded-lg theme-shadow p-6">
            <h3 className="text-lg font-semibold theme-text-primary mb-2">Step 1</h3>
            <p className="theme-text-secondary">Upload your bank PDF statement</p>
          </div>
          <div className="theme-surface rounded-lg theme-shadow p-6">
            <h3 className="text-lg font-semibold theme-text-primary mb-2">Step 2</h3>
            <p className="theme-text-secondary">Review and edit parsed transactions</p>
          </div>
          <div className="theme-surface rounded-lg theme-shadow p-6">
            <h3 className="text-lg font-semibold theme-text-primary mb-2">Step 3</h3>
            <p className="theme-text-secondary">Create income and expense records</p>
          </div>
        </div>
      </div>


      {showUploader && (
        <PdfUploader
          onTransactionsParsed={handleTransactionsParsed}
          onClose={handleUploaderClose}
        />
      )}

      {showReview && (
        <TransactionReview
          transactions={parsedTransactions}
          onTransactionsValidated={handleTransactionsValidated}
          onClose={handleClose}
        />
      )}
    </div>
  );
};
