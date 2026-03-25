import { ExpenseApiClient } from "../../infra/api/ExpenseApiClient";

export class ExpenseApiActions {
  private expenseApiClient: ExpenseApiClient;

  constructor(expenseApiClient: ExpenseApiClient) {
    this.expenseApiClient = expenseApiClient;
  }

  async deleteAllExpenses(
    token: string,
    workspaceId?: string,
  ): Promise<number> {
    this.expenseApiClient.setToken(token);
    if (workspaceId) {
      this.expenseApiClient.setWorkspaceId(workspaceId);
    }

    const response = await this.expenseApiClient.getExpenses();

    if (response.error) {
      throw new Error(`Failed to fetch expenses: ${response.error}`);
    }
    if (!response.data) {
      return 0;
    }

    const expenses = response.data;
    let deletedCount = 0;

    for (const expense of expenses) {
      try {
        await this.expenseApiClient.deleteExpense(expense.id);
        deletedCount++;
      } catch (error: any) {
        console.error(
          `Failed to delete expense ${expense.id}: ${error.message}`,
        );
      }
    }

    return deletedCount;
  }
}
