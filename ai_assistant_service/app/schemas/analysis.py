from typing import Literal

from pydantic import BaseModel, Field


class AnalysisSection(BaseModel):
    title: str = Field(..., description="Section title")
    content: str = Field(..., description="Section content (markdown)")
    priority: Literal["high", "medium", "low"] = Field(default="medium", description="Priority level")


class AnalysisResponse(BaseModel):
    prompt_id: str = Field(..., description="The prompt that was analyzed")
    sections: list[AnalysisSection] = Field(..., description="Analysis result sections")
    cached: bool = Field(default=False, description="Whether result was served from cache")
    language: str = Field(default="ru", description="Response language")
