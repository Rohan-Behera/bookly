from datetime import datetime, timedelta
from unittest.mock import AsyncMock, Mock
import uuid

import pytest

from src import app
from src.auth import routes as auth_routes
from src.auth.dependencies import get_current_user, get_user_service
from src.auth.utils import create_url__safe_token, generate_password_hash, create_access_token


auth_prefix = "/api/V1/auth"


def override_user_service(fake_user_service):
    app.dependency_overrides[get_user_service] = lambda: fake_user_service


def remove_user_service_override():
    app.dependency_overrides.pop(get_user_service, None)


def patch_role_checker_allow(monkeypatch):
    async def fake_call(self, current_user):
        return True

    monkeypatch.setattr(auth_routes.RoleChecker, "__call__", fake_call)


async def fake_delay(*args, **kwargs):
    return None


async def fake_add_jti(*args, **kwargs):
    return None


# Create a new user account successfully and send verification email
def test_create_user_account_success(fake_session, fake_user_service, test_client, monkeypatch):
    fake_user_service.reset_mock()
    fake_user_service.user_exists = AsyncMock(return_value=False)
    fake_user_service.create_user = AsyncMock(
        return_value={
            "email": "emma@example.com",
            "username": "emmawats",
            "first_name": "Emma",
            "last_name": "Watson",
            "is_verified": False,
        }
    )
    from unittest.mock import Mock
    monkeypatch.setattr(auth_routes.send_email, "delay", Mock(return_value=None))
    override_user_service(fake_user_service)

    response = test_client.post(
        url=f"{auth_prefix}/signup",
        json={
            "first_name": "Emma",
            "last_name": "Watson",
            "username": "emmawats",
            "email": "emma@example.com",
            "password": "emma1234",
        },
    )

    assert response.status_code == 201
    assert response.json()["message"] == "Account Created! Check email to verify your account"
    assert response.json()["user"]["email"] == "emma@example.com"
    fake_user_service.user_exists.assert_awaited_once_with("emma@example.com", fake_session)
    fake_user_service.create_user.assert_awaited_once()
    remove_user_service_override()


# Attempt to create an account when the email already exists (should 403)
def test_create_user_account_already_exists(fake_session, fake_user_service, test_client, monkeypatch):
    fake_user_service.reset_mock()
    fake_user_service.user_exists = AsyncMock(return_value=True)
    from unittest.mock import Mock
    monkeypatch.setattr(auth_routes.send_email, "delay", Mock(return_value=None))
    override_user_service(fake_user_service)

    response = test_client.post(
        url=f"{auth_prefix}/signup",
        json={
            "first_name": "Emma",
            "last_name": "Watson",
            "username": "emmawats",
            "email": "emma@example.com",
            "password": "emma1234",
        },
    )

    assert response.status_code == 403
    assert response.json()["error_code"] == "user_exists"
    remove_user_service_override()


# Verify a user account using a valid token (should mark verified)
def test_verify_user_account_success(fake_session, fake_user_service, test_client):
    fake_user_service.reset_mock()
    email = "emma@example.com"
    token = create_url__safe_token({"email": email})
    user = Mock(email=email, is_verified=False)
    fake_user_service.get_user_by_email = AsyncMock(return_value=user)
    fake_user_service.update_user = AsyncMock(return_value=Mock(email=email, is_verified=True))
    override_user_service(fake_user_service)

    response = test_client.get(f"{auth_prefix}/verify/{token}")

    assert response.status_code == 200
    assert response.json()["Message"] == "Account verified sucessfully"
    fake_user_service.get_user_by_email.assert_awaited_once_with(email=email, session=fake_session)
    remove_user_service_override()


# Verify route with token for non-existent user (should return 404)
def test_verify_user_account_not_found(fake_session, fake_user_service, test_client):
    fake_user_service.reset_mock()
    email = "emma@example.com"
    token = create_url__safe_token({"email": email})
    fake_user_service.get_user_by_email = AsyncMock(return_value=None)
    override_user_service(fake_user_service)

    response = test_client.get(f"{auth_prefix}/verify/{token}")

    assert response.status_code == 404
    assert response.json()["error_code"] == "user_not_found"
    remove_user_service_override()


# Verify route with an invalid token (should return server error)
def test_verify_user_account_invalid_token(test_client):
    response = test_client.get(f"{auth_prefix}/verify/invalid-token")

    assert response.status_code == 500
    assert response.json()["Message"] == "Error occured during verification"


# Login with correct credentials and receive access + refresh tokens
def test_login_users_success(fake_session, fake_user_service, test_client, monkeypatch):
    fake_user_service.reset_mock()
    password = "emma1234"
    user = Mock(
        email="emma@example.com",
        password=generate_password_hash(password),
        uid="uuid-1234",
        role="user",
    )
    fake_user_service.get_user_by_email = AsyncMock(return_value=user)
    override_user_service(fake_user_service)

    response = test_client.post(
        url=f"{auth_prefix}/login",
        json={"email": "emma@example.com", "password": password},
    )

    assert response.status_code == 200
    body = response.json()
    assert body["message"] == "login Successful"
    assert "access_token" in body
    assert "refresh_token" in body
    assert body["user"]["email"] == "emma@example.com"
    fake_user_service.get_user_by_email.assert_awaited_once_with("emma@example.com", fake_session)
    remove_user_service_override()


# Login with incorrect password should return invalid credentials (400)
def test_login_users_invalid_password(fake_user_service, test_client):
    fake_user_service.reset_mock()
    user = Mock(
        email="emma@example.com",
        password=generate_password_hash("correct-password"),
        uid="uuid-1234",
        role="user",
    )
    fake_user_service.get_user_by_email = AsyncMock(return_value=user)
    override_user_service(fake_user_service)

    response = test_client.post(
        url=f"{auth_prefix}/login",
        json={"email": "emma@example.com", "password": "wrong-password"},
    )

    assert response.status_code == 400
    assert response.json()["error_code"] == "invalid_email_or_password"
    remove_user_service_override()


# Exchange a valid refresh token for a new access token (200)
def test_refresh_token_success(test_client, monkeypatch):
    # create a real refresh token and call endpoint
    token = create_access_token(
        user_data={"email": "emma@example.com", "user_uid": "uuid-1234"},
        refresh=True,
        expiry=timedelta(minutes=5),
    )

    response = test_client.get(f"{auth_prefix}/refresh-token", headers={"Authorization": f"Bearer {token}"})

    assert response.status_code == 200
    assert "access_token" in response.json()


# Expired refresh token should be rejected (401 or not-authenticated)
def test_refresh_token_expired(test_client, monkeypatch):

    # override the RefreshTokenBearer dependency to return an expired token details
    expired = {
        "exp": int((datetime.now() - timedelta(minutes=5)).timestamp()),
        "user": {"email": "emma@example.com", "user_uid": "uuid-1234"},
        "refresh": True,
    }


    # Override the RefreshTokenBearer dependency to return the expired payload
    app.dependency_overrides[auth_routes.RefreshTokenBearer] = lambda: expired

    response = test_client.get(f"{auth_prefix}/refresh-token")

    assert response.status_code == 401
    body = response.json()
    assert (
        ("error_code" in body and body["error_code"] == "invalid_token")
        or ("message" in body and "invalid" in body["message"].lower())
        or ("detail" in body and "not authenticated" in body["detail"].lower())
    )

    app.dependency_overrides.pop(auth_routes.RefreshTokenBearer, None)


# Retrieve the current user's profile with a valid access token
def test_get_me_success(test_client, monkeypatch):
    from types import SimpleNamespace
    user_obj = SimpleNamespace(
        uid=str(uuid.uuid4()),
        email="emma@example.com",
        username="emmawats",
        first_name="Emma",
        last_name="Watson",
        password="hidden",
        is_verified=True,
        created_at="2024-01-01T00:00:00",
        updated_at="2024-01-01T00:00:00",
        books=[],
        reviews=[],
        role="user",
    )

    app.dependency_overrides[get_current_user] = lambda: user_obj

    response = test_client.get(f"{auth_prefix}/me")

    assert response.status_code == 200
    assert response.json()["email"] == "emma@example.com"

    app.dependency_overrides.pop(get_current_user, None)


# Send a welcome/generic email via the send-mail endpoint
def test_send_mail_success(test_client, monkeypatch):
    from unittest.mock import Mock
    monkeypatch.setattr(auth_routes.send_email, "delay", Mock(return_value=None))

    response = test_client.post(
        f"{auth_prefix}/send-mail",
        json={"addresses": ["emma@example.com"]},
    )

    assert response.status_code == 200
    assert response.json()["Message"] == "Email sent sucessfully"


# Logout/revoke token (add jti to blocklist) and return success
def test_logout_success(test_client, monkeypatch):
    # create a real access token
    token = create_access_token(
        user_data={"email": "emma@example.com", "user_uid": "uuid-1234", "role": "user"},
        refresh=False,
        expiry=timedelta(minutes=5),
    )

    # mock add_jti_to_blocklist
    _orig_add = auth_routes.add_jti_to_blocklist
    auth_routes.add_jti_to_blocklist = AsyncMock(return_value=None)

    response = test_client.get(f"{auth_prefix}/logout", headers={"Authorization": f"Bearer {token}"})

    assert response.status_code == 200
    assert response.json()["Message"] == "logout Sucessfully"
    assert auth_routes.add_jti_to_blocklist.await_count == 1

    # restore
    auth_routes.add_jti_to_blocklist = _orig_add


# Request a password reset email (should instruct user to check email)
def test_password_reset_request_success(test_client, monkeypatch):
    from unittest.mock import Mock
    monkeypatch.setattr(auth_routes.send_email, "delay", Mock(return_value=None))

    response = test_client.post(
        f"{auth_prefix}/password-reset-request",
        json={"email": "emma@example.com"},
    )

    assert response.status_code == 200
    assert response.json()["message"] == "Please check your email for instructions to reset your password"


# Validate a password-reset token via GET (token is valid)
def test_password_reset_confirm_get_valid_token(test_client):
    token = create_url__safe_token({"email": "emma@example.com"})

    response = test_client.get(f"{auth_prefix}/password-reset-confirm/{token}")

    assert response.status_code == 200
    assert response.json()["message"] == "Token is valid"
    assert response.json()["token"] == token


# Validate an invalid password-reset token via GET (should 400)
def test_password_reset_confirm_get_invalid_token(test_client):
    response = test_client.get(f"{auth_prefix}/password-reset-confirm/invalid-token")

    assert response.status_code == 400
    assert response.json()["detail"] == "Invalid or expired token"


# Attempt to reset password with mismatched passwords (400)
def test_reset_password_mismatch(test_client):
    token = create_url__safe_token({"email": "emma@example.com"})

    response = test_client.post(
        f"{auth_prefix}/password-reset-confirm/{token}",
        json={"new_password": "first-pass", "confirm_password": "second-pass"},
    )

    assert response.status_code == 400
    assert response.json()["detail"] == "Passwords donot match"


# Successfully reset password with valid token and matching passwords
def test_reset_password_success(fake_session, fake_user_service, test_client):
    fake_user_service.reset_mock()
    email = "emma@example.com"
    token = create_url__safe_token({"email": email})
    user = Mock(email=email)
    fake_user_service.get_user_by_email = AsyncMock(return_value=user)
    fake_user_service.update_user = AsyncMock(return_value=Mock(email=email))
    override_user_service(fake_user_service)

    response = test_client.post(
        f"{auth_prefix}/password-reset-confirm/{token}",
        json={"new_password": "new-password", "confirm_password": "new-password"},
    )

    assert response.status_code == 200
    assert response.json()["Message"] == "Password Reset sucessfully"
    fake_user_service.get_user_by_email.assert_awaited_once_with(email=email, session=fake_session)
    fake_user_service.update_user.assert_awaited_once()
    remove_user_service_override()


# Reset password when user does not exist (should return 404)
def test_reset_password_user_not_found(fake_session, fake_user_service, test_client):
    fake_user_service.reset_mock()
    email = "emma@example.com"
    token = create_url__safe_token({"email": email})
    fake_user_service.get_user_by_email = AsyncMock(return_value=None)
    override_user_service(fake_user_service)

    response = test_client.post(
        f"{auth_prefix}/password-reset-confirm/{token}",
        json={"new_password": "new-password", "confirm_password": "new-password"},
    )

    assert response.status_code == 404
    assert response.json()["error_code"] == "user_not_found"
    remove_user_service_override()
