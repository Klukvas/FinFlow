import { CategoryApiClient } from '@/services/api/categoryApiClient';
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
  
  const category = useMemo(() => new CategoryApiClient(getToken, refreshAccessToken), [token, refreshAccessToken]);
  const user = useMemo(() => new UserApiClient(getToken, refreshAccessToken), [token, refreshAccessToken]);
  const expense = useMemo(() => new ExpenseApiClient(getToken, refreshAccessToken), [token, refreshAccessToken]);
  const income = useMemo(() => new IncomeApiClient(getToken, refreshAccessToken), [token, refreshAccessToken]);
  const goals = useMemo(() => new GoalsApiClient(getToken, refreshAccessToken), [token, refreshAccessToken]);
  const pdfParser = useMemo(() => new PDFParserApiClient(getToken, refreshAccessToken), [token, refreshAccessToken]);
  
  return {
    category,
    user,
    expense,
    income,
    goals,
    pdfParser
  };
}; 