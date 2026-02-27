from app.schemas.prompts import PromptId, PromptBlock, PromptMetadata, PromptBlockMetadata


# Data sources required for each prompt
PROMPT_DATA_SOURCES: dict[PromptId, list[str]] = {
    # Expenses block - need expenses, categories, accounts, recurring
    PromptId.EXPENSES_REDUCE_SPENDING: ["expenses", "categories", "accounts", "recurring"],
    PromptId.EXPENSES_SAVE_MORE: ["expenses", "incomes", "categories", "recurring"],
    PromptId.EXPENSES_ANOMALIES: ["expenses", "categories", "recurring"],
    # Goals block - need goals, incomes, expenses, accounts, categories
    PromptId.GOALS_REALISTIC: ["goals", "incomes", "expenses", "accounts", "categories"],
    PromptId.GOALS_FASTER: ["goals", "incomes", "expenses", "categories"],
    PromptId.GOALS_PRIORITIZE: ["goals", "incomes", "expenses", "debts", "categories"],
    # Debts block - need debts, incomes, expenses, accounts, categories
    PromptId.DEBTS_PAY_FIRST: ["debts", "incomes", "expenses", "categories"],
    PromptId.DEBTS_RISK_ASSESSMENT: ["debts", "incomes", "expenses", "accounts", "categories"],
    PromptId.DEBTS_REPAYMENT_STRATEGY: ["debts", "incomes", "expenses", "goals", "categories"],
}

# Minimum data thresholds (minimum records needed for meaningful analysis)
PROMPT_MIN_THRESHOLDS: dict[PromptId, dict[str, int]] = {
    PromptId.EXPENSES_REDUCE_SPENDING: {"expenses": 5},
    PromptId.EXPENSES_SAVE_MORE: {"expenses": 5},
    PromptId.EXPENSES_ANOMALIES: {"expenses": 10},
    PromptId.GOALS_REALISTIC: {"goals": 1},
    PromptId.GOALS_FASTER: {"goals": 1},
    PromptId.GOALS_PRIORITIZE: {"goals": 2},
    PromptId.DEBTS_PAY_FIRST: {"debts": 1},
    PromptId.DEBTS_RISK_ASSESSMENT: {"debts": 1},
    PromptId.DEBTS_REPAYMENT_STRATEGY: {"debts": 1},
}


PROMPT_BLOCKS: list[PromptBlockMetadata] = [
    PromptBlockMetadata(
        block=PromptBlock.EXPENSES,
        title_key="aiAssistant.blocks.expenses.title",
        prompts=[
            PromptMetadata(
                id=PromptId.EXPENSES_REDUCE_SPENDING,
                block=PromptBlock.EXPENSES,
                title_key="aiAssistant.prompts.expenses_reduce_spending.title",
                description_key="aiAssistant.prompts.expenses_reduce_spending.description",
                icon="TrendingDown",
            ),
            PromptMetadata(
                id=PromptId.EXPENSES_SAVE_MORE,
                block=PromptBlock.EXPENSES,
                title_key="aiAssistant.prompts.expenses_save_more.title",
                description_key="aiAssistant.prompts.expenses_save_more.description",
                icon="PiggyBank",
            ),
            PromptMetadata(
                id=PromptId.EXPENSES_ANOMALIES,
                block=PromptBlock.EXPENSES,
                title_key="aiAssistant.prompts.expenses_anomalies.title",
                description_key="aiAssistant.prompts.expenses_anomalies.description",
                icon="AlertTriangle",
            ),
        ],
    ),
    PromptBlockMetadata(
        block=PromptBlock.GOALS,
        title_key="aiAssistant.blocks.goals.title",
        prompts=[
            PromptMetadata(
                id=PromptId.GOALS_REALISTIC,
                block=PromptBlock.GOALS,
                title_key="aiAssistant.prompts.goals_realistic.title",
                description_key="aiAssistant.prompts.goals_realistic.description",
                icon="Target",
            ),
            PromptMetadata(
                id=PromptId.GOALS_FASTER,
                block=PromptBlock.GOALS,
                title_key="aiAssistant.prompts.goals_faster.title",
                description_key="aiAssistant.prompts.goals_faster.description",
                icon="Zap",
            ),
            PromptMetadata(
                id=PromptId.GOALS_PRIORITIZE,
                block=PromptBlock.GOALS,
                title_key="aiAssistant.prompts.goals_prioritize.title",
                description_key="aiAssistant.prompts.goals_prioritize.description",
                icon="ListOrdered",
            ),
        ],
    ),
    PromptBlockMetadata(
        block=PromptBlock.DEBTS,
        title_key="aiAssistant.blocks.debts.title",
        prompts=[
            PromptMetadata(
                id=PromptId.DEBTS_PAY_FIRST,
                block=PromptBlock.DEBTS,
                title_key="aiAssistant.prompts.debts_pay_first.title",
                description_key="aiAssistant.prompts.debts_pay_first.description",
                icon="ArrowUpCircle",
            ),
            PromptMetadata(
                id=PromptId.DEBTS_RISK_ASSESSMENT,
                block=PromptBlock.DEBTS,
                title_key="aiAssistant.prompts.debts_risk_assessment.title",
                description_key="aiAssistant.prompts.debts_risk_assessment.description",
                icon="Shield",
            ),
            PromptMetadata(
                id=PromptId.DEBTS_REPAYMENT_STRATEGY,
                block=PromptBlock.DEBTS,
                title_key="aiAssistant.prompts.debts_repayment_strategy.title",
                description_key="aiAssistant.prompts.debts_repayment_strategy.description",
                icon="Map",
            ),
        ],
    ),
]
