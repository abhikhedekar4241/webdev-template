import uuid
from sqlmodel import Session
from app.services.notifications import notification_service

async def test_create_and_list_notifications(session: Session, alice):
    await notification_service.create_notification(
        session, user_id=alice.id, type="test_event", data={"foo": "bar"}
    )
    await notification_service.create_notification(
        session, user_id=alice.id, type="test_event_2", data={"baz": "qux"}
    )
    
    notifications = await notification_service.list_for_user(session, user_id=alice.id)
    assert len(notifications) == 2
    assert notifications[0].type == "test_event_2"
    assert notifications[1].type == "test_event"

async def test_mark_as_read(session: Session, alice):
    n = await notification_service.create_notification(
        session, user_id=alice.id, type="test", data={}
    )
    assert n.read_at is None
    
    marked = await notification_service.mark_as_read(session, notification_id=n.id, user_id=alice.id)
    assert marked is not None
    assert marked.read_at is not None

async def test_mark_as_read_wrong_user(session: Session, alice):
    n = await notification_service.create_notification(
        session, user_id=alice.id, type="test", data={}
    )
    other_id = uuid.uuid4()
    marked = await notification_service.mark_as_read(session, notification_id=n.id, user_id=other_id)
    assert marked is None

async def test_mark_all_as_read(session: Session, alice):
    await notification_service.create_notification(session, user_id=alice.id, type="t1", data={})
    await notification_service.create_notification(session, user_id=alice.id, type="t2", data={})
    
    await notification_service.mark_all_as_read(session, user_id=alice.id)
    
    unread = await notification_service.list_for_user(session, user_id=alice.id, unread_only=True)
    assert len(unread) == 0
