import uuid
from datetime import UTC, datetime, timedelta

import pytest
from fastapi.testclient import TestClient

from app.core.security import create_access_token
from app.services.auth import auth_service
from app.services.verification import verification_service


def auth_header(user_id: uuid.UUID) -> dict:
    return {"Authorization": f"Bearer {create_access_token(str(user_id))}"}


@pytest.fixture
async def unverified_user(session):
    return await auth_service.create_user(
        session,
        email="unverified@example.com",
        password="password123",
        full_name="Unverified User",
    )


async def test_generate_otp_is_6_digits(session, unverified_user):
    otp_record = await verification_service.create_otp(
        session, user_id=unverified_user.id
    )
    assert len(otp_record.otp) == 6
    assert otp_record.otp.isdigit()


async def test_otp_expires_in_10_minutes(session, unverified_user):
    otp_record = await verification_service.create_otp(
        session, user_id=unverified_user.id
    )
    delta = otp_record.expires_at.replace(tzinfo=UTC) - datetime.now(UTC)
    assert 590 < delta.total_seconds() < 610


async def test_verify_otp_marks_user_verified(session, unverified_user):
    otp_record = await verification_service.create_otp(
        session, user_id=unverified_user.id
    )
    result = await verification_service.verify_otp(
        session, email=unverified_user.email, otp=otp_record.otp
    )
    assert result is not None
    assert result.is_verified is True


async def test_verify_otp_marks_record_used(session, unverified_user):
    otp_record = await verification_service.create_otp(
        session, user_id=unverified_user.id
    )
    await verification_service.verify_otp(
        session, email=unverified_user.email, otp=otp_record.otp
    )
    await session.refresh(otp_record)
    assert otp_record.used_at is not None


async def test_verify_wrong_otp_returns_none(session, unverified_user):
    await verification_service.create_otp(session, user_id=unverified_user.id)
    result = await verification_service.verify_otp(
        session, email=unverified_user.email, otp="000000"
    )
    assert result is None


async def test_verify_expired_otp_returns_none(session, unverified_user):
    otp_record = await verification_service.create_otp(
        session, user_id=unverified_user.id
    )
    otp_record.expires_at = datetime.now(UTC) - timedelta(seconds=1)
    session.add(otp_record)
    await session.commit()
    result = await verification_service.verify_otp(
        session, email=unverified_user.email, otp=otp_record.otp
    )
    assert result is None


async def test_verify_used_otp_returns_none(session, unverified_user):
    otp_record = await verification_service.create_otp(
        session, user_id=unverified_user.id
    )
    await verification_service.verify_otp(
        session, email=unverified_user.email, otp=otp_record.otp
    )
    await session.refresh(unverified_user)
    result = await verification_service.verify_otp(
        session, email=unverified_user.email, otp=otp_record.otp
    )
    assert result is None


async def test_has_recent_otp_true_within_60s(session, unverified_user):
    await verification_service.create_otp(session, user_id=unverified_user.id)
    assert (
        await verification_service.has_recent_otp(session, user_id=unverified_user.id)
        is True
    )


async def test_has_recent_otp_false_after_60s(session, unverified_user):
    otp_record = await verification_service.create_otp(
        session, user_id=unverified_user.id
    )
    otp_record.created_at = datetime.now(UTC) - timedelta(seconds=61)
    session.add(otp_record)
    await session.commit()
    assert (
        await verification_service.has_recent_otp(session, user_id=unverified_user.id)
        is False
    )


# --- API tests ---


async def test_login_unverified_returns_403(client: TestClient, session):
    await auth_service.create_user(
        session,
        email="blocked@example.com",
        password="password123",
        full_name="Blocked",
    )
    resp = await client.post(
        "/api/v1/auth/login",
        data={"username": "blocked@example.com", "password": "password123"},
    )
    assert resp.status_code == 403
    assert resp.json()["detail"] == "Email not verified"


async def test_register_creates_unverified_user(client: TestClient):
    resp = await client.post(
        "/api/v1/auth/register",
        json={
            "email": "new@example.com",
            "password": "password123",
            "full_name": "New",
        },
    )
    assert resp.status_code == 201
    assert resp.json()["is_verified"] is False


async def test_verify_email_returns_token(client: TestClient, session):
    user = await auth_service.create_user(
        session,
        email="verify@example.com",
        password="password123",
        full_name="Verify Me",
    )
    otp_record = await verification_service.create_otp(session, user_id=user.id)
    resp = await client.post(
        "/api/v1/auth/verify-email",
        json={"email": "verify@example.com", "otp": otp_record.otp},
    )
    assert resp.status_code == 200
    assert "access_token" in resp.json()


async def test_verify_email_wrong_otp_returns_400(client: TestClient, session):
    await auth_service.create_user(
        session,
        email="wrongotp@example.com",
        password="password123",
        full_name="Wrong OTP",
    )
    resp = await client.post(
        "/api/v1/auth/verify-email",
        json={"email": "wrongotp@example.com", "otp": "999999"},
    )
    assert resp.status_code == 400


async def test_resend_verification_success(client: TestClient, session):
    await auth_service.create_user(
        session,
        email="resend@example.com",
        password="password123",
        full_name="Resend",
    )
    resp = await client.post(
        "/api/v1/auth/resend-verification",
        json={"email": "resend@example.com"},
    )
    assert resp.status_code == 200


async def test_resend_verification_rate_limit(client: TestClient, session):
    user = await auth_service.create_user(
        session,
        email="ratelimit@example.com",
        password="password123",
        full_name="Rate",
    )
    await verification_service.create_otp(session, user_id=user.id)
    resp = await client.post(
        "/api/v1/auth/resend-verification",
        json={"email": "ratelimit@example.com"},
    )
    assert resp.status_code == 429


async def test_login_after_verification_succeeds(client: TestClient, session):
    user = await auth_service.create_user(
        session,
        email="afterverify@example.com",
        password="password123",
        full_name="After",
    )
    otp_record = await verification_service.create_otp(session, user_id=user.id)
    await client.post(
        "/api/v1/auth/verify-email",
        json={"email": "afterverify@example.com", "otp": otp_record.otp},
    )
    resp = await client.post(
        "/api/v1/auth/login",
        data={"username": "afterverify@example.com", "password": "password123"},
    )
    assert resp.status_code == 200
    assert "access_token" in resp.json()
