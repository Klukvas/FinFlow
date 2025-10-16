import { ApiClient } from '../api/ApiClient';
import { CreateUserRequest, CreateCategoryRequest, CreateExpenseRequest, CreateIncomeRequest, CreateAccountRequest } from '../types/api';

export class ApiTestUtils {
  private apiClient: ApiClient;

  constructor(config?: any) {
    this.apiClient = new ApiClient(config);
  }

  get client(): ApiClient {
    return this.apiClient;
  }

  // Authentication helpers
  async loginAsTestUser(): Promise<void> {
    const testCredentials = {
      email: 'test@example.com',
      password: 'testpassword123'
    };

    const response = await this.apiClient.login(testCredentials);
    if (response.error) {
      throw new Error(`Login failed: ${response.error}`);
    }
  }

  async registerTestUser(): Promise<void> {
    const testUser: CreateUserRequest = {
      email: 'test@example.com',
      username: 'testuser',
      password: 'testpassword123'
    };

    const response = await this.apiClient.register(testUser);
    if (response.error) {
      throw new Error(`Registration failed: ${response.error}`);
    }
  }

  async ensureTestUserExists(): Promise<void> {
    try {
      await this.loginAsTestUser();
    } catch {
      // User doesn't exist, try to register
      try {
        await this.registerTestUser();
      } catch (error) {
        // If registration fails, user might already exist, try login again
        await this.loginAsTestUser();
      }
    }
  }

  // Test data creation helpers
  async createTestCategory(name: string, type: 'EXPENSE' | 'INCOME' = 'EXPENSE'): Promise<number> {
    const categoryData: CreateCategoryRequest = {
      name,
      type
    };

    const response = await this.apiClient.category.createCategory(categoryData);
    if (response.error) {
      throw new Error(`Failed to create category: ${response.error}`);
    }
    return response.data!.id;
  }

  async createTestAccount(name: string, balance: number = 1000): Promise<number> {
    const accountData: CreateAccountRequest = {
      name,
      balance,
      currency: 'USD',
      account_type: 'checking'
    };

    const response = await this.apiClient.account.createAccount(accountData);
    if (response.error) {
      throw new Error(`Failed to create account: ${response.error}`);
    }
    return response.data!.id;
  }

  async createTestExpense(amount: number, categoryId?: number, accountId?: number): Promise<number> {
    const expenseData: CreateExpenseRequest = {
      amount,
      category_id: categoryId,
      account_id: accountId,
      currency: 'USD',
      description: `Test expense of ${amount}`,
      date: new Date().toISOString().split('T')[0]
    };

    const response = await this.apiClient.expense.createExpense(expenseData);
    if (response.error) {
      throw new Error(`Failed to create expense: ${response.error}`);
    }
    return response.data!.id;
  }

  async createTestIncome(amount: number, categoryId?: number, accountId?: number): Promise<number> {
    const incomeData: CreateIncomeRequest = {
      amount,
      category_id: categoryId,
      account_id: accountId,
      currency: 'USD',
      description: `Test income of ${amount}`,
      date: new Date().toISOString().split('T')[0]
    };

    const response = await this.apiClient.income.createIncome(incomeData);
    if (response.error) {
      throw new Error(`Failed to create income: ${response.error}`);
    }
    return response.data!.id;
  }

  // Cleanup helpers
  async cleanupTestData(): Promise<void> {
    try {
      // Get all expenses and delete them
      const expensesResponse = await this.apiClient.expense.getExpenses();
      if (expensesResponse.data) {
        for (const expense of expensesResponse.data) {
          await this.apiClient.expense.deleteExpense(expense.id);
        }
      }

      // Get all incomes and delete them
      const incomesResponse = await this.apiClient.income.getIncomes();
      if (incomesResponse.data) {
        for (const income of incomesResponse.data) {
          await this.apiClient.income.deleteIncome(income.id);
        }
      }

      // Get all categories and delete them
      const categoriesResponse = await this.apiClient.category.getAllCategoriesFlat();
      if (categoriesResponse.data) {
        for (const category of categoriesResponse.data) {
          await this.apiClient.category.deleteCategory(category.id);
        }
      }

      // Get all accounts and delete them
      const accountsResponse = await this.apiClient.account.getAllAccounts();
      if (accountsResponse.data) {
        for (const account of accountsResponse.data) {
          await this.apiClient.account.deleteAccount(account.id);
        }
      }
    } catch (error) {
      console.warn('Error during cleanup:', error);
    }
  }

  // Health check
  async checkServicesHealth(): Promise<void> {
    const health = await this.apiClient.healthCheck();
    const unhealthyServices = Object.entries(health)
      .filter(([_, isHealthy]) => !isHealthy)
      .map(([service]) => service);

    if (unhealthyServices.length > 0) {
      throw new Error(`Unhealthy services: ${unhealthyServices.join(', ')}`);
    }
  }

  // Setup for tests
  async setupForTest(): Promise<void> {
    await this.checkServicesHealth();
    await this.ensureTestUserExists();
  }

  // Teardown for tests
  async teardownAfterTest(): Promise<void> {
    await this.cleanupTestData();
    await this.apiClient.logout();
  }
}
