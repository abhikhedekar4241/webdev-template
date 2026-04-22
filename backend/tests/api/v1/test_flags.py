from unittest.mock import patch
from fastapi.testclient import TestClient
from tests.helpers import get_auth_header

MOCK_FLAGS = {"flags": {"new_dashboard": False, "beta_exports": False}}

async def test_api_set_flag_override(client: TestClient, session, alice, alice_org):
    with patch("app.services.flags.flags_service._load_yaml", return_value=MOCK_FLAGS):
        resp = await client.patch(
            f"/api/v1/orgs/{alice_org.id}/flags/new_dashboard",
            json={"enabled": True},
            headers=get_auth_header(alice.id),
        )
    assert resp.status_code == 200
    assert resp.json()["enabled"] is True

async def test_api_get_flag_status(client: TestClient, session, alice, alice_org):
    with patch("app.services.flags.flags_service._load_yaml", return_value=MOCK_FLAGS):
        resp = await client.get(
            f"/api/v1/orgs/{alice_org.id}/flags/new_dashboard",
            headers=get_auth_header(alice.id),
        )
    assert resp.status_code == 200
    assert resp.json()["enabled"] is False
