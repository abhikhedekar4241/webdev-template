import uuid
from datetime import datetime, timedelta

import pytest
from fastapi.testclient import TestClient

from app.core.security import create_access_token
from app.models.verification import EmailVerification
from app.services.auth import auth_service
from app.services.verification import verification_service


def auth_header(user_id: uuid.UUID) -> dict:
    return {"Authorization": f"Bearer {create_access_token(str(user_id))}"}


@pytest.fixture
def unverified_user(session):
    return auth_service.create_user(
        session,
        email="unverified@example.com",
        password="password123",
        full_name="Unverified User",
    )


def test_generate_otp_is_6_digits(session, unverified_user):
    otp_record = verification_service.create_otp(session, user_id=unverified_user.id)
    assert len(otp_record.otp) == 6
    assert otp_record.otp.isdigit()


def test_otp_expires_in_10_minutes(session, unverified_user):
    otp_record = verification_service.create_otp(session, user_id=unverified_user.id)
    delta = otp_record.expires_at - datetime.utcnow()
    assert 590 < delta.total_seconds() < 610


def test_verify_otp_marks_user_verified(session, unverified_user):
    otp_record = verification_service.create_otp(session, user_id=unverified_user.id)
    result = verification_service.verify_otp(
        session, email=unverified_user.email, otp=otp_record.otp
    )
    assert result is not None
    assert result.is_verified is True


def test_verify_otp_marks_record_used(session, unverified_user):
    otp_record = verification_service.create_otp(session, user_id=unverified_user.id)
    verification_service.verify_otp(
        session, email=unverified_user.email, otp=otp_record.otp
    )
    session.refresh(otp_record)
    assert otp_record.used_at is not None


def test_verify_wrong_otp_returns_none(session, unverified_user):
    verification_service.create_otp(session, user_id=unverified_user.id)
    result = verification_service.verify_otp(
        session, email=unverified_user.email, otp="000000"
    )
    assert result is None


def test_verify_expired_otp_returns_none(session, unverified_user):
    otp_record = verification_service.create_otp(session, user_id=unverified_user.id)
    otp_record.expires_at = datetime.utcnow() - timedelta(seconds=1)
    session.add(otp_record)
    session.commit()
    result = verification_service.verify_otp(
        session, email=unverified_user.email, otp=otp_record.otp
    )
    assert result is None


def test_verify_used_otp_returns_none(session, unverified_user):
    otp_record = verification_service.create_otp(session, user_id=unverified_user.id)
    verification_service.verify_otp(
        session, email=unverified_user.email, otp=otp_record.otp
    )
    session.refresh(unverified_user)
    result = verification_service.verify_otp(
        session, email=unverified_user.email, otp=otp_record.otp
    )
    assert result is None


def test_has_recent_otp_true_within_60s(session, unverified_user):
    verification_service.create_otp(session, user_id=unverified_user.id)
    assert verification_service.has_recent_otp(session, user_id=unverified_user.id) is True


def test_has_recent_otp_false_after_60s(session, unverified_user):
    otp_record = verification_service.create_otp(session, user_id=unverified_user.id)
    otp_record.created_at = datetime.utcnow() - timedelta(seconds=61)
    session.add(otp_record)
    session.commit()
    assert verification_service.has_recent_otp(session, user_id=unverified_user.id) is False
