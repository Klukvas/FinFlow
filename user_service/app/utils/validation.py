import re
from typing import List
from app.config import settings
from app.exceptions import PasswordPolicyError, UsernamePolicyError, UserValidationError

def validate_password_strength(password: str) -> None:
    """Validate password against security policy"""
    errors = []
    
    if len(password) < settings.MIN_PASSWORD_LENGTH:
        errors.append(f"Password must be at least {settings.MIN_PASSWORD_LENGTH} characters long")
    
    if len(password) > settings.MAX_PASSWORD_LENGTH:
        errors.append(f"Password must be no more than {settings.MAX_PASSWORD_LENGTH} characters long")
    
    if settings.REQUIRE_UPPERCASE and not re.search(r'[A-Z]', password):
        errors.append("Password must contain at least one uppercase letter")
    
    if settings.REQUIRE_LOWERCASE and not re.search(r'[a-z]', password):
        errors.append("Password must contain at least one lowercase letter")
    
    if settings.REQUIRE_NUMBERS and not re.search(r'\d', password):
        errors.append("Password must contain at least one number")
    
    if settings.REQUIRE_SPECIAL_CHARS and not re.search(r'[!@#$%^&*(),.?":{}|<>]', password):
        errors.append("Password must contain at least one special character")
    
    # Check for common weak patterns
    if re.search(r'(.)\1{2,}', password):
        errors.append("Password cannot contain more than 2 consecutive identical characters")
    
    if errors:
        raise PasswordPolicyError("; ".join(errors))

def validate_username(username: str) -> None:
    """Validate username format and requirements"""
    errors = []
    
    if len(username) < settings.MIN_USERNAME_LENGTH:
        errors.append(f"Username must be at least {settings.MIN_USERNAME_LENGTH} characters long")
    
    if len(username) > settings.MAX_USERNAME_LENGTH:
        errors.append(f"Username must be no more than {settings.MAX_USERNAME_LENGTH} characters long")
    
    # Username should only contain alphanumeric characters, underscores, and hyphens
    if not re.match(r'^[a-zA-Z0-9_-]+$', username):
        errors.append("Username can only contain letters, numbers, underscores, and hyphens")
    
    # Username should start with a letter or number
    if not re.match(r'^[a-zA-Z0-9]', username):
        errors.append("Username must start with a letter or number")
    
    # Username should not end with underscore or hyphen
    if username.endswith('_') or username.endswith('-'):
        errors.append("Username cannot end with underscore or hyphen")
    
    # Check for reserved usernames
    reserved_usernames = ['admin', 'root', 'administrator', 'user', 'test', 'api', 'www', 'mail', 'ftp']
    if username.lower() in reserved_usernames:
        errors.append("This username is reserved and cannot be used")
    
    if errors:
        raise UsernamePolicyError("; ".join(errors))

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

