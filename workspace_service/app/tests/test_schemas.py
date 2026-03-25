"""
Unit tests for workspace and internal Pydantic schemas.

Tests cover:
- WorkspaceCreate validation (name length, type)
- WorkspaceUpdate validation (optional name)
- WorkspaceResponse serialisation (from_attributes, computed fields)
- WorkspaceListResponse
- AuthorizeRequest (role migration)
- AuthorizeResponse
- UserWorkspaceItem, UserWorkspacesResponse
- CreatePersonalWorkspaceRequest, CreatePersonalWorkspaceResponse
- DefaultWorkspaceResponse
"""
import pytest
from datetime import datetime, timezone
from uuid import uuid4

from pydantic import ValidationError

from app.schemas.workspace import (
    WorkspaceCreate,
    WorkspaceUpdate,
    WorkspaceResponse,
    WorkspaceListResponse,
)
from app.schemas.internal import (
    AuthorizeRequest,
    AuthorizeResponse,
    UserWorkspaceItem,
    UserWorkspacesResponse,
    CreatePersonalWorkspaceRequest,
    CreatePersonalWorkspaceResponse,
    DefaultWorkspaceResponse,
    ROLE_MIGRATION_MAP,
)
from app.models.workspace import WorkspaceType
from app.models.member import MemberRole


# ==================== WorkspaceCreate ====================


class TestWorkspaceCreate:
    """Tests for WorkspaceCreate schema."""

    def test_valid_shared(self):
        data = WorkspaceCreate(name="Test Workspace", type=WorkspaceType.SHARED)
        assert data.name == "Test Workspace"
        assert data.type == WorkspaceType.SHARED

    def test_default_type_is_shared(self):
        data = WorkspaceCreate(name="Budget")
        assert data.type == WorkspaceType.SHARED

    def test_name_min_length(self):
        with pytest.raises(ValidationError):
            WorkspaceCreate(name="")

    def test_name_max_length(self):
        with pytest.raises(ValidationError):
            WorkspaceCreate(name="x" * 256)

    def test_name_exactly_max(self):
        data = WorkspaceCreate(name="x" * 255)
        assert len(data.name) == 255

    def test_missing_name_raises(self):
        with pytest.raises(ValidationError):
            WorkspaceCreate()

    def test_personal_type(self):
        data = WorkspaceCreate(name="My Space", type=WorkspaceType.PERSONAL)
        assert data.type == WorkspaceType.PERSONAL


# ==================== WorkspaceUpdate ====================


class TestWorkspaceUpdate:
    """Tests for WorkspaceUpdate schema."""

    def test_empty_update(self):
        """All fields are optional."""
        data = WorkspaceUpdate()
        assert data.name is None

    def test_name_update(self):
        data = WorkspaceUpdate(name="New Name")
        assert data.name == "New Name"

    def test_name_too_long(self):
        with pytest.raises(ValidationError):
            WorkspaceUpdate(name="x" * 256)

    def test_name_empty_string_raises(self):
        with pytest.raises(ValidationError):
            WorkspaceUpdate(name="")


# ==================== WorkspaceResponse ====================


class TestWorkspaceResponse:
    """Tests for WorkspaceResponse schema."""

    def test_full_response(self):
        ws_id = uuid4()
        now = datetime.now(timezone.utc)
        resp = WorkspaceResponse(
            id=ws_id,
            name="Shared",
            type=WorkspaceType.SHARED,
            owner_user_id=1,
            created_at=now,
            updated_at=None,
            archived_at=None,
            is_archived=False,
            member_count=3,
            current_user_role="owner",
        )
        assert resp.id == ws_id
        assert resp.is_archived is False
        assert resp.is_read_only is False
        assert resp.member_count == 3

    def test_is_read_only_default_false(self):
        ws_id = uuid4()
        now = datetime.now(timezone.utc)
        resp = WorkspaceResponse(
            id=ws_id,
            name="Test",
            type=WorkspaceType.SHARED,
            owner_user_id=1,
            created_at=now,
            is_archived=False,
        )
        assert resp.is_read_only is False

    def test_from_attributes_config(self):
        """from_attributes is True, enabling ORM mode."""
        assert WorkspaceResponse.model_config.get("from_attributes") is True


# ==================== WorkspaceListResponse ====================


class TestWorkspaceListResponse:
    """Tests for WorkspaceListResponse schema."""

    def test_empty_list(self):
        resp = WorkspaceListResponse(workspaces=[], total=0)
        assert resp.total == 0
        assert resp.workspaces == []

    def test_with_items(self):
        ws_id = uuid4()
        now = datetime.now(timezone.utc)
        item = WorkspaceResponse(
            id=ws_id,
            name="WS",
            type=WorkspaceType.SHARED,
            owner_user_id=1,
            created_at=now,
            is_archived=False,
        )
        resp = WorkspaceListResponse(workspaces=[item], total=1)
        assert resp.total == 1
        assert len(resp.workspaces) == 1


# ==================== AuthorizeRequest ====================


class TestAuthorizeRequest:
    """Tests for AuthorizeRequest schema with role migration."""

    def test_valid_request(self):
        req = AuthorizeRequest(user_id=1, required_role=MemberRole.READ)
        assert req.user_id == 1
        assert req.required_role == MemberRole.READ

    def test_default_role_is_read(self):
        req = AuthorizeRequest(user_id=5)
        assert req.required_role == MemberRole.READ

    def test_migrate_member_to_read(self):
        req = AuthorizeRequest(user_id=1, required_role="member")
        assert req.required_role == MemberRole.READ

    def test_migrate_viewer_to_read(self):
        req = AuthorizeRequest(user_id=1, required_role="viewer")
        assert req.required_role == MemberRole.READ

    def test_migrate_admin_to_full(self):
        req = AuthorizeRequest(user_id=1, required_role="admin")
        assert req.required_role == MemberRole.FULL

    def test_new_role_names_pass_through(self):
        req = AuthorizeRequest(user_id=1, required_role="owner")
        assert req.required_role == MemberRole.OWNER

    def test_role_migration_map_values(self):
        assert ROLE_MIGRATION_MAP["member"] == "read"
        assert ROLE_MIGRATION_MAP["viewer"] == "read"
        assert ROLE_MIGRATION_MAP["admin"] == "full"


# ==================== AuthorizeResponse ====================


class TestAuthorizeResponse:
    """Tests for AuthorizeResponse schema."""

    def test_authorized(self):
        ws_id = uuid4()
        resp = AuthorizeResponse(
            authorized=True,
            role=MemberRole.FULL,
            workspace_id=ws_id,
            user_id=1,
        )
        assert resp.authorized is True
        assert resp.role == MemberRole.FULL

    def test_role_optional(self):
        ws_id = uuid4()
        resp = AuthorizeResponse(
            authorized=False,
            workspace_id=ws_id,
            user_id=1,
        )
        assert resp.role is None


# ==================== UserWorkspaceItem / Response ====================


class TestUserWorkspaceItem:
    """Tests for UserWorkspaceItem schema."""

    def test_basic(self):
        item = UserWorkspaceItem(
            id=uuid4(),
            name="Personal",
            role=MemberRole.OWNER,
            type="personal",
            is_default=True,
        )
        assert item.is_default is True

    def test_is_default_defaults_false(self):
        item = UserWorkspaceItem(
            id=uuid4(),
            name="Shared",
            role=MemberRole.FULL,
            type="shared",
        )
        assert item.is_default is False


class TestUserWorkspacesResponse:
    """Tests for UserWorkspacesResponse schema."""

    def test_empty(self):
        resp = UserWorkspacesResponse(workspaces=[])
        assert resp.workspaces == []


# ==================== CreatePersonalWorkspace ====================


class TestCreatePersonalWorkspaceRequest:
    """Tests for CreatePersonalWorkspaceRequest schema."""

    def test_valid(self):
        req = CreatePersonalWorkspaceRequest(user_id=42)
        assert req.user_id == 42


class TestCreatePersonalWorkspaceResponse:
    """Tests for CreatePersonalWorkspaceResponse schema."""

    def test_valid(self):
        ws_id = uuid4()
        resp = CreatePersonalWorkspaceResponse(workspace_id=ws_id)
        assert resp.workspace_id == ws_id


# ==================== DefaultWorkspaceResponse ====================


class TestDefaultWorkspaceResponse:
    """Tests for DefaultWorkspaceResponse schema."""

    def test_valid(self):
        ws_id = uuid4()
        resp = DefaultWorkspaceResponse(
            workspace_id=ws_id,
            name="Personal",
            type="personal",
        )
        assert resp.workspace_id == ws_id
        assert resp.name == "Personal"
        assert resp.type == "personal"
