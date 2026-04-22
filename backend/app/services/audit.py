import uuid
from typing import Any

import structlog
from sqlmodel.ext.asyncio.session import AsyncSession

from app.models.audit_log import AuditLog

logger = structlog.get_logger()


async def log_event(
    session: AsyncSession,
    *,
    event: str,
    user_id: uuid.UUID | None = None,
    org_id: uuid.UUID | None = None,
    metadata: dict[str, Any] | None = None,
) -> None:
    try:
        entry = AuditLog(
            event=event,
            user_id=user_id,
            org_id=org_id,
            extra=metadata or {},
        )
        session.add(entry)
        await session.flush()
        logger.info("audit_event", audit_event=event, user_id=str(user_id), org_id=str(org_id))
    except Exception as exc:
        logger.error("audit_log_failed", audit_event=event, error=str(exc))
