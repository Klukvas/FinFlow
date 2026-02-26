from fastapi import APIRouter, Depends, status, Query, Path
from typing import List, Annotated, Optional
from uuid import UUID

from app.schemas.category import CategoryCreate, CategoryCreateFromMCC, CategoryCreateFromMCCBatch, CategoryBatchCreateResponse, CategoryOut, CategoryListResponse, SupportedLanguage, CategoryStatisticsResponse
from app.services.category import CategoryService
from app.dependencies import get_category_service, get_current_user_id, get_workspace_id
from app.exceptions import (
    CategoryNotFoundError,
    CategoryValidationError,
    CategoryOwnershipError,
    CircularRelationshipError,
    CategoryDepthExceededError,
    CategoryNameConflictError,
    CategoryLimitExceededError
)
from app.utils.logger import get_logger

router = APIRouter(prefix="/categories", tags=["Categories"])
logger = get_logger(__name__)

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
    user_id: int = Depends(get_current_user_id),
    workspace_id: UUID = Depends(get_workspace_id)
) -> CategoryOut:
    """
    Create a new category.
    
    - **name**: Category name (minimum 3 characters)
    - **parent_id**: Optional parent category ID for hierarchical organization
    
    Requires X-Workspace-Id header with workspace UUID.
    Returns the created category with its ID and user association.
    """
    logger.info(
        f"[ROUTER] POST /categories - Creating category",
        category="api",
        operation="create_category_endpoint",
        user_id=user_id,
        workspace_id=str(workspace_id),
        category_name=category.name,
        category_type=category.type.value if hasattr(category.type, 'value') else str(category.type),
        parent_id=category.parent_id,
        category_data=category.dict() if hasattr(category, 'dict') else str(category)
    )
    
    try:
        result = service.create(category, user_id, workspace_id)
        
        logger.info(
            f"[ROUTER] POST /categories - Category created successfully",
            category="api",
            operation="create_category_success",
            user_id=user_id,
            workspace_id=str(workspace_id),
            category_id=result.id,
            category_name=result.name
        )
        
        return result
    except Exception as e:
        logger.error(
            f"[ROUTER] POST /categories - Failed to create category: {e.__class__.__name__}",
            category="api",
            operation="create_category_error",
            user_id=user_id,
            workspace_id=str(workspace_id),
            exception_type=e.__class__.__name__,
            exception_message=str(e),
            category_data=category.dict() if hasattr(category, 'dict') else str(category)
        )
        raise

@router.post(
    "/from-mcc", 
    response_model=CategoryOut, 
    status_code=status.HTTP_201_CREATED,
    summary="Create a category from MCC code",
    description="Create a new category based on a Merchant Category Code (MCC) with optional custom name and translations",
    responses={
        201: {"description": "Category created successfully from MCC"},
        400: {"description": "Validation error, MCC code not found, or category already exists"},
        401: {"description": "Unauthorized - invalid or missing token"},
        404: {"description": "Parent category not found"},
    }
)
def create_category_from_mcc(
    category: CategoryCreateFromMCC,
    language: Annotated[Optional[SupportedLanguage], Query(description="Language for MCC translation (ru, uk, en)")] = None,
    service: CategoryService = Depends(get_category_service),
    user_id: int = Depends(get_current_user_id),
    workspace_id: UUID = Depends(get_workspace_id)
) -> CategoryOut:
    """
    Create a new category from an MCC code.
    
    - **mcc_code**: MCC code to create category from (1-9999)
    - **parent_id**: Optional parent category ID for hierarchical organization
    - **type**: Category type - expense or income (default: expense)
    - **custom_name**: Optional custom name override. If not provided, uses MCC translation or English name
    - **language**: Language code for MCC translation ('ru', 'uk', 'en')
    
    The system will automatically:
    - Use the translated name if language is provided and translation exists
    - Fall back to English name if no translation is available
    - Use custom_name if provided (overrides translation)
    - Mark the category as system-created (created_by: SYSTEM)
    - Prevent duplicate categories for the same MCC code per user
    
    Requires X-Workspace-Id header with workspace UUID.
    Returns the created category with its ID and user association.
    """
    return service.create_from_mcc(category, user_id, workspace_id, language.value if language else None)

@router.post(
    "/from-mcc/batch", 
    response_model=CategoryBatchCreateResponse, 
    status_code=status.HTTP_201_CREATED,
    summary="Create multiple categories from MCC codes",
    description="Create multiple categories from MCC codes in a single request with comprehensive error handling",
    responses={
        201: {"description": "Batch category creation completed (check individual results)"},
        400: {"description": "Validation error or duplicate MCC codes in batch"},
        401: {"description": "Unauthorized - invalid or missing token"},
        422: {"description": "Invalid request data"},
    }
)
def create_categories_from_mcc_batch(
    batch_data: CategoryCreateFromMCCBatch,
    service: CategoryService = Depends(get_category_service),
    user_id: int = Depends(get_current_user_id),
    workspace_id: UUID = Depends(get_workspace_id)
) -> CategoryBatchCreateResponse:
    """
    Create multiple categories from MCC codes in a single request.
    
    - **categories**: List of MCC-based categories to create (1-50 items)
    - **language**: Default language for all categories (optional)
    
    Each category in the batch can have:
    - **mcc_code**: MCC code to create category from (1-9999)
    - **parent_id**: Optional parent category ID for hierarchical organization
    - **type**: Category type - expense or income (default: expense)
    - **custom_name**: Optional custom name override
    
    The batch operation:
    - Processes each category individually
    - Continues processing even if some categories fail
    - Returns detailed results for each category creation attempt
    - Prevents duplicate MCC codes within the same batch
    - Uses batch language as default for all categories
    - Respects subscription limits per category
    
    Returns a comprehensive response with:
    - Individual results for each category
    - Summary statistics (total, successful, failed)
    - Detailed error messages for failed categories
    
    Requires X-Workspace-Id header with workspace UUID.
    """
    return service.create_from_mcc_batch(batch_data, user_id, workspace_id)

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
    user_id: int = Depends(get_current_user_id),
    workspace_id: UUID = Depends(get_workspace_id)
) -> CategoryListResponse:
    """
    Get all categories for the authenticated user with pagination support.
    
    - **flat**: If true, returns a flat list of all categories
    - **flat**: If false, returns root categories with their children (hierarchical)
    - **page**: Page number (starts from 1)
    - **size**: Number of items per page (1-100, default 50)
    
    Requires X-Workspace-Id header with workspace UUID.
    Returns paginated results with metadata including total count, current page, and total pages.
    """
    if flat:
        categories, total = service.get_all_flat(user_id, workspace_id, page, size)
    else:
        categories, total = service.get_all(user_id, workspace_id, page, size)
    
    pages = (total + size - 1) // size  # Calculate total pages
    
    return CategoryListResponse(
        items=categories,
        total=total,
        page=page,
        size=size,
        pages=pages
    )

@router.get(
    "/statistics", 
    response_model=CategoryStatisticsResponse,
    summary="Get category statistics",
    description="Get statistics about the authenticated user's categories including counts by type and hierarchy",
    responses={
        200: {"description": "Statistics retrieved successfully"},
        401: {"description": "Unauthorized - invalid or missing token"},
    }
)
def get_category_statistics(
    service: CategoryService = Depends(get_category_service),
    user_id: int = Depends(get_current_user_id),
    workspace_id: UUID = Depends(get_workspace_id)
) -> CategoryStatisticsResponse:
    """
    Get category statistics for the authenticated user.
    
    Returns:
    - **total_categories**: Total number of categories
    - **expense_categories**: Number of expense categories
    - **income_categories**: Number of income categories
    - **parent_categories**: Number of parent categories (categories without a parent)
    - **child_categories**: Number of child categories (categories with a parent)
    
    Requires X-Workspace-Id header with workspace UUID.
    """
    statistics = service.get_statistics(user_id, workspace_id)
    return CategoryStatisticsResponse(**statistics)

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
    user_id: int = Depends(get_current_user_id),
    workspace_id: UUID = Depends(get_workspace_id)
) -> CategoryOut:
    """
    Get a specific category by ID.
    
    Requires X-Workspace-Id header with workspace UUID.
    Returns the category details if it exists and belongs to the authenticated user.
    """
    return service.get(category_id, user_id, workspace_id)

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
    user_id: int = Depends(get_current_user_id),
    workspace_id: UUID = Depends(get_workspace_id)
) -> List[CategoryOut]:
    """
    Get direct children of a category.
    
    Requires X-Workspace-Id header with workspace UUID.
    Returns a list of categories that have the specified category as their parent.
    """
    return service.get_children(category_id, user_id, workspace_id)

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
    user_id: int = Depends(get_current_user_id),
    workspace_id: UUID = Depends(get_workspace_id)
) -> CategoryOut:
    """
    Update an existing category.
    
    - **name**: New category name (minimum 3 characters)
    - **parent_id**: New parent category ID (can be null for root category)
    
    Requires X-Workspace-Id header with workspace UUID.
    Validates against circular relationships and name uniqueness.
    """
    return service.update(category_id, updated, user_id, workspace_id)

@router.delete(
    "/{category_id}",
    status_code=204,
    summary="Delete category",
    description="Delete a category (only if it has no children)",
    responses={
        204: {"description": "Category deleted successfully"},
        400: {"description": "Cannot delete category with children"},
        401: {"description": "Unauthorized - invalid or missing token"},
        404: {"description": "Category not found"},
    }
)
def delete_category(
    category_id: Annotated[int, Path(description="Category ID", gt=0)],
    service: CategoryService = Depends(get_category_service),
    user_id: int = Depends(get_current_user_id),
    workspace_id: UUID = Depends(get_workspace_id)
):
    """
    Delete a category.

    Requires X-Workspace-Id header with workspace UUID.
    The category must not have any children. Delete child categories first.
    """
    service.delete(category_id, user_id, workspace_id)