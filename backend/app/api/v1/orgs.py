import uuid
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.exc import IntegrityError
from sqlmodel import Session, select

from app.api.deps import get_current_user
from app.core.db import get_session
from app.models.org import OrgMembership, OrgRole
from app.models.user import User
from app.services.orgs import org_service

router = APIRouter(prefix="/api/v1/orgs", tags=["orgs"])


# --- Schemas ---


class OrgCreate(BaseModel):
    name: str
    slug: str


class OrgUpdate(BaseModel):
    name: str | None = None
    slug: str | None = None


class OrgResponse(BaseModel):
    id: uuid.UUID
    name: str
    slug: str
    created_by: uuid.UUID
    created_at: datetime


class MembershipResponse(BaseModel):
    user_id: uuid.UUID
    email: str
    full_name: str
    role: OrgRole
    joined_at: datetime


class RoleUpdate(BaseModel):
    role: OrgRole


# --- Helpers ---


def _require_org(session: Session, org_id: uuid.UUID, current_user: User):
    """Return org if current user is a member, else raise 404."""
    org = org_service.get_org_for_member(
        session, org_id=org_id, user_id=current_user.id
    )
    if not org:
        raise HTTPException(status_code=404, detail="Organization not found")
    return org


def _require_role(
    session: Session, org_id: uuid.UUID, user_id: uuid.UUID, allowed: list[OrgRole]
):
    membership = org_service.get_membership(session, org_id=org_id, user_id=user_id)
    if not membership or membership.role not in allowed:
        raise HTTPException(status_code=403, detail="Insufficient permissions")
    return membership


# --- Endpoints ---


@router.post("/", response_model=OrgResponse, status_code=201)
def create_org(
    body: OrgCreate,
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user),
):
    if not body.slug or not body.slug.strip():
        raise HTTPException(status_code=422, detail="Slug cannot be empty")
    try:
        org = org_service.create_org(
            session, name=body.name, slug=body.slug, created_by=current_user.id
        )
    except IntegrityError:
        session.rollback()
        raise HTTPException(status_code=409, detail="An organization with this slug already exists")
    return org


@router.get("/", response_model=list[OrgResponse])
def list_orgs(
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user),
):
    return org_service.list_user_orgs(session, user_id=current_user.id)


@router.get("/{org_id}", response_model=OrgResponse)
def get_org(
    org_id: uuid.UUID,
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user),
):
    return _require_org(session, org_id, current_user)


@router.patch("/{org_id}", response_model=OrgResponse)
def update_org(
    org_id: uuid.UUID,
    body: OrgUpdate,
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user),
):
    org = _require_org(session, org_id, current_user)
    _require_role(session, org_id, current_user.id, [OrgRole.owner, OrgRole.admin])
    try:
        return org_service.update_org(session, org=org, name=body.name, slug=body.slug)
    except IntegrityError:
        session.rollback()
        raise HTTPException(status_code=409, detail="An organization with this slug already exists")


@router.delete("/{org_id}", status_code=204)
def delete_org(
    org_id: uuid.UUID,
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user),
):
    org = _require_org(session, org_id, current_user)
    _require_role(session, org_id, current_user.id, [OrgRole.owner])
    org_service.soft_delete_org(session, org=org)


@router.get("/{org_id}/members", response_model=list[MembershipResponse])
def list_members(
    org_id: uuid.UUID,
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user),
):
    _require_org(session, org_id, current_user)
    memberships = org_service.list_members(session, org_id=org_id)
    result = []
    for m in memberships:
        user = session.exec(select(User).where(User.id == m.user_id)).first()
        result.append(
            MembershipResponse(
                user_id=m.user_id,
                email=user.email if user else "",
                full_name=user.full_name if user else "",
                role=m.role,
                joined_at=m.joined_at,
            )
        )
    return result


@router.patch("/{org_id}/members/{user_id}", response_model=MembershipResponse)
def change_member_role(
    org_id: uuid.UUID,
    user_id: uuid.UUID,
    body: RoleUpdate,
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user),
):
    _require_org(session, org_id, current_user)
    _require_role(session, org_id, current_user.id, [OrgRole.owner, OrgRole.admin])
    membership = org_service.change_role(
        session, org_id=org_id, user_id=user_id, role=body.role
    )
    if not membership:
        raise HTTPException(status_code=404, detail="Member not found")
    user = session.exec(select(User).where(User.id == membership.user_id)).first()
    return MembershipResponse(
        user_id=membership.user_id,
        email=user.email if user else "",
        full_name=user.full_name if user else "",
        role=membership.role,
        joined_at=membership.joined_at,
    )


@router.delete("/{org_id}/members/{user_id}", status_code=204)
def remove_member(
    org_id: uuid.UUID,
    user_id: uuid.UUID,
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user),
):
    _require_org(session, org_id, current_user)
    _require_role(session, org_id, current_user.id, [OrgRole.owner, OrgRole.admin])
    target_membership = org_service.get_membership(session, org_id=org_id, user_id=user_id)
    if target_membership and target_membership.role == OrgRole.owner:
        raise HTTPException(status_code=403, detail="Cannot remove the org owner")
    org_service.remove_member(session, org_id=org_id, user_id=user_id)
