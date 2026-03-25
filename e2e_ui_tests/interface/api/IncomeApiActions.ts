import { IncomeApiClient } from "../../infra/api/IncomeApiClient";

export class IncomeApiActions {
  private incomeApiClient: IncomeApiClient;

  constructor(incomeApiClient: IncomeApiClient) {
    this.incomeApiClient = incomeApiClient;
  }

  async deleteAllIncomes(
    token: string,
    workspaceId?: string,
  ): Promise<number> {
    this.incomeApiClient.setToken(token);
    if (workspaceId) {
      this.incomeApiClient.setWorkspaceId(workspaceId);
    }

    const response = await this.incomeApiClient.getIncomes();

    if (response.error) {
      throw new Error(`Failed to fetch incomes: ${response.error}`);
    }
    if (!response.data) {
      return 0;
    }

    const incomes = response.data;
    let deletedCount = 0;

    for (const income of incomes) {
      try {
        await this.incomeApiClient.deleteIncome(income.id);
        deletedCount++;
      } catch (error: any) {
        console.error(
          `Failed to delete income ${income.id}: ${error.message}`,
        );
      }
    }

    return deletedCount;
  }
}
