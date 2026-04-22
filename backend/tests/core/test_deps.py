import pytest
from fastapi import HTTPException
from app.api.deps import get_current_user, get_current_superuser
from app.core.security import create_access_token
import uuid

def test_get_current_user_invalid_api_key(session):
    with pytest.raises(HTTPException) as exc:
        get_current_user(token="sk_live_invalid", session=session)
    assert exc.value.status_code == 401
    assert "API key" in exc.value.detail

def test_get_current_user_api_key_missing_user(session):
    from app.services.api_keys import api_key_service
    # Create key for a non-existent user
    key_rec, raw_key = api_key_service.create(session, org_id=uuid.uuid4(), name="k", created_by=uuid.uuid4())
    session.commit()
    
    with pytest.raises(HTTPException) as exc:
        get_current_user(token=raw_key, session=session)
    assert exc.value.status_code == 401
    assert "User not found" in exc.value.detail

def test_get_current_user_inactive(session, alice):
    alice.is_active = False
    session.add(alice)
    session.commit()
    
    token = create_access_token(alice.id)
    with pytest.raises(HTTPException) as exc:
        get_current_user(token=token, session=session)
    assert exc.value.status_code == 401
    assert "inactive" in exc.value.detail

def test_get_current_user_malformed_token(session):
    with pytest.raises(HTTPException) as exc:
        get_current_user(token="not-a-jwt", session=session)
    assert exc.value.status_code == 401

def test_get_current_user_invalid_uuid_subject(session):
    # Create a token with a non-UUID subject
    from jose import jwt
    from app.core.config import settings
    token = jwt.encode({"sub": "not-a-uuid"}, settings.SECRET_KEY, algorithm=settings.ALGORITHM)
    
    with pytest.raises(HTTPException) as exc:
        get_current_user(token=token, session=session)
    assert exc.value.status_code == 401
    assert "Invalid token subject" in exc.value.detail

def test_get_current_superuser_forbidden(alice):
    with pytest.raises(HTTPException) as exc:
        get_current_superuser(current_user=alice)
    assert exc.value.status_code == 403
