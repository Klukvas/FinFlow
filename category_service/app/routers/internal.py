from fastapi import APIRouter, Depends, status, Query, Path, Request, HTTPException
from typing import Annotated

from app.schemas.category import CategoryOut
from app.services.category import CategoryService
from app.dependencies import verify_internal_token, get_category_service_internal
from app.exceptions import CategoryNotFoundError, CategoryOwnershipError
from app.utils.logger import get_logger, log_operation

# Create a separate router for internal endpoints
internal_router = APIRouter(prefix="/internal", tags=["Internal"])
logger = get_logger(__name__)


@internal_router.get(
    "/categories/{category_id}",
    response_model=CategoryOut,
    summary="Get category for internal validation",
    description="Internal endpoint for other services to validate category ownership and retrieve category details",
    responses={
        200: {"description": "Category found and belongs to user"},
        403: {"description": "Invalid internal token or unauthorized access"},
        404: {"description": "Category not found"},
    }
)
async def get_category_internal(
    category_id: Annotated[int, Path(description="Category ID to validate", gt=0)],
    user_id: Annotated[int, Query(description="User ID to validate ownership", gt=0)],
    category_service: CategoryService = Depends(get_category_service_internal),
    _: None = Depends(verify_internal_token)
) -> CategoryOut:
    """
    Internal endpoint for other services to validate category ownership.
    
    This endpoint is used by other microservices to:
    - Validate that a category exists
    - Verify that the category belongs to the specified user
    - Retrieve category details for internal processing
    
    Args:
        category_id: The ID of the category to validate
        user_id: The ID of the user who should own the category
        category_service: Injected category service instance
        
    Returns:
        CategoryOut: The category details if found and owned by user
        
    Raises:
        HTTPException: 403 if invalid internal token or unauthorized access
        HTTPException: 404 if category not found
    """
    try:
        # Use the service method for proper validation and error handling
        category = category_service.get_by_id_internal(category_id, user_id)
        
        log_operation(
            logger,
            "Internal category validation",
            user_id,
            category_id,
            f"Category '{category.name}' validated successfully"
        )
        
        return category
        
    except (CategoryNotFoundError, CategoryOwnershipError) as e:
        # These exceptions already have proper HTTP status codes
        raise e
    except Exception as e:
        logger.error(f"Unexpected error in internal category validation: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error while validating category"
        )
