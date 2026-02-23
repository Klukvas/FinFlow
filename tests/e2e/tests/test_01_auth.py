"""E2E tests for authentication flows."""
import pytest

from tests.e2e.clients.user_client import UserApiClient
from tests.e2e.helpers.test_data import unique_email, strong_password

pytestmark = pytest.mark.auth


class TestRegistration:

    async def test_register_new_user(self):
        client = UserApiClient()
        result = await client.register(unique_email(), strong_password())
        data = result.raise_on_error()
        assert "access_token" in data
        assert data["token_type"] == "bearer"

    async def test_register_duplicate_email_fails(self):
        email = unique_email()
        client = UserApiClient()
        await client.register(email, strong_password())
        result = await client.register(email, strong_password())
        assert not result.ok
        assert result.status_code in (400, 409)

    async def test_register_weak_password_fails(self):
        client = UserApiClient()
        result = await client.register(unique_email(), "weak")
        assert not result.ok
        assert result.status_code == 400


class TestLogin:

    async def test_login_success(self):
        email, password = unique_email(), strong_password()
        client = UserApiClient()
        await client.register(email, password)
        result = await client.login(email, password)
        data = result.raise_on_error()
        assert "access_token" in data

    async def test_login_wrong_password(self):
        email, password = unique_email(), strong_password()
        client = UserApiClient()
        await client.register(email, password)
        result = await client.login(email, "WrongPass999!")
        assert not result.ok
        assert result.status_code in (400, 401)

    async def test_login_nonexistent_email(self):
        client = UserApiClient()
        result = await client.login("nonexistent@test.com", strong_password())
        assert not result.ok


class TestProfile:

    async def test_get_profile(self, user_client):
        result = await user_client.get_me()
        data = result.raise_on_error()
        assert "email" in data
        assert "id" in data

    async def test_get_profile_unauthenticated(self):
        client = UserApiClient()
        result = await client.get_me()
        assert not result.ok
        assert result.status_code in (401, 403)


class TestTokenRefresh:

    async def test_refresh_token_flow(self):
        email, password = unique_email(), strong_password()
        client = UserApiClient()
        reg = await client.register(email, password)
        data = reg.raise_on_error()
        refresh = data.get("refresh_token")
        if refresh:
            result = await client.refresh_token(refresh)
            new_data = result.raise_on_error()
            assert "access_token" in new_data


class TestPasswordChange:

    async def test_change_password_and_login(self):
        email, old_pass = unique_email(), strong_password()
        new_pass = "NewPass456!"
        client = UserApiClient()
        await client.register_and_auth(email, old_pass)
        change_result = await client.change_password(old_pass, new_pass)
        assert change_result.ok or change_result.status_code == 200

        client2 = UserApiClient()
        login_result = await client2.login(email, new_pass)
        login_result.raise_on_error()
