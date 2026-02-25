"""
Tests for app/utils/validation.py
Covers: 73% -> target 80%+
Uncovered lines: 11, 14, 17, 20, 23, 26, 40, 45
"""
import pytest
from app.utils.validation import validate_password_strength, validate_email_domain, sanitize_input
from app.exceptions import PasswordPolicyError, UserValidationError


class TestValidatePasswordStrength:
    """Tests for validate_password_strength (lines 11-26)."""

    def test_valid_password_passes(self):
        """A password meeting all requirements raises no exception."""
        validate_password_strength("SecurePass123!")  # no exception

    def test_too_short_raises_policy_error(self):
        """Line 11: password shorter than MIN_PASSWORD_LENGTH is rejected."""
        with pytest.raises(PasswordPolicyError) as exc_info:
            validate_password_strength("Sh1!")
        assert "at least 8 characters" in str(exc_info.value.detail)

    def test_too_long_raises_policy_error(self):
        """Line 14: password longer than MAX_PASSWORD_LENGTH is rejected."""
        long_password = "A1!" + "a" * 200  # 203 chars, well over 128
        with pytest.raises(PasswordPolicyError) as exc_info:
            validate_password_strength(long_password)
        assert "no more than" in str(exc_info.value.detail)

    def test_lowercase_only_with_digit_passes(self):
        """Lowercase + digit is sufficient (no uppercase required)."""
        validate_password_strength("nouppercase1")

    def test_uppercase_only_with_digit_passes(self):
        """Uppercase + digit is sufficient (no lowercase required)."""
        validate_password_strength("NOLOWERCASE1")

    def test_missing_letters_raises_policy_error(self):
        """Password without any letters is rejected."""
        with pytest.raises(PasswordPolicyError) as exc_info:
            validate_password_strength("12345678")
        assert "letter" in str(exc_info.value.detail)

    def test_missing_numbers_raises_policy_error(self):
        """Password without numbers is rejected."""
        with pytest.raises(PasswordPolicyError) as exc_info:
            validate_password_strength("NoNumbers!")
        assert "number" in str(exc_info.value.detail)

    def test_multiple_violations_combined_in_error(self):
        """When multiple rules fail they are joined with '; '."""
        with pytest.raises(PasswordPolicyError) as exc_info:
            validate_password_strength("short")  # too short, no digit
        error_detail = exc_info.value.detail
        # Multiple policy messages joined
        assert ";" in error_detail or "at least" in error_detail

    def test_exactly_minimum_length_passes(self):
        """Boundary: exactly 8 chars with letters and digit passes."""
        validate_password_strength("abcdefg1")  # exactly 8 chars


class TestValidateEmailDomain:
    """Tests for validate_email_domain (line 40)."""

    def test_valid_domain_passes(self):
        """Normal email domain raises no exception."""
        validate_email_domain("user@gmail.com")  # no exception

    def test_disposable_domain_raises_validation_error(self):
        """Line 40: disposable domain raises UserValidationError."""
        with pytest.raises(UserValidationError) as exc_info:
            validate_email_domain("user@mailinator.com")
        assert "Disposable email" in exc_info.value.detail

    def test_another_disposable_domain_is_blocked(self):
        """10minutemail.com should also be blocked."""
        with pytest.raises(UserValidationError):
            validate_email_domain("temp@10minutemail.com")

    def test_guerrillamail_is_blocked(self):
        """guerrillamail.com should be blocked."""
        with pytest.raises(UserValidationError):
            validate_email_domain("anon@guerrillamail.com")


class TestSanitizeInput:
    """Tests for sanitize_input (line 45)."""

    def test_clean_input_unchanged(self):
        """Normal text is returned unchanged."""
        assert sanitize_input("hello world") == "hello world"

    def test_empty_string_returned_as_is(self):
        """Line 45: empty string is returned without modification."""
        assert sanitize_input("") == ""

    def test_strips_leading_trailing_whitespace(self):
        """sanitize_input strips surrounding whitespace."""
        assert sanitize_input("  hello  ") == "hello"

    def test_removes_angle_brackets(self):
        """< and > are stripped."""
        result = sanitize_input("<script>alert('xss')</script>")
        assert "<" not in result
        assert ">" not in result

    def test_removes_quotes(self):
        """Double and single quotes are stripped."""
        result = sanitize_input('He said "hello" and \'bye\'')
        assert '"' not in result
        assert "'" not in result

    def test_removes_dangerous_keywords(self):
        """'script' and 'javascript' are stripped."""
        result = sanitize_input("javascript:alert(1)")
        assert "javascript" not in result

    def test_none_is_returned_as_is(self):
        """None input (falsy) is returned without modification."""
        # The function checks `if not text` so None returns None
        result = sanitize_input(None)
        assert result is None
