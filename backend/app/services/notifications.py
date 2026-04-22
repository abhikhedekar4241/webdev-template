import uuid
from datetime import UTC, datetime
from typing import Any

from sqlmodel import select
from sqlmodel.ext.asyncio.session import AsyncSession

from app.models.notification import Notification
from app.services.base import CRUDBase


class NotificationService(CRUDBase[Notification]):
    async def create_notification(
        self,
        session: AsyncSession,
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
        await session.flush()
        return notification

    async def list_for_user(
        self, session: AsyncSession, *, user_id: uuid.UUID, unread_only: bool = False
    ) -> list[Notification]:
        statement = select(Notification).where(Notification.user_id == user_id)
        if unread_only:
            statement = statement.where(Notification.read_at.is_(None))  # type: ignore
        statement = statement.order_by(Notification.created_at.desc())
        return list((await session.exec(statement)).all())

    async def mark_as_read(
        self, session: AsyncSession, *, notification_id: uuid.UUID, user_id: uuid.UUID
    ) -> Notification | None:
        notification = await session.get(Notification, notification_id)
        if not notification or notification.user_id != user_id:
            return None
        notification.read_at = datetime.now(UTC)
        session.add(notification)
        await session.flush()
        return notification

    async def mark_all_as_read(self, session: AsyncSession, *, user_id: uuid.UUID) -> None:
        statement = select(Notification).where(
            Notification.user_id == user_id, Notification.read_at.is_(None)  # type: ignore
        )
        notifications = (await session.exec(statement)).all()
        now = datetime.now(UTC)
        for n in notifications:
            n.read_at = now
            session.add(n)
        await session.flush()


notification_service = NotificationService(Notification)
