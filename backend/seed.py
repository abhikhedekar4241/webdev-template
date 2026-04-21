"""Seed development data: 2 users, 1 org, roles, enough to develop against immediately."""

import sys

sys.path.insert(0, "/app")

from sqlmodel import Session, select

from app.core.db import engine
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


def seed():
    with Session(engine) as session:
        # Create users
        users = {}
        for u in USERS:
            existing = auth_service.get_by_email(session, u["email"])
            if not existing:
                user = auth_service.create_user(
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

        # Create org
        admin = users["admin@example.com"]
        member = users["member@example.com"]

        existing_org = session.exec(
            select(Organization).where(Organization.slug == "demo-org")
        ).first()

        if not existing_org:
            org = org_service.create_org(
                session, name="Demo Org", slug="demo-org", created_by=admin.id
            )
            org_service.add_member(
                session, org_id=org.id, user_id=member.id, role=OrgRole.member
            )
            print(
                f"Created org: demo-org (admin: {admin.email}, member: {member.email})"
            )
        else:
            org = existing_org
            print("Org already exists: demo-org")

        # Create pending invitation for demonstration
        from app.models.invitation import OrgInvitation
        from sqlmodel import select as sa_select

        existing_invite = session.exec(
            sa_select(OrgInvitation).where(
                OrgInvitation.invited_email == "invited@example.com"
            )
        ).first()

        if not existing_invite:
            invitation_service.create_invitation(
                session,
                org_id=org.id,
                invited_email="invited@example.com",
                role=OrgRole.member,
                invited_by=admin.id,
            )
            print("Created pending invitation for: invited@example.com")

    print("Seed complete.")


if __name__ == "__main__":
    seed()
