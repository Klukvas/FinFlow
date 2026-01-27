#!/usr/bin/env python3
"""
WayForPay Configuration Diagnostic Tool

This script checks your WayForPay configuration and helps diagnose
why the payment form might not be displaying.

Run from payment_service directory:
    python check_wayforpay_config.py

Or from docker:
    docker-compose exec payment_service python check_wayforpay_config.py
"""

import sys
import os
from pathlib import Path

# Add app to path
sys.path.insert(0, str(Path(__file__).parent))

from app.config import settings
from app.clients.wayforpay_client import WayForPayClient
from decimal import Decimal


def check_status_icon(is_valid: bool) -> str:
    """Return a status icon"""
    return "✅" if is_valid else "❌"


def print_header(text: str):
    """Print a section header"""
    print("\n" + "=" * 80)
    print(f"  {text}")
    print("=" * 80)


def check_configuration():
    """Check WayForPay configuration"""
    print_header("WayForPay Configuration Check")
    
    issues = []
    warnings = []
    
    # Check merchant account
    print("\n1. Merchant Account")
    if not settings.wayforpay_merchant_account:
        print(f"   {check_status_icon(False)} NOT CONFIGURED")
        issues.append("WAYFORPAY_MERCHANT_ACCOUNT is empty")
    elif settings.wayforpay_merchant_account == "test_merch_n1":
        print(f"   {check_status_icon(False)} USING DEFAULT TEST CREDENTIALS")
        print(f"   Value: {settings.wayforpay_merchant_account}")
        issues.append("Using default test_merch_n1 - this will NOT work!")
    else:
        print(f"   {check_status_icon(True)} Configured")
        print(f"   Value: {settings.wayforpay_merchant_account}")
    
    # Check secret key
    print("\n2. Merchant Secret Key")
    if not settings.wayforpay_merchant_secret_key:
        print(f"   {check_status_icon(False)} NOT CONFIGURED")
        issues.append("WAYFORPAY_MERCHANT_SECRET_KEY is empty")
    elif settings.wayforpay_merchant_secret_key == "flk3409refn54t54t*FNJRET":
        print(f"   {check_status_icon(False)} USING DEFAULT TEST CREDENTIALS")
        issues.append("Using default test secret key - this will NOT work!")
    else:
        print(f"   {check_status_icon(True)} Configured")
        print(f"   Length: {len(settings.wayforpay_merchant_secret_key)} characters")
        print(f"   Preview: {settings.wayforpay_merchant_secret_key[:10]}...")
    
    # Check merchant domain
    print("\n3. Merchant Domain")
    if not settings.wayforpay_merchant_domain:
        print(f"   {check_status_icon(False)} NOT CONFIGURED")
        issues.append("WAYFORPAY_MERCHANT_DOMAIN is empty")
    elif settings.wayforpay_merchant_domain == "www.market.ua":
        print(f"   {check_status_icon(False)} USING DEFAULT TEST DOMAIN")
        print(f"   Value: {settings.wayforpay_merchant_domain}")
        issues.append("Using default test domain - must match your WayForPay registration!")
    else:
        print(f"   {check_status_icon(True)} Configured")
        print(f"   Value: {settings.wayforpay_merchant_domain}")
    
    # Check callback URL
    print("\n4. Callback URL (Webhook)")
    if not settings.wayforpay_callback_url:
        print(f"   {check_status_icon(False)} NOT CONFIGURED")
        issues.append("WAYFORPAY_CALLBACK_URL is empty")
    else:
        is_https = settings.wayforpay_callback_url.startswith("https://")
        print(f"   {check_status_icon(is_https)} {'HTTPS' if is_https else 'NOT HTTPS'}")
        print(f"   Value: {settings.wayforpay_callback_url}")
        if not is_https:
            warnings.append("Callback URL should use HTTPS for webhooks to work")
        
        # Check if using localhost (won't work with WayForPay)
        if "localhost" in settings.wayforpay_callback_url or "127.0.0.1" in settings.wayforpay_callback_url:
            print(f"   ⚠️  Using localhost - WayForPay cannot reach this!")
            warnings.append("Use ngrok or a public URL for local development")
    
    # Check return URL
    print("\n5. Return URL")
    if not settings.wayforpay_return_url:
        print(f"   {check_status_icon(False)} NOT CONFIGURED")
        issues.append("WAYFORPAY_RETURN_URL is empty")
    else:
        print(f"   {check_status_icon(True)} Configured")
        print(f"   Value: {settings.wayforpay_return_url}")
    
    # Check API URL
    print("\n6. API URL")
    print(f"   {check_status_icon(True)} {settings.wayforpay_api_url}")
    
    return issues, warnings


def test_signature_generation():
    """Test signature generation"""
    print_header("Signature Generation Test")
    
    try:
        client = WayForPayClient()
        
        # Test data
        test_fields = [
            client.merchant_account,
            client.merchant_domain,
            "TEST_ORDER_123",
            "1234567890",
            "100.00",
            "UAH",
            "Test Product",
            "1",
            "100.00"
        ]
        
        print("\nGenerating test signature...")
        print(f"Fields to sign: {'; '.join(test_fields)}")
        
        signature = client.generate_signature(test_fields)
        
        print(f"\n{check_status_icon(True)} Signature generated successfully!")
        print(f"Signature: {signature}")
        print(f"Length: {len(signature)} characters")
        
        return True
    except Exception as e:
        print(f"\n{check_status_icon(False)} Signature generation failed!")
        print(f"Error: {e}")
        return False


def test_form_generation():
    """Test payment form generation"""
    print_header("Payment Form Generation Test")
    
    try:
        client = WayForPayClient()
        
        print("\nGenerating test payment form...")
        
        form_data = client.create_payment_form(
            order_reference="TEST_ORDER_123",
            amount=Decimal("100.00"),
            currency="UAH",
            product_name="Test Product",
            product_count=1,
            product_price=Decimal("100.00"),
            return_url=settings.wayforpay_return_url or "http://localhost:3000/payment/return",
            service_url=settings.wayforpay_callback_url or "http://localhost:8013/v1/webhooks/wayforpay",
            request_recurring_token=True,
        )
        
        print(f"\n{check_status_icon(True)} Form data generated successfully!")
        print(f"Form fields: {len(form_data)}")
        
        # Check required fields
        required_fields = [
            'merchantAccount', 'merchantDomainName', 'orderReference',
            'orderDate', 'amount', 'currency', 'productName',
            'productCount', 'productPrice', 'merchantSignature',
            'returnUrl', 'serviceUrl'
        ]
        
        print("\nForm field validation:")
        all_present = True
        for field in required_fields:
            is_present = field in form_data
            all_present = all_present and is_present
            print(f"  {check_status_icon(is_present)} {field}: {form_data.get(field, 'MISSING')}")
        
        # Check special fields
        print("\nSpecial fields:")
        print(f"  straightforward (force form): {form_data.get('straightforward', 'NOT SET')}")
        print(f"  recToken (recurring): {form_data.get('recToken', 'NOT SET')}")
        print(f"  language: {form_data.get('language', 'NOT SET')}")
        
        return all_present
    except Exception as e:
        print(f"\n{check_status_icon(False)} Form generation failed!")
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()
        return False


def print_summary(issues, warnings, signature_ok, form_ok):
    """Print summary and recommendations"""
    print_header("Summary & Recommendations")
    
    if not issues and not warnings and signature_ok and form_ok:
        print("\n✅ All checks passed!")
        print("\nYour WayForPay configuration looks good.")
        print("\nIf you're still experiencing issues:")
        print("1. Verify your credentials in WayForPay dashboard")
        print("2. Ensure your merchant account is active")
        print("3. Check that your domain is registered correctly")
        print("4. Make sure callback URL is accessible from internet")
        print("5. Review payment service logs for errors")
    else:
        print("\n❌ Configuration issues found!\n")
        
        if issues:
            print("CRITICAL ISSUES (must fix):")
            for i, issue in enumerate(issues, 1):
                print(f"  {i}. {issue}")
        
        if warnings:
            print("\nWARNINGS:")
            for i, warning in enumerate(warnings, 1):
                print(f"  {i}. {warning}")
        
        if not signature_ok:
            print("\n⚠️  Signature generation failed - check secret key")
        
        if not form_ok:
            print("\n⚠️  Form generation incomplete - check configuration")
        
        print("\n" + "=" * 80)
        print("NEXT STEPS:")
        print("=" * 80)
        print("\n1. Read the setup guide:")
        print("   cat WAYFORPAY_SETUP.md")
        print("\n2. Get real WayForPay credentials:")
        print("   - Sign up at https://wayforpay.com/")
        print("   - Complete merchant verification")
        print("   - Get your merchant account ID and secret key")
        print("\n3. Update .env.docker with real credentials")
        print("\n4. Restart payment service:")
        print("   docker-compose restart payment_service")
        print("\n5. Test again:")
        print("   docker-compose exec payment_service python check_wayforpay_config.py")


def main():
    """Main diagnostic function"""
    print("\n" + "=" * 80)
    print("  WayForPay Configuration Diagnostic Tool")
    print("=" * 80)
    print("\nThis tool checks if your WayForPay integration is properly configured.")
    print("If the payment form is not displaying, this will help identify why.")
    
    # Run checks
    issues, warnings = check_configuration()
    signature_ok = test_signature_generation()
    form_ok = test_form_generation()
    
    # Print summary
    print_summary(issues, warnings, signature_ok, form_ok)
    
    print("\n" + "=" * 80)
    print()


if __name__ == "__main__":
    main()
