import React, { useState, useEffect } from 'react';
import { useApiClients } from '@/hooks/useApiClients';
import { PdfUploader, TransactionReview } from '@/components/ui/pdf';
import { ParsedTransaction, TransactionValidation } from '@/services/api/pdfParserApiClient';
import { useTheme } from '@/contexts/ThemeContext';

export const PdfParser: React.FC = () => {
  const { income, expense, debt } = useApiClients();
  const { actualTheme } = useTheme();
  const [showUploader, setShowUploader] = useState(false);
  const [showReview, setShowReview] = useState(false);
  const [parsedTransactions, setParsedTransactions] = useState<ParsedTransaction[]>([]);
  const [isCreating, setIsCreating] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [success, setSuccess] = useState<string | null>(null);


  const handleTransactionsParsed = (transactions: ParsedTransaction[]) => {
    setParsedTransactions(transactions);
    setShowUploader(false);
    setShowReview(true);
  };

  const handleTransactionsValidated = async (validatedTransactions: TransactionValidation[]) => {
    try {
      setIsCreating(true);
      setError(null);
      setSuccess(null);

      console.log('PdfParser: handleTransactionsValidated called with', validatedTransactions.length, 'transactions');
      console.log('PdfParser: All transactions:', validatedTransactions);

      const validTransactions = validatedTransactions.filter(txn => txn.is_valid);
      
      console.log('PdfParser: Valid transactions:', validTransactions.length, validTransactions);
      
      if (validTransactions.length === 0) {
        setError('No valid transactions to create');
        return;
      }

      let incomeCount = 0;
      let expenseCount = 0;
      const errors: string[] = [];

      console.log('PdfParser: Starting to create', validTransactions.length, 'transactions');

      // Create transactions in parallel
      const createPromises = validTransactions.map(async (transaction, index) => {
        try {
          console.log(`PdfParser: Creating transaction ${index + 1}/${validTransactions.length}:`, transaction);
          
          if (transaction.transaction_type === 'income') {
            const incomeData = {
              amount: transaction.amount,
              description: transaction.description,
              date: transaction.transaction_date,
              ...(transaction.category_id && { category_id: transaction.category_id })
            };
            console.log('PdfParser: Creating income with data:', incomeData);
            const response = await income.createIncome(incomeData);
            console.log('PdfParser: Income creation response:', response);
            
            if ('error' in response) {
              console.error('PdfParser: Income creation failed:', response.error);
              errors.push(`Income creation failed: ${response.error}`);
            } else {
              console.log('PdfParser: Income created successfully');
              incomeCount++;
            }
          } else if (transaction.transaction_type === 'debt') {
            // For debt transactions, create a debt payment
            if (!transaction.category_id) {
              console.warn('PdfParser: Skipping debt transaction without category_id');
              errors.push(`Debt transaction requires a category: ${transaction.description}`);
            } else {
              // First, try to find an existing debt with this description or create a default debt
              // For now, we'll create a debt payment without a specific debt ID
              // This is a simplified approach - in a real app, you'd want to match or create debts
              console.log('PdfParser: Debt transactions not yet fully implemented - treating as expense');
              
              const expenseData = {
                amount: transaction.amount,
                description: `[DEBT] ${transaction.description}`,
                date: transaction.transaction_date,
                category_id: transaction.category_id
              };
              console.log('PdfParser: Creating debt expense with data:', expenseData);
              const response = await expense.createExpense(expenseData);
              console.log('PdfParser: Debt expense creation response:', response);
              
              if ('error' in response) {
                console.error('PdfParser: Debt expense creation failed:', response.error);
                errors.push(`Debt expense creation failed: ${response.error}`);
              } else {
                console.log('PdfParser: Debt expense created successfully');
                expenseCount++;
              }
            }
          } else {
            // Default to expense for any other transaction type
            const expenseData = {
              amount: transaction.amount,
              description: transaction.description,
              date: transaction.transaction_date,
              ...(transaction.category_id && { category_id: transaction.category_id })
            };
            console.log('PdfParser: Creating expense with data:', expenseData);
            const response = await expense.createExpense(expenseData);
            console.log('PdfParser: Expense creation response:', response);
            
            if ('error' in response) {
              console.error('PdfParser: Expense creation failed:', response.error);
              errors.push(`Expense creation failed: ${response.error}`);
            } else {
              console.log('PdfParser: Expense created successfully');
              expenseCount++;
            }
          }
        } catch (err) {
          console.error(`PdfParser: Failed to create ${transaction.transaction_type}:`, err);
          errors.push(`Failed to create ${transaction.transaction_type}: ${err}`);
        }
      });

      console.log('PdfParser: Waiting for all promises to complete...');
      await Promise.all(createPromises);

      console.log('PdfParser: All promises completed. Results:', {
        incomeCount,
        expenseCount,
        errors: errors.length
      });

      if (errors.length > 0) {
        console.error('PdfParser: Errors occurred:', errors);
        setError(`Some transactions failed to create: ${errors.join(', ')}`);
      }

      setSuccess(`Successfully created ${incomeCount} income and ${expenseCount} expense transactions`);
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
