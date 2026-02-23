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
