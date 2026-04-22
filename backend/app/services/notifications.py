import uuid
from datetime import UTC, datetime
from typing import Any

from sqlmodel import Session, select

from app.models.notification import Notification
from app.services.base import CRUDBase


class NotificationService(CRUDBase[Notification]):
    def create_notification(
        self,
        session: Session,
        *,
        user_id: uuid.UUID,
        type: str,
        data: dict[str, Any],
    ) -> Notification:
        notification = Notification(
            user_id=user_id,
            type=type,
            data=data,
        )
        session.add(notification)
        session.flush()
        return notification

    def list_for_user(
        self, session: Session, *, user_id: uuid.UUID, unread_only: bool = False
    ) -> list[Notification]:
        statement = select(Notification).where(Notification.user_id == user_id)
        if unread_only:
            statement = statement.where(Notification.read_at.is_(None))  # type: ignore
        statement = statement.order_by(Notification.created_at.desc())
        return list(session.exec(statement).all())

    def mark_as_read(
        self, session: Session, *, notification_id: uuid.UUID, user_id: uuid.UUID
    ) -> Notification | None:
        notification = session.get(Notification, notification_id)
        if not notification or notification.user_id != user_id:
            return None
        notification.read_at = datetime.now(UTC)
        session.add(notification)
        session.flush()
        return notification

    def mark_all_as_read(self, session: Session, *, user_id: uuid.UUID) -> None:
        statement = select(Notification).where(
            Notification.user_id == user_id, Notification.read_at.is_(None)  # type: ignore
        )
        notifications = session.exec(statement).all()
        now = datetime.now(UTC)
        for n in notifications:
            n.read_at = now
            session.add(n)
        session.flush()


notification_service = NotificationService(Notification)
