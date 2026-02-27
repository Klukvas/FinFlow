import logging

from fastapi import APIRouter, Depends, HTTPException, Query, status
from typing import Annotated
from uuid import UUID
from sqlalchemy.orm import Session

from app.dependencies import verify_internal_token
from app.models.debt import Debt
from app.database import get_db

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/internal", tags=["Internal"])


@router.get(
    '/debts/ai-summary',
    summary="Get debts summary for AI analysis",
    description="Internal endpoint returning aggregated debt data for AI assistant analysis",
    responses={
        200: {"description": "Debts summary retrieved successfully"},
        403: {"description": "Invalid internal token"},
    }
)
async def get_debts_ai_summary(
    user_id: Annotated[int, Query(description="User ID", gt=0)],
    workspace_id: Annotated[UUID, Query(description="Workspace ID")],
    db: Session = Depends(get_db),
    _: None = Depends(verify_internal_token),
) -> dict:
    """
    Internal endpoint returning all active debts for AI analysis.

    Returns aggregated data without PII for the AI assistant to analyze
    debt structure and provide financial insights.
    """
    try:
        debts = (
            db.query(Debt)
            .filter(
                Debt.user_id == user_id,
                Debt.workspace_id == workspace_id,
                Debt.is_active.is_(True),
            )
            .limit(200)
            .all()
        )
        return {
            "items": [
                {
                    "name": d.name,
                    "debt_type": d.debt_type,
                    "current_balance": float(d.current_balance),
                    "interest_rate": float(d.interest_rate) if d.interest_rate else None,
                    "due_date": str(d.due_date) if d.due_date else None,
                    "minimum_payment": float(d.minimum_payment) if d.minimum_payment else None,
                    "currency": d.currency,
                }
                for d in debts
            ]
        }
    except Exception as e:
        logger.error(f"Error fetching debts AI summary: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve debts summary",
        )
