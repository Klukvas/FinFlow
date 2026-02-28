from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.bank_connection import BankConnection
from shared.auth.dependencies import verify_internal_token

router = APIRouter()


@router.get("/internal/health")
async def internal_health():
    return {"status": "healthy", "service": "bank-sync-service"}


@router.get(
    "/internal/connections/user/{user_id}",
    dependencies=[Depends(verify_internal_token)],
)
def get_user_connections(
    user_id: int,
    db: Session = Depends(get_db),
):
    """For other services to check if a user has bank sync configured."""
    connections = (
        db.query(BankConnection)
        .filter(
            BankConnection.user_id == user_id,
            BankConnection.is_active == True,
        )
        .all()
    )
    return [
        {
            "id": c.id,
            "bank_type": c.bank_type,
            "is_active": c.is_active,
            "last_sync_at": c.last_sync_at.isoformat() if c.last_sync_at else None,
        }
        for c in connections
    ]
