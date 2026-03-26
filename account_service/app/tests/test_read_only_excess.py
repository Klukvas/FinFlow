"""
Tests for read-only excess behavior in AccountService.

When a user downgrades their plan (or the plan limit changes),
accounts beyond the new limit become read-only. The oldest N accounts
(by created_at ASC) remain editable; the rest are read-only.

Covers:
- list endpoint: is_read_only flag computed via get_read_only_ids
- update/archive blocked on read-only accounts
- full flow: create accounts, change limit, verify behavior
- boundary cases: exactly at limit, zero limit
"""
import pytest
from random import randint
from unittest.mock import patch, MagicMock
from uuid import UUID
from starlette import status

from app.services.account import AccountService
from app.models.account import Account, AccountType
from app.schemas.account import AccountCreate, AccountUpdate
from app.exceptions import (
    AccountReadOnlyExcessError,
    AccountLimitExceededError,
)
from app.tests.conftest import (
    TEST_WORKSPACE_ID,
    TestingSessionLocal,
    create_account_in_db,
)
from shared.clients.subscription import SubscriptionClient

# Save real methods before conftest autouse fixtures patch them at the class level.
# Tests that need the actual logic (with get_user_features mocked) restore these.
_real_get_read_only_ids = SubscriptionClient.get_read_only_ids
_real_check_modify_allowed = SubscriptionClient.check_modify_allowed

USER_ID = 1

WORKSPACE_HEADER = {"X-Workspace-Id": str(TEST_WORKSPACE_ID)}


def _auth_headers(user_id: int) -> dict:
    return {"Authorization": "Bearer test-token", **WORKSPACE_HEADER}


def _make_service(db_session) -> AccountService:
    """Build an AccountService with mocked external clients."""
    expense_client = MagicMock()
    income_client = MagicMock()
    currency_client = MagicMock()

    with patch(
        "shared.clients.workspace.WorkspaceClient.authorize",
        return_value=(True, "owner"),
    ), patch(
        "shared.clients.subscription.SubscriptionClient.check_limit",
        return_value=(True, None),
    ), patch(
        "shared.clients.subscription.SubscriptionClient.check_modify_allowed",
        return_value=True,
    ):
        service = AccountService(db_session, expense_client, income_client, currency_client)

    return service


def _features_with_limit(limit: int) -> dict:
    """Return a features dict with a given account limit."""
    return {"accounts": {"enabled": True, "limit_value": limit, "feature_code": "accounts"}}


def _features_unlimited() -> dict:
    """Return a features dict with no account limit."""
    return {"accounts": {"enabled": True, "limit_value": None, "feature_code": "accounts"}}


# ---------------------------------------------------------------------------
# Service-level: get_read_only_ids via _get_ordered_ids
# ---------------------------------------------------------------------------


class TestGetReadOnlyIdsInListContext:
    """Verify that get_read_only_ids returns the correct IDs based on limit."""

    def test_over_limit_marks_excess_as_read_only(self, db_session):
        """3 accounts, limit 2 → newest account is read-only."""
        service = _make_service(db_session)
        a1 = create_account_in_db(db_session, owner_id=USER_ID, name="First")
        a2 = create_account_in_db(db_session, owner_id=USER_ID, name="Second")
        a3 = create_account_in_db(db_session, owner_id=USER_ID, name="Third")

        ordered_ids = service._get_ordered_ids(TEST_WORKSPACE_ID)

        with patch.object(
            service.subscription_client,
            "get_user_features",
            return_value=_features_with_limit(2),
        ), patch.object(
            service.subscription_client,
            "get_read_only_ids",
            _real_get_read_only_ids.__get__(service.subscription_client),
        ):
            read_only = service.subscription_client.get_read_only_ids(
                USER_ID, "accounts", ordered_ids
            )

        assert a1.id not in read_only
        assert a2.id not in read_only
        assert a3.id in read_only

    def test_within_limit_all_editable(self, db_session):
        """2 accounts, limit 3 → no read-only accounts."""
        service = _make_service(db_session)
        a1 = create_account_in_db(db_session, owner_id=USER_ID, name="First")
        a2 = create_account_in_db(db_session, owner_id=USER_ID, name="Second")

        ordered_ids = service._get_ordered_ids(TEST_WORKSPACE_ID)

        with patch.object(
            service.subscription_client,
            "get_user_features",
            return_value=_features_with_limit(3),
        ), patch.object(
            service.subscription_client,
            "get_read_only_ids",
            _real_get_read_only_ids.__get__(service.subscription_client),
        ):
            read_only = service.subscription_client.get_read_only_ids(
                USER_ID, "accounts", ordered_ids
            )

        assert read_only == set()

    def test_unlimited_plan_no_read_only(self, db_session):
        """Unlimited plan → no read-only accounts regardless of count."""
        service = _make_service(db_session)
        for i in range(5):
            create_account_in_db(db_session, owner_id=USER_ID, name=f"Acc {i}")

        ordered_ids = service._get_ordered_ids(TEST_WORKSPACE_ID)

        with patch.object(
            service.subscription_client,
            "get_user_features",
            return_value=_features_unlimited(),
        ), patch.object(
            service.subscription_client,
            "get_read_only_ids",
            _real_get_read_only_ids.__get__(service.subscription_client),
        ):
            read_only = service.subscription_client.get_read_only_ids(
                USER_ID, "accounts", ordered_ids
            )

        assert read_only == set()

    def test_service_unreachable_fails_open(self, db_session):
        """When subscription service is down, no accounts are read-only."""
        service = _make_service(db_session)
        for i in range(3):
            create_account_in_db(db_session, owner_id=USER_ID, name=f"Acc {i}")

        ordered_ids = service._get_ordered_ids(TEST_WORKSPACE_ID)

        with patch.object(
            service.subscription_client,
            "get_user_features",
            return_value=None,
        ), patch.object(
            service.subscription_client,
            "get_read_only_ids",
            _real_get_read_only_ids.__get__(service.subscription_client),
        ):
            read_only = service.subscription_client.get_read_only_ids(
                USER_ID, "accounts", ordered_ids
            )

        assert read_only == set()


# ---------------------------------------------------------------------------
# Router-level: list endpoint is_read_only flag
# ---------------------------------------------------------------------------


class TestListEndpointReadOnlyFlag:
    """Verify is_read_only is set correctly on GET /accounts/ responses."""

    def test_over_limit_response_has_read_only_flag(self, client, db_session):
        """3 accounts, limit 2 → newest account in response has is_read_only=true."""
        user_id = randint(1000, 2000)
        a1 = create_account_in_db(db_session, owner_id=user_id, name="First")
        a2 = create_account_in_db(db_session, owner_id=user_id, name="Second")
        a3 = create_account_in_db(db_session, owner_id=user_id, name="Third")

        with patch("shared.auth.dependencies.decode_token", return_value=user_id), \
             patch(
                 "shared.clients.subscription.SubscriptionClient.get_read_only_ids",
                 return_value={a3.id},
             ), \
             patch(
                 "shared.clients.subscription.SubscriptionClient.check_modify_allowed",
                 return_value=True,
             ):
            response = client.get("/accounts/", headers=_auth_headers(user_id))

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        by_id = {item["id"]: item for item in data}

        assert by_id[a1.id]["is_read_only"] is False
        assert by_id[a2.id]["is_read_only"] is False
        assert by_id[a3.id]["is_read_only"] is True

    def test_within_limit_all_editable_in_response(self, client, db_session):
        """2 accounts, limit 5 → all is_read_only=false."""
        user_id = randint(1000, 2000)
        a1 = create_account_in_db(db_session, owner_id=user_id, name="First")
        a2 = create_account_in_db(db_session, owner_id=user_id, name="Second")

        with patch("shared.auth.dependencies.decode_token", return_value=user_id), \
             patch(
                 "shared.clients.subscription.SubscriptionClient.get_read_only_ids",
                 return_value=set(),
             ):
            response = client.get("/accounts/", headers=_auth_headers(user_id))

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        for item in data:
            assert item["is_read_only"] is False

    def test_empty_list_no_read_only(self, client):
        """No accounts → empty list, no read-only."""
        user_id = randint(1000, 2000)

        with patch("shared.auth.dependencies.decode_token", return_value=user_id):
            response = client.get("/accounts/", headers=_auth_headers(user_id))

        assert response.status_code == status.HTTP_200_OK
        assert response.json() == []


# ---------------------------------------------------------------------------
# Full flow tests
# ---------------------------------------------------------------------------


class TestReadOnlyFullFlow:
    """End-to-end scenarios simulating plan changes and their effects."""

    def test_create_3_downgrade_to_2_oldest_editable_newest_read_only(self, db_session):
        """
        Create 3 accounts, then simulate downgrade to limit=2.
        Oldest 2 should be editable, 3rd (newest) should be read-only.
        """
        service = _make_service(db_session)

        a1 = create_account_in_db(db_session, owner_id=USER_ID, name="Account 1")
        a2 = create_account_in_db(db_session, owner_id=USER_ID, name="Account 2")
        a3 = create_account_in_db(db_session, owner_id=USER_ID, name="Account 3")

        ordered_ids = service._get_ordered_ids(TEST_WORKSPACE_ID)
        assert len(ordered_ids) == 3

        # Simulate downgrade: limit = 2. Restore real methods so they use mocked get_user_features.
        features = _features_with_limit(2)
        with patch.object(
            service.subscription_client, "get_user_features", return_value=features
        ), patch.object(
            service.subscription_client,
            "check_modify_allowed",
            _real_check_modify_allowed.__get__(service.subscription_client),
        ), patch.object(
            service.subscription_client,
            "get_read_only_ids",
            _real_get_read_only_ids.__get__(service.subscription_client),
        ):
            # check_modify_allowed for oldest 2 should return True
            assert service.subscription_client.check_modify_allowed(
                USER_ID, a1.id, "accounts", ordered_ids
            ) is True
            assert service.subscription_client.check_modify_allowed(
                USER_ID, a2.id, "accounts", ordered_ids
            ) is True
            # check_modify_allowed for 3rd should return False
            assert service.subscription_client.check_modify_allowed(
                USER_ID, a3.id, "accounts", ordered_ids
            ) is False

            # get_read_only_ids should mark only a3
            read_only = service.subscription_client.get_read_only_ids(
                USER_ID, "accounts", ordered_ids
            )
            assert read_only == {a3.id}

    def test_update_read_only_account_raises(self, db_session):
        """Updating an account that exceeds the limit raises AccountReadOnlyExcessError."""
        service = _make_service(db_session)

        a1 = create_account_in_db(db_session, owner_id=USER_ID, name="Editable")
        a2 = create_account_in_db(db_session, owner_id=USER_ID, name="ReadOnly")

        features = _features_with_limit(1)
        with patch.object(
            service.subscription_client, "check_modify_allowed", return_value=False
        ), patch.object(
            service.subscription_client, "get_user_features", return_value=features
        ):
            with pytest.raises(AccountReadOnlyExcessError) as exc_info:
                service.update_account(
                    a2.id, AccountUpdate(name="Nope"), USER_ID, TEST_WORKSPACE_ID
                )

            assert exc_info.value.account_id == a2.id
            assert exc_info.value.error_code == "RECORD_READ_ONLY_EXCESS"

    def test_update_editable_account_succeeds_when_over_limit(self, db_session):
        """Updating the oldest account (within limit) succeeds even when over total limit."""
        service = _make_service(db_session)

        a1 = create_account_in_db(db_session, owner_id=USER_ID, name="Editable")
        a2 = create_account_in_db(db_session, owner_id=USER_ID, name="ReadOnly")

        # check_modify_allowed returns True for a1 (within limit)
        with patch.object(
            service.subscription_client, "check_modify_allowed", return_value=True
        ):
            updated = service.update_account(
                a1.id, AccountUpdate(name="Still Editable"), USER_ID, TEST_WORKSPACE_ID
            )
            assert updated.name == "Still Editable"

    def test_archive_account_does_not_check_read_only(self, db_session):
        """
        Archive does NOT call _check_modify_allowed, so archiving a read-only account
        should succeed. This lets users reduce their account count to get within limits.
        """
        service = _make_service(db_session)

        a1 = create_account_in_db(db_session, owner_id=USER_ID, name="First")
        a2 = create_account_in_db(db_session, owner_id=USER_ID, name="Second (excess)")

        # Even with modify blocked, archive should work because it doesn't call _check_modify_allowed
        archived = service.archive_account(a2.id, USER_ID, TEST_WORKSPACE_ID)
        assert archived.is_archived is True
        assert archived.is_active is False

    def test_update_read_only_via_router_returns_403(self, client, db_session):
        """PUT on a read-only account returns HTTP 403."""
        user_id = randint(1000, 2000)
        a1 = create_account_in_db(db_session, owner_id=user_id, name="Editable")
        a2 = create_account_in_db(db_session, owner_id=user_id, name="ReadOnly")

        with patch("shared.auth.dependencies.decode_token", return_value=user_id), \
             patch(
                 "shared.clients.subscription.SubscriptionClient.check_modify_allowed",
                 return_value=False,
             ), \
             patch(
                 "shared.clients.subscription.SubscriptionClient.get_user_features",
                 return_value=_features_with_limit(1),
             ):
            response = client.put(
                f"/accounts/{a2.id}",
                json={"name": "Attempt"},
                headers=_auth_headers(user_id),
            )

        assert response.status_code == status.HTTP_403_FORBIDDEN
        data = response.json()
        assert data["errorCode"] == "RECORD_READ_ONLY_EXCESS"
        assert "current_count" in data
        assert "limit" in data

    def test_create_then_downgrade_blocks_new_creation(self, db_session):
        """After downgrade, creating a new account is blocked by check_limit."""
        service = _make_service(db_session)

        create_account_in_db(db_session, owner_id=USER_ID, name="Account 1")
        create_account_in_db(db_session, owner_id=USER_ID, name="Account 2")
        create_account_in_db(db_session, owner_id=USER_ID, name="Account 3")

        # Now simulate downgrade: limit = 2, current count = 3
        with patch.object(
            service.subscription_client, "check_limit", return_value=(False, 2)
        ):
            with pytest.raises(AccountLimitExceededError):
                service.create_account(
                    AccountCreate(name="Fourth", type=AccountType.CASH),
                    USER_ID,
                    TEST_WORKSPACE_ID,
                )


# ---------------------------------------------------------------------------
# Boundary cases
# ---------------------------------------------------------------------------


class TestReadOnlyBoundaryCases:
    """Edge cases around the limit boundary."""

    def test_exactly_at_limit_all_editable(self, db_session):
        """count == limit → all accounts editable, but can't create more."""
        service = _make_service(db_session)

        a1 = create_account_in_db(db_session, owner_id=USER_ID, name="First")
        a2 = create_account_in_db(db_session, owner_id=USER_ID, name="Second")

        ordered_ids = service._get_ordered_ids(TEST_WORKSPACE_ID)
        assert len(ordered_ids) == 2

        features = _features_with_limit(2)
        with patch.object(
            service.subscription_client, "get_user_features", return_value=features
        ), patch.object(
            service.subscription_client,
            "get_read_only_ids",
            _real_get_read_only_ids.__get__(service.subscription_client),
        ), patch.object(
            service.subscription_client,
            "check_modify_allowed",
            _real_check_modify_allowed.__get__(service.subscription_client),
        ):
            # All editable
            read_only = service.subscription_client.get_read_only_ids(
                USER_ID, "accounts", ordered_ids
            )
            assert read_only == set()

            # Both modify-allowed
            assert service.subscription_client.check_modify_allowed(
                USER_ID, a1.id, "accounts", ordered_ids
            ) is True
            assert service.subscription_client.check_modify_allowed(
                USER_ID, a2.id, "accounts", ordered_ids
            ) is True

    def test_exactly_at_limit_cannot_create_more(self, db_session):
        """count == limit → creation is blocked."""
        service = _make_service(db_session)

        create_account_in_db(db_session, owner_id=USER_ID, name="First")
        create_account_in_db(db_session, owner_id=USER_ID, name="Second")

        # limit=2, current_count=2 → can_create=False
        with patch.object(
            service.subscription_client, "check_limit", return_value=(False, 2)
        ):
            with pytest.raises(AccountLimitExceededError):
                service.create_account(
                    AccountCreate(name="Third", type=AccountType.CASH),
                    USER_ID,
                    TEST_WORKSPACE_ID,
                )

    def test_zero_limit_all_read_only(self, db_session):
        """limit=0 → every account is read-only."""
        service = _make_service(db_session)

        a1 = create_account_in_db(db_session, owner_id=USER_ID, name="First")
        a2 = create_account_in_db(db_session, owner_id=USER_ID, name="Second")

        ordered_ids = service._get_ordered_ids(TEST_WORKSPACE_ID)

        features = _features_with_limit(0)
        with patch.object(
            service.subscription_client, "get_user_features", return_value=features
        ), patch.object(
            service.subscription_client,
            "get_read_only_ids",
            _real_get_read_only_ids.__get__(service.subscription_client),
        ), patch.object(
            service.subscription_client,
            "check_modify_allowed",
            _real_check_modify_allowed.__get__(service.subscription_client),
        ):
            read_only = service.subscription_client.get_read_only_ids(
                USER_ID, "accounts", ordered_ids
            )
            assert read_only == {a1.id, a2.id}

            # Neither is modifiable
            assert service.subscription_client.check_modify_allowed(
                USER_ID, a1.id, "accounts", ordered_ids
            ) is False
            assert service.subscription_client.check_modify_allowed(
                USER_ID, a2.id, "accounts", ordered_ids
            ) is False

    def test_zero_limit_update_blocked(self, db_session):
        """limit=0 → updating any account raises AccountReadOnlyExcessError."""
        service = _make_service(db_session)

        a1 = create_account_in_db(db_session, owner_id=USER_ID, name="First")

        features = _features_with_limit(0)
        with patch.object(
            service.subscription_client, "check_modify_allowed", return_value=False
        ), patch.object(
            service.subscription_client, "get_user_features", return_value=features
        ):
            with pytest.raises(AccountReadOnlyExcessError) as exc_info:
                service.update_account(
                    a1.id, AccountUpdate(name="Nope"), USER_ID, TEST_WORKSPACE_ID
                )
            assert exc_info.value.limit == 0

    def test_one_account_limit_one_editable(self, db_session):
        """Single account, limit=1 → account is editable."""
        service = _make_service(db_session)

        a1 = create_account_in_db(db_session, owner_id=USER_ID, name="Only One")

        ordered_ids = service._get_ordered_ids(TEST_WORKSPACE_ID)

        features = _features_with_limit(1)
        with patch.object(
            service.subscription_client, "get_user_features", return_value=features
        ), patch.object(
            service.subscription_client,
            "get_read_only_ids",
            _real_get_read_only_ids.__get__(service.subscription_client),
        ):
            read_only = service.subscription_client.get_read_only_ids(
                USER_ID, "accounts", ordered_ids
            )
            assert read_only == set()

    def test_feature_disabled_all_editable(self, db_session):
        """When feature is disabled, all accounts remain editable (fail-open)."""
        service = _make_service(db_session)

        a1 = create_account_in_db(db_session, owner_id=USER_ID, name="First")
        a2 = create_account_in_db(db_session, owner_id=USER_ID, name="Second")

        ordered_ids = service._get_ordered_ids(TEST_WORKSPACE_ID)

        disabled_features = {"accounts": {"enabled": False, "limit_value": 1}}
        with patch.object(
            service.subscription_client, "get_user_features", return_value=disabled_features
        ), patch.object(
            service.subscription_client,
            "get_read_only_ids",
            _real_get_read_only_ids.__get__(service.subscription_client),
        ):
            read_only = service.subscription_client.get_read_only_ids(
                USER_ID, "accounts", ordered_ids
            )
            assert read_only == set()

    def test_feature_missing_all_editable(self, db_session):
        """When accounts feature is not in features dict, all accounts are editable."""
        service = _make_service(db_session)

        a1 = create_account_in_db(db_session, owner_id=USER_ID, name="First")

        ordered_ids = service._get_ordered_ids(TEST_WORKSPACE_ID)

        with patch.object(
            service.subscription_client, "get_user_features", return_value={}
        ), patch.object(
            service.subscription_client,
            "get_read_only_ids",
            _real_get_read_only_ids.__get__(service.subscription_client),
        ):
            read_only = service.subscription_client.get_read_only_ids(
                USER_ID, "accounts", ordered_ids
            )
            assert read_only == set()

    def test_multiple_excess_accounts_all_marked(self, db_session):
        """5 accounts, limit 2 → 3 newest are read-only."""
        service = _make_service(db_session)

        accounts = []
        for i in range(5):
            acc = create_account_in_db(db_session, owner_id=USER_ID, name=f"Acc {i}")
            accounts.append(acc)

        ordered_ids = service._get_ordered_ids(TEST_WORKSPACE_ID)

        features = _features_with_limit(2)
        with patch.object(
            service.subscription_client, "get_user_features", return_value=features
        ), patch.object(
            service.subscription_client,
            "get_read_only_ids",
            _real_get_read_only_ids.__get__(service.subscription_client),
        ):
            read_only = service.subscription_client.get_read_only_ids(
                USER_ID, "accounts", ordered_ids
            )

        # First 2 editable, last 3 read-only
        assert accounts[0].id not in read_only
        assert accounts[1].id not in read_only
        assert accounts[2].id in read_only
        assert accounts[3].id in read_only
        assert accounts[4].id in read_only
        assert len(read_only) == 3

    def test_read_only_error_contains_accurate_counts(self, db_session):
        """AccountReadOnlyExcessError should contain current_count and limit from features."""
        service = _make_service(db_session)

        for i in range(4):
            create_account_in_db(db_session, owner_id=USER_ID, name=f"Acc {i}")

        accounts = service.get_user_accounts(USER_ID, TEST_WORKSPACE_ID)
        # Pick the last created account (which would be excess)
        target_id = accounts[0].id  # get_user_accounts returns desc order

        features = _features_with_limit(2)
        with patch.object(
            service.subscription_client, "check_modify_allowed", return_value=False
        ), patch.object(
            service.subscription_client, "get_user_features", return_value=features
        ):
            with pytest.raises(AccountReadOnlyExcessError) as exc_info:
                service.update_account(
                    target_id, AccountUpdate(name="Nope"), USER_ID, TEST_WORKSPACE_ID
                )
            assert exc_info.value.current_count == 4
            assert exc_info.value.limit == 2
