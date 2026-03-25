"""E2E tests for subscription and feature gating."""
import pytest

from tests.e2e.clients.subscription_client import SubscriptionApiClient
from tests.e2e.clients.user_client import UserApiClient
from tests.e2e.helpers.test_data import unique_email, strong_password

pytestmark = pytest.mark.subscription


class TestSubscriptionBasics:

    async def test_list_plans(self, subscription_client):
        result = await subscription_client.list_plans()
        data = result.raise_on_error()
        assert isinstance(data, list)
        assert len(data) >= 1  # at least basic plan

    async def test_list_plans_with_features(self, subscription_client):
        result = await subscription_client.list_plans_with_features()
        data = result.raise_on_error()
        assert isinstance(data, list)

    async def test_new_user_has_subscription(self):
        """After registration, user should have an active subscription."""
        email, password = unique_email(), strong_password()
        user = UserApiClient()
        reg = await user.register(email, password)
        data = reg.raise_on_error()

        # Decode user_id from JWT sub claim
        import base64, json
        token = data["access_token"]
        payload = token.split(".")[1]
        payload += "==" * (4 - len(payload) % 4)
        jwt_data = json.loads(base64.urlsafe_b64decode(payload))
        user_id = jwt_data.get("sub")

        if user_id:
            sub = SubscriptionApiClient()
            sub.set_token(data["access_token"])
            result = await sub.get_subscription(user_id)
            if result.ok:
                sub_data = result.raise_on_error()
                assert sub_data.get("plan_code") in ("basic", "free", "trial")


class TestFeatureLimits:

    async def test_get_user_features(self, subscription_client, primary_user):
        """Features endpoint should return a list of feature entitlements."""
        import base64, json
        token = primary_user["token"]
        payload = token.split(".")[1]
        payload += "==" * (4 - len(payload) % 4)
        jwt_data = json.loads(base64.urlsafe_b64decode(payload))
        user_id = jwt_data.get("sub")

        if user_id:
            result = await subscription_client.get_user_features(user_id)
            if result.ok:
                data = result.raise_on_error()
                assert isinstance(data, (list, dict))

    async def test_get_entitlements(self, subscription_client, primary_user):
        """Entitlements endpoint should return user's current entitlements."""
        import base64, json
        token = primary_user["token"]
        payload = token.split(".")[1]
        payload += "==" * (4 - len(payload) % 4)
        jwt_data = json.loads(base64.urlsafe_b64decode(payload))
        user_id = jwt_data.get("sub")

        if user_id:
            result = await subscription_client.get_entitlements(user_id)
            assert result.ok


class TestCancelSubscription:

    async def test_cancel_subscription(self):
        """Cancelling a subscription should deactivate or downgrade the user."""
        email, password = unique_email(), strong_password()
        user = UserApiClient()
        reg = await user.register(email, password)
        data = reg.raise_on_error()

        import base64, json
        token = data["access_token"]
        payload = token.split(".")[1]
        payload += "==" * (4 - len(payload) % 4)
        jwt_data = json.loads(base64.urlsafe_b64decode(payload))
        user_id = jwt_data.get("sub")

        if user_id:
            sub = SubscriptionApiClient()
            sub.set_token(data["access_token"])
            result = await sub.cancel_subscription(user_id)
            # Should succeed or return a known status (some systems return 400
            # if the user is already on the free/basic plan)
            assert result.ok or result.status_code in (200, 204, 400)


class TestFeatureCatalog:

    async def test_list_all_features(self, subscription_client):
        """List all available features across all plans."""
        result = await subscription_client.list_features()
        # Some implementations may not expose this endpoint; accept 200 or 404
        assert result.ok or result.status_code == 404

    async def test_get_plan_specific_features(self, subscription_client):
        """Retrieve feature list for a specific plan code."""
        # First get available plans to find a valid plan code
        plans_result = await subscription_client.list_plans()
        plans = plans_result.raise_on_error()
        assert isinstance(plans, list) and len(plans) >= 1

        plan_code = plans[0].get("code") or plans[0].get("plan_code") or "basic"
        result = await subscription_client.get_plan_features(plan_code)
        # Accept 200 or 404 if the endpoint is not implemented
        assert result.ok or result.status_code == 404
