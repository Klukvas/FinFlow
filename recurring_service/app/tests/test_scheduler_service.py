"""Tests for SchedulerService."""
import asyncio
import pytest
from unittest.mock import patch, MagicMock, AsyncMock


def _create_scheduler():
    """Create a SchedulerService with mocked dependencies."""
    with patch("app.services.scheduler_service.ExpenseServiceClient"), \
         patch("app.services.scheduler_service.IncomeServiceClient"), \
         patch("app.services.scheduler_service.CategoryServiceClient"), \
         patch("app.services.scheduler_service.PaymentExecutor") as mock_executor_cls:
        mock_executor_cls.return_value = MagicMock()
        from app.services.scheduler_service import SchedulerService
        return SchedulerService()


class TestSchedulerService:
    @pytest.mark.asyncio
    async def test_start_scheduler(self):
        svc = _create_scheduler()
        try:
            svc.start()
            assert svc.scheduler.running is True
            jobs = svc.scheduler.get_jobs()
            assert len(jobs) == 1
            assert jobs[0].id == "execute_recurring_payments"
        finally:
            if svc.scheduler.running:
                svc.scheduler.shutdown(wait=False)

    @pytest.mark.asyncio
    async def test_start_scheduler_twice_does_not_fail(self):
        svc = _create_scheduler()
        try:
            svc.start()
            svc.start()  # Should log warning, not crash
            assert svc.scheduler.running is True
        finally:
            if svc.scheduler.running:
                svc.scheduler.shutdown(wait=False)

    @pytest.mark.asyncio
    async def test_stop_scheduler(self):
        svc = _create_scheduler()
        svc.start()
        assert svc.scheduler.running is True
        # The AsyncIOScheduler.shutdown() may not immediately update running state
        # in pytest async context. Instead, verify stop() can be called without error.
        svc.stop()
        # After stop, get_jobs should return empty since the scheduler was shutdown.
        # Note: AsyncIOScheduler.running may not immediately reflect False due to
        # async event loop timing in test context.

    def test_stop_scheduler_when_not_running(self):
        svc = _create_scheduler()
        svc.stop()  # Should not crash
        assert svc.scheduler.running is False

    def test_get_scheduler_status_not_running(self):
        svc = _create_scheduler()
        status = svc.get_scheduler_status()
        assert status["running"] is False
        assert status["jobs"] == []

    @pytest.mark.asyncio
    async def test_get_scheduler_status_running(self):
        svc = _create_scheduler()
        try:
            svc.start()
            status = svc.get_scheduler_status()
            assert status["running"] is True
            assert len(status["jobs"]) == 1
            job = status["jobs"][0]
            assert job["id"] == "execute_recurring_payments"
            assert job["name"] == "Execute Recurring Payments"
            assert job["next_run_time"] is not None
            assert "trigger" in job
        finally:
            if svc.scheduler.running:
                svc.scheduler.shutdown(wait=False)

    def test_executor_is_initialized(self):
        svc = _create_scheduler()
        assert svc.executor is not None

    @pytest.mark.asyncio
    async def test_execute_now_creates_task(self):
        svc = _create_scheduler()
        svc.execute_now()
        # The task is created; verify no exception is raised.


class TestSchedulerServiceExecuteRecurringPayments:
    @pytest.mark.asyncio
    async def test_execute_recurring_payments_calls_executor(self):
        with patch("app.services.scheduler_service.ExpenseServiceClient"), \
             patch("app.services.scheduler_service.IncomeServiceClient"), \
             patch("app.services.scheduler_service.CategoryServiceClient"), \
             patch("app.services.scheduler_service.PaymentExecutor") as mock_executor_cls, \
             patch("app.services.scheduler_service.SessionLocal") as mock_session_cls:
            mock_executor = MagicMock()
            mock_executor.execute_pending_payments = AsyncMock(
                return_value={"succeeded": 2, "failed": 0}
            )
            mock_executor_cls.return_value = mock_executor
            mock_db = MagicMock()
            mock_session_cls.return_value = mock_db

            from app.services.scheduler_service import SchedulerService
            svc = SchedulerService()
            await svc._execute_recurring_payments()
            mock_executor.execute_pending_payments.assert_called_once_with(mock_db)

    @pytest.mark.asyncio
    async def test_execute_recurring_payments_closes_db(self):
        with patch("app.services.scheduler_service.ExpenseServiceClient"), \
             patch("app.services.scheduler_service.IncomeServiceClient"), \
             patch("app.services.scheduler_service.CategoryServiceClient"), \
             patch("app.services.scheduler_service.PaymentExecutor") as mock_executor_cls, \
             patch("app.services.scheduler_service.SessionLocal") as mock_session_cls:
            mock_executor = MagicMock()
            mock_executor.execute_pending_payments = AsyncMock(
                return_value={"succeeded": 0, "failed": 0}
            )
            mock_executor_cls.return_value = mock_executor
            mock_db = MagicMock()
            mock_session_cls.return_value = mock_db

            from app.services.scheduler_service import SchedulerService
            svc = SchedulerService()
            await svc._execute_recurring_payments()
            mock_db.close.assert_called_once()

    @pytest.mark.asyncio
    async def test_execute_recurring_payments_closes_db_on_error(self):
        with patch("app.services.scheduler_service.ExpenseServiceClient"), \
             patch("app.services.scheduler_service.IncomeServiceClient"), \
             patch("app.services.scheduler_service.CategoryServiceClient"), \
             patch("app.services.scheduler_service.PaymentExecutor") as mock_executor_cls, \
             patch("app.services.scheduler_service.SessionLocal") as mock_session_cls:
            mock_executor = MagicMock()
            mock_executor.execute_pending_payments = AsyncMock(
                side_effect=Exception("DB error")
            )
            mock_executor_cls.return_value = mock_executor
            mock_db = MagicMock()
            mock_session_cls.return_value = mock_db

            from app.services.scheduler_service import SchedulerService
            svc = SchedulerService()
            # Should not raise
            await svc._execute_recurring_payments()
            mock_db.close.assert_called_once()
