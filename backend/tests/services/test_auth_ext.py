from app.models.user import User
from app.services.auth import auth_service


async def test_authenticate_user_not_found(session):
    assert (
        await auth_service.authenticate(session, email="not@found.com", password="p")
        is None
    )


async def test_authenticate_oauth_only(session):
    user = User(
        email="oauth@only.com", full_name="O", is_verified=True, hashed_password=None
    )
    session.add(user)
    await session.commit()
    assert (
        await auth_service.authenticate(session, email="oauth@only.com", password="p")
        is None
    )


async def test_authenticate_wrong_password(session, alice):
    # alice is created by fixture with password 'password'
    assert (
        await auth_service.authenticate(session, email=alice.email, password="wrong")
        is None
    )
