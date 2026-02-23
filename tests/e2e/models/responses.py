"""Immutable response wrappers for API client methods."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Generic, Optional, TypeVar

T = TypeVar("T")


@dataclass(frozen=True)
class ApiResponse(Generic[T]):
    """Immutable envelope returned by every client method."""

    data: Optional[T] = None
    error: Optional[str] = None
    status_code: Optional[int] = None
    raw: Optional[dict[str, Any]] = field(default=None, repr=False)

    @property
    def ok(self) -> bool:
        return self.error is None and self.data is not None

    def raise_on_error(self) -> T:
        """Return data or raise AssertionError with full context."""
        if self.error is not None:
            raise AssertionError(
                f"API request failed [{self.status_code}]: {self.error}\n"
                f"Raw response: {self.raw}"
            )
        assert self.data is not None
        return self.data
