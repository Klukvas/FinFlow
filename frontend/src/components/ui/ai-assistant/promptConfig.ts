export interface PromptCardConfig {
  id: string;
  titleKey: string;
  descriptionKey: string;
  icon: string;
}

export interface PromptBlockConfig {
  block: string;
  titleKey: string;
  prompts: PromptCardConfig[];
}

export const PROMPT_BLOCKS: PromptBlockConfig[] = [
  {
    block: 'expenses',
    titleKey: 'aiAssistant.blocks.expenses.title',
    prompts: [
      {
        id: 'expenses_reduce_spending',
        titleKey: 'aiAssistant.prompts.expenses_reduce_spending.title',
        descriptionKey: 'aiAssistant.prompts.expenses_reduce_spending.description',
        icon: 'TrendingDown',
      },
      {
        id: 'expenses_save_more',
        titleKey: 'aiAssistant.prompts.expenses_save_more.title',
        descriptionKey: 'aiAssistant.prompts.expenses_save_more.description',
        icon: 'PiggyBank',
      },
      {
        id: 'expenses_anomalies',
        titleKey: 'aiAssistant.prompts.expenses_anomalies.title',
        descriptionKey: 'aiAssistant.prompts.expenses_anomalies.description',
        icon: 'AlertTriangle',
      },
    ],
  },
  {
    block: 'goals',
    titleKey: 'aiAssistant.blocks.goals.title',
    prompts: [
      {
        id: 'goals_realistic',
        titleKey: 'aiAssistant.prompts.goals_realistic.title',
        descriptionKey: 'aiAssistant.prompts.goals_realistic.description',
        icon: 'Target',
      },
      {
        id: 'goals_faster',
        titleKey: 'aiAssistant.prompts.goals_faster.title',
        descriptionKey: 'aiAssistant.prompts.goals_faster.description',
        icon: 'Zap',
      },
      {
        id: 'goals_prioritize',
        titleKey: 'aiAssistant.prompts.goals_prioritize.title',
        descriptionKey: 'aiAssistant.prompts.goals_prioritize.description',
        icon: 'ListOrdered',
      },
    ],
  },
  {
    block: 'debts',
    titleKey: 'aiAssistant.blocks.debts.title',
    prompts: [
      {
        id: 'debts_pay_first',
        titleKey: 'aiAssistant.prompts.debts_pay_first.title',
        descriptionKey: 'aiAssistant.prompts.debts_pay_first.description',
        icon: 'ArrowUpCircle',
      },
      {
        id: 'debts_risk_assessment',
        titleKey: 'aiAssistant.prompts.debts_risk_assessment.title',
        descriptionKey: 'aiAssistant.prompts.debts_risk_assessment.description',
        icon: 'Shield',
      },
      {
        id: 'debts_repayment_strategy',
        titleKey: 'aiAssistant.prompts.debts_repayment_strategy.title',
        descriptionKey: 'aiAssistant.prompts.debts_repayment_strategy.description',
        icon: 'Map',
      },
    ],
  },
];
