import uuid

import pytest

from app.models.audit_log import AuditLog
from app.models.org import OrgMembership, Organization
from app.models.user import User
from app.services.audit import log_event


@pytest.fixture(autouse=True)
def create_tables(session):
    User.__table__.create(session.get_bind(), checkfirst=True)
    Organization.__table__.create(session.get_bind(), checkfirst=True)
    OrgMembership.__table__.create(session.get_bind(), checkfirst=True)
    AuditLog.__table__.create(session.get_bind(), checkfirst=True)
    yield
    AuditLog.__table__.drop(session.get_bind())
    OrgMembership.__table__.drop(session.get_bind())
    Organization.__table__.drop(session.get_bind())
    User.__table__.drop(session.get_bind())


def test_log_event_creates_record(session):
    user_id = uuid.uuid4()
    log_event(session, event="user.login", user_id=user_id)
    from sqlmodel import select
    logs = session.exec(select(AuditLog)).all()
    assert len(logs) == 1
    assert logs[0].event == "user.login"
    assert logs[0].user_id == user_id


def test_log_event_with_org_and_metadata(session):
    org_id = uuid.uuid4()
    log_event(
        session,
        event="org.created",
        org_id=org_id,
        metadata={"org_name": "Acme"},
    )
    from sqlmodel import select
    log = session.exec(select(AuditLog)).first()
    assert log.org_id == org_id
    assert log.extra == {"org_name": "Acme"}


def test_log_event_all_optional(session):
    log_event(session, event="system.startup")
    from sqlmodel import select
    log = session.exec(select(AuditLog)).first()
    assert log.event == "system.startup"
    assert log.user_id is None
    assert log.org_id is None
