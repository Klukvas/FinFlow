from fastapi import HTTPException, status
from typing import Optional

class CategoryNotFoundError(HTTPException):
    def __init__(self, category_id: Optional[int] = None, detail: Optional[str] = None):
        if detail is None:
            detail = f"Category with ID {category_id} not found" if category_id else "Category not found"
        super().__init__(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=detail
        )

class CategoryValidationError(HTTPException):
    def __init__(self, detail: str):
        super().__init__(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=detail
        )

class CircularRelationshipError(CategoryValidationError):
    def __init__(self, category_id: int, parent_id: int):
        super().__init__(
            detail=f"Category {category_id} cannot be its own parent or create a circular relationship with parent {parent_id}"
        )

class CategoryDepthExceededError(CategoryValidationError):
    def __init__(self, max_depth: int):
        super().__init__(
            detail=f"Maximum category depth of {max_depth} levels exceeded"
        )

class CategoryNameConflictError(CategoryValidationError):
    def __init__(self, name: str, user_id: int):
        super().__init__(
            detail=f"Category name '{name}' already exists for this user"
        )

class CategoryOwnershipError(HTTPException):
    def __init__(self, category_id: int, user_id: int):
        super().__init__(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f"Category {category_id} does not belong to user {user_id}"
        )

