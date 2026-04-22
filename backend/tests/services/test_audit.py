import uuid
from unittest.mock import MagicMock
import pytest
from sqlmodel import select, Session

from app.models.audit_log import AuditLog
from app.services.audit import log_event

async def test_log_event_creates_record(session: Session):
    user_id = uuid.uuid4()
    await log_event(session, event="user.login", user_id=user_id)
    logs = (await session.exec(select(AuditLog))).all()
    assert len(logs) == 1
    assert logs[0].event == "user.login"
    assert logs[0].user_id == user_id


async def test_log_event_with_org_and_metadata(session: Session):
    org_id = uuid.uuid4()
    await log_event(
        session,
        event="org.created",
        org_id=org_id,
        metadata={"org_name": "Acme"},
    )
    log = (await session.exec(select(AuditLog))).first()
    assert log.org_id == org_id
    assert log.extra == {"org_name": "Acme"}


async def test_log_event_all_optional(session: Session):
    await log_event(session, event="system.startup")
    log = (await session.exec(select(AuditLog))).first()
    assert log.event == "system.startup"
    assert log.user_id is None
    assert log.org_id is None

async def test_log_event_success(session: Session):
    user_id = uuid.uuid4()
    await log_event(session, event="test_event", user_id=user_id)
    
    entry = (await session.exec(select(AuditLog).where(AuditLog.event == "test_event"))).first()
    assert entry is not None
    assert entry.user_id == user_id

async def test_log_event_failure():
    # Use a mock session that fails on add/flush
    mock_session = MagicMock()
    mock_session.add.side_effect = Exception("DB error")
    
    # Should not raise exception
    await log_event(mock_session, event="failed_event")
