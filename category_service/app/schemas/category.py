from pydantic import BaseModel, Field, ConfigDict, field_validator
from typing import List, Optional
import re
from enum import Enum

class CategoryType(str, Enum):
    EXPENSE = "EXPENSE"
    INCOME = "INCOME"

class CategoryBase(BaseModel):
    name: str = Field(
        min_length=3, 
        max_length=100,
        description="Category name must be between 3 and 100 characters long",
        examples=["Food", "Transportation", "Entertainment"]
    )
    parent_id: Optional[int] = Field(
        None,
        description="Parent category ID for hierarchical organization",
        examples=[1, 2, 3]
    )
    type: CategoryType = Field(
        default=CategoryType.EXPENSE,
        description="Category type - expense or income",
        examples=["expense", "income"]
    )

    @field_validator('name')
    @classmethod
    def validate_name(cls, v: str) -> str:
        """Validate category name format"""
        if not v or not v.strip():
            raise ValueError('Category name cannot be empty or only whitespace')
        
        # Remove extra whitespace
        v = v.strip()
        
        return v

class CategoryCreate(CategoryBase):
    """Schema for creating a new category"""
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "name": "Food & Dining",
                "parent_id": None
            }
        }
    )

class CategoryUpdate(CategoryBase):
    """Schema for updating an existing category"""
    name: Optional[str] = Field(
        None,
        min_length=3, 
        max_length=100,
        description="Category name must be between 3 and 100 characters long"
    )
    parent_id: Optional[int] = Field(
        None,
        description="Parent category ID for hierarchical organization"
    )
    
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "name": "Food & Dining Updated",
                "parent_id": 1
            }
        }
    )

class CategoryOut(CategoryBase):
    """Schema for category output with all fields"""
    id: int = Field(description="Unique category identifier", examples=[1, 2, 3])
    user_id: int = Field(description="ID of the user who owns this category", examples=[1, 2, 3])
    children: List['CategoryOut'] = Field(
        default_factory=list,
        description="List of child categories"
    )

    model_config = ConfigDict(
        from_attributes=True,
        json_schema_extra={
            "example": {
                "id": 1,
                "name": "Food & Dining",
                "parent_id": None,
                "user_id": 1,
                "children": [
                    {
                        "id": 2,
                        "name": "Restaurants",
                        "parent_id": 1,
                        "user_id": 1,
                        "children": []
                    }
                ]
            }
        }
    )

class CategorySummary(BaseModel):
    """Simplified category schema for lists and summaries"""
    id: int
    name: str
    parent_id: Optional[int]
    children_count: int = Field(description="Number of direct children")

    model_config = ConfigDict(from_attributes=True)

# Update forward references
CategoryOut.model_rebuild()