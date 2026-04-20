import re
import uuid
from datetime import datetime

from sqlmodel import Session, select

from app.models.org import Organization, OrgMembership, OrgRole
from app.services.base import CRUDBase


def _slugify(s: str) -> str:
    return re.sub(r"[^a-z0-9-]", "-", s.lower()).strip("-")


class OrgService(CRUDBase[Organization]):
    def create_org(
        self,
        session: Session,
        *,
        name: str,
        slug: str,
        created_by: uuid.UUID,
    ) -> Organization:
        org = Organization(name=name, slug=slug, created_by=created_by)
        session.add(org)
        session.flush()  # get org.id without committing yet
        membership = OrgMembership(
            org_id=org.id, user_id=created_by, role=OrgRole.owner
        )
        session.add(membership)
        session.commit()
        session.refresh(org)
        return org

    def list_user_orgs(
        self, session: Session, *, user_id: uuid.UUID
    ) -> list[Organization]:
        return list(
            session.exec(
                select(Organization)
                .join(OrgMembership, OrgMembership.org_id == Organization.id)
                .where(OrgMembership.user_id == user_id)
                .where(Organization.deleted_at.is_(None))  # type: ignore[arg-type]
            ).all()
        )

    def get_org_for_member(
        self, session: Session, *, org_id: uuid.UUID, user_id: uuid.UUID
    ) -> Organization | None:
        membership = self.get_membership(session, org_id=org_id, user_id=user_id)
        if not membership:
            return None
        org = session.get(Organization, org_id)
        if not org or org.deleted_at is not None:
            return None
        return org

    def get_membership(
        self, session: Session, *, org_id: uuid.UUID, user_id: uuid.UUID
    ) -> OrgMembership | None:
        return session.exec(
            select(OrgMembership)
            .where(OrgMembership.org_id == org_id)
            .where(OrgMembership.user_id == user_id)
        ).first()

    def update_org(
        self,
        session: Session,
        *,
        org: Organization,
        name: str | None = None,
        slug: str | None = None,
    ) -> Organization:
        if name is not None:
            org.name = name
        if slug is not None:
            org.slug = slug
        session.add(org)
        session.commit()
        session.refresh(org)
        return org

    def soft_delete_org(self, session: Session, *, org: Organization) -> Organization:
        org.deleted_at = datetime.utcnow()
        session.add(org)
        session.commit()
        session.refresh(org)
        return org

    def list_members(
        self, session: Session, *, org_id: uuid.UUID
    ) -> list[OrgMembership]:
        return list(
            session.exec(
                select(OrgMembership).where(OrgMembership.org_id == org_id)
            ).all()
        )

    def add_member(
        self,
        session: Session,
        *,
        org_id: uuid.UUID,
        user_id: uuid.UUID,
        role: OrgRole,
    ) -> OrgMembership:
        membership = OrgMembership(org_id=org_id, user_id=user_id, role=role)
        session.add(membership)
        session.commit()
        session.refresh(membership)
        return membership

    def change_role(
        self,
        session: Session,
        *,
        org_id: uuid.UUID,
        user_id: uuid.UUID,
        role: OrgRole,
    ) -> OrgMembership | None:
        membership = self.get_membership(session, org_id=org_id, user_id=user_id)
        if not membership:
            return None
        membership.role = role
        session.add(membership)
        session.commit()
        session.refresh(membership)
        return membership

    def remove_member(
        self, session: Session, *, org_id: uuid.UUID, user_id: uuid.UUID
    ) -> None:
        membership = self.get_membership(session, org_id=org_id, user_id=user_id)
        if membership:
            session.delete(membership)
            session.commit()


org_service = OrgService(Organization)
