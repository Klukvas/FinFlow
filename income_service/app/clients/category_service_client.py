from fastapi import HTTPException
from app.clients.base import BaseHttpClient
from starlette import status
from app.exceptions import IncomeValidationError, ExternalServiceError
from app.config import settings
from app.utils.logger import get_logger, log_security_event
from typing import Dict, Any

class CategoryServiceClient(BaseHttpClient):
    def __init__(self):
        super().__init__(base_url=settings.CATEGORY_SERVICE_URL)
        self.logger = get_logger(__name__)

    async def validate_category(self, category_id: int, user_id: int) -> Dict[str, Any]:
        """
        Validate that a category exists and belongs to the user.
        
        Args:
            category_id: The ID of the category to validate
            user_id: The ID of the user who should own the category
            
        Returns:
            Dict containing category information if valid
            
        Raises:
            HTTPException: If category validation fails
        """
        try:
            headers = {
                "Content-Type": "application/json",
                "X-Internal-Token": settings.INTERNAL_SECRET_TOKEN
            }
            
            response = await self.get(
                f"/internal/categories/{category_id}?user_id={user_id}",
                headers=headers
            )
            
            if response.status_code == status.HTTP_404_NOT_FOUND:
                log_security_event(
                    self.logger,
                    "Category validation failed - not found",
                    user_id,
                    f"Category ID: {category_id}"
                )
                raise IncomeValidationError("Category not found")
            
            if response.status_code == status.HTTP_403_FORBIDDEN:
                log_security_event(
                    self.logger,
                    "Category validation failed - unauthorized access",
                    user_id,
                    f"Category ID: {category_id}"
                )
                raise IncomeValidationError("Category does not belong to user")
            
            if response.status_code != status.HTTP_200_OK:
                self.logger.error(f"Unexpected response from category service: {response.status_code}")
                raise IncomeValidationError("Category validation service error")
            
            # Parse and return category data
            category_data = response.json()
            self.logger.info(f"Category {category_id} validated successfully for user {user_id}")
            return category_data
            
        except HTTPException:
            # Re-raise HTTP exceptions as-is
            raise
        except Exception as e:
            self.logger.error(f"Unexpected error during category validation: {e}")
            raise ExternalServiceError(
                service="category-service",
                detail=f"Failed to validate category: {str(e)}"
            )
