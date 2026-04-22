import uuid

import structlog
from fastapi import APIRouter, Depends, HTTPException
from sqlmodel.ext.asyncio.session import AsyncSession

from app.api.deps import get_current_user
from app.core.db import get_session
from app.models.org import OrgRole
from app.models.user import User
from app.schemas.api_keys import ApiKeyCreate, ApiKeyCreated, ApiKeyResponse
from app.services.api_keys import api_key_service
from app.services.orgs import org_service

router = APIRouter(prefix="/api/v1/orgs", tags=["api-keys"])
logger = structlog.get_logger()


async def _require_owner_or_admin(session: AsyncSession, org_id: uuid.UUID, user: User) -> None:
    membership = await org_service.get_membership(session, org_id=org_id, user_id=user.id)
    if not membership or membership.role not in (OrgRole.owner, OrgRole.admin):
        raise HTTPException(status_code=403, detail="Insufficient permissions")


@router.post("/{org_id}/api-keys", response_model=ApiKeyCreated, status_code=201)
async def create_api_key(
    org_id: uuid.UUID,
    body: ApiKeyCreate,
    session: AsyncSession = Depends(get_session),
    current_user: User = Depends(get_current_user),
) -> ApiKeyCreated:
    await _require_owner_or_admin(session, org_id, current_user)
    record, raw_key = await api_key_service.create(
        session, org_id=org_id, name=body.name, created_by=current_user.id
    )
    await session.commit()
    await session.refresh(record)

    return ApiKeyCreated(
        id=record.id,
        name=record.name,
        key_prefix=record.key_prefix,
        created_at=record.created_at,
        last_used_at=record.last_used_at,
        expires_at=record.expires_at,
        key=raw_key,
    )


@router.get("/{org_id}/api-keys", response_model=list[ApiKeyResponse])
async def list_api_keys(
    org_id: uuid.UUID,
    session: AsyncSession = Depends(get_session),
    current_user: User = Depends(get_current_user),
) -> list[ApiKeyResponse]:
    membership = await org_service.get_membership(
        session, org_id=org_id, user_id=current_user.id
    )
    if not membership:
        raise HTTPException(status_code=403, detail="Not a member of this organization")
    keys = await api_key_service.list_for_org(session, org_id=org_id)
    return [ApiKeyResponse.model_validate(k) for k in keys]


@router.delete("/{org_id}/api-keys/{key_id}", status_code=204)
async def revoke_api_key(
    org_id: uuid.UUID,
    key_id: uuid.UUID,
    session: AsyncSession = Depends(get_session),
    current_user: User = Depends(get_current_user),
) -> None:
    await _require_owner_or_admin(session, org_id, current_user)
    revoked = await api_key_service.revoke(session, key_id=key_id, org_id=org_id)
    if not revoked:
        raise HTTPException(status_code=404, detail="API key not found")
    await session.commit()
