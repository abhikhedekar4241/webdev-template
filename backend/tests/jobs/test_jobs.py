import uuid
from datetime import UTC, datetime, timedelta

import pytest
from sqlmodel import Session, select

from app.jobs.examples import cleanup_expired_invitations_task, send_welcome_email_task
from app.models.invitation import InvitationStatus, OrgInvitation


def test_send_welcome_email_task():
    result = send_welcome_email_task.run(user_email="test@example.com", full_name="Test")
    assert result["status"] == "sent"
    assert result["to"] == "test@example.com"


def test_cleanup_expired_invitations_task(session: Session):
    # Create one expired and one non-expired invitation
    now = datetime.now(UTC)
    
    expired = OrgInvitation(
        org_id=uuid.uuid4(),
        invited_email="expired@example.com",
        invited_by=uuid.uuid4(),
        expires_at=now - timedelta(days=1),
        status=InvitationStatus.pending
    )
    valid = OrgInvitation(
        org_id=uuid.uuid4(),
        invited_email="valid@example.com",
        invited_by=uuid.uuid4(),
        expires_at=now + timedelta(days=1),
        status=InvitationStatus.pending
    )
    
    session.add(expired)
    session.add(valid)
    session.commit()

    # We use .run() to call the function directly without celery infrastructure
    # But wait, cleanup_expired_invitations_task uses app.core.db.engine
    # In tests, we want it to use our test session/engine.
    # Since the task creates its own session using engine, we might need to patch it.
    
    from unittest.mock import patch
    from app.core import db
    
    with patch("app.core.db.engine", session.get_bind()):
        result = cleanup_expired_invitations_task.run()
    
    assert result["expired_count"] == 1
    
    session.refresh(expired)
    session.refresh(valid)
    
    assert expired.status == InvitationStatus.declined
    assert valid.status == InvitationStatus.pending
