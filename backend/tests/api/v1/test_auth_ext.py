import secrets
import pytest
from httpx import AsyncClient
from sqlmodel import select
from sqlmodel.ext.asyncio.session import AsyncSession
from app.core.config import settings
from app.models.org import Organization
from tests.helpers import get_auth_header

async def test_onboarding_with_org_creation(client: AsyncClient, alice, session: AsyncSession):
    resp = await client.post(
        "/api/v1/auth/onboarding",
        json={"full_name": "Alice Updated", "org_name": "New Org"},
        headers=get_auth_header(alice.id),
    )
    assert resp.status_code == 200
    assert resp.json()["full_name"] == "Alice Updated"
    
    # Verify org was created
    org = (await session.exec(select(Organization).where(Organization.name == "New Org"))).first()
    assert org is not None
    assert org.created_by == alice.id

async def test_onboarding_with_existing_slug_collision(client: AsyncClient, alice, alice_org, session: AsyncSession):
    # alice_org slug is usually 'alice-corp' (depends on factory/fixture)
    # Let's force it
    alice_org.slug = "colliding-slug"
    session.add(alice_org)
    await session.commit()
    await session.refresh(alice_org)
    
    resp = await client.post(
        "/api/v1/auth/onboarding",
        json={"full_name": "Alice Collide", "org_name": "Colliding Slug"},
        headers=get_auth_header(alice.id),
    )
    assert resp.status_code == 200
    
    # Verify new org has a modified slug
    org = (await session.exec(select(Organization).where(Organization.name == "Colliding Slug"))).first()
    assert org is not None
    assert org.slug.startswith("colliding-slug-")

async def test_google_login_not_configured(client: AsyncClient):
    from unittest.mock import patch
    with patch("app.api.v1.auth.settings") as mock_settings:
        mock_settings.GOOGLE_CLIENT_ID = None
        resp = await client.get("/api/v1/auth/google", follow_redirects=False)
        assert resp.status_code == 501

async def test_google_login_redirect(client: AsyncClient):
    from unittest.mock import patch
    with patch("app.api.v1.auth.settings") as mock_settings:
        mock_settings.GOOGLE_CLIENT_ID = "some-id"
        mock_settings.BACKEND_URL = "http://test"
        resp = await client.get("/api/v1/auth/google", follow_redirects=False)
        assert resp.status_code == 307
        assert "accounts.google.com" in resp.headers["location"]

async def test_google_callback_state_mismatch(client: AsyncClient):
    client.cookies.set("oauth_state", "real-state")
    resp = await client.get("/api/v1/auth/google/callback?state=wrong-state", follow_redirects=False)
    assert resp.status_code == 307
    assert "error=oauth_failed" in resp.headers["location"]

async def test_google_callback_oauth_error(client: AsyncClient):
    from unittest.mock import patch
    import httpx
    client.cookies.set("oauth_state", "state123")
    with patch("app.api.v1.auth.oauth_service.exchange_code", side_effect=httpx.HTTPError("fail")):
        resp = await client.get("/api/v1/auth/google/callback?state=state123&code=c", follow_redirects=False)
        assert resp.status_code == 307
        assert "error=oauth_failed" in resp.headers["location"]

async def test_register_already_verified(client: AsyncClient, session):
    from app.models.user import User
    user = User(email="v@f.com", full_name="V", is_verified=True)
    session.add(user)
    await session.commit()
    
    resp = await client.post("/api/v1/auth/register", json={"email": "v@f.com", "password": "password", "full_name": "V"})
    assert resp.status_code == 409

async def test_resend_too_soon(client: AsyncClient, alice, session):
    from app.services.verification import verification_service
    await verification_service.create_otp(session, user_id=alice.id)
    await session.commit()
    await session.refresh(alice)
    
    resp = await client.post("/api/v1/auth/resend-verification", json={"email": alice.email})
    assert resp.status_code == 429
