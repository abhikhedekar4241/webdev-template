import pytest
from app.services.auth import auth_service
from app.models.user import User

def test_authenticate_user_not_found(session):
    assert auth_service.authenticate(session, email="not@found.com", password="p") is None

def test_authenticate_oauth_only(session):
    user = User(email="oauth@only.com", full_name="O", is_verified=True, hashed_password=None)
    session.add(user)
    session.commit()
    assert auth_service.authenticate(session, email="oauth@only.com", password="p") is None

def test_authenticate_wrong_password(session, alice):
    # alice is created by fixture with password 'password'
    assert auth_service.authenticate(session, email=alice.email, password="wrong") is None
