"""
Unit tests for dependency injection functions.

Tests cover:
- get_workspace_service returns WorkspaceService with given db
- get_invite_service returns InviteService with given db
"""
import pytest
from unittest.mock import MagicMock

from app.dependencies import get_workspace_service, get_invite_service
from app.services.workspace import WorkspaceService
from app.services.invite import InviteService


class TestGetWorkspaceService:
    """Tests for get_workspace_service dependency."""

    def test_returns_workspace_service(self):
        mock_db = MagicMock()
        service = get_workspace_service(db=mock_db)
        assert isinstance(service, WorkspaceService)

    def test_service_has_db(self):
        mock_db = MagicMock()
        service = get_workspace_service(db=mock_db)
        assert service.db is mock_db

    def test_different_sessions_yield_different_services(self):
        db1 = MagicMock()
        db2 = MagicMock()
        s1 = get_workspace_service(db=db1)
        s2 = get_workspace_service(db=db2)
        assert s1 is not s2
        assert s1.db is not s2.db


class TestGetInviteService:
    """Tests for get_invite_service dependency."""

    def test_returns_invite_service(self):
        mock_db = MagicMock()
        service = get_invite_service(db=mock_db)
        assert isinstance(service, InviteService)

    def test_service_has_db(self):
        mock_db = MagicMock()
        service = get_invite_service(db=mock_db)
        assert service.db is mock_db

    def test_different_sessions_yield_different_services(self):
        db1 = MagicMock()
        db2 = MagicMock()
        s1 = get_invite_service(db=db1)
        s2 = get_invite_service(db=db2)
        assert s1 is not s2
