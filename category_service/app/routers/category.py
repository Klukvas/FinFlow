from fastapi import APIRouter, Depends, status, Query, Path
from typing import List, Annotated

from app.schemas.category import CategoryCreate, CategoryOut, CategoryListResponse
from app.services.category import CategoryService
from app.dependencies import get_category_service, get_current_user_id
from app.exceptions import (
    CategoryNotFoundError,
    CategoryValidationError,
    CategoryOwnershipError,
    CircularRelationshipError,
    CategoryDepthExceededError,
    CategoryNameConflictError
)

router = APIRouter(prefix="/categories", tags=["Categories"])

@router.post(
    "/", 
    response_model=CategoryOut, 
    status_code=status.HTTP_201_CREATED,
    summary="Create a new category",
    description="Create a new category with optional parent category for hierarchical organization",
    responses={
        201: {"description": "Category created successfully"},
        400: {"description": "Validation error or constraint violation"},
        401: {"description": "Unauthorized - invalid or missing token"},
        404: {"description": "Parent category not found"},
    }
)
def create_category(
    category: CategoryCreate,
    service: CategoryService = Depends(get_category_service),
    user_id: int = Depends(get_current_user_id)
) -> CategoryOut:
    """
    Create a new category.
    
    - **name**: Category name (minimum 3 characters)
    - **parent_id**: Optional parent category ID for hierarchical organization
    
    Returns the created category with its ID and user association.
    """
    return service.create(category, user_id)

@router.get(
    "/", 
    response_model=CategoryListResponse,
    summary="Get all categories",
    description="Retrieve all categories for the authenticated user, either as a hierarchical tree or flat list with pagination support",
    responses={
        200: {"description": "Categories retrieved successfully"},
        401: {"description": "Unauthorized - invalid or missing token"},
    }
)
def read_categories(
    flat: Annotated[bool, Query(description="Return flat list instead of hierarchical tree")] = False,
    page: Annotated[int, Query(description="Page number", ge=1)] = 1,
    size: Annotated[int, Query(description="Number of items per page", ge=1, le=100)] = 50,
    service: CategoryService = Depends(get_category_service),
    user_id: int = Depends(get_current_user_id)
) -> CategoryListResponse:
    """
    Get all categories for the authenticated user with pagination support.
    
    - **flat**: If true, returns a flat list of all categories
    - **flat**: If false, returns root categories with their children (hierarchical)
    - **page**: Page number (starts from 1)
    - **size**: Number of items per page (1-100, default 50)
    
    Returns paginated results with metadata including total count, current page, and total pages.
    """
    if flat:
        categories, total = service.get_all_flat(user_id, page, size)
    else:
        categories, total = service.get_all(user_id, page, size)
    
    pages = (total + size - 1) // size  # Calculate total pages
    
    return CategoryListResponse(
        items=categories,
        total=total,
        page=page,
        size=size,
        pages=pages
    )

@router.get(
    "/{category_id}", 
    response_model=CategoryOut,
    summary="Get category by ID",
    description="Retrieve a specific category by its ID",
    responses={
        200: {"description": "Category found"},
        401: {"description": "Unauthorized - invalid or missing token"},
        404: {"description": "Category not found"},
    }
)
def read_category(
    category_id: Annotated[int, Path(description="Category ID", gt=0)],
    service: CategoryService = Depends(get_category_service),
    user_id: int = Depends(get_current_user_id)
) -> CategoryOut:
    """
    Get a specific category by ID.
    
    Returns the category details if it exists and belongs to the authenticated user.
    """
    return service.get(category_id, user_id)

@router.get(
    "/{category_id}/children", 
    response_model=List[CategoryOut],
    summary="Get category children",
    description="Get direct children of a specific category",
    responses={
        200: {"description": "Children retrieved successfully"},
        401: {"description": "Unauthorized - invalid or missing token"},
        404: {"description": "Category not found"},
    }
)
def read_category_children(
    category_id: Annotated[int, Path(description="Category ID", gt=0)],
    service: CategoryService = Depends(get_category_service),
    user_id: int = Depends(get_current_user_id)
) -> List[CategoryOut]:
    """
    Get direct children of a category.
    
    Returns a list of categories that have the specified category as their parent.
    """
    return service.get_children(category_id, user_id)

@router.put(
    "/{category_id}", 
    response_model=CategoryOut,
    summary="Update category",
    description="Update an existing category's name and/or parent",
    responses={
        200: {"description": "Category updated successfully"},
        400: {"description": "Validation error or constraint violation"},
        401: {"description": "Unauthorized - invalid or missing token"},
        404: {"description": "Category or parent category not found"},
    }
)
def update_category(
    category_id: Annotated[int, Path(description="Category ID", gt=0)],
    updated: CategoryCreate,
    service: CategoryService = Depends(get_category_service),
    user_id: int = Depends(get_current_user_id)
) -> CategoryOut:
    """
    Update an existing category.
    
    - **name**: New category name (minimum 3 characters)
    - **parent_id**: New parent category ID (can be null for root category)
    
    Validates against circular relationships and name uniqueness.
    """
    return service.update(category_id, updated, user_id)

@router.delete(
    "/{category_id}",
    summary="Delete category",
    description="Delete a category (only if it has no children)",
    responses={
        200: {"description": "Category deleted successfully"},
        400: {"description": "Cannot delete category with children"},
        401: {"description": "Unauthorized - invalid or missing token"},
        404: {"description": "Category not found"},
    }
)
def delete_category(
    category_id: Annotated[int, Path(description="Category ID", gt=0)],
    service: CategoryService = Depends(get_category_service),
    user_id: int = Depends(get_current_user_id)
) -> dict:
    """
    Delete a category.
    
    The category must not have any children. Delete child categories first.
    """
    return service.delete(category_id, user_id)