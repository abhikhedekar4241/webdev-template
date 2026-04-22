import uuid
from datetime import UTC, datetime, timedelta
from unittest.mock import MagicMock, patch

from sqlalchemy import create_engine
from sqlmodel import Session, SQLModel
from sqlmodel.pool import StaticPool

from app.jobs.examples import cleanup_expired_invitations_task, send_welcome_email_task
from app.models.invitation import InvitationStatus, OrgInvitation


async def test_send_welcome_email_task():
    result = send_welcome_email_task.run(
        user_email="test@example.com", full_name="Test"
    )
    assert result["status"] == "sent"
    assert result["to"] == "test@example.com"


def test_cleanup_expired_invitations_task():
    # Create a dedicated sync in-memory engine for this task test
    sync_engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    SQLModel.metadata.create_all(sync_engine)

    now = datetime.now(UTC)
    expired = OrgInvitation(
        org_id=uuid.uuid4(),
        invited_email="expired@example.com",
        invited_by=uuid.uuid4(),
        expires_at=now - timedelta(days=1),
        status=InvitationStatus.pending,
    )
    valid = OrgInvitation(
        org_id=uuid.uuid4(),
        invited_email="valid@example.com",
        invited_by=uuid.uuid4(),
        expires_at=now + timedelta(days=1),
        status=InvitationStatus.pending,
    )

    with Session(sync_engine) as session:
        session.add(expired)
        session.add(valid)
        session.commit()

        # Patch the async engine so the task uses our sync engine
        mock_async_engine = MagicMock()
        mock_async_engine.sync_engine = sync_engine

        with patch("app.core.db.engine", mock_async_engine):
            result = cleanup_expired_invitations_task.run()

        assert result["expired_count"] == 1

        session.refresh(expired)
        session.refresh(valid)
        assert expired.status == InvitationStatus.declined
        assert valid.status == InvitationStatus.pending
