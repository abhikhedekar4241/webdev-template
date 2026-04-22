from fastapi.testclient import TestClient
from sqlmodel import Session

from app.services.notifications import notification_service
from tests.helpers import get_auth_header


async def test_api_list_notifications(client: TestClient, session: Session, alice):
    await notification_service.create_notification(
        session, user_id=alice.id, type="t1", data={}
    )
    await session.commit()

    resp = await client.get("/api/v1/notifications/", headers=get_auth_header(alice.id))
    assert resp.status_code == 200
    assert len(resp.json()) == 1


async def test_api_mark_read(client: TestClient, session: Session, alice):
    n = await notification_service.create_notification(
        session, user_id=alice.id, type="t1", data={}
    )
    await session.commit()

    resp = await client.patch(
        f"/api/v1/notifications/{n.id}/read", headers=get_auth_header(alice.id)
    )
    assert resp.status_code == 200
    assert resp.json()["read_at"] is not None


async def test_api_mark_all_read(client: TestClient, session: Session, alice):
    await notification_service.create_notification(
        session, user_id=alice.id, type="t1", data={}
    )
    await session.commit()

    resp = await client.post(
        "/api/v1/notifications/read-all", headers=get_auth_header(alice.id)
    )
    assert resp.status_code == 204

    unread = await notification_service.list_for_user(
        session, user_id=alice.id, unread_only=True
    )
    assert len(unread) == 0
