from __future__ import annotations

import hashlib
import hmac
import logging
from datetime import datetime
from decimal import Decimal
from typing import Optional, Any
import httpx

from ..config import settings

logger = logging.getLogger("payment_service.wayforpay_client")


class WayForPayClient:
    """Client for WayForPay payment gateway"""

    def __init__(self):
        self.merchant_account = settings.wayforpay_merchant_account
        self.secret_key = settings.wayforpay_merchant_secret_key
        self.merchant_domain = settings.wayforpay_merchant_domain
        self.api_url = settings.wayforpay_api_url
        
        # Validate configuration on init
        self._validate_configuration()

    def _validate_configuration(self):
        """
        Validate WayForPay configuration on initialization.
        Logs configuration info for debugging.
        """
        # Check for test credentials (informational only - they may work in some cases)
        if not self.merchant_account:
            logger.warning(
                "⚠️ WAYFORPAY_MERCHANT_ACCOUNT is not configured!"
            )
        elif self.merchant_account == "test_merch_n1":
            logger.info(
                "Using test_merch_n1 merchant account. "
                "If payment form is skipped, this might be due to: "
                "1) Expired/unreachable callback URL (check ngrok), "
                "2) Domain mismatch, "
                "3) Network issues. "
                "Run ./test_wayforpay_credentials.sh to diagnose."
            )
        
        if not self.secret_key:
            logger.warning(
                "⚠️ WAYFORPAY_MERCHANT_SECRET_KEY is not configured!"
            )
        elif self.secret_key == "flk3409refn54t54t*FNJRET":
            logger.info(
                "Using default test secret key. "
                "If this worked before, ensure callback URL is reachable."
            )
        
        if not self.merchant_domain:
            logger.warning(
                "⚠️ WAYFORPAY_MERCHANT_DOMAIN is not configured!"
            )
        elif self.merchant_domain == "www.market.ua":
            logger.info(
                "Using www.market.ua merchant domain. "
                "This should work with test_merch_n1 credentials."
            )
        
        # Log configuration status (without exposing secrets)
        logger.info(
            "WayForPay client initialized",
            extra={
                "merchant_account": self.merchant_account,
                "merchant_domain": self.merchant_domain,
                "api_url": self.api_url,
                "has_secret_key": bool(self.secret_key),
                "secret_key_length": len(self.secret_key) if self.secret_key else 0,
            }
        )

    def generate_signature(self, fields: list[str]) -> str:
        """
        Generate merchant signature for WayForPay
        
        Args:
            fields: List of field values to sign (in specific order)
        
        Returns:
            HMAC MD5 signature (as hex string)
        """
        string_to_sign = ";".join(str(f) for f in fields)
        signature = hmac.new(
            self.secret_key.encode("utf-8"),
            string_to_sign.encode("utf-8"),
            hashlib.md5,
        ).hexdigest()
        
        # Log signature generation for debugging (first attempt)
        logger.debug(
            "Generated signature",
            extra={
                "string_to_sign_preview": string_to_sign[:100] + "..." if len(string_to_sign) > 100 else string_to_sign,
                "signature_preview": signature[:20] + "...",
                "field_count": len(fields),
            }
        )
        
        return signature

    def verify_signature(self, signature: str, fields: list[str]) -> bool:
        """
        Verify merchant signature from WayForPay callback
        
        Args:
            signature: Signature to verify
            fields: List of field values (in specific order)
        
        Returns:
            True if signature is valid
        """
        expected_signature = self.generate_signature(fields)
        return hmac.compare_digest(signature, expected_signature)

    def create_payment_form(
        self,
        order_reference: str,
        amount: Decimal,
        currency: str,
        product_name: str,
        product_count: int,
        product_price: Decimal,
        return_url: str,
        service_url: str,
        request_recurring_token: bool = False,  # Deprecated: WayForPay returns token automatically
    ) -> dict[str, Any]:
        """
        Generate payment form data for WayForPay
        
        Args:
            order_reference: Unique order reference
            amount: Payment amount
            currency: Currency code (UAH, USD, EUR)
            product_name: Product name/description
            product_count: Number of products
            product_price: Price per product
            return_url: URL to redirect user after payment
            service_url: Callback URL for payment notifications
        
        Returns:
            Dictionary with form fields for WayForPay
        """
        order_date = int(datetime.utcnow().timestamp())

        # Fields for signature (order matters!)
        signature_fields = [
            self.merchant_account,
            self.merchant_domain,
            order_reference,
            str(order_date),
            str(amount),
            currency,
            product_name,
            str(product_count),
            str(product_price),
        ]

        signature = self.generate_signature(signature_fields)

        form_data = {
            "merchantAccount": self.merchant_account,
            "merchantDomainName": self.merchant_domain,
            "orderReference": order_reference,
            "orderDate": order_date,
            "amount": str(amount),
            "currency": currency,
            "productName": [product_name],
            "productCount": [product_count],
            "productPrice": [str(product_price)],
            "merchantSignature": signature,
            "returnUrl": return_url,
            "serviceUrl": service_url,
            "language": "UA",
            "straightforward": 1,  # Force payment form display (required for test accounts)
        }
        
        # Note: WayForPay returns recToken automatically in the webhook callback
        # when a successful payment is processed. No need to request it in form data.
        # The token will be included in the serviceUrl (webhook) response.

        logger.info(
            f"Generated payment form for order {order_reference}",
            extra={
                "order_reference": order_reference,
                "amount": str(amount),
                "currency": currency,
                "request_recurring_token": request_recurring_token,
                "has_recToken": "recToken" in form_data,
            },
        )

        return form_data

    def verify_callback_signature(self, callback_data: dict[str, Any]) -> bool:
        """
        Verify signature from WayForPay callback
        
        Args:
            callback_data: Callback payload from WayForPay
        
        Returns:
            True if signature is valid
        """
        merchant_signature = callback_data.get("merchantSignature", "")
        
        # Fields for signature verification (order matters!)
        signature_fields = [
            callback_data.get("merchantAccount", ""),
            callback_data.get("orderReference", ""),
            str(callback_data.get("amount", "")),
            callback_data.get("currency", ""),
            callback_data.get("authCode", ""),
            callback_data.get("cardPan", ""),
            callback_data.get("transactionStatus", ""),
            callback_data.get("reasonCode", ""),
        ]

        is_valid = self.verify_signature(merchant_signature, signature_fields)

        logger.info(
            f"Callback signature verification: {'VALID' if is_valid else 'INVALID'}",
            extra={
                "order_reference": callback_data.get("orderReference"),
                "transaction_status": callback_data.get("transactionStatus"),
                "signature_valid": is_valid,
            },
        )

        return is_valid

    async def verify_payment_status(self, order_reference: str) -> Optional[dict[str, Any]]:
        """
        Verify payment status via WayForPay API
        
        Args:
            order_reference: Order reference to check
        
        Returns:
            Payment status response or None if failed
        """
        signature_fields = [self.merchant_account, order_reference]
        signature = self.generate_signature(signature_fields)

        request_data = {
            "transactionType": "CHECK_STATUS",
            "merchantAccount": self.merchant_account,
            "orderReference": order_reference,
            "merchantSignature": signature,
        }

        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.post(self.api_url, json=request_data)
                response.raise_for_status()
                data = response.json()

                logger.info(
                    f"Payment status check for order {order_reference}",
                    extra={
                        "order_reference": order_reference,
                        "status": data.get("transactionStatus"),
                    },
                )

                return data
        except Exception as e:
            logger.error(
                f"Failed to check payment status for order {order_reference}: {e}",
                extra={"order_reference": order_reference, "error": str(e)},
            )
            return None

    async def charge_recurring(
        self,
        order_reference: str,
        amount: Decimal,
        currency: str,
        recurring_token: str,
        product_name: str,
    ) -> Optional[dict[str, Any]]:
        """
        Charge using recurring token
        
        Args:
            order_reference: New unique order reference
            amount: Amount to charge
            currency: Currency code
            recurring_token: Recurring payment token from initial payment
            product_name: Product description
        
        Returns:
            Charge response or None if failed
        """
        order_date = int(datetime.utcnow().timestamp())
        
        # Fields for signature
        signature_fields = [
            self.merchant_account,
            order_reference,
            str(amount),
            currency,
        ]
        
        signature = self.generate_signature(signature_fields)

        request_data = {
            "transactionType": "CHARGE",
            "merchantAccount": self.merchant_account,
            "orderReference": order_reference,
            "orderDate": order_date,
            "amount": str(amount),
            "currency": currency,
            "productName": [product_name],
            "productCount": [1],
            "productPrice": [str(amount)],
            "recToken": recurring_token,
            "merchantSignature": signature,
        }

        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.post(self.api_url, json=request_data)
                response.raise_for_status()
                data = response.json()

                logger.info(
                    f"Recurring charge for order {order_reference}",
                    extra={
                        "order_reference": order_reference,
                        "amount": str(amount),
                        "status": data.get("transactionStatus"),
                        "reason_code": data.get("reasonCode"),
                    },
                )

                return data
        except Exception as e:
            logger.error(
                f"Failed to charge recurring payment for order {order_reference}: {e}",
                extra={"order_reference": order_reference, "error": str(e)},
            )
            return None

    async def refund_payment(
        self,
        order_reference: str,
        amount: Decimal,
        currency: str,
        comment: Optional[str] = None,
    ) -> Optional[dict[str, Any]]:
        """
        Request refund via WayForPay API
        
        Args:
            order_reference: Order reference to refund
            amount: Amount to refund
            currency: Currency code
            comment: Optional refund reason
        
        Returns:
            Refund response or None if failed
        """
        signature_fields = [self.merchant_account, order_reference, str(amount), currency]
        signature = self.generate_signature(signature_fields)

        request_data = {
            "transactionType": "REFUND",
            "merchantAccount": self.merchant_account,
            "orderReference": order_reference,
            "amount": str(amount),
            "currency": currency,
            "comment": comment or "Refund",
            "merchantSignature": signature,
        }

        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.post(self.api_url, json=request_data)
                response.raise_for_status()
                data = response.json()

                logger.info(
                    f"Refund request for order {order_reference}",
                    extra={
                        "order_reference": order_reference,
                        "amount": str(amount),
                        "status": data.get("reasonCode"),
                    },
                )

                return data
        except Exception as e:
            logger.error(
                f"Failed to refund payment for order {order_reference}: {e}",
                extra={"order_reference": order_reference, "error": str(e)},
            )
            return None
