from __future__ import annotations

import logging
from typing import Optional, List, Union
from uuid import UUID
from datetime import datetime
from sqlalchemy.orm import Session
from sqlalchemy import desc

from ..models.models import Payment, PaymentStatus
from ..utils.errors import NotFoundError

logger = logging.getLogger("payment_service.payment_repository")


class PaymentRepository:
    """Repository for Payment operations"""

    def __init__(self, db: Session):
        self.db = db

    def create(self, payment: Payment) -> Payment:
        """Create a new payment"""
        self.db.add(payment)
        self.db.commit()
        self.db.refresh(payment)
        
        logger.info(
            f"Created payment {payment.id}",
            extra={
                "payment_id": str(payment.id),
                "order_reference": payment.order_reference,
                "amount": str(payment.amount),
                "status": payment.status.value,
            },
        )
        
        return payment

    def get_by_id(self, payment_id: UUID) -> Optional[Payment]:
        """Get payment by ID"""
        return self.db.query(Payment).filter(Payment.id == payment_id).first()

    def get_by_id_or_raise(self, payment_id: UUID) -> Payment:
        """Get payment by ID or raise NotFoundError"""
        payment = self.get_by_id(payment_id)
        if not payment:
            raise NotFoundError(
                f"Payment {payment_id} not found",
                error_code="@payment_service/PAYMENT_NOT_FOUND",
                details={"payment_id": str(payment_id)},
            )
        return payment

    def get_by_order_reference(self, order_reference: str) -> Optional[Payment]:
        """Get payment by order reference"""
        return self.db.query(Payment).filter(Payment.order_reference == order_reference).first()

    def get_by_order_reference_or_raise(self, order_reference: str) -> Payment:
        """Get payment by order reference or raise NotFoundError"""
        payment = self.get_by_order_reference(order_reference)
        if not payment:
            raise NotFoundError(
                f"Payment with order reference {order_reference} not found",
                error_code="@payment_service/PAYMENT_NOT_FOUND",
                details={"order_reference": order_reference},
            )
        return payment

    def get_by_user_id(
        self,
        user_id: Union[str, int, UUID],
        limit: int = 50,
        offset: int = 0,
    ) -> List[Payment]:
        """Get payments by user ID"""
        return (
            self.db.query(Payment)
            .filter(Payment.user_id == str(user_id))
            .order_by(desc(Payment.created_at))
            .limit(limit)
            .offset(offset)
            .all()
        )

    def get_by_workspace_id(
        self,
        workspace_id: Union[str, int, UUID],
        limit: int = 50,
        offset: int = 0,
    ) -> List[Payment]:
        """Get payments by workspace ID"""
        return (
            self.db.query(Payment)
            .filter(Payment.workspace_id == str(workspace_id))
            .order_by(desc(Payment.created_at))
            .limit(limit)
            .offset(offset)
            .all()
        )

    def update_status(
        self,
        payment: Payment,
        new_status: PaymentStatus,
        reason: Optional[str] = None,
    ) -> Payment:
        """Update payment status"""
        old_status = payment.status
        payment.status = new_status
        payment.updated_at = datetime.utcnow()

        if new_status == PaymentStatus.PAID:
            payment.paid_at = datetime.utcnow()
        elif new_status in (PaymentStatus.FAILED, PaymentStatus.EXPIRED, PaymentStatus.CANCELED):
            payment.failed_at = datetime.utcnow()
            if reason:
                payment.failure_reason = reason
        elif new_status in (PaymentStatus.REFUNDED, PaymentStatus.PARTIALLY_REFUNDED):
            payment.refunded_at = datetime.utcnow()

        self.db.commit()
        self.db.refresh(payment)

        logger.info(
            f"Updated payment {payment.id} status: {old_status.value} -> {new_status.value}",
            extra={
                "payment_id": str(payment.id),
                "order_reference": payment.order_reference,
                "status_from": old_status.value,
                "status_to": new_status.value,
                "reason": reason,
            },
        )

        return payment

    def update(self, payment: Payment) -> Payment:
        """Update payment"""
        payment.updated_at = datetime.utcnow()
        self.db.commit()
        self.db.refresh(payment)
        return payment

    def count_by_status(self, status: PaymentStatus) -> int:
        """Count payments by status"""
        return self.db.query(Payment).filter(Payment.status == status).count()
