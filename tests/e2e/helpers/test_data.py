"""Test data factory functions. All return new data, no mutation."""
from __future__ import annotations

import uuid
from datetime import date, timedelta


def unique_email() -> str:
    return f"e2e_{uuid.uuid4().hex[:8]}@test.example.com"


def strong_password() -> str:
    return "TestPass123!"


def category_name(prefix: str = "E2E") -> str:
    return f"{prefix}_{uuid.uuid4().hex[:6]}"


def workspace_name() -> str:
    return f"E2E Workspace {uuid.uuid4().hex[:6]}"


def account_name() -> str:
    return f"E2E Account {uuid.uuid4().hex[:6]}"


def date_range(days_back: int = 30) -> tuple[str, str]:
    end = date.today()
    start = end - timedelta(days=days_back)
    return start.isoformat(), end.isoformat()
