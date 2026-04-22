"""Seed development data: 2 users, 1 org, roles, enough to develop against immediately."""

import asyncio
import sys

sys.path.insert(0, "/app")

from sqlmodel import select
from sqlmodel.ext.asyncio.session import AsyncSession

from app.core.db import engine
from app.models.invitation import OrgInvitation
from app.models.org import Organization, OrgRole
from app.services.auth import auth_service
from app.services.invitations import invitation_service
from app.services.orgs import org_service

USERS = [
    {
        "email": "admin@example.com",
        "password": "password123",
        "full_name": "Admin User",
    },
    {
        "email": "member@example.com",
        "password": "password123",
        "full_name": "Member User",
    },
]


async def seed():
    async with AsyncSession(engine, expire_on_commit=False) as session:
        # Create users
        users = {}
        for u in USERS:
            existing = await auth_service.get_by_email(session, email=u["email"])
            if not existing:
                user = await auth_service.create_user(
                    session,
                    email=u["email"],
                    password=u["password"],
                    full_name=u["full_name"],
                )
                print(f"Created user: {u['email']}")
            else:
                user = existing
                print(f"User already exists: {u['email']}")
            users[u["email"]] = user

        # Mark seed users as verified so dev login works
        admin = users["admin@example.com"]
        admin.is_superuser = True
        if not admin.is_verified:
            admin.is_verified = True
        session.add(admin)
        await session.commit()
        await session.refresh(admin)

        member = users["member@example.com"]
        if not member.is_verified:
            member.is_verified = True
        session.add(member)
        await session.commit()
        await session.refresh(member)

        # Create org

        existing_org = (await session.exec(
            select(Organization).where(Organization.slug == "demo-org")
        )).first()

        if not existing_org:
            org = await org_service.create_org(
                session, name="Demo Org", slug="demo-org", created_by=admin.id
            )
            await org_service.add_member(
                session, org_id=org.id, user_id=member.id, role=OrgRole.member
            )
            print(
                f"Created org: demo-org (admin: {admin.email}, member: {member.email})"
            )
        else:
            org = existing_org
            print("Org already exists: demo-org")

        # Create pending invitation for demonstration
        existing_invite = (await session.exec(
            select(OrgInvitation).where(
                OrgInvitation.invited_email == "invited@example.com"
            )
        )).first()

        if not existing_invite:
            await invitation_service.create_invitation(
                session,
                org_id=org.id,
                invited_email="invited@example.com",
                role=OrgRole.member,
                invited_by=admin.id,
            )
            print("Created pending invitation for: invited@example.com")

        await session.commit()

    print("Seed complete.")


if __name__ == "__main__":
    asyncio.run(seed())
