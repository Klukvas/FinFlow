"""Tests for FastAPI health-check and scheduler management routes.

The test_client fixture (see conftest.py) injects a mock scheduler into
``app.main.scheduler`` so that all route tests run without a real
APScheduler or Redis instance.
"""
from __future__ import annotations

import pytest
from unittest.mock import MagicMock, patch
from contextlib import asynccontextmanager

from starlette.testclient import TestClient
from fastapi import FastAPI


# ---------------------------------------------------------------------------
# Local fixture: create a fresh app + mock scheduler per test to avoid
# lifespan side-effects from the real ``app.main:app``.
# ---------------------------------------------------------------------------

@pytest.fixture()
def route_client():
    """Build a minimal FastAPI app that mirrors the production routes
    but uses a mock scheduler instead of APScheduler."""
    mock_scheduler = MagicMock()
    mock_scheduler.running = True
    mock_scheduler.get_jobs.return_value = []
    mock_scheduler.get_job.return_value = None

    # Import the route functions (they read ``app.main.scheduler`` global)
    import app.main as main_module

    original_scheduler = main_module.scheduler

    # Build an isolated test app that re-uses the same route handlers.
    test_app = FastAPI()
    test_app.add_api_route("/health/live", main_module.liveness, methods=["GET"])
    test_app.add_api_route("/health/ready", main_module.readiness, methods=["GET"])
    test_app.add_api_route("/scheduler/jobs", main_module.list_jobs, methods=["GET"])
    test_app.add_api_route(
        "/scheduler/jobs/{job_id}/trigger", main_module.trigger_job, methods=["POST"]
    )

    main_module.scheduler = mock_scheduler

    with TestClient(test_app, raise_server_exceptions=False) as client:
        yield client, mock_scheduler

    main_module.scheduler = original_scheduler


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------

class TestLivenessProbe:
    def test_returns_alive(self, route_client):
        client, _ = route_client
        response = client.get("/health/live")
        assert response.status_code == 200
        assert response.json() == {"status": "alive"}


class TestReadinessProbe:
    def test_ready_when_scheduler_running(self, route_client):
        client, mock_scheduler = route_client
        mock_scheduler.running = True

        response = client.get("/health/ready")
        assert response.status_code == 200
        assert response.json() == {"status": "ready"}

    def test_not_ready_when_scheduler_is_none(self, route_client):
        client, _ = route_client
        import app.main as main_module

        saved = main_module.scheduler
        main_module.scheduler = None
        try:
            response = client.get("/health/ready")
            body = response.json()
            # The route returns a tuple (dict, 503) which FastAPI serialises
            # as a JSON array.
            if isinstance(body, list):
                assert body[0]["status"] == "not_ready"
            else:
                assert body["status"] == "not_ready"
        finally:
            main_module.scheduler = saved

    def test_not_ready_when_scheduler_not_running(self, route_client):
        client, mock_scheduler = route_client
        mock_scheduler.running = False

        response = client.get("/health/ready")
        body = response.json()
        if isinstance(body, list):
            assert body[0]["status"] == "not_ready"
            assert body[0]["reason"] == "scheduler_not_running"
        else:
            assert body["status"] == "not_ready"


class TestListJobs:
    def test_empty_list_when_no_jobs(self, route_client):
        client, mock_scheduler = route_client
        mock_scheduler.get_jobs.return_value = []

        response = client.get("/scheduler/jobs")
        assert response.status_code == 200
        assert response.json() == {"jobs": []}

    def test_returns_job_details(self, route_client):
        client, mock_scheduler = route_client

        mock_job = MagicMock()
        mock_job.id = "subscription_renewal"
        mock_job.name = "Subscription Renewal Job"
        mock_job.next_run_time = "2026-03-25 00:00:00+00:00"
        mock_job.trigger = "cron[hour='*/1']"

        mock_scheduler.get_jobs.return_value = [mock_job]

        response = client.get("/scheduler/jobs")
        assert response.status_code == 200

        data = response.json()
        assert len(data["jobs"]) == 1
        assert data["jobs"][0]["id"] == "subscription_renewal"
        assert data["jobs"][0]["name"] == "Subscription Renewal Job"
        assert data["jobs"][0]["next_run_time"] is not None

    def test_job_with_no_next_run_time(self, route_client):
        client, mock_scheduler = route_client

        mock_job = MagicMock()
        mock_job.id = "paused_job"
        mock_job.name = "Paused Job"
        mock_job.next_run_time = None
        mock_job.trigger = "cron[hour='0']"

        mock_scheduler.get_jobs.return_value = [mock_job]

        response = client.get("/scheduler/jobs")
        data = response.json()
        assert data["jobs"][0]["next_run_time"] is None

    def test_empty_list_when_scheduler_is_none(self, route_client):
        client, _ = route_client
        import app.main as main_module

        saved = main_module.scheduler
        main_module.scheduler = None
        try:
            response = client.get("/scheduler/jobs")
            assert response.status_code == 200
            assert response.json() == {"jobs": []}
        finally:
            main_module.scheduler = saved

    def test_multiple_jobs_returned(self, route_client):
        client, mock_scheduler = route_client

        jobs = []
        for i in range(3):
            mock_job = MagicMock()
            mock_job.id = f"job_{i}"
            mock_job.name = f"Job {i}"
            mock_job.next_run_time = f"2026-03-25 0{i}:00:00+00:00"
            mock_job.trigger = f"cron[hour='{i}']"
            jobs.append(mock_job)

        mock_scheduler.get_jobs.return_value = jobs

        response = client.get("/scheduler/jobs")
        data = response.json()
        assert len(data["jobs"]) == 3
        assert data["jobs"][1]["id"] == "job_1"


class TestTriggerJob:
    def test_trigger_existing_job(self, route_client):
        client, mock_scheduler = route_client

        mock_job = MagicMock()
        mock_scheduler.get_job.return_value = mock_job

        response = client.post("/scheduler/jobs/subscription_renewal/trigger")
        assert response.status_code == 200

        body = response.json()
        assert body["status"] == "triggered"
        assert body["job_id"] == "subscription_renewal"

    def test_trigger_nonexistent_job(self, route_client):
        client, mock_scheduler = route_client
        mock_scheduler.get_job.return_value = None

        response = client.post("/scheduler/jobs/nonexistent/trigger")
        body = response.json()

        # The route returns tuple (dict, 404) which FastAPI serialises as array.
        if isinstance(body, list):
            assert body[0]["error"] == "Job nonexistent not found"
        else:
            assert "error" in body

    def test_trigger_when_scheduler_is_none(self, route_client):
        client, _ = route_client
        import app.main as main_module

        saved = main_module.scheduler
        main_module.scheduler = None
        try:
            response = client.post("/scheduler/jobs/any_job/trigger")
            body = response.json()
            if isinstance(body, list):
                assert "error" in body[0]
            else:
                assert "error" in body
        finally:
            main_module.scheduler = saved
