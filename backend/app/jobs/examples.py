"""
Example Celery tasks.

Run the worker with:
  celery -A app.worker.celery_app worker --loglevel=info

Dispatch from application code:
  from app.jobs.examples import send_welcome_email_task
  send_welcome_email_task.delay(user_email="alice@example.com", full_name="Alice")
"""
from datetime import UTC

import structlog

from app.worker import celery_app

logger = structlog.get_logger()


@celery_app.task(bind=True, max_retries=3)
def send_welcome_email_task(self, *, user_email: str, full_name: str) -> dict:
    """Send a welcome email asynchronously."""
    try:
        logger.info("task_send_welcome_email", user_email=user_email, full_name=full_name)
        return {"status": "sent", "to": user_email}
    except Exception as exc:
        logger.error("task_failed", task="send_welcome_email", error=str(exc))
        raise self.retry(exc=exc, countdown=60)


@celery_app.task(bind=True, max_retries=3)
def cleanup_expired_invitations_task(self) -> dict:
    """Periodic task to clean up expired invitations."""
    from datetime import datetime

    from sqlmodel import Session, select

    from app.core.db import engine
    from app.models.invitation import InvitationStatus, OrgInvitation

    try:
        with Session(engine) as session:
            expired = session.exec(
                select(OrgInvitation)
                .where(OrgInvitation.status == InvitationStatus.pending)
                .where(OrgInvitation.expires_at < datetime.now(UTC))
            ).all()

            count = len(expired)
            for inv in expired:
                inv.status = InvitationStatus.declined
                session.add(inv)
            session.commit()

        logger.info("cleanup_expired_invitations", count=count)
        return {"expired_count": count}
    except Exception as exc:
        logger.error("task_failed", task="cleanup_expired_invitations", error=str(exc))
        raise self.retry(exc=exc, countdown=120)
