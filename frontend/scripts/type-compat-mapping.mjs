/**
 * Mapping between manual frontend TypeScript types and generated OpenAPI schemas.
 *
 * Each entry maps a hand-written interface (in frontend/src/types/*.ts) to the
 * corresponding generated schema (in frontend/src/types/generated/schemas/*.json).
 *
 * UI-only types (ExpenseFilters, GoalFormData, PaymentUIState, etc.) that have
 * no backend equivalent are intentionally excluded.
 */

export const TYPE_MAPPINGS = [
  // ── account_service ──────────────────────────────────────────────
  { manual: "AccountCreate",             manualFile: "account.ts",       generated: "AccountCreate",             service: "account_service" },
  { manual: "AccountResponse",           manualFile: "account.ts",       generated: "AccountResponse",           service: "account_service" },
  { manual: "AccountUpdate",             manualFile: "account.ts",       generated: "AccountUpdate",             service: "account_service" },
  { manual: "AccountSummary",            manualFile: "account.ts",       generated: "AccountSummary",            service: "account_service" },
  { manual: "AccountTransactionSummary", manualFile: "account.ts",       generated: "AccountTransactionSummary", service: "account_service" },
  { manual: "AccountStatisticsResponse", manualFile: "account.ts",       generated: "AccountStatisticsResponse", service: "account_service" },

  // ── expense_service ──────────────────────────────────────────────
  { manual: "ExpenseCreate",             manualFile: "expense.ts",       generated: "ExpenseCreate",             service: "expense_service" },
  { manual: "ExpenseResponse",           manualFile: "expense.ts",       generated: "ExpenseResponse",           service: "expense_service" },
  { manual: "ExpenseUpdate",             manualFile: "expense.ts",       generated: "ExpenseUpdate",             service: "expense_service" },
  { manual: "ExpenseListResponse",       manualFile: "expense.ts",       generated: "ExpenseListResponse",       service: "expense_service" },
  { manual: "CategoryExpenseStatistics", manualFile: "expense.ts",       generated: "CategoryExpenseStatistics", service: "expense_service" },
  { manual: "ExpensesByCategoryResponse",manualFile: "expense.ts",       generated: "ExpensesByCategoryResponse",service: "expense_service" },

  // ── income_service ───────────────────────────────────────────────
  { manual: "IncomeCreate",              manualFile: "income.ts",        generated: "IncomeCreate",              service: "income_service" },
  { manual: "IncomeOut",                 manualFile: "income.ts",        generated: "IncomeOut",                 service: "income_service" },
  { manual: "IncomeUpdate",              manualFile: "income.ts",        generated: "IncomeUpdate",              service: "income_service" },
  { manual: "IncomeListResponse",        manualFile: "income.ts",        generated: "IncomeListResponse",        service: "income_service" },
  { manual: "IncomeSummary",             manualFile: "income.ts",        generated: "IncomeSummary",             service: "income_service" },
  { manual: "IncomeStats",              manualFile: "income.ts",        generated: "IncomeStats",              service: "income_service" },
  { manual: "CategoryIncomeStatistics",  manualFile: "income.ts",        generated: "CategoryIncomeStatistics",  service: "income_service" },
  { manual: "IncomesByCategoryResponse", manualFile: "income.ts",        generated: "IncomesByCategoryResponse", service: "income_service" },

  // ── category_service ─────────────────────────────────────────────
  { manual: "Category",                  manualFile: "category.ts",      generated: "CategoryOut",               service: "category_service" },
  { manual: "CreateCategoryRequest",     manualFile: "category.ts",      generated: "CategoryCreate",            service: "category_service" },
  { manual: "CategoryListResponse",      manualFile: "category.ts",      generated: "CategoryListResponse",      service: "category_service" },
  { manual: "CategoryStatisticsResponse",manualFile: "category.ts",      generated: "CategoryStatisticsResponse",service: "category_service" },

  // ── debt_service (debts) ─────────────────────────────────────────
  { manual: "DebtCreate",               manualFile: "debt.ts",          generated: "DebtCreate",               service: "debt_service" },
  { manual: "DebtUpdate",               manualFile: "debt.ts",          generated: "DebtUpdate",               service: "debt_service" },
  { manual: "DebtResponse",             manualFile: "debt.ts",          generated: "DebtResponse",             service: "debt_service" },
  { manual: "DebtSummary",              manualFile: "debt.ts",          generated: "DebtSummary",              service: "debt_service" },
  { manual: "DebtPaymentCreate",        manualFile: "debt.ts",          generated: "DebtPaymentCreate",        service: "debt_service" },
  { manual: "DebtPaymentResponse",      manualFile: "debt.ts",          generated: "DebtPaymentResponse",      service: "debt_service" },

  // ── debt_service (contacts) ──────────────────────────────────────
  { manual: "ContactCreate",            manualFile: "contact.ts",       generated: "ContactCreate",            service: "debt_service" },
  { manual: "ContactUpdate",            manualFile: "contact.ts",       generated: "ContactUpdate",            service: "debt_service" },
  { manual: "ContactResponse",          manualFile: "contact.ts",       generated: "ContactResponse",          service: "debt_service" },
  { manual: "ContactSummary",           manualFile: "contact.ts",       generated: "ContactSummary",           service: "debt_service" },

  // ── goals_service ────────────────────────────────────────────────
  { manual: "Goal",                     manualFile: "goal.ts",          generated: "GoalResponse",             service: "goals_service" },
  { manual: "CreateGoalRequest",        manualFile: "goal.ts",          generated: "GoalCreate",               service: "goals_service" },
  { manual: "UpdateGoalRequest",        manualFile: "goal.ts",          generated: "GoalUpdate",               service: "goals_service" },
  { manual: "GoalProgressUpdate",       manualFile: "goal.ts",          generated: "GoalProgressUpdate",       service: "goals_service" },
  { manual: "GoalListResponse",         manualFile: "goal.ts",          generated: "GoalListResponse",         service: "goals_service" },
  { manual: "GoalStatistics",           manualFile: "goal.ts",          generated: "GoalStatistics",           service: "goals_service" },
  { manual: "Milestone",                manualFile: "goal.ts",          generated: "MilestoneResponse",        service: "goals_service" },
  { manual: "CreateMilestoneRequest",   manualFile: "goal.ts",          generated: "MilestoneCreate",          service: "goals_service" },
  { manual: "MilestoneProgressUpdate",  manualFile: "goal.ts",          generated: "MilestoneProgressUpdate",  service: "goals_service" },

  // ── user_service ─────────────────────────────────────────────────
  { manual: "User",                     manualFile: "user.ts",          generated: "UserOut",                  service: "user_service" },
  { manual: "UserCreate",               manualFile: "user.ts",          generated: "UserCreate",               service: "user_service" },
  { manual: "UserUpdate",               manualFile: "user.ts",          generated: "UserUpdate",               service: "user_service" },
  { manual: "UserLogin",                manualFile: "user.ts",          generated: "UserLogin",                service: "user_service" },
  { manual: "TokenResponse",            manualFile: "user.ts",          generated: "TokenResponse",            service: "user_service" },
  { manual: "PasswordChange",           manualFile: "user.ts",          generated: "PasswordChange",           service: "user_service" },

  // ── payment_service ──────────────────────────────────────────────
  { manual: "Payment",                  manualFile: "payment.ts",       generated: "PaymentOut",               service: "payment_service" },
  { manual: "CreatePaymentRequest",     manualFile: "payment.ts",       generated: "CreatePaymentRequest",     service: "payment_service" },
  { manual: "CreatePaymentResponse",    manualFile: "payment.ts",       generated: "CreatePaymentResponse",    service: "payment_service" },
  { manual: "PaymentEvent",             manualFile: "payment.ts",       generated: "PaymentEventOut",          service: "payment_service" },
  { manual: "ChangePlanRequest",        manualFile: "payment.ts",       generated: "ChangePlanRequest",        service: "payment_service" },
  { manual: "ChangePlanResponse",       manualFile: "payment.ts",       generated: "ChangePlanResponse",       service: "payment_service" },

  // ── subscription_service ─────────────────────────────────────────
  { manual: "SubscriptionResponse",     manualFile: "subscription.ts",  generated: "app__schemas__subscription__SubscriptionOut", service: "subscription_service" },
  { manual: "PlanResponse",             manualFile: "subscription.ts",  generated: "PlanOut",                  service: "subscription_service" },
  { manual: "UserFeature",              manualFile: "subscription.ts",  generated: "UserFeatureOut",           service: "subscription_service" },
  { manual: "UserEntitlements",         manualFile: "subscription.ts",  generated: "EntitlementsOut",          service: "subscription_service" },
  { manual: "PlanWithFeatures",         manualFile: "subscription.ts",  generated: "PlanWithFeaturesOut",      service: "subscription_service" },
  { manual: "PlanFeature",              manualFile: "subscription.ts",  generated: "app__schemas__plan__PlanFeatureOut", service: "subscription_service" },

  // ── workspace_service ────────────────────────────────────────────
  { manual: "Workspace",                manualFile: "workspace.ts",     generated: "WorkspaceResponse",        service: "workspace_service" },
  { manual: "WorkspaceCreate",          manualFile: "workspace.ts",     generated: "WorkspaceCreate",          service: "workspace_service" },
  { manual: "WorkspaceUpdate",          manualFile: "workspace.ts",     generated: "WorkspaceUpdate",          service: "workspace_service" },
  { manual: "WorkspaceMember",          manualFile: "workspace.ts",     generated: "MemberResponse",           service: "workspace_service" },
  { manual: "WorkspaceMemberUpdate",    manualFile: "workspace.ts",     generated: "MemberRoleUpdate",         service: "workspace_service" },
  { manual: "WorkspaceInvite",          manualFile: "workspace.ts",     generated: "InviteResponse",           service: "workspace_service" },
  { manual: "MyInvite",                 manualFile: "workspace.ts",     generated: "MyInviteResponse",         service: "workspace_service" },
  { manual: "WorkspaceInviteCreate",    manualFile: "workspace.ts",     generated: "InviteCreate",             service: "workspace_service" },

  // ── bank_sync_service ────────────────────────────────────────────
  { manual: "BankConnection",           manualFile: "bankSync.ts",      generated: "ConnectionResponse",       service: "bank_sync_service" },
  { manual: "LinkedAccount",            manualFile: "bankSync.ts",      generated: "LinkedAccountResponse",    service: "bank_sync_service" },
  { manual: "SyncStatus",               manualFile: "bankSync.ts",      generated: "SyncStatusResponse",       service: "bank_sync_service" },
  { manual: "SyncRequest",              manualFile: "bankSync.ts",      generated: "SyncRequest",              service: "bank_sync_service" },
  { manual: "LinkAccountRequest",       manualFile: "bankSync.ts",      generated: "LinkAccountRequest",       service: "bank_sync_service" },
  { manual: "ConnectionCreate",         manualFile: "bankSync.ts",      generated: "ConnectionCreate",         service: "bank_sync_service" },
  { manual: "SyncPreviewTransaction",   manualFile: "bankSync.ts",      generated: "SyncPreviewTransaction",   service: "bank_sync_service" },
  { manual: "SyncPreviewResponse",      manualFile: "bankSync.ts",      generated: "SyncPreviewResponse",      service: "bank_sync_service" },
  { manual: "SyncConfirmTransaction",   manualFile: "bankSync.ts",      generated: "SyncConfirmTransaction",   service: "bank_sync_service" },

  // ── ai_assistant_service ─────────────────────────────────────────
  { manual: "AnalysisRequest",          manualFile: "aiAssistant.ts",   generated: "AnalysisRequest",          service: "ai_assistant_service" },
  { manual: "AnalysisResponse",         manualFile: "aiAssistant.ts",   generated: "AnalysisResponse",         service: "ai_assistant_service" },
  { manual: "AnalysisSection",          manualFile: "aiAssistant.ts",   generated: "AnalysisSection",          service: "ai_assistant_service" },
  { manual: "PromptMetadata",           manualFile: "aiAssistant.ts",   generated: "PromptMetadata",           service: "ai_assistant_service" },
  { manual: "PromptBlockMetadata",      manualFile: "aiAssistant.ts",   generated: "PromptBlockMetadata",      service: "ai_assistant_service" },
];
