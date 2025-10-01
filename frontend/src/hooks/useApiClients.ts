import { AccountApiClient } from '@/services/api/accountApiClient';
import { CategoryApiClient } from '@/services/api/categoryApiClient';
import { ContactApiClient } from '@/services/api/contactApiClient';
import { CurrencyApiClient } from '@/services/api/currencyApiClient';
import { DebtApiClient } from '@/services/api/debtApiClient';
import { ExpenseApiClient } from '@/services/api/expenseApiClient';
import { IncomeApiClient } from '@/services/api/incomeApiClient';
import { UserApiClient } from '@/services/api/userApiClient';
import { GoalsApiClient } from '@/services/api/goalsApi';
import { PDFParserApiClient } from '@/services/api/pdfParserApiClient';
import { useAuth } from '@/contexts/AuthContext';
import { useMemo } from 'react';

export const useApiClients = () => {
  const { token, refreshAccessToken } = useAuth();
  
  const getToken = () => token;
  
  const account = useMemo(() => new AccountApiClient(getToken, refreshAccessToken), [token, refreshAccessToken]);
  const category = useMemo(() => new CategoryApiClient(getToken, refreshAccessToken), [token, refreshAccessToken]);
  const contact = useMemo(() => new ContactApiClient(getToken, refreshAccessToken), [token, refreshAccessToken]);
  const currency = useMemo(() => new CurrencyApiClient(), []);
  const debt = useMemo(() => new DebtApiClient(getToken, refreshAccessToken), [token, refreshAccessToken]);
  const user = useMemo(() => new UserApiClient(getToken, refreshAccessToken), [token, refreshAccessToken]);
  const expense = useMemo(() => new ExpenseApiClient(getToken, refreshAccessToken), [token, refreshAccessToken]);
  const income = useMemo(() => new IncomeApiClient(getToken, refreshAccessToken), [token, refreshAccessToken]);
  const goals = useMemo(() => new GoalsApiClient(getToken, refreshAccessToken), [token, refreshAccessToken]);
  const pdfParser = useMemo(() => new PDFParserApiClient(getToken, refreshAccessToken), [token, refreshAccessToken]);
  
  return {
    account,
    category,
    contact,
    currency,
    debt,
    user,
    expense,
    income,
    goals,
    pdfParser
  };
}; 