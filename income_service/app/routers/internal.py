from datetime import datetime, timedelta, timezone

from fastapi import APIRouter, Depends, Query, HTTPException, status
from typing import Annotated, List
from uuid import UUID

from app.schemas.income import IncomeCreate, IncomeOut
from app.services.income import IncomeService
from app.dependencies import verify_internal_token, get_income_service_internal
from app.utils.logger import get_logger
from app.models.income import Income
from app.exceptions import IncomeErrorCodes, IncomeLimitExceededError

# Create a separate router for internal endpoints
router = APIRouter(prefix="/internal", tags=["Internal"])
logger = get_logger(__name__)


@router.post(
    '/',
    response_model=IncomeOut,
    summary="Create income for internal use",
    description="Internal endpoint for other services to create incomes",
    responses={
        200: {"description": "Income created successfully"},
        400: {"description": "Invalid income data"},
        403: {"description": "Invalid internal token or unauthorized access"},
        429: {"description": "Subscription income limit exceeded"},
    }
)
async def internal_income_create(
    income: IncomeCreate,
    user_id: Annotated[int, Query(description="User ID to validate ownership", gt=0)],
    workspace_id: Annotated[UUID, Query(description="Workspace ID for the income")],
    service: IncomeService = Depends(get_income_service_internal),
    _: None = Depends(verify_internal_token)
) -> IncomeOut:
    """
    Internal endpoint for other services to create incomes.

    This endpoint is used by other microservices (e.g. recurring_service) to
    create incomes on behalf of users.
    """
    try:
        created_income = await service.create(income, user_id, workspace_id)

        logger.info(f"Internal income created: {created_income.id} for user {user_id}")

        return created_income

    except IncomeLimitExceededError as e:
        logger.warning(f"Income limit exceeded for user {user_id}: {e}")
        raise HTTPException(
            status_code=429,
            detail={"error_code": "INCOME_LIMIT_EXCEEDED", "message": str(e)}
        )
    except Exception as e:
        logger.error(f"Unexpected error in internal income creation: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error while creating income"
        )


@router.get(
    '/incomes/account/{account_id}',
    response_model=List[IncomeOut],
    summary="Get incomes by account",
    description="Internal endpoint to get incomes for a specific account",
    responses={
        200: {"description": "Incomes retrieved successfully"},
        403: {"description": "Invalid internal token"},
        404: {"description": "Account not found"},
    }
)
async def get_incomes_by_account(
    account_id: int,
    user_id: Annotated[int, Query(description="User ID to validate ownership", gt=0)],
    workspace_id: Annotated[UUID, Query(..., description="Workspace ID")],
    limit: Annotated[int, Query(description="Maximum number of incomes to return", ge=1, le=1000)] = 100,
    offset: Annotated[int, Query(description="Number of incomes to skip", ge=0)] = 0,
    service: IncomeService = Depends(get_income_service_internal),
    _: None = Depends(verify_internal_token)
) -> List[IncomeOut]:
    """
    Internal endpoint to get incomes for a specific account.
    """
    try:
        filters = [
            Income.account_id == account_id,
            Income.user_id == user_id,
            Income.workspace_id == workspace_id,
        ]
        incomes = service.db.query(Income).filter(*filters).order_by(Income.date.desc()).offset(offset).limit(limit).all()

        logger.info(f"Retrieved {len(incomes)} incomes for account {account_id} and user {user_id}")

        return [IncomeOut.model_validate(income) for income in incomes]

    except Exception as e:
        logger.error(f"Unexpected error retrieving incomes by account: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error while retrieving incomes"
        )


@router.get(
    '/incomes/account/{account_id}/validate',
    summary="Validate account for incomes",
    description="Internal endpoint to validate that an account can be used for incomes",
    responses={
        200: {"description": "Account is valid for incomes"},
        403: {"description": "Invalid internal token"},
        404: {"description": "Account not found or not owned by user"},
    }
)
async def validate_account_for_incomes(
    account_id: int,
    user_id: Annotated[int, Query(description="User ID to validate ownership", gt=0)],
    service: IncomeService = Depends(get_income_service_internal),
    _: None = Depends(verify_internal_token)
) -> dict:
    """
    Internal endpoint to validate that an account can be used for incomes.
    """
    try:
        account_data = await service.account_client.validate_account(account_id, user_id)

        logger.info(f"Account {account_id} validated successfully for user {user_id}")

        return {
            "valid": True,
            "account_id": account_id,
            "user_id": user_id,
            "account": account_data.get("account", {})
        }

    except Exception as e:
        logger.error(f"Account validation failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Account not found or not owned by user"
        )


@router.get(
    '/incomes/ai-summary',
    summary="Get income summary for AI analysis",
    description="Internal endpoint returning aggregated income data for AI assistant analysis",
    responses={
        200: {"description": "Income summary retrieved successfully"},
        403: {"description": "Invalid internal token"},
    }
)
async def get_incomes_ai_summary(
    user_id: Annotated[int, Query(description="User ID", gt=0)],
    workspace_id: Annotated[UUID, Query(description="Workspace ID")],
    service: IncomeService = Depends(get_income_service_internal),
    _: None = Depends(verify_internal_token),
) -> dict:
    """
    Internal endpoint returning last 3 months of incomes for AI analysis.

    Returns aggregated data without PII for the AI assistant to analyze
    income patterns and provide financial insights.
    """
    try:
        three_months_ago = datetime.now(timezone.utc) - timedelta(days=90)
        incomes = (
            service.db.query(Income)
            .filter(
                Income.user_id == user_id,
                Income.workspace_id == workspace_id,
                Income.date >= three_months_ago,
            )
            .order_by(Income.date.desc())
            .limit(500)
            .all()
        )
        return {
            "items": [
                {
                    "amount": float(i.amount),
                    "category_id": i.category_id,
                    "currency": i.currency,
                    "date": str(i.date),
                }
                for i in incomes
            ]
        }
    except Exception as e:
        logger.error(f"Error fetching incomes AI summary: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve incomes summary",
        )
