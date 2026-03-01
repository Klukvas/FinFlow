from pydantic import BaseModel, Field, ConfigDict, field_validator
from typing import List, Optional
from uuid import UUID
import re
from enum import Enum

class CategoryType(str, Enum):
    EXPENSE = "EXPENSE"
    INCOME = "INCOME"

class SupportedLanguage(str, Enum):
    """Supported languages for translations"""
    RU = "ru"
    UK = "uk"
    EN = "en"

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
    monthly_budget: Optional[float] = Field(
        None,
        ge=0,
        description="Monthly budget amount for this category",
        examples=[500.00, 1000.00]
    )

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "name": "Food & Dining",
                "parent_id": None,
                "monthly_budget": 500.00
            }
        }
    )

class CategoryCreateFromMCC(BaseModel):
    """Schema for creating a category from an MCC code"""
    mcc_code: int = Field(
        description="MCC code to create category from",
        examples=[5411, 5812, 4121]
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
    custom_name: Optional[str] = Field(
        None,
        min_length=3,
        max_length=100,
        description="Custom name override (optional). If not provided, uses MCC translation or English name",
        examples=["My Custom Grocery Store", "Personal Food Expenses"]
    )

    @field_validator('mcc_code')
    @classmethod
    def validate_mcc_code(cls, v: int) -> int:
        """Validate MCC code format"""
        if v <= 0 or v > 9999:
            raise ValueError('MCC code must be between 1 and 9999')
        return v

    @field_validator('custom_name')
    @classmethod
    def validate_custom_name(cls, v: Optional[str]) -> Optional[str]:
        """Validate custom name format"""
        if v is not None:
            if not v or not v.strip():
                raise ValueError('Custom name cannot be empty or only whitespace')
            v = v.strip()
        return v

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "mcc_code": 5411,
                "parent_id": None,
                "type": "EXPENSE",
                "custom_name": "My Grocery Store"
            }
        }
    )

class CategoryCreateFromMCCBatch(BaseModel):
    """Schema for creating multiple categories from MCC codes in a single request"""
    categories: List[CategoryCreateFromMCC] = Field(
        min_length=1,
        max_length=50,
        description="List of MCC-based categories to create (1-50 items)",
        examples=[[{"mcc_code": 5411}, {"mcc_code": 5812, "custom_name": "My Restaurant"}]]
    )
    language: Optional[SupportedLanguage] = Field(
        None,
        description="Default language for all categories (can be overridden per category)",
        examples=["ru", "uk", "en"]
    )

    @field_validator('categories')
    @classmethod
    def validate_categories(cls, v: List[CategoryCreateFromMCC]) -> List[CategoryCreateFromMCC]:
        """Validate that categories list is not empty and has unique MCC codes"""
        if not v:
            raise ValueError('Categories list cannot be empty')
        
        # Check for duplicate MCC codes in the batch
        mcc_codes = [cat.mcc_code for cat in v]
        if len(mcc_codes) != len(set(mcc_codes)):
            raise ValueError('Duplicate MCC codes found in batch request')
        
        return v

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "categories": [
                    {"mcc_code": 5411},
                    {"mcc_code": 5812, "custom_name": "My Restaurant"},
                    {"mcc_code": 4121, "parent_id": 1, "type": "INCOME"}
                ],
                "language": "ru"
            }
        }
    )

class CategoryBatchCreateResult(BaseModel):
    """Schema for individual category creation result"""
    mcc_code: int = Field(description="MCC code that was processed")
    success: bool = Field(description="Whether the category was created successfully")
    category_id: Optional[int] = Field(None, description="ID of created category (if successful)")
    category_name: Optional[str] = Field(None, description="Name of created category (if successful)")
    error: Optional[str] = Field(None, description="Error message (if failed)")

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "mcc_code": 5411,
                "success": True,
                "category_id": 1,
                "category_name": "Grocery Stores, Supermarkets",
                "error": None
            }
        }
    )

class CategoryBatchCreateResponse(BaseModel):
    """Response schema for batch category creation"""
    results: List[CategoryBatchCreateResult] = Field(description="Results for each category creation attempt")
    total_requested: int = Field(description="Total number of categories requested")
    successful: int = Field(description="Number of categories created successfully")
    failed: int = Field(description="Number of categories that failed to create")
    language: Optional[SupportedLanguage] = Field(None, description="Language used for translations")

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "results": [
                    {
                        "mcc_code": 5411,
                        "success": True,
                        "category_id": 1,
                        "category_name": "Grocery Stores, Supermarkets",
                        "error": None
                    },
                    {
                        "mcc_code": 9999,
                        "success": False,
                        "category_id": None,
                        "category_name": None,
                        "error": "MCC code 9999 not found"
                    }
                ],
                "total_requested": 2,
                "successful": 1,
                "failed": 1,
                "language": "ru"
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
    monthly_budget: Optional[float] = Field(
        None,
        ge=0,
        description="Monthly budget amount for this category",
        examples=[500.00, 1000.00]
    )

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "name": "Food & Dining Updated",
                "parent_id": 1,
                "monthly_budget": 500.00
            }
        }
    )

class CategoryOut(CategoryBase):
    """Schema for category output with all fields"""
    id: int = Field(description="Unique category identifier", examples=[1, 2, 3])
    user_id: int = Field(description="ID of the user who owns this category", examples=[1, 2, 3])
    workspace_id: UUID = Field(description="Workspace ID this category belongs to")
    monthly_budget: Optional[float] = Field(None, description="Monthly budget amount for this category")
    children: List['CategoryOut'] = Field(
        default_factory=list,
        description="List of child categories"
    )
    is_read_only: bool = Field(default=False, description="True if record exceeds plan limit and cannot be edited")

    model_config = ConfigDict(
        from_attributes=True,
        json_schema_extra={
            "example": {
                "id": 1,
                "name": "Food & Dining",
                "parent_id": None,
                "user_id": 1,
                "workspace_id": "550e8400-e29b-41d4-a716-446655440000",
                "children": [
                    {
                        "id": 2,
                        "name": "Restaurants",
                        "parent_id": 1,
                        "user_id": 1,
                        "workspace_id": "550e8400-e29b-41d4-a716-446655440000",
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

class CategoryListResponse(BaseModel):
    """Paginated response schema for categories"""
    items: List[CategoryOut]
    total: int = Field(description="Total number of categories")
    page: int = Field(description="Current page number")
    size: int = Field(description="Number of items per page")
    pages: int = Field(description="Total number of pages")

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "items": [
                    {
                        "id": 1,
                        "name": "Food & Dining",
                        "parent_id": None,
                        "user_id": 1,
                        "type": "EXPENSE",
                        "children": []
                    }
                ],
                "total": 25,
                "page": 1,
                "size": 10,
                "pages": 3
            }
        }
    )

class DefaultCategoryOut(BaseModel):
    """Schema for default MCC categories with translations"""
    mcc_code: int = Field(description="MCC code identifier", examples=[5411, 5812])
    name: str = Field(description="Default English name", examples=["Grocery Stores, Supermarkets"])
    translation: Optional[str] = Field(
        None, 
        description="Translated name in user's language", 
        examples=["Продуктовые магазины, супермаркеты"]
    )
    is_default: bool = Field(description="Whether this is a default category", default=True)

    model_config = ConfigDict(
        from_attributes=True,
        json_schema_extra={
            "example": {
                "mcc_code": 5411,
                "name": "Grocery Stores, Supermarkets",
                "translation": "Продуктовые магазины, супермаркеты",
                "is_default": True
            }
        }
    )

class DefaultCategoryListResponse(BaseModel):
    """Response schema for default categories list"""
    items: List[DefaultCategoryOut]
    total: int = Field(description="Total number of default categories")
    language: Optional[SupportedLanguage] = Field(
        None, 
        description="Language code for translations (ru, uk, en)", 
        examples=["ru", "uk", "en"]
    )

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "items": [
                    {
                        "mcc_code": 5411,
                        "name": "Grocery Stores, Supermarkets",
                        "translation": "Продуктовые магазины, супермаркеты",
                        "is_default": True
                    }
                ],
                "total": 15,
                "language": "ru"
            }
        }
    )

class MCCCodeListResponse(BaseModel):
    """Response schema for all MCC codes list"""
    items: List[DefaultCategoryOut]
    total: int = Field(description="Total number of MCC codes")
    language: Optional[SupportedLanguage] = Field(
        None, 
        description="Language code for translations (ru, uk, en)", 
        examples=["ru", "uk", "en"]
    )

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "items": [
                    {
                        "mcc_code": 5411,
                        "name": "Grocery Stores, Supermarkets",
                        "translation": "Продуктовые магазины, супермаркеты",
                        "is_default": True
                    },
                    {
                        "mcc_code": 1234,
                        "name": "Some Other Store",
                        "translation": None,
                        "is_default": False
                    }
                ],
                "total": 100,
                "language": "ru"
            }
        }
    )

class CategoryStatisticsResponse(BaseModel):
    """Response schema for category statistics"""
    total_categories: int = Field(description="Total number of categories")
    expense_categories: int = Field(description="Number of expense categories")
    income_categories: int = Field(description="Number of income categories")
    parent_categories: int = Field(description="Number of parent categories")
    child_categories: int = Field(description="Number of child categories")

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "total_categories": 23,
                "expense_categories": 15,
                "income_categories": 8,
                "parent_categories": 10,
                "child_categories": 13
            }
        }
    )

# Update forward references
CategoryOut.model_rebuild()