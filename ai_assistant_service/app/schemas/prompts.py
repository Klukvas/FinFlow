from enum import Enum
from typing import Literal

from pydantic import BaseModel, Field


class PromptId(str, Enum):
    # Expenses block
    EXPENSES_REDUCE_SPENDING = "expenses_reduce_spending"
    EXPENSES_SAVE_MORE = "expenses_save_more"
    EXPENSES_ANOMALIES = "expenses_anomalies"
    # Goals block
    GOALS_REALISTIC = "goals_realistic"
    GOALS_FASTER = "goals_faster"
    GOALS_PRIORITIZE = "goals_prioritize"
    # Debts block
    DEBTS_PAY_FIRST = "debts_pay_first"
    DEBTS_RISK_ASSESSMENT = "debts_risk_assessment"
    DEBTS_REPAYMENT_STRATEGY = "debts_repayment_strategy"


class PromptBlock(str, Enum):
    EXPENSES = "expenses"
    GOALS = "goals"
    DEBTS = "debts"


class AnalysisRequest(BaseModel):
    prompt_id: PromptId = Field(..., description="ID of the selected prompt")
    language: Literal["ru", "en", "uk"] = Field(default="ru", description="Response language")


class PromptMetadata(BaseModel):
    id: PromptId
    block: PromptBlock
    title_key: str
    description_key: str
    icon: str


class PromptBlockMetadata(BaseModel):
    block: PromptBlock
    title_key: str
    prompts: list[PromptMetadata]
