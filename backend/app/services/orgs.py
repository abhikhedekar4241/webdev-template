import uuid
from datetime import UTC, datetime

import structlog
from sqlmodel import select
from sqlmodel.ext.asyncio.session import AsyncSession

from app.core.exceptions import OrgAlreadyExistsError
from app.models.org import Organization, OrgMembership, OrgRole
from app.models.user import User
from app.services.base import CRUDBase

logger = structlog.get_logger()


class OrgService(CRUDBase[Organization]):
    async def create_org(
        self,
        session: AsyncSession,
        *,
        name: str,
        slug: str,
        created_by: uuid.UUID,
    ) -> Organization:
        existing = await self.get_by_slug(session, slug=slug)
        if existing:
            raise OrgAlreadyExistsError()

        org = Organization(name=name, slug=slug, created_by=created_by)
        session.add(org)
        await session.flush()
        
        membership = OrgMembership(
            org_id=org.id, user_id=created_by, role=OrgRole.owner
        )
        session.add(membership)
        await session.flush()
        
        logger.info(
            "org_created", 
            org_id=str(org.id), 
            org_slug=org.slug,
            created_by=str(created_by)
        )
        return org

    async def get_by_slug(self, session: AsyncSession, *, slug: str) -> Organization | None:
        return (await session.exec(
            select(Organization).where(Organization.slug == slug)
        )).first()

    async def list_user_orgs(
        self, session: AsyncSession, *, user_id: uuid.UUID
    ) -> list[Organization]:
        return list(
            (await session.exec(
                select(Organization)
                .join(OrgMembership, OrgMembership.org_id == Organization.id)
                .where(OrgMembership.user_id == user_id)
                .where(Organization.deleted_at.is_(None))  # type: ignore[arg-type]
            )).all()
        )

    async def get_org_for_member(
        self, session: AsyncSession, *, org_id: uuid.UUID, user_id: uuid.UUID
    ) -> Organization | None:
        membership = await self.get_membership(session, org_id=org_id, user_id=user_id)
        if not membership:
            return None
        org = await session.get(Organization, org_id)
        if not org or org.deleted_at is not None:
            return None
        return org

    async def get_org_for_member_by_slug(
        self, session: AsyncSession, *, slug: str, user_id: uuid.UUID
    ) -> Organization | None:
        org = await self.get_by_slug(session, slug=slug)
        if not org or org.deleted_at is not None:
            return None
        membership = self.get_membership(session, org_id=org.id, user_id=user_id)
        if not membership:
            return None
        return org

    async def get_membership(
        self, session: AsyncSession, *, org_id: uuid.UUID, user_id: uuid.UUID
    ) -> OrgMembership | None:
        return (await session.exec(
            select(OrgMembership)
            .where(OrgMembership.org_id == org_id)
            .where(OrgMembership.user_id == user_id)
        )).first()

    async def update_org(
        self,
        session: AsyncSession,
        *,
        org: Organization,
        name: str | None = None,
        slug: str | None = None,
    ) -> Organization:
        if slug and slug != org.slug:
            existing = await self.get_by_slug(session, slug=slug)
            if existing:
                raise OrgAlreadyExistsError()
            org.slug = slug

        if name is not None:
            org.name = name
            
        session.add(org)
        await session.flush()
        logger.info("org_updated", org_id=str(org.id), org_slug=org.slug)
        return org

    async def soft_delete_org(self, session: AsyncSession, *, org: Organization) -> Organization:
        org.deleted_at = datetime.now(UTC)
        session.add(org)
        await session.flush()
        logger.info("org_soft_deleted", org_id=str(org.id), org_slug=org.slug)
        return org

    async def list_members(self, session: AsyncSession, *, org_id: uuid.UUID) -> list[OrgMembership]:
        return list(
            (await session.exec(
                select(OrgMembership).where(OrgMembership.org_id == org_id)
            )).all()
        )

    async def list_members_with_users(
        self, session: AsyncSession, *, org_id: uuid.UUID
    ) -> list[tuple[OrgMembership, User]]:
        """Fix N+1 query problem by joining User."""
        return list(
            (await session.exec(
                select(OrgMembership, User)
                .join(User, OrgMembership.user_id == User.id)
                .where(OrgMembership.org_id == org_id)
            )).all()
        )

    async def add_member(
        self,
        session: AsyncSession,
        *,
        org_id: uuid.UUID,
        user_id: uuid.UUID,
        role: OrgRole,
    ) -> OrgMembership:
        membership = OrgMembership(org_id=org_id, user_id=user_id, role=role)
        session.add(membership)
        await session.flush()
        logger.info(
            "member_added", 
            org_id=str(org_id), 
            user_id=str(user_id), 
            role=role
        )
        return membership

    async def change_role(
        self,
        session: AsyncSession,
        *,
        org_id: uuid.UUID,
        user_id: uuid.UUID,
        role: OrgRole,
    ) -> OrgMembership | None:
        membership = await self.get_membership(session, org_id=org_id, user_id=user_id)
        if not membership:
            return None
        membership.role = role
        session.add(membership)
        await session.flush()
        logger.info(
            "member_role_changed", 
            org_id=str(org_id), 
            user_id=str(user_id), 
            role=role
        )
        return membership

    async def remove_member(
        self, session: AsyncSession, *, org_id: uuid.UUID, user_id: uuid.UUID
    ) -> None:
        membership = await self.get_membership(session, org_id=org_id, user_id=user_id)
        if membership:
            await session.delete(membership)
            await session.flush()
            logger.info("member_removed", org_id=str(org_id), user_id=str(user_id))


org_service = OrgService(Organization)
