"""Tests for scheduler_service configuration and validation.

Since conftest.py replaces ``app.config`` in sys.modules to avoid
requiring real env vars at import time, this file loads the real
Settings class by reading the source and extracting just the class
definition, without executing the module-level ``settings = Settings()``
line.
"""
from __future__ import annotations

import ast
import importlib.util
import os
import textwrap
from unittest.mock import patch

import pytest
from pydantic import ValidationError
from pydantic_settings import BaseSettings
from pydantic import Field, model_validator


# ---------------------------------------------------------------------------
# Load the real Settings class from source without executing module-level code
# ---------------------------------------------------------------------------

def _load_real_settings_class():
    """Parse config.py's AST and exec only the Settings class definition."""
    config_path = os.path.normpath(
        os.path.join(os.path.dirname(__file__), os.pardir, "config.py")
    )

    with open(config_path, "r") as f:
        source = f.read()

    tree = ast.parse(source)

    # Extract only import statements and the Settings class definition.
    class_source_lines = []
    for node in tree.body:
        if isinstance(node, (ast.Import, ast.ImportFrom)):
            class_source_lines.append(ast.get_source_segment(source, node))
        elif isinstance(node, ast.ClassDef) and node.name == "Settings":
            class_source_lines.append(ast.get_source_segment(source, node))

    class_source = "\n\n".join(class_source_lines)

    # Execute the class definition in an isolated namespace.
    namespace = {
        "__builtins__": __builtins__,
        "BaseSettings": BaseSettings,
        "Field": Field,
        "model_validator": model_validator,
    }
    exec(class_source, namespace)

    return namespace["Settings"]


_RealSettings = _load_real_settings_class()


def _make_settings(**env_vars):
    """Create a Settings instance with the given env vars (isolated)."""
    with patch.dict("os.environ", env_vars, clear=True):
        return _RealSettings()


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------

class TestSettingsDefaults:
    def test_default_scheduler_timezone(self):
        s = _make_settings(
            DATABASE_URL="sqlite:///:memory:",
            internal_secret_token="real-secret-token-value",
        )
        assert s.scheduler_timezone == "UTC"

    def test_default_renewal_cron(self):
        s = _make_settings(
            DATABASE_URL="sqlite:///:memory:",
            internal_secret_token="real-secret-token-value",
        )
        assert s.renewal_check_cron == "0 */1 * * *"

    def test_default_max_retry(self):
        s = _make_settings(
            DATABASE_URL="sqlite:///:memory:",
            internal_secret_token="real-secret-token-value",
        )
        assert s.max_retry_attempts == 3

    def test_default_job_settings(self):
        s = _make_settings(
            DATABASE_URL="sqlite:///:memory:",
            internal_secret_token="real-secret-token-value",
        )
        assert s.job_max_instances == 1
        assert s.job_coalesce is True
        assert s.job_misfire_grace_time == 300

    def test_default_renewal_window_days(self):
        s = _make_settings(
            DATABASE_URL="sqlite:///:memory:",
            internal_secret_token="real-secret-token-value",
        )
        assert s.renewal_window_days == 1

    def test_default_retry_delay(self):
        s = _make_settings(
            DATABASE_URL="sqlite:///:memory:",
            internal_secret_token="real-secret-token-value",
        )
        assert s.retry_delay_seconds == 300


class TestSettingsValidation:
    def test_rejects_empty_internal_token(self):
        with pytest.raises(ValidationError):
            _make_settings(
                DATABASE_URL="sqlite:///:memory:",
                internal_secret_token="",
            )

    def test_rejects_placeholder_token(self):
        for placeholder in [
            "your-secret-key-here",
            "my-secret-token",
            "changeme-in-production",
            "your-internal-secret-token-here",
        ]:
            with pytest.raises(ValidationError):
                _make_settings(
                    DATABASE_URL="sqlite:///:memory:",
                    internal_secret_token=placeholder,
                )

    def test_accepts_real_token(self):
        s = _make_settings(
            DATABASE_URL="sqlite:///:memory:",
            internal_secret_token="production-strong-token-abc123",
        )
        assert s.internal_secret_token == "production-strong-token-abc123"

    def test_requires_database_url(self):
        with pytest.raises(ValidationError):
            _make_settings(
                internal_secret_token="real-token",
            )


class TestSettingsOverride:
    def test_env_override_cron(self):
        s = _make_settings(
            DATABASE_URL="sqlite:///:memory:",
            internal_secret_token="real-secret-token-value",
            renewal_check_cron="*/30 * * * *",
        )
        assert s.renewal_check_cron == "*/30 * * * *"

    def test_env_override_max_retries(self):
        s = _make_settings(
            DATABASE_URL="sqlite:///:memory:",
            internal_secret_token="real-secret-token-value",
            max_retry_attempts="5",
        )
        assert s.max_retry_attempts == 5

    def test_env_override_service_urls(self):
        s = _make_settings(
            DATABASE_URL="sqlite:///:memory:",
            internal_secret_token="real-secret-token-value",
            subscription_service_url="http://sub:9090",
            payment_service_url="http://pay:9091",
        )
        assert s.subscription_service_url == "http://sub:9090"
        assert s.payment_service_url == "http://pay:9091"
