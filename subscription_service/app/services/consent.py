"""
Consent recording and management service for WayForPay compliance
"""
from __future__ import annotations

from datetime import datetime
from typing import Dict
from sqlalchemy.orm import Session

from ..models.models import SubscriptionConsentLog, Subscription
from ..utils.errors import NotFoundError, ValidationError

# Current consent version
CURRENT_CONSENT_VERSION = "v1.0.0"

# Consent text templates (versioned)
CONSENT_TEXTS = {
    "v1.0.0": {
        "en": """I agree to subscribe to {plan_name} plan

By subscribing, I confirm that:
• My payment card details will be securely tokenized and stored by WayForPay payment processor
• I authorize automatic monthly charges of {amount} {currency} to my payment card
• Charges will occur on the {day} of each month starting from {start_date}
• I can cancel my subscription at any time from my account settings
• Upon cancellation, no future charges will be made

I have read and agree to the Terms of Service and Subscription & Payment Policy.""",
        
        "uk": """Я погоджуюся оформити підписку на план {plan_name}

Підписуючись, я підтверджую, що:
• Дані моєї платіжної картки будуть безпечно токенізовані та збережені платіжною системою WayForPay
• Я надаю дозвіл на автоматичне щомісячне списання {amount} {currency} з моєї платіжної картки
• Списання відбуватиметься {day} числа кожного місяця, починаючи з {start_date}
• Я можу скасувати підписку в будь-який час в налаштуваннях мого облікового запису
• Після скасування жодних подальших списань не відбудеться

Я прочитав(-ла) та погоджуюся з Умовами надання послуг та Політикою підписки та оплати."""
    }
}


class ConsentService:
    """Service for managing subscription consent"""
    
    def __init__(self, db: Session):
        self.db = db
    
    def record_consent(
        self,
        subscription_id: int,
        user_id: str,
        consent_version: str,
        consent_language: str,
        plan_name: str,
        plan_code: str,
        amount: str,
        currency: str,
        ip_address: str,
        user_agent: str,
        browser_fingerprint: str = None,
    ) -> SubscriptionConsentLog:
        """
        Record user consent for subscription in audit log.
        
        This creates an immutable record of what the user agreed to,
        when they agreed, and from where. Required for WayForPay compliance.
        
        Args:
            subscription_id: Subscription ID
            user_id: User ID
            consent_version: Consent version (e.g., "v1.0.0")
            consent_language: Language code (e.g., "en", "uk")
            plan_name: Human-readable plan name
            plan_code: Plan code
            amount: Subscription amount
            currency: Currency code
            ip_address: User's IP address
            user_agent: User's browser user agent
            browser_fingerprint: Optional browser fingerprint
            
        Returns:
            Created consent log entry
            
        Raises:
            NotFoundError: If subscription not found
            ValidationError: If validation fails
        """
        # Verify subscription exists
        subscription = self.db.query(Subscription).filter_by(id=subscription_id).first()
        if not subscription:
            raise NotFoundError(
                f"Subscription {subscription_id} not found",
                error_code="@subscription_service/SUBSCRIPTION_NOT_FOUND"
            )
        
        # Get consent text template
        consent_text = self._get_consent_text(
            version=consent_version,
            language=consent_language,
            plan_name=plan_name,
            amount=amount,
            currency=currency,
        )
        
        # Create consent log entry (immutable audit record)
        consent_log = SubscriptionConsentLog(
            subscription_id=subscription_id,
            user_id=user_id,
            consent_version=consent_version,
            consent_text=consent_text,
            consent_language=consent_language,
            consent_given_at=datetime.utcnow(),
            ip_address=ip_address,
            user_agent=user_agent,
            browser_fingerprint=browser_fingerprint,
            consent_metadata={
                "plan_code": plan_code,
                "plan_name": plan_name,
                "amount": str(amount),
                "currency": currency,
            }
        )
        
        self.db.add(consent_log)
        
        # Update subscription with consent information
        subscription.consent_given = True
        subscription.consent_version = consent_version
        subscription.consent_timestamp = datetime.utcnow()
        subscription.consent_ip_address = ip_address
        subscription.consent_user_agent = user_agent
        
        self.db.commit()
        self.db.refresh(consent_log)
        
        return consent_log
    
    def _get_consent_text(
        self,
        version: str,
        language: str,
        plan_name: str,
        amount: str,
        currency: str,
    ) -> str:
        """
        Get consent text template and fill with user's values.
        
        Args:
            version: Consent version
            language: Language code
            plan_name: Plan name
            amount: Amount
            currency: Currency
            
        Returns:
            Filled consent text
            
        Raises:
            ValidationError: If version or language not found
        """
        if version not in CONSENT_TEXTS:
            raise ValidationError(
                f"Unknown consent version: {version}",
                error_code="@subscription_service/UNKNOWN_CONSENT_VERSION",
                details={"available_versions": list(CONSENT_TEXTS.keys())}
            )
        
        if language not in CONSENT_TEXTS[version]:
            raise ValidationError(
                f"Unknown language: {language}",
                error_code="@subscription_service/UNKNOWN_LANGUAGE",
                details={
                    "available_languages": list(CONSENT_TEXTS[version].keys()),
                    "fallback": "en"
                }
            )
        
        template = CONSENT_TEXTS[version][language]
        
        # Fill template with user's subscription details
        today = datetime.utcnow()
        filled_text = template.format(
            plan_name=plan_name,
            amount=amount,
            currency=currency,
            day=today.day,
            start_date=today.strftime("%Y-%m-%d"),
        )
        
        return filled_text
    
    def get_user_consent_history(self, user_id: str) -> list[SubscriptionConsentLog]:
        """
        Get consent history for a user.
        
        Useful for compliance audits and user data export requests.
        
        Args:
            user_id: User ID
            
        Returns:
            List of consent log entries
        """
        return self.db.query(SubscriptionConsentLog).filter_by(
            user_id=user_id
        ).order_by(
            SubscriptionConsentLog.created_at.desc()
        ).all()
    
    @staticmethod
    def get_current_consent_version() -> str:
        """Get the current consent version"""
        return CURRENT_CONSENT_VERSION
    
    @staticmethod
    def get_supported_languages() -> list[str]:
        """Get list of supported languages for consent text"""
        return list(CONSENT_TEXTS[CURRENT_CONSENT_VERSION].keys())
