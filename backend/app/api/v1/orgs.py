import uuid

import structlog
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.exc import IntegrityError
from sqlmodel.ext.asyncio.session import AsyncSession

from app.api.deps import get_current_user, require_org, require_role
from app.core.db import get_session
from app.models.org import OrgRole
from app.models.user import User
from app.schemas.orgs import (
    MembershipResponse,
    OrgCreate,
    OrgResponse,
    OrgUpdate,
    RoleUpdate,
)
from app.services.orgs import org_service

router = APIRouter(prefix="/api/v1/orgs", tags=["orgs"])
logger = structlog.get_logger()


@router.post("/", response_model=OrgResponse, status_code=201)
async def create_org(
    body: OrgCreate,
    session: AsyncSession = Depends(get_session),
    current_user: User = Depends(get_current_user),
):
    if not body.slug or not body.slug.strip():
        raise HTTPException(status_code=422, detail="Slug cannot be empty")
    try:
        org = await org_service.create_org(
            session, name=body.name, slug=body.slug, created_by=current_user.id
        )
        await session.commit()
        await session.refresh(org)
        return org
    except IntegrityError:
        await session.rollback()
        raise HTTPException(
            status_code=409, detail="An organization with this slug already exists"
        )


@router.get("/", response_model=list[OrgResponse])
async def list_orgs(
    session: AsyncSession = Depends(get_session),
    current_user: User = Depends(get_current_user),
):
    return await org_service.list_user_orgs(session, user_id=current_user.id)


@router.get("/slug/{slug}", response_model=OrgResponse)
async def get_org_by_slug(
    slug: str,
    session: AsyncSession = Depends(get_session),
    current_user: User = Depends(get_current_user),
):
    org = await org_service.get_org_for_member_by_slug(
        session, slug=slug, user_id=current_user.id
    )
    if not org:
        raise HTTPException(status_code=404, detail="Organization not found")
    return org


@router.get("/{org_id}", response_model=OrgResponse)
async def get_org(
    org_id: uuid.UUID,
    session: AsyncSession = Depends(get_session),
    current_user: User = Depends(get_current_user),
):
    return await require_org(session, org_id, current_user.id)


@router.patch("/{org_id}", response_model=OrgResponse)
async def update_org(
    org_id: uuid.UUID,
    body: OrgUpdate,
    session: AsyncSession = Depends(get_session),
    current_user: User = Depends(get_current_user),
):
    org = await require_org(session, org_id, current_user.id)
    await require_role(session, org_id, current_user.id, [OrgRole.owner, OrgRole.admin])
    try:
        updated = await org_service.update_org(
            session, org=org, name=body.name, slug=body.slug
        )
        await session.commit()
        await session.refresh(updated)
        return updated
    except IntegrityError:
        await session.rollback()
        raise HTTPException(
            status_code=409, detail="An organization with this slug already exists"
        )


@router.delete("/{org_id}", status_code=204)
async def delete_org(
    org_id: uuid.UUID,
    session: AsyncSession = Depends(get_session),
    current_user: User = Depends(get_current_user),
):
    org = await require_org(session, org_id, current_user.id)
    await require_role(session, org_id, current_user.id, [OrgRole.owner])
    await org_service.soft_delete_org(session, org=org)
    await session.commit()


@router.get("/{org_id}/members", response_model=list[MembershipResponse])
async def list_members(
    org_id: uuid.UUID,
    session: AsyncSession = Depends(get_session),
    current_user: User = Depends(get_current_user),
):
    await require_org(session, org_id, current_user.id)
    memberships_with_users = await org_service.list_members_with_users(
        session, org_id=org_id
    )
    return [
        MembershipResponse(
            user_id=m.user_id,
            email=u.email,
            full_name=u.full_name,
            role=m.role,
            joined_at=m.joined_at,
        )
        for m, u in memberships_with_users
    ]


@router.patch("/{org_id}/members/{user_id}", response_model=MembershipResponse)
async def change_member_role(
    org_id: uuid.UUID,
    user_id: uuid.UUID,
    body: RoleUpdate,
    session: AsyncSession = Depends(get_session),
    current_user: User = Depends(get_current_user),
):
    await require_org(session, org_id, current_user.id)
    await require_role(session, org_id, current_user.id, [OrgRole.owner, OrgRole.admin])
    membership = await org_service.change_role(
        session, org_id=org_id, user_id=user_id, role=body.role
    )
    if not membership:
        raise HTTPException(status_code=404, detail="Member not found")

    await session.commit()
    await session.refresh(membership)

    user = await session.get(User, membership.user_id)
    return MembershipResponse(
        user_id=membership.user_id,
        email=user.email if user else "",
        full_name=user.full_name if user else "",
        role=membership.role,
        joined_at=membership.joined_at,
    )


@router.delete("/{org_id}/members/{user_id}", status_code=204)
async def remove_member(
    org_id: uuid.UUID,
    user_id: uuid.UUID,
    session: AsyncSession = Depends(get_session),
    current_user: User = Depends(get_current_user),
):
    await require_org(session, org_id, current_user.id)
    await require_role(session, org_id, current_user.id, [OrgRole.owner, OrgRole.admin])
    target_membership = await org_service.get_membership(
        session, org_id=org_id, user_id=user_id
    )
    if target_membership and target_membership.role == OrgRole.owner:
        raise HTTPException(status_code=403, detail="Cannot remove the org owner")
    await org_service.remove_member(session, org_id=org_id, user_id=user_id)
    await session.commit()
