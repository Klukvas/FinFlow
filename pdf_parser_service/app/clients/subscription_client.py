"""
Subscription Client for PDF Parser Service.

This client communicates with the subscription service to:
- Get user's subscription plan and feature limits
- Check if user can upload PDFs (monthly quota)
- Check if PDF record count is within plan limits

Pattern follows expense_service/app/clients/subscription.py
"""
from __future__ import annotations

import httpx
from typing import Dict, Any, Optional
from app.config.config import settings
from app.utils.logger import get_logger

logger = get_logger(__name__)


class SubscriptionClient:
    """Client for interacting with subscription service to check PDF upload limits"""

    def __init__(self, base_url: Optional[str] = None) -> None:
        self.base_url = base_url or settings.subscription_service_url.rstrip("/")
        self.client = httpx.Client(timeout=5.0)

    def get_user_features(self, user_id: int) -> Dict[str, Any]:
        """
        Get user's feature entitlements from subscription service.

        Returns dict with feature codes as keys:
        {
            "pdf_uploads_per_month": {
                "feature_code": "pdf_uploads_per_month",
                "enabled": true,
                "limit_value": 10,
                "plan_code": "professional"
            },
            "pdf_records_per_upload": {
                "feature_code": "pdf_records_per_upload",
                "enabled": true,
                "limit_value": 100,
                "plan_code": "professional"
            },
            ...
        }
        """
        url = f"{self.base_url}/v1/internal/features/{user_id}"
        headers = {"X-Internal-Token": settings.internal_service_token}

        try:
            resp = self.client.get(url, headers=headers)
            if resp.status_code == 200:
                features = resp.json()
                # Convert list to dict for easier lookup
                return {f["feature_code"]: f for f in features}
            logger.warning(f"Failed to fetch features for user {user_id}: {resp.status_code}")
            return {}
        except Exception as e:
            logger.error(f"Error fetching user features: {e}")
            return {}

    def check_pdf_upload_limit(self, user_id: int, current_count: int) -> bool:
        """
        Check if user can upload more PDFs this month.

        Args:
            user_id: User ID
            current_count: Number of PDFs already uploaded this month

        Returns:
            True if user can upload, False if limit exceeded
        """
        features = self.get_user_features(user_id)
        pdf_feature = features.get("pdf_uploads_per_month", {})

        if not pdf_feature.get("enabled", False):
            return False

        limit = pdf_feature.get("limit_value")
        if limit is None:
            return True  # Unlimited (Enterprise plan)

        return current_count < limit

    def check_pdf_records_limit(self, user_id: int, record_count: int) -> bool:
        """
        Check if PDF has acceptable number of records for user's plan.

        Args:
            user_id: User ID
            record_count: Number of records in PDF

        Returns:
            True if record count is within limit, False otherwise
        """
        features = self.get_user_features(user_id)
        records_feature = features.get("pdf_records_per_upload", {})

        if not records_feature.get("enabled", False):
            return False

        limit = records_feature.get("limit_value")
        if limit is None:
            return True  # Unlimited (Enterprise plan)

        return record_count <= limit

    def get_pdf_limits(self, user_id: int) -> Dict[str, Optional[int]]:
        """
        Get both PDF limits for a user.

        Returns:
            {
                "uploads_per_month": 10 or None (unlimited),
                "records_per_upload": 100 or None (unlimited),
                "plan_code": "professional"
            }
        """
        features = self.get_user_features(user_id)

        uploads_feature = features.get("pdf_uploads_per_month", {})
        records_feature = features.get("pdf_records_per_upload", {})

        return {
            "uploads_per_month": uploads_feature.get("limit_value"),
            "records_per_upload": records_feature.get("limit_value"),
            "plan_code": uploads_feature.get("plan_code", "unknown")
        }

    def close(self):
        """Close HTTP client"""
        self.client.close()
