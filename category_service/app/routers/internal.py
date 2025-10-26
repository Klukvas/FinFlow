from fastapi import APIRouter, Depends, status, Query, Path, Request, HTTPException
from typing import Annotated

from app.schemas.category import CategoryOut, MCCCodeListResponse, DefaultCategoryListResponse, SupportedLanguage
from app.services.category import CategoryService
from app.services.mcc_categories import DefaultCategoryService
from app.dependencies import verify_internal_token, get_category_service_internal, get_default_category_service
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


@internal_router.get(
    "/mcc/codes",
    response_model=MCCCodeListResponse,
    summary="Get all MCC codes for internal services",
    description="Internal endpoint for other services to retrieve MCC codes with translations",
    responses={
        200: {"description": "MCC codes retrieved successfully"},
        403: {"description": "Invalid internal token"},
    }
)
async def get_mcc_codes_internal(
    language: Annotated[SupportedLanguage, Query(description="Language code for translations (ru, uk, en)")] = SupportedLanguage.en,
    service: DefaultCategoryService = Depends(get_default_category_service),
    _: None = Depends(verify_internal_token)
) -> MCCCodeListResponse:
    """
    Internal endpoint for other services to retrieve MCC codes.
    
    This endpoint is used by other microservices to:
    - Get all MCC codes with translations
    - Retrieve category information for PDF parsing
    
    Args:
        language: Language code for translations
        service: Injected MCC service instance
        
    Returns:
        MCCCodeListResponse: List of MCC codes with translations
        
    Raises:
        HTTPException: 403 if invalid internal token
    """
    try:
        logger.info(f"Language parameter: {language}, value: {language.value}")
        language_value = language.value
        logger.info(f"Language value to pass: {language_value}")
        mcc_codes = service.get_all_mcc_codes(language_value)
        
        log_operation(
            logger,
            "Internal MCC codes retrieval",
            0,  # Internal service call
            None,
            f"Retrieved {len(mcc_codes)} MCC codes for language {language.value}"
        )
        
        return MCCCodeListResponse(
            items=mcc_codes,
            total=len(mcc_codes),
            language=language
        )
        
    except Exception as e:
        logger.error(f"Unexpected error in internal MCC codes retrieval: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error while retrieving MCC codes"
        )


@internal_router.get(
    "/mcc/defaults",
    response_model=DefaultCategoryListResponse,
    summary="Get default MCC categories for internal services",
    description="Internal endpoint for other services to retrieve default MCC categories with translations",
    responses={
        200: {"description": "Default MCC categories retrieved successfully"},
        403: {"description": "Invalid internal token"},
    }
)
async def get_default_categories_internal(
    language: Annotated[SupportedLanguage, Query(description="Language code for translations (ru, uk, en)")] = SupportedLanguage.en,
    service: DefaultCategoryService = Depends(get_default_category_service),
    _: None = Depends(verify_internal_token)
) -> DefaultCategoryListResponse:
    """
    Internal endpoint for other services to retrieve default MCC categories.
    
    This endpoint is used by other microservices to:
    - Get default MCC categories with translations
    - Retrieve category templates for PDF parsing
    
    Args:
        language: Language code for translations
        service: Injected MCC service instance
        
    Returns:
        DefaultCategoryListResponse: List of default MCC categories with translations
        
    Raises:
        HTTPException: 403 if invalid internal token
    """
    try:
        categories = service.get_default_categories(language.value)
        
        log_operation(
            logger,
            "Internal default categories retrieval",
            0,  # Internal service call
            None,
            f"Retrieved {len(categories)} default categories for language {language.value}"
        )
        
        return DefaultCategoryListResponse(
            items=categories,
            total=len(categories),
            language=language
        )
        
    except Exception as e:
        logger.error(f"Unexpected error in internal default categories retrieval: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error while retrieving default categories"
        )


@internal_router.get(
    "/categories/check-mcc/{mcc_code}",
    summary="Check if user has category with MCC code",
    description="Internal endpoint to check if user already has a category with the given MCC code",
    responses={
        200: {"description": "Category existence check completed"},
        403: {"description": "Invalid internal token"},
    }
)
async def check_category_exists_by_mcc(
    mcc_code: Annotated[int, Path(description="MCC code to check", gt=0)],
    user_id: Annotated[int, Query(description="User ID to check", gt=0)],
    category_service: CategoryService = Depends(get_category_service_internal),
    _: None = Depends(verify_internal_token)
) -> dict:
    """
    Internal endpoint to check if user has a category with the given MCC code.
    
    This endpoint is used by other microservices to:
    - Check if user already has a category with specific MCC code
    - Determine if new category needs to be created
    
    Args:
        mcc_code: MCC code to check
        user_id: User ID to check
        category_service: Injected category service instance
        
    Returns:
        dict: {"exists": bool} - whether category exists
        
    Raises:
        HTTPException: 403 if invalid internal token
    """
    try:
        exists = category_service.check_category_exists_by_mcc(mcc_code, user_id)
        
        log_operation(
            logger,
            "Internal category existence check",
            user_id,
            mcc_code,
            f"Category with MCC {mcc_code} {'exists' if exists else 'does not exist'}"
        )
        
        return {"exists": exists}
        
    except Exception as e:
        logger.error(f"Unexpected error in internal category existence check: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error while checking category existence"
        )


@internal_router.post(
    "/categories/check-mcc-batch",
    summary="Check multiple MCC codes for user categories",
    description="Internal endpoint to check multiple MCC codes for user categories in a single request",
    responses={
        200: {"description": "Batch MCC check completed"},
        403: {"description": "Invalid internal token"},
    }
)
async def check_categories_exist_by_mcc_batch(
    request: dict,
    category_service: CategoryService = Depends(get_category_service_internal),
    _: None = Depends(verify_internal_token)
) -> dict:
    """
    Internal endpoint to check multiple MCC codes for user categories.
    
    This endpoint is used by other microservices to:
    - Check multiple MCC codes in a single request
    - Reduce API calls and improve performance
    
    Args:
        request: {"mcc_codes": [int], "user_id": int}
        
    Returns:
        dict: {"results": [{"mcc_code": int, "exists": bool, "category_id": int|null}]}
    """
    try:
        mcc_codes = request.get("mcc_codes", [])
        user_id = request.get("user_id")
        
        if not mcc_codes or not user_id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="mcc_codes and user_id are required"
            )
        
        results = category_service.check_categories_exist_by_mcc_batch(mcc_codes, user_id)
        
        log_operation(
            logger,
            "Internal batch MCC category existence check",
            user_id,
            len(mcc_codes),
            f"Checked {len(mcc_codes)} MCC codes"
        )
        
        return {"results": results}
        
    except Exception as e:
        logger.error(f"Unexpected error in batch MCC category existence check: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error while checking MCC codes"
        )

@internal_router.get(
    "/categories/get-by-mcc/{mcc_code}",
    summary="Get category info by MCC code",
    description="Internal endpoint to get category information including ID by MCC code",
    responses={
        200: {"description": "Category information retrieved successfully"},
        403: {"description": "Invalid internal token"},
        404: {"description": "Category not found"},
    }
)
async def get_category_by_mcc(
    mcc_code: Annotated[int, Path(description="MCC code to check", gt=0)],
    user_id: Annotated[int, Query(description="User ID to check", gt=0)],
    category_service: CategoryService = Depends(get_category_service_internal),
    _: None = Depends(verify_internal_token)
) -> dict:
    """
    Internal endpoint to get category information by MCC code.
    
    This endpoint is used by other microservices to:
    - Get category ID if user has a category with specific MCC code
    - Retrieve category information for PDF parsing
    
    Args:
        mcc_code: MCC code to check
        user_id: User ID to check
        category_service: Injected category service instance
        
    Returns:
        dict: {"exists": bool, "category_id": int|null} - category existence and ID
        
    Raises:
        HTTPException: 403 if invalid internal token
    """
    try:
        category_info = category_service.get_category_by_mcc(mcc_code, user_id)
        
        log_operation(
            logger,
            "Internal category retrieval by MCC",
            user_id,
            mcc_code,
            f"Category with MCC {mcc_code} {'found' if category_info['exists'] else 'not found'}"
        )
        
        return category_info
        
    except Exception as e:
        logger.error(f"Unexpected error in internal category retrieval by MCC: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error while retrieving category by MCC"
        )
