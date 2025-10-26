from fastapi import APIRouter, Depends, Query
from typing import Optional, Annotated

from app.schemas.category import DefaultCategoryListResponse, MCCCodeListResponse, SupportedLanguage
from app.services.mcc_categories import DefaultCategoryService
from app.dependencies import get_default_category_service, get_current_user_id

router = APIRouter(prefix="/mcc", tags=["MCC Codes"])

@router.get(
    "/defaults",
    response_model=DefaultCategoryListResponse,
    summary="Get default MCC categories",
    description="Retrieve all default MCC categories with optional translations",
    responses={
        200: {"description": "Default categories retrieved successfully"},
        401: {"description": "Unauthorized - invalid or missing token"},
    }
)
def get_default_categories(
    language: Annotated[Optional[SupportedLanguage], Query(description="Language code for translations (ru, uk, en)")] = None,
    service: DefaultCategoryService = Depends(get_default_category_service),
    user_id: int = Depends(get_current_user_id)
) -> DefaultCategoryListResponse:
    """
    Get all default MCC categories with optional translations.
    
    - **language**: Language code ('ru', 'uk', 'en') to get translated names.
                   If not provided or 'en', returns English names.
    
    Returns a list of default categories that users can use as templates for creating their own categories.
    If language is provided, translations will be included when available.
    """
    categories = service.get_default_categories(language.value if language else None)
    
    return DefaultCategoryListResponse(
        items=categories,
        total=len(categories),
        language=language
    )

@router.get(
    "/codes",
    response_model=MCCCodeListResponse,
    summary="Get all MCC codes",
    description="Retrieve all MCC codes with optional translations",
    responses={
        200: {"description": "All MCC codes retrieved successfully"},
        401: {"description": "Unauthorized - invalid or missing token"},
    }
)
def get_all_mcc_codes(
    language: Annotated[Optional[SupportedLanguage], Query(description="Language code for translations (ru, uk, en)")] = None,
    service: DefaultCategoryService = Depends(get_default_category_service),
    user_id: int = Depends(get_current_user_id)
) -> MCCCodeListResponse:
    """
    Get all MCC codes with optional translations.
    
    - **language**: Language code ('ru', 'uk', 'en') to get translated names.
                   If not provided or 'en', returns English names.
    
    Returns a list of all MCC codes (both default and non-default) that can be used
    for creating categories. If language is provided, translations will be included when available.
    """
    mcc_codes = service.get_all_mcc_codes(language.value if language else None)
    
    return MCCCodeListResponse(
        items=mcc_codes,
        total=len(mcc_codes),
        language=language
    )
