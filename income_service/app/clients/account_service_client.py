from fastapi import HTTPException
from app.clients.base import BaseHttpClient
from starlette import status
from app.exceptions import ExternalServiceError
from app.config import settings
from app.utils.logger import get_logger, log_security_event
from typing import Dict, Any

class AccountServiceClient(BaseHttpClient):
    def __init__(self):
        super().__init__(base_url=settings.account_service_url)
        self.logger = get_logger(__name__)

    async def validate_account(self, account_id: int, user_id: int) -> Dict[str, Any]:
        """
        Validate that an account exists and belongs to the user.
        
        Args:
            account_id: The ID of the account to validate
            user_id: The ID of the user who should own the account
            
        Returns:
            Dict containing account information if valid
            
        Raises:
            HTTPException: If account validation fails
        """
        try:
            response = await self.get(
                f"/internal/accounts/{account_id}/validate?user_id={user_id}",
                headers={"X-Internal-Token": settings.internal_secret}
            )
            
            if response.status_code == status.HTTP_404_NOT_FOUND:
                log_security_event(
                    self.logger,
                    "Account validation failed - not found",
                    user_id,
                    f"Account ID: {account_id}"
                )
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST, 
                    detail="Account not found or not owned by user"
                )
            
            if response.status_code == status.HTTP_403_FORBIDDEN:
                log_security_event(
                    self.logger,
                    "Account validation failed - unauthorized access",
                    user_id,
                    f"Account ID: {account_id}"
                )
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Account not owned by user"
                )
            
            if response.status_code != status.HTTP_200_OK:
                self.logger.error(f"Unexpected response from account service: {response.status_code}")
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail="Account validation service error"
                )
            
            # Parse and return account data
            account_data = response.json()
            self.logger.info(f"Account {account_id} validated successfully for user {user_id}")
            return account_data
            
        except HTTPException:
            # Re-raise HTTP exceptions as-is
            raise
        except Exception as e:
            self.logger.error(f"Unexpected error during account validation: {e}")
            raise ExternalServiceError(
                service="account-service",
                detail=f"Failed to validate account: {str(e)}"
            )

    async def update_account_balance(self, account_id: int, user_id: int, amount_change: float, transaction_currency: str = "USD") -> Dict[str, Any]:
        """
        Update account balance by adding/subtracting an amount with automatic currency conversion.
        
        Args:
            account_id: The ID of the account to update
            user_id: The ID of the user who owns the account
            amount_change: The amount to add (positive) or subtract (negative)
            transaction_currency: The currency of the transaction (default: USD)
            
        Returns:
            Dict containing updated account information
            
        Raises:
            HTTPException: If account update fails
        """
        try:
            response = await self.put(
                f"/internal/accounts/{account_id}/balance",
                headers={"X-Internal-Token": settings.internal_secret},
                params={
                    "user_id": user_id, 
                    "amount_change": amount_change,
                    "transaction_currency": transaction_currency
                }
            )
            
            if response.status_code == status.HTTP_404_NOT_FOUND:
                log_security_event(
                    self.logger,
                    "Account balance update failed - not found",
                    user_id,
                    f"Account ID: {account_id}"
                )
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST, 
                    detail="Account not found or not owned by user"
                )
            
            if response.status_code == status.HTTP_400_BAD_REQUEST:
                log_security_event(
                    self.logger,
                    "Account balance update failed - insufficient funds",
                    user_id,
                    f"Account ID: {account_id}, Amount: {amount_change}"
                )
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Insufficient funds in account"
                )
            
            if response.status_code != status.HTTP_200_OK:
                self.logger.error(f"Unexpected response from account service: {response.status_code}")
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail="Account balance update service error"
                )
            
            # Parse and return account data
            account_data = response.json()
            self.logger.info(f"Account {account_id} balance updated by {amount_change} for user {user_id}")
            return account_data
            
        except HTTPException:
            # Re-raise HTTP exceptions as-is
            raise
        except Exception as e:
            self.logger.error(f"Unexpected error during account balance update: {e}")
            raise ExternalServiceError(
                service="account-service",
                detail=f"Failed to update account balance: {str(e)}"
            )
