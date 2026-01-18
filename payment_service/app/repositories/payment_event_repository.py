from __future__ import annotations

import logging
from typing import Optional, List
from uuid import UUID
from sqlalchemy.orm import Session
from sqlalchemy import desc

from ..models.models import PaymentEvent, PaymentEventType

logger = logging.getLogger("payment_service.payment_event_repository")


class PaymentEventRepository:
    """Repository for PaymentEvent operations"""

    def __init__(self, db: Session):
        self.db = db

    def create(self, event: PaymentEvent) -> PaymentEvent:
        """Create a new payment event"""
        self.db.add(event)
        self.db.commit()
        self.db.refresh(event)
        
        logger.info(
            f"Created payment event {event.id}",
            extra={
                "event_id": str(event.id),
                "payment_id": str(event.payment_id),
                "event_type": event.event_type.value,
            },
        )
        
        return event

    def get_by_id(self, event_id: UUID) -> Optional[PaymentEvent]:
        """Get event by ID"""
        return self.db.query(PaymentEvent).filter(PaymentEvent.id == event_id).first()

    def get_by_payment_id(
        self,
        payment_id: UUID,
        limit: int = 100,
    ) -> List[PaymentEvent]:
        """Get events by payment ID"""
        return (
            self.db.query(PaymentEvent)
            .filter(PaymentEvent.payment_id == payment_id)
            .order_by(desc(PaymentEvent.created_at))
            .limit(limit)
            .all()
        )

    def get_by_provider_event_id(self, provider_event_id: str) -> Optional[PaymentEvent]:
        """Get event by provider event ID (for idempotency)"""
        return (
            self.db.query(PaymentEvent)
            .filter(PaymentEvent.provider_event_id == provider_event_id)
            .first()
        )

    def has_callback_been_processed(
        self,
        payment_id: UUID,
        provider_event_id: Optional[str],
        payload_hash: str,
    ) -> bool:
        """
        Check if callback has already been processed (for idempotency)
        
        Args:
            payment_id: Payment ID
            provider_event_id: Provider event ID (if available)
            payload_hash: Hash of callback payload
        
        Returns:
            True if callback was already processed
        """
        # If provider gives us event ID, use it
        if provider_event_id:
            existing = self.get_by_provider_event_id(provider_event_id)
            if existing:
                logger.info(
                    f"Callback already processed (provider_event_id: {provider_event_id})",
                    extra={
                        "payment_id": str(payment_id),
                        "provider_event_id": provider_event_id,
                    },
                )
                return True

        # Otherwise, check by payload hash
        # This is a simple implementation - in production you might want more sophisticated duplicate detection
        events = self.get_by_payment_id(payment_id, limit=50)
        for event in events:
            if event.event_type == PaymentEventType.CALLBACK:
                # Here we could compute hash of event.payload_raw and compare
                # For now, we rely on provider_event_id
                pass

        return False
