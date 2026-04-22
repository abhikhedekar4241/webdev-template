import uuid

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlmodel.ext.asyncio.session import AsyncSession

from app.api.deps import get_current_user
from app.core.db import get_session
from app.models.org import OrgRole
from app.models.user import User
from app.services.flags import flags_service
from app.services.orgs import org_service

router = APIRouter(prefix="/api/v1/orgs", tags=["flags"])


class FlagOverrideRequest(BaseModel):
    enabled: bool


class FlagStatusResponse(BaseModel):
    flag_name: str
    enabled: bool


@router.patch("/{org_id}/flags/{flag_name}", response_model=FlagStatusResponse)
async def set_flag_override(
    org_id: uuid.UUID,
    flag_name: str,
    body: FlagOverrideRequest,
    session: AsyncSession = Depends(get_session),
    current_user: User = Depends(get_current_user),
):
    membership = await org_service.get_membership(
        session, org_id=org_id, user_id=current_user.id
    )
    if not membership or membership.role not in (OrgRole.owner, OrgRole.admin):
        raise HTTPException(status_code=403, detail="Insufficient permissions")

    defaults = flags_service.list_defaults()
    if flag_name not in defaults:
        raise HTTPException(status_code=404, detail=f"Unknown flag: {flag_name}")

    override = await flags_service.set_override(
        session, org_id=org_id, flag_name=flag_name, enabled=body.enabled
    )
    return {"flag_name": flag_name, "enabled": override.enabled}


@router.get("/{org_id}/flags/{flag_name}", response_model=FlagStatusResponse)
async def get_flag_status(
    org_id: uuid.UUID,
    flag_name: str,
    session: AsyncSession = Depends(get_session),
    current_user: User = Depends(get_current_user),
):
    membership = await org_service.get_membership(
        session, org_id=org_id, user_id=current_user.id
    )
    if not membership:
        raise HTTPException(status_code=403, detail="Not a member of this organization")

    enabled = await flags_service.is_enabled(
        session, org_id=org_id, flag_name=flag_name
    )
    return {"flag_name": flag_name, "enabled": enabled}
