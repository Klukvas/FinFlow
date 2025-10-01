import { AuthHttpClient, ApiError } from './AuthHttpClient';
import { config } from '@/config/env';
import { 
  ContactCreate, 
  ContactUpdate, 
  ContactResponse, 
  ContactSummary 
} from '@/types/contact';

export class ContactApiClient {
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

  async createContact(contact: ContactCreate): Promise<ContactResponse | ApiError> {
    try {
      const response = await this.httpClient.post<ContactResponse>('/contacts/', contact);
      return response;
    } catch (error) {
      console.error('ContactApiClient: Error creating contact:', error);
      return { error: 'Failed to create contact' };
    }
  }

  async getContacts(skip: number = 0, limit: number = 100): Promise<ContactResponse[] | ApiError> {
    try {
      const response = await this.httpClient.get<ContactResponse[]>(`/contacts/?skip=${skip}&limit=${limit}`);
      return response;
    } catch (error) {
      console.error('ContactApiClient: Error fetching contacts:', error);
      return { error: 'Failed to fetch contacts' };
    }
  }

  async getContact(contactId: number): Promise<ContactResponse | ApiError> {
    try {
      const response = await this.httpClient.get<ContactResponse>(`/contacts/${contactId}`);
      return response;
    } catch (error) {
      console.error('ContactApiClient: Error fetching contact:', error);
      return { error: 'Failed to fetch contact' };
    }
  }

  async updateContact(contactId: number, contact: ContactUpdate): Promise<ContactResponse | ApiError> {
    try {
      const response = await this.httpClient.put<ContactResponse>(`/contacts/${contactId}`, contact);
      return response;
    } catch (error) {
      console.error('ContactApiClient: Error updating contact:', error);
      return { error: 'Failed to update contact' };
    }
  }

  async deleteContact(contactId: number): Promise<boolean | ApiError> {
    try {
      await this.httpClient.delete(`/contacts/${contactId}`);
      return true;
    } catch (error) {
      console.error('ContactApiClient: Error deleting contact:', error);
      return { error: 'Failed to delete contact' };
    }
  }

  async getContactSummaries(): Promise<ContactSummary[] | ApiError> {
    try {
      const response = await this.httpClient.get<ContactSummary[]>('/contacts/summaries/');
      return response;
    } catch (error) {
      console.error('ContactApiClient: Error fetching contact summaries:', error);
      return { error: 'Failed to fetch contact summaries' };
    }
  }
}
