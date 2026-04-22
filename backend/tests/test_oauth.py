from unittest.mock import patch

from fastapi.testclient import TestClient
from sqlmodel import select

from app.models.oauth_account import UserOAuthAccount
from app.services.auth import auth_service


def _google_token():
    return {"access_token": "fake_google_access_token", "token_type": "Bearer"}


def _google_user(sub="google-sub-123", email="oauth@example.com", name="OAuth User"):
    return {"sub": sub, "email": email, "name": name}


def test_google_login_not_configured_returns_501(client: TestClient):
    resp = client.get("/api/v1/auth/google")
    assert resp.status_code == 501


def test_google_callback_invalid_state_redirects_to_error(client: TestClient):
    client.cookies.set("oauth_state", "correct")
    resp = client.get(
        "/api/v1/auth/google/callback",
        params={"code": "abc", "state": "wrong"},
        follow_redirects=False,
    )
    assert resp.status_code == 307
    assert "error=oauth_failed" in resp.headers["location"]


def test_google_callback_missing_code_redirects_to_error(client: TestClient):
    client.cookies.set("oauth_state", "state123")
    resp = client.get(
        "/api/v1/auth/google/callback",
        params={"state": "state123", "error": "access_denied"},
        follow_redirects=False,
    )
    assert resp.status_code in (302, 307)
    assert "oauth_failed" in resp.headers["location"]


def test_google_callback_creates_new_user(client: TestClient, session):
    client.cookies.set("oauth_state", "state123")
    with patch("app.api.v1.auth.oauth_service.exchange_code", return_value=_google_token()):
        with patch(
            "app.api.v1.auth.oauth_service.get_google_user_info",
            return_value=_google_user(),
        ):
            resp = client.get(
                "/api/v1/auth/google/callback",
                params={"code": "fake_code", "state": "state123"},
                follow_redirects=False,
            )
    assert resp.status_code in (302, 307)
    location = resp.headers["location"]
    assert "/auth/callback?token=" in location

    # User was created and verified
    user = auth_service.get_by_email(session, email="oauth@example.com")
    assert user is not None
    assert user.is_verified is True
    assert user.hashed_password is None  # OAuth-only user


def test_google_callback_links_existing_email(client: TestClient, session):
    existing = auth_service.create_user(
        session,
        email="oauth@example.com",
        password="password123",
        full_name="Existing",
        is_verified=True,
    )
    client.cookies.set("oauth_state", "state123")
    with patch("app.api.v1.auth.oauth_service.exchange_code", return_value=_google_token()):
        with patch(
            "app.api.v1.auth.oauth_service.get_google_user_info",
            return_value=_google_user(email=existing.email),
        ):
            resp = client.get(
                "/api/v1/auth/google/callback",
                params={"code": "fake_code", "state": "state123"},
                follow_redirects=False,
            )
    assert resp.status_code in (302, 307)

    # OAuth account was linked to existing user
    session.expire_all()
    oauth = session.exec(
        select(UserOAuthAccount).where(UserOAuthAccount.user_id == existing.id)
    ).first()
    assert oauth is not None
    assert oauth.provider == "google"


def test_google_callback_uses_existing_oauth_account(client: TestClient, session):
    user = auth_service.create_user(
        session,
        email="oauth2@example.com",
        password="password123",
        full_name="Existing",
        is_verified=True,
    )
    oauth = UserOAuthAccount(
        user_id=user.id,
        provider="google",
        provider_user_id="google-sub-456",
        provider_email=user.email,
    )
    session.add(oauth)
    session.commit()

    client.cookies.set("oauth_state", "state123")
    with patch("app.api.v1.auth.oauth_service.exchange_code", return_value=_google_token()):
        with patch(
            "app.api.v1.auth.oauth_service.get_google_user_info",
            return_value=_google_user(sub="google-sub-456", email=user.email),
        ):
            resp = client.get(
                "/api/v1/auth/google/callback",
                params={"code": "fake_code", "state": "state123"},
                follow_redirects=False,
            )
    assert resp.status_code in (302, 307)
    assert "/auth/callback?token=" in resp.headers["location"]


def test_google_callback_inactive_user_redirects_to_error(client: TestClient, session):
    user = auth_service.create_user(
        session,
        email="inactive@example.com",
        password="password123",
        full_name="Inactive",
        is_verified=True,
    )
    user.is_active = False
    session.add(user)
    session.commit()

    client.cookies.set("oauth_state", "state123")
    with patch("app.api.v1.auth.oauth_service.exchange_code", return_value=_google_token()):
        with patch(
            "app.api.v1.auth.oauth_service.get_google_user_info",
            return_value=_google_user(email=user.email),
        ):
            resp = client.get(
                "/api/v1/auth/google/callback",
                params={"code": "fake_code", "state": "state123"},
                follow_redirects=False,
            )
    assert resp.status_code in (302, 307)
    assert "oauth_failed" in resp.headers["location"]
