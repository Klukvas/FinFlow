from datetime import datetime, timedelta
from typing import Dict, Optional
from app.config import settings
from app.exceptions import RateLimitError, AccountLockedError
from app.utils.logger import get_logger

logger = get_logger(__name__)

class RateLimiter:
    """Simple in-memory rate limiter (in production, use Redis or similar)"""
    
    def __init__(self):
        self.attempts: Dict[str, list] = {}
        self.locked_accounts: Dict[str, datetime] = {}
    
    def check_rate_limit(self, identifier: str, max_attempts: int = None, window_minutes: int = 1) -> None:
        """Check if identifier has exceeded rate limit"""
        max_attempts = max_attempts or settings.RATE_LIMIT_PER_MINUTE
        now = datetime.now()
        window_start = now - timedelta(minutes=window_minutes)
        
        # Clean old attempts
        if identifier in self.attempts:
            self.attempts[identifier] = [
                attempt_time for attempt_time in self.attempts[identifier]
                if attempt_time > window_start
            ]
        else:
            self.attempts[identifier] = []
        
        # Check if rate limit exceeded
        if len(self.attempts[identifier]) >= max_attempts:
            logger.warning(f"Rate limit exceeded for identifier: {identifier}")
            raise RateLimitError()
        
        # Record this attempt
        self.attempts[identifier].append(now)
    
    def check_account_lockout(self, email: str) -> None:
        """Check if account is locked due to failed login attempts"""
        if email in self.locked_accounts:
            lockout_time = self.locked_accounts[email]
            if datetime.now() < lockout_time:
                remaining_minutes = int((lockout_time - datetime.now()).total_seconds() / 60)
                logger.warning(f"Account locked for email: {email}, remaining: {remaining_minutes} minutes")
                raise AccountLockedError(remaining_minutes)
            else:
                # Lockout period expired, remove from locked accounts
                del self.locked_accounts[email]
    
    def record_failed_login(self, email: str) -> None:
        """Record a failed login attempt"""
        now = datetime.now()
        window_start = now - timedelta(minutes=5)  # 5-minute window for login attempts
        
        if email not in self.attempts:
            self.attempts[email] = []
        
        # Clean old attempts
        self.attempts[email] = [
            attempt_time for attempt_time in self.attempts[email]
            if attempt_time > window_start
        ]
        
        # Add this failed attempt
        self.attempts[email].append(now)
        
        # Check if account should be locked
        if len(self.attempts[email]) >= settings.MAX_LOGIN_ATTEMPTS:
            lockout_until = now + timedelta(minutes=settings.LOCKOUT_DURATION_MINUTES)
            self.locked_accounts[email] = lockout_until
            logger.warning(f"Account locked for email: {email} until {lockout_until}")
    
    def record_successful_login(self, email: str) -> None:
        """Record a successful login and clear failed attempts"""
        if email in self.attempts:
            del self.attempts[email]
        if email in self.locked_accounts:
            del self.locked_accounts[email]

# Global rate limiter instance
rate_limiter = RateLimiter()

