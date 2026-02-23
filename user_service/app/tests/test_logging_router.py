"""
Tests for app/routers/logging.py
Covers: 44% -> target 80%+
Uncovered lines: 73-162, 185-234, 243-264
"""
import pytest
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)


class TestFrontendLogsSubmit:
    """Tests for POST /api/logging/frontend (lines 63-162)."""

    def test_submit_single_log_entry(self):
        """Basic log submission returns 200 with success=True."""
        payload = {
            "logs": [
                {
                    "level": "info",
                    "message": "Page loaded",
                }
            ]
        }
        response = client.post("/api/logging/frontend", json=payload)
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["processed"] == 1

    def test_submit_multiple_log_entries(self):
        """Multiple log entries are all processed."""
        payload = {
            "logs": [
                {"level": "info", "message": "event A"},
                {"level": "warn", "message": "event B"},
                {"level": "error", "message": "event C"},
            ],
            "session_id": "sess-123",
            "user_id": 42,
        }
        response = client.post("/api/logging/frontend", json=payload)
        assert response.status_code == 200
        data = response.json()
        assert data["processed"] == 3

    def test_submit_log_with_all_optional_fields(self):
        """Log entry with all optional fields is accepted."""
        payload = {
            "logs": [
                {
                    "level": "error",
                    "message": "Unhandled exception",
                    "timestamp": "2026-02-23T10:00:00Z",
                    "source": "app.js:42",
                    "stack": "Error: ...\n  at app.js:42",
                    "user_id": 1,
                    "session_id": "abc-def",
                    "url": "https://app.example.com/dashboard",
                    "user_agent": "Mozilla/5.0",
                    "extra": {"component": "Dashboard"},
                }
            ]
        }
        response = client.post("/api/logging/frontend", json=payload)
        assert response.status_code == 200
        assert response.json()["success"] is True

    def test_submit_log_debug_level(self):
        """Debug-level logs are accepted and mapped correctly."""
        payload = {"logs": [{"level": "debug", "message": "trace info"}]}
        response = client.post("/api/logging/frontend", json=payload)
        assert response.status_code == 200

    def test_submit_log_warning_alias(self):
        """'warning' level (not just 'warn') is accepted."""
        payload = {"logs": [{"level": "warning", "message": "low disk space"}]}
        response = client.post("/api/logging/frontend", json=payload)
        assert response.status_code == 200

    def test_submit_log_unknown_level_falls_back_to_info(self):
        """Unknown log level falls back to 'info'."""
        payload = {"logs": [{"level": "trace", "message": "some trace"}]}
        response = client.post("/api/logging/frontend", json=payload)
        assert response.status_code == 200

    def test_submit_empty_log_batch(self):
        """Empty logs list is accepted and returns processed=0."""
        payload = {"logs": []}
        response = client.post("/api/logging/frontend", json=payload)
        assert response.status_code == 200
        assert response.json()["processed"] == 0

    def test_submit_log_with_batch_session_id_fallback(self):
        """Log entry without session_id uses batch session_id."""
        payload = {
            "logs": [{"level": "info", "message": "test"}],
            "session_id": "batch-sess-456",
        }
        response = client.post("/api/logging/frontend", json=payload)
        assert response.status_code == 200

    def test_submit_log_with_log_level_alias(self):
        """'log' level is mapped to 'info'."""
        payload = {"logs": [{"level": "log", "message": "console.log output"}]}
        response = client.post("/api/logging/frontend", json=payload)
        assert response.status_code == 200


class TestFrontendErrorSubmit:
    """Tests for POST /api/logging/frontend/error (lines 164-234)."""

    def test_submit_error_basic(self):
        """Basic error log submission returns 200."""
        payload = {
            "level": "error",
            "message": "TypeError: Cannot read property 'x' of undefined",
        }
        response = client.post("/api/logging/frontend/error", json=payload)
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["processed"] == 1

    def test_submit_error_with_stack_trace(self):
        """Error with stack trace is processed correctly."""
        payload = {
            "level": "error",
            "message": "Something broke",
            "stack": "Error: Something broke\n  at foo.js:10",
            "source": "foo.js:10",
            "url": "https://app.example.com",
            "session_id": "err-sess-001",
        }
        response = client.post("/api/logging/frontend/error", json=payload)
        assert response.status_code == 200

    def test_submit_error_with_extra_fields(self):
        """Error with extra metadata fields is accepted."""
        payload = {
            "level": "error",
            "message": "Payment failed",
            "extra": {"amount": 99.99, "currency": "USD"},
            "user_id": 7,
        }
        response = client.post("/api/logging/frontend/error", json=payload)
        assert response.status_code == 200

    def test_submit_error_with_user_agent(self):
        """Error with explicit user_agent is recorded."""
        payload = {
            "level": "error",
            "message": "Safari crash",
            "user_agent": "Safari/537.36",
        }
        response = client.post("/api/logging/frontend/error", json=payload)
        assert response.status_code == 200


class TestLoggingHealthCheck:
    """Tests for GET /api/logging/health (lines 236-264)."""

    def test_health_check_returns_healthy(self):
        """Health check endpoint returns healthy status."""
        response = client.get("/api/logging/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        assert data["service"] == "frontend_logging"
        assert "timestamp" in data
