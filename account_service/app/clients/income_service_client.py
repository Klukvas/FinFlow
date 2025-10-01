from fastapi import HTTPException
from app.clients.base import BaseHttpClient
from starlette import status
from app.exceptions import ExternalServiceError
from app.config import settings
from app.utils.logger import get_logger, log_security_event
from typing import Dict, Any, List

class IncomeServiceClient(BaseHttpClient):
    def __init__(self):
        super().__init__(base_url=settings.income_service_url)
        self.logger = get_logger(__name__)

    def get_incomes_by_account(self, account_id: int, user_id: int, limit: int = 100, offset: int = 0) -> List[Dict[str, Any]]:
        """
        Get incomes for a specific account.
        
        Args:
            account_id: The ID of the account
            user_id: The ID of the user
            limit: Maximum number of incomes to return
            offset: Number of incomes to skip
            
        Returns:
            List of income dictionaries
            
        Raises:
            HTTPException: If the request fails
        """
        try:
            response = self.get(
                f"/internal/incomes/account/{account_id}",
                headers={"X-Internal-Token": settings.internal_secret_token},
                params={"user_id": user_id, "limit": limit, "offset": offset}
            )
            
            if response.status_code == status.HTTP_404_NOT_FOUND:
                log_security_event(
                    self.logger,
                    "Incomes not found for account",
                    user_id,
                    f"Account ID: {account_id}"
                )
                return []
            
            if response.status_code != status.HTTP_200_OK:
                self.logger.error(f"Unexpected response from income service: {response.status_code}")
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail="Failed to fetch incomes"
                )
            
            return response.json()
            
        except HTTPException:
            raise
        except Exception as e:
            self.logger.error(f"Unexpected error during income fetch: {e}")
            raise ExternalServiceError(
                service="income-service",
                detail=f"Failed to fetch incomes: {str(e)}"
            )

    def validate_account_exists(self, account_id: int, user_id: int) -> bool:
        """
        Validate that an account exists and belongs to the user.
        
        Args:
            account_id: The ID of the account to validate
            user_id: The ID of the user who should own the account
            
        Returns:
            True if account exists and belongs to user, False otherwise
        """
        try:
            response = self.get(
                f"/internal/incomes/account/{account_id}/validate",
                headers={"X-Internal-Token": settings.internal_secret_token},
                params={"user_id": user_id}
            )
            
            return response.status_code == status.HTTP_200_OK
            
        except Exception as e:
            self.logger.error(f"Error validating account with income service: {e}")
            return False
