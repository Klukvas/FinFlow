"""
Consent validation utilities for WayForPay compliance
"""
from datetime import datetime, timezone
from typing import Dict, Optional
from ..utils.errors import ValidationError

# Current consent version - increment when terms change materially
CURRENT_CONSENT_VERSION = "v1.0.0"

# Maximum age of consent timestamp (1 hour)
MAX_CONSENT_AGE_SECONDS = 3600


def validate_subscription_consent(metadata: Optional[Dict]) -> None:
    """
    Validate that user consent is properly recorded for subscription payments.
    
    This is required for WayForPay compliance and consumer protection laws.
    
    Args:
        metadata: Payment metadata containing consent information
        
    Raises:
        ValidationError: If consent validation fails
    """
    if not metadata:
        raise ValidationError(
            "Metadata required for subscription payments",
            error_code="@payment_service/METADATA_REQUIRED",
            details={
                "required_fields": ["consent_given", "consent_version", "consent_timestamp"]
            }
        )
    
    # Check consent_given flag
    if not metadata.get('consent_given'):
        raise ValidationError(
            "User consent required for subscription payments. "
            "User must explicitly agree to recurring charges and payment data storage.",
            error_code="@payment_service/CONSENT_REQUIRED",
            details={
                "consent_given": metadata.get('consent_given', False),
                "help": "User must check the consent checkbox before payment"
            }
        )
    
    # Check consent_version
    consent_version = metadata.get('consent_version')
    if not consent_version:
        raise ValidationError(
            "Consent version required",
            error_code="@payment_service/CONSENT_VERSION_REQUIRED",
            details={
                "current_version": CURRENT_CONSENT_VERSION
            }
        )
    
    if consent_version != CURRENT_CONSENT_VERSION:
        raise ValidationError(
            f"Consent version mismatch. Please refresh the page and try again.",
            error_code="@payment_service/CONSENT_VERSION_MISMATCH",
            details={
                "expected_version": CURRENT_CONSENT_VERSION,
                "received_version": consent_version,
                "help": "User may have outdated page - ask them to refresh"
            }
        )
    
    # Validate timestamp is recent (within last hour)
    consent_timestamp_str = metadata.get('consent_timestamp')
    if consent_timestamp_str:
        try:
            # Parse ISO format timestamp
            consent_time = datetime.fromisoformat(consent_timestamp_str.replace('Z', '+00:00'))
            
            # Ensure timezone-aware
            if consent_time.tzinfo is None:
                consent_time = consent_time.replace(tzinfo=timezone.utc)
            
            # Check age
            now = datetime.now(timezone.utc)
            time_diff = (now - consent_time).total_seconds()
            
            if time_diff > MAX_CONSENT_AGE_SECONDS:
                raise ValidationError(
                    "Consent timestamp is too old. Please try again.",
                    error_code="@payment_service/CONSENT_EXPIRED",
                    details={
                        "consent_age_seconds": int(time_diff),
                        "max_age_seconds": MAX_CONSENT_AGE_SECONDS,
                        "help": "User session may have timed out - ask them to re-consent"
                    }
                )
            
            if time_diff < -60:  # More than 1 minute in the future
                raise ValidationError(
                    "Consent timestamp is in the future. Please check your system clock.",
                    error_code="@payment_service/CONSENT_FUTURE_TIMESTAMP",
                    details={
                        "consent_timestamp": consent_timestamp_str,
                        "server_time": now.isoformat()
                    }
                )
                
        except ValueError as e:
            raise ValidationError(
                "Invalid consent timestamp format",
                error_code="@payment_service/INVALID_TIMESTAMP",
                details={
                    "consent_timestamp": consent_timestamp_str,
                    "expected_format": "ISO 8601 (e.g., 2026-01-28T10:30:00Z)",
                    "error": str(e)
                }
            )


def get_current_consent_version() -> str:
    """Get the current consent version"""
    return CURRENT_CONSENT_VERSION
