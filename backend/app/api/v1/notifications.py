import uuid
from datetime import UTC, datetime
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlmodel.ext.asyncio.session import AsyncSession

from app.api.deps import get_current_user, get_session
from app.models.invitation import OrgInvitation
from app.models.user import User
from app.schemas.notifications import NotificationResponse
from app.services.notifications import notification_service

router = APIRouter(prefix="/api/v1/notifications", tags=["notifications"])


@router.get("/", response_model=list[NotificationResponse])
async def list_notifications(
    unread_only: bool = Query(False),
    session: AsyncSession = Depends(get_session),
    current_user: User = Depends(get_current_user),
) -> Any:
    """List notifications for the current user, enriched with live invitation status."""
    notifications = await notification_service.list_for_user(
        session, user_id=current_user.id, unread_only=unread_only
    )

    # Enrich invitation notifications with live status
    for n in notifications:
        if n.type == "org_invitation" and "invitation_id" in n.data:
            inv = await session.get(OrgInvitation, uuid.UUID(n.data["invitation_id"]))
            if inv:
                # Add live status to the data payload returned to frontend
                n.data["invitation_status"] = inv.status
                if inv.expires_at < datetime.now(UTC) and inv.status == "pending":
                    n.data["invitation_status"] = "expired"
            else:
                n.data["invitation_status"] = "deleted"

    return [NotificationResponse.model_validate(n) for n in notifications]


@router.patch("/{notification_id}/read", response_model=NotificationResponse)
async def mark_notification_read(
    notification_id: uuid.UUID,
    session: AsyncSession = Depends(get_session),
    current_user: User = Depends(get_current_user),
) -> Any:
    """Mark a specific notification as read."""
    notification = await notification_service.mark_as_read(
        session, notification_id=notification_id, user_id=current_user.id
    )
    if not notification:
        raise HTTPException(status_code=404, detail="Notification not found")
    await session.commit()
    await session.refresh(notification)
    return NotificationResponse.model_validate(notification)


@router.post("/read-all", status_code=204)
async def mark_all_read(
    session: AsyncSession = Depends(get_session),
    current_user: User = Depends(get_current_user),
) -> None:
    """Mark all unread notifications as read."""
    await notification_service.mark_all_as_read(session, user_id=current_user.id)
    await session.commit()
