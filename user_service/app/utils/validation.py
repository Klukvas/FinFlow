import re
from typing import List
from app.config import settings
from app.exceptions import PasswordPolicyError, UserValidationError

def validate_password_strength(password: str) -> None:
    """Validate password against security policy"""
    errors = []

    if len(password) < settings.MIN_PASSWORD_LENGTH:
        errors.append(f"Password must be at least {settings.MIN_PASSWORD_LENGTH} characters long")

    if len(password) > settings.MAX_PASSWORD_LENGTH:
        errors.append(f"Password must be no more than {settings.MAX_PASSWORD_LENGTH} characters long")

    if not re.search(r'[a-zA-Z]', password):
        errors.append("Password must contain at least one letter")

    if settings.REQUIRE_NUMBERS and not re.search(r'\d', password):
        errors.append("Password must contain at least one number")

    if errors:
        raise PasswordPolicyError("; ".join(errors))

def validate_email_domain(email: str) -> None:
    """Validate email domain (basic check)"""
    # Extract domain from email
    domain = email.split('@')[1].lower()
    
    # List of common disposable email domains (in production, use a more comprehensive list)
    disposable_domains = [
        '10minutemail.com', 'tempmail.org', 'guerrillamail.com',
        'mailinator.com', 'throwaway.email', 'temp-mail.org'
    ]
    
    if domain in disposable_domains:
        raise UserValidationError("Disposable email addresses are not allowed")

def sanitize_input(text: str) -> str:
    """Sanitize user input to prevent XSS and other attacks"""
    if not text:
        return text
    
    # Remove potentially dangerous characters
    dangerous_chars = ['<', '>', '"', "'", '&', ';', '(', ')', 'script', 'javascript', 'vbscript']
    
    for char in dangerous_chars:
        text = text.replace(char, '')
    
    return text.strip()

