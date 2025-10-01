import { AuthHttpClient, ApiError } from './AuthHttpClient';
import { config } from '@/config/env';
import { 
  DebtCreate, 
  DebtUpdate, 
  DebtResponse, 
  DebtSummary,
  DebtPaymentCreate,
  DebtPaymentResponse
} from '@/types/debt';

export class DebtApiClient {
  private httpClient: AuthHttpClient;

  constructor(
    getToken: () => string | null,
    refreshToken: () => Promise<boolean>
  ) {
    this.httpClient = new AuthHttpClient(
      config.api.debtServiceUrl,
      getToken,
      refreshToken
    );
  }

  async createDebt(debt: DebtCreate): Promise<DebtResponse | ApiError> {
    try {
      const response = await this.httpClient.post<DebtResponse>('/debts/', debt);
      return response;
    } catch (error) {
      console.error('DebtApiClient: Error creating debt:', error);
      return { error: 'Failed to create debt' };
    }
  }

  async getDebts(
    skip: number = 0, 
    limit: number = 100, 
    activeOnly: boolean = false, 
    paidOffOnly: boolean = false
  ): Promise<DebtResponse[] | ApiError> {
    try {
      const params = new URLSearchParams({
        skip: skip.toString(),
        limit: limit.toString(),
        active_only: activeOnly.toString(),
        paid_off_only: paidOffOnly.toString()
      });
      
      const response = await this.httpClient.get<DebtResponse[]>(`/debts/?${params}`);
      return response;
    } catch (error) {
      console.error('DebtApiClient: Error fetching debts:', error);
      return { error: 'Failed to fetch debts' };
    }
  }

  async getDebt(debtId: number): Promise<DebtResponse | ApiError> {
    try {
      const response = await this.httpClient.get<DebtResponse>(`/debts/${debtId}`);
      return response;
    } catch (error) {
      console.error('DebtApiClient: Error fetching debt:', error);
      return { error: 'Failed to fetch debt' };
    }
  }

  async updateDebt(debtId: number, debt: DebtUpdate): Promise<DebtResponse | ApiError> {
    try {
      const response = await this.httpClient.put<DebtResponse>(`/debts/${debtId}`, debt);
      return response;
    } catch (error) {
      console.error('DebtApiClient: Error updating debt:', error);
      return { error: 'Failed to update debt' };
    }
  }

  async deleteDebt(debtId: number): Promise<boolean | ApiError> {
    try {
      await this.httpClient.delete(`/debts/${debtId}`);
      return true;
    } catch (error) {
      console.error('DebtApiClient: Error deleting debt:', error);
      return { error: 'Failed to delete debt' };
    }
  }

  async createPayment(debtId: number, payment: DebtPaymentCreate): Promise<DebtPaymentResponse | ApiError> {
    try {
      const response = await this.httpClient.post<DebtPaymentResponse>(`/debts/${debtId}/payments/`, payment);
      return response;
    } catch (error) {
      console.error('DebtApiClient: Error creating payment:', error);
      return { error: 'Failed to create payment' };
    }
  }

  async getPayments(debtId: number, skip: number = 0, limit: number = 100): Promise<DebtPaymentResponse[] | ApiError> {
    try {
      const params = new URLSearchParams({
        skip: skip.toString(),
        limit: limit.toString()
      });
      
      const response = await this.httpClient.get<DebtPaymentResponse[]>(`/debts/${debtId}/payments/?${params}`);
      return response;
    } catch (error) {
      console.error('DebtApiClient: Error fetching payments:', error);
      return { error: 'Failed to fetch payments' };
    }
  }

  async getDebtSummary(): Promise<DebtSummary | ApiError> {
    try {
      const response = await this.httpClient.get<DebtSummary>('/debts/summary/');
      return response;
    } catch (error) {
      console.error('DebtApiClient: Error fetching debt summary:', error);
      return { error: 'Failed to fetch debt summary' };
    }
  }
}
