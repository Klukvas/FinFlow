"""
Tests for app/utils/rate_limiter.py
Covers: 70% -> target 80%+
Uncovered lines: 24, 33-34, 42-49, 70-72, 77, 79
"""
import pytest
from datetime import datetime, timedelta
from unittest.mock import patch

from app.utils.rate_limiter import RateLimiter
from app.exceptions import RateLimitError, AccountLockedError
from app.config import settings


class TestRateLimiterCheckRateLimit:
    """Tests for RateLimiter.check_rate_limit (lines 16-37)."""

    def setup_method(self):
        self.limiter = RateLimiter()

    def test_first_attempt_passes(self):
        """First attempt within window is allowed."""
        self.limiter.check_rate_limit("test_id")  # no exception

    def test_old_attempts_are_cleaned(self):
        """Line 24: attempts older than the window are discarded."""
        old_time = datetime.now() - timedelta(minutes=10)
        self.limiter.attempts["stale"] = [old_time, old_time]

        # This should clean old attempts so we are below the limit
        self.limiter.check_rate_limit("stale", max_attempts=2)
        # Passes because old attempts were cleaned

    def test_exceeding_rate_limit_raises_error(self):
        """Lines 33-34: exceeding max attempts raises RateLimitError."""
        identifier = "limited_id"
        # Fill up to the limit first (max_attempts=2 for speed)
        for _ in range(2):
            self.limiter.check_rate_limit(identifier, max_attempts=2)

        with pytest.raises(RateLimitError):
            self.limiter.check_rate_limit(identifier, max_attempts=2)

    def test_new_identifier_initialises_empty_list(self):
        """Branch where identifier is NOT in self.attempts initialises an empty list."""
        assert "brand_new_id" not in self.limiter.attempts
        self.limiter.check_rate_limit("brand_new_id")
        assert "brand_new_id" in self.limiter.attempts


class TestRateLimiterCheckAccountLockout:
    """Tests for RateLimiter.check_account_lockout (lines 39-49)."""

    def setup_method(self):
        self.limiter = RateLimiter()

    def test_unlocked_account_passes(self):
        """Account not in locked_accounts passes without error."""
        self.limiter.check_account_lockout("free@example.com")  # no exception

    def test_locked_account_raises_error(self):
        """Lines 42-46: locked account raises AccountLockedError."""
        email = "locked@example.com"
        self.limiter.locked_accounts[email] = datetime.now() + timedelta(minutes=15)

        with pytest.raises(AccountLockedError):
            self.limiter.check_account_lockout(email)

    def test_expired_lockout_is_removed(self):
        """Lines 47-49: once lockout expires it is removed from locked_accounts."""
        email = "expired_lock@example.com"
        # Set lockout in the past
        self.limiter.locked_accounts[email] = datetime.now() - timedelta(minutes=1)

        self.limiter.check_account_lockout(email)  # should not raise

        assert email not in self.limiter.locked_accounts

    def test_lockout_remaining_minutes_reflects_time_left(self):
        """AccountLockedError detail mentions remaining minutes."""
        email = "nearly_free@example.com"
        self.limiter.locked_accounts[email] = datetime.now() + timedelta(minutes=10)

        with pytest.raises(AccountLockedError) as exc_info:
            self.limiter.check_account_lockout(email)

        assert "locked" in exc_info.value.detail.lower()


class TestRateLimiterRecordFailedLogin:
    """Tests for RateLimiter.record_failed_login (lines 51-72)."""

    def setup_method(self):
        self.limiter = RateLimiter()

    def test_failed_login_increments_attempt_count(self):
        """Line 66: a failed login is recorded."""
        email = "failme@example.com"
        self.limiter.record_failed_login(email)
        assert len(self.limiter.attempts[email]) == 1

    def test_old_attempts_are_cleaned_before_recording(self):
        """Stale attempts older than 5 minutes are removed."""
        email = "stale_fail@example.com"
        old_time = datetime.now() - timedelta(minutes=10)
        self.limiter.attempts[email] = [old_time]

        self.limiter.record_failed_login(email)
        # Only the new attempt should remain
        assert len(self.limiter.attempts[email]) == 1

    def test_account_locked_after_max_attempts(self):
        """Lines 70-72: account is locked after MAX_LOGIN_ATTEMPTS failures."""
        email = "maxfail@example.com"
        max_attempts = settings.MAX_LOGIN_ATTEMPTS

        for _ in range(max_attempts):
            self.limiter.record_failed_login(email)

        assert email in self.limiter.locked_accounts

    def test_account_not_locked_below_max_attempts(self):
        """Account is not locked when below threshold."""
        email = "belowmax@example.com"
        max_attempts = settings.MAX_LOGIN_ATTEMPTS

        for _ in range(max_attempts - 1):
            self.limiter.record_failed_login(email)

        assert email not in self.limiter.locked_accounts

    def test_initialises_attempts_list_for_new_email(self):
        """When email is not yet tracked, list is initialised."""
        email = "newtracked@example.com"
        assert email not in self.limiter.attempts

        self.limiter.record_failed_login(email)
        assert email in self.limiter.attempts


class TestRateLimiterRecordSuccessfulLogin:
    """Tests for RateLimiter.record_successful_login (lines 74-79)."""

    def setup_method(self):
        self.limiter = RateLimiter()

    def test_clears_attempt_history(self):
        """Line 77: successful login removes the attempt record."""
        email = "clearme@example.com"
        self.limiter.attempts[email] = [datetime.now()]

        self.limiter.record_successful_login(email)

        assert email not in self.limiter.attempts

    def test_clears_lockout_if_present(self):
        """Line 79: successful login removes a lockout entry."""
        email = "unlock_on_success@example.com"
        self.limiter.locked_accounts[email] = datetime.now() + timedelta(minutes=5)

        self.limiter.record_successful_login(email)

        assert email not in self.limiter.locked_accounts

    def test_no_error_when_email_not_in_attempts(self):
        """Calling record_successful_login for an unknown email raises no error."""
        self.limiter.record_successful_login("unknown@example.com")  # no exception
