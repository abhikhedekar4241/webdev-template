# Invitations Implementation Plan (Plan 4 of 6)

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Implement org invitations — create invite (owner/admin), list pending invites for current user, accept/decline with email guard — plus the invite email template, `InvitationCard` component, and the `/invitations` frontend page.

**Architecture:** Backend: single `OrgInvitation` SQLModel table; `InvitationService` owns all business logic; router reuses `get_current_user` and org membership checks from Plans 2-3. Frontend: TanStack Query handles list/accept/decline; `InvitationCard` is a self-contained card component rendered on the invitations page.

**Tech Stack:** SQLModel, Alembic, Jinja2 (email), Zustand 4, TanStack Query 5, shadcn/ui

**Prerequisite:** Plans 2 (Auth) and 3 (Orgs) must be complete.

---

## File Map

**Backend (new):**
- Create: `backend/app/models/invitation.py` — `OrgInvitation` + `InvitationStatus` enum
- Modify: `backend/app/models/__init__.py`
- Modify: `backend/alembic/env.py`
- Create: `backend/alembic/versions/<hash>_add_invitations.py`
- Create: `backend/app/services/invitations.py`
- Create: `backend/app/api/v1/invitations.py`
- Modify: `backend/app/main.py`
- Create: `backend/app/emails/templates/invite.html`
- Create: `backend/tests/test_invitations.py`
- Modify: `backend/tests/factories.py` — add `InvitationFactory`
- Modify: `backend/seed.py` — add pending invitation

**Frontend (new):**
- Create: `frontend/src/services/invitations.ts`
- Create: `frontend/src/queries/invitations.ts`
- Create: `frontend/src/components/shared/InvitationCard.tsx`
- Create: `frontend/src/app/invitations/page.tsx`

---

## Task 1: OrgInvitation Model + Migration

**Files:**
- Create: `backend/app/models/invitation.py`
- Modify: `backend/app/models/__init__.py`
- Modify: `backend/alembic/env.py`

- [ ] **Step 1: Create `backend/app/models/invitation.py`**

```python
import enum
import uuid
from datetime import datetime

from sqlmodel import Field, SQLModel

from app.models.org import OrgRole


class InvitationStatus(str, enum.Enum):
    pending = "pending"
    accepted = "accepted"
    declined = "declined"


class OrgInvitation(SQLModel, table=True):
    __tablename__ = "org_invitations"

    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    org_id: uuid.UUID = Field(foreign_key="organizations.id", index=True)
    invited_email: str = Field(index=True)
    role: OrgRole = Field(default=OrgRole.member)
    invited_by: uuid.UUID = Field(foreign_key="users.id")
    status: InvitationStatus = Field(default=InvitationStatus.pending)
    expires_at: datetime
    created_at: datetime = Field(default_factory=datetime.utcnow)
```

- [ ] **Step 2: Update `backend/app/models/__init__.py`**

```python
from app.models.user import User  # noqa: F401
from app.models.password_reset import PasswordResetToken  # noqa: F401
from app.models.org import Organization, OrgMembership, OrgRole  # noqa: F401
from app.models.invitation import InvitationStatus, OrgInvitation  # noqa: F401
```

- [ ] **Step 3: Update `backend/alembic/env.py` — add invitation model import**

Add after the org model import:

```python
from app.models.invitation import InvitationStatus, OrgInvitation  # noqa: F401
```

- [ ] **Step 4: Generate migration**

```bash
cd backend && alembic revision --autogenerate -m "add org invitations"
```

Expected: New file with `op.create_table("org_invitations", ...)`.

- [ ] **Step 5: Apply migration**

```bash
cd backend && alembic upgrade head
```

Expected: `Running upgrade  -> <hash>, add org invitations`

- [ ] **Step 6: Commit**

```bash
git add backend/app/models/invitation.py backend/app/models/__init__.py backend/alembic/
git commit -m "feat: add OrgInvitation SQLModel model with migration"
```

---

## Task 2: Invitation Service

**Files:**
- Create: `backend/app/services/invitations.py`
- Create: `backend/tests/test_invitation_service.py`

- [ ] **Step 1: Write the failing tests**

Create `backend/tests/test_invitation_service.py`:

```python
import uuid
from datetime import datetime, timedelta

import pytest

from app.models.invitation import InvitationStatus, OrgInvitation
from app.models.org import OrgMembership, OrgRole, Organization
from app.models.user import User
from app.services.auth import auth_service
from app.services.invitations import invitation_service
from app.services.orgs import org_service


@pytest.fixture(autouse=True)
def create_tables(session):
    User.__table__.create(session.get_bind(), checkfirst=True)
    Organization.__table__.create(session.get_bind(), checkfirst=True)
    OrgMembership.__table__.create(session.get_bind(), checkfirst=True)
    OrgInvitation.__table__.create(session.get_bind(), checkfirst=True)
    yield
    OrgInvitation.__table__.drop(session.get_bind())
    OrgMembership.__table__.drop(session.get_bind())
    Organization.__table__.drop(session.get_bind())
    User.__table__.drop(session.get_bind())


@pytest.fixture
def alice(session):
    return auth_service.create_user(
        session, email="alice@example.com", password="pass", full_name="Alice"
    )


@pytest.fixture
def org(session, alice):
    return org_service.create_org(
        session, name="Acme", slug="acme", created_by=alice.id
    )


def test_create_invitation(session, alice, org):
    inv = invitation_service.create_invitation(
        session,
        org_id=org.id,
        invited_email="newbie@example.com",
        role=OrgRole.member,
        invited_by=alice.id,
    )
    assert inv.org_id == org.id
    assert inv.invited_email == "newbie@example.com"
    assert inv.role == OrgRole.member
    assert inv.status == InvitationStatus.pending
    assert inv.expires_at > datetime.utcnow()


def test_list_pending_for_email(session, alice, org):
    invitation_service.create_invitation(
        session,
        org_id=org.id,
        invited_email="target@example.com",
        role=OrgRole.member,
        invited_by=alice.id,
    )
    result = invitation_service.list_pending_for_email(session, "target@example.com")
    assert len(result) == 1
    assert result[0].invited_email == "target@example.com"


def test_list_pending_for_email_excludes_non_pending(session, alice, org):
    inv = invitation_service.create_invitation(
        session,
        org_id=org.id,
        invited_email="target@example.com",
        role=OrgRole.member,
        invited_by=alice.id,
    )
    inv.status = InvitationStatus.accepted
    session.add(inv)
    session.commit()
    result = invitation_service.list_pending_for_email(session, "target@example.com")
    assert len(result) == 0


def test_accept_invitation(session, alice, org):
    bob = auth_service.create_user(
        session, email="bob@example.com", password="pass", full_name="Bob"
    )
    inv = invitation_service.create_invitation(
        session,
        org_id=org.id,
        invited_email=bob.email,
        role=OrgRole.member,
        invited_by=alice.id,
    )
    result = invitation_service.accept_invitation(session, invitation=inv, user=bob)
    assert result is True
    # Bob should now be a member
    membership = org_service.get_membership(session, org_id=org.id, user_id=bob.id)
    assert membership is not None
    assert membership.role == OrgRole.member
    session.refresh(inv)
    assert inv.status == InvitationStatus.accepted


def test_accept_invitation_wrong_email(session, alice, org):
    bob = auth_service.create_user(
        session, email="bob@example.com", password="pass", full_name="Bob"
    )
    inv = invitation_service.create_invitation(
        session,
        org_id=org.id,
        invited_email="other@example.com",
        role=OrgRole.member,
        invited_by=alice.id,
    )
    result = invitation_service.accept_invitation(session, invitation=inv, user=bob)
    assert result is False


def test_decline_invitation(session, alice, org):
    bob = auth_service.create_user(
        session, email="bob@example.com", password="pass", full_name="Bob"
    )
    inv = invitation_service.create_invitation(
        session,
        org_id=org.id,
        invited_email=bob.email,
        role=OrgRole.member,
        invited_by=alice.id,
    )
    result = invitation_service.decline_invitation(session, invitation=inv, user=bob)
    assert result is True
    session.refresh(inv)
    assert inv.status == InvitationStatus.declined


def test_decline_invitation_wrong_email(session, alice, org):
    bob = auth_service.create_user(
        session, email="bob@example.com", password="pass", full_name="Bob"
    )
    inv = invitation_service.create_invitation(
        session,
        org_id=org.id,
        invited_email="other@example.com",
        role=OrgRole.member,
        invited_by=alice.id,
    )
    result = invitation_service.decline_invitation(session, invitation=inv, user=bob)
    assert result is False
```

- [ ] **Step 2: Run tests to confirm they fail**

```bash
cd backend && pytest tests/test_invitation_service.py -v
```

Expected: `ImportError` — `app.services.invitations` does not exist yet.

- [ ] **Step 3: Create `backend/app/services/invitations.py`**

```python
import uuid
from datetime import datetime, timedelta

from sqlmodel import Session, select

from app.models.invitation import InvitationStatus, OrgInvitation
from app.models.org import OrgRole
from app.models.user import User
from app.services.base import CRUDBase
from app.services.orgs import org_service

INVITATION_TTL_DAYS = 7


class InvitationService(CRUDBase[OrgInvitation]):
    def create_invitation(
        self,
        session: Session,
        *,
        org_id: uuid.UUID,
        invited_email: str,
        role: OrgRole,
        invited_by: uuid.UUID,
    ) -> OrgInvitation:
        inv = OrgInvitation(
            org_id=org_id,
            invited_email=invited_email,
            role=role,
            invited_by=invited_by,
            expires_at=datetime.utcnow() + timedelta(days=INVITATION_TTL_DAYS),
        )
        session.add(inv)
        session.commit()
        session.refresh(inv)
        return inv

    def list_pending_for_email(
        self, session: Session, email: str
    ) -> list[OrgInvitation]:
        return list(
            session.exec(
                select(OrgInvitation)
                .where(OrgInvitation.invited_email == email)
                .where(OrgInvitation.status == InvitationStatus.pending)
            ).all()
        )

    def accept_invitation(
        self, session: Session, *, invitation: OrgInvitation, user: User
    ) -> bool:
        if invitation.invited_email != user.email:
            return False
        invitation.status = InvitationStatus.accepted
        session.add(invitation)
        org_service.add_member(
            session,
            org_id=invitation.org_id,
            user_id=user.id,
            role=invitation.role,
        )
        session.commit()
        return True

    def decline_invitation(
        self, session: Session, *, invitation: OrgInvitation, user: User
    ) -> bool:
        if invitation.invited_email != user.email:
            return False
        invitation.status = InvitationStatus.declined
        session.add(invitation)
        session.commit()
        return True


invitation_service = InvitationService(OrgInvitation)
```

- [ ] **Step 4: Run tests to confirm they pass**

```bash
cd backend && pytest tests/test_invitation_service.py -v
```

Expected: 8 passed.

- [ ] **Step 5: Commit**

```bash
git add backend/app/services/invitations.py backend/tests/test_invitation_service.py
git commit -m "feat: add InvitationService with create, list, accept, decline"
```

---

## Task 3: Invitation API + Email Template

**Files:**
- Create: `backend/app/api/v1/invitations.py`
- Modify: `backend/app/main.py`
- Create: `backend/app/emails/templates/invite.html`

- [ ] **Step 1: Create `backend/app/emails/templates/invite.html`**

```html
<!DOCTYPE html>
<html>
<head><meta charset="utf-8"><title>You're invited</title></head>
<body>
  <h1>You've been invited to join {{ org_name }}!</h1>
  <p>Hi there,</p>
  <p>
    <strong>{{ invited_by_name }}</strong> has invited you to join
    <strong>{{ org_name }}</strong> as a <strong>{{ role }}</strong>.
  </p>
  <p>
    <a href="{{ invitations_url }}">View your invitations</a>
  </p>
  <p>This invitation expires in 7 days.</p>
  <p>If you don't have an account yet, you'll be asked to sign up first.</p>
</body>
</html>
```

- [ ] **Step 2: Create `backend/app/api/v1/invitations.py`**

```python
import uuid
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, EmailStr
from sqlmodel import Session

from app.api.deps import get_current_user
from app.core.config import settings
from app.core.db import get_session
from app.models.invitation import OrgInvitation
from app.models.org import OrgRole
from app.models.user import User
from app.services.invitations import invitation_service
from app.services.orgs import org_service
from app.services.email import email_service

router = APIRouter(prefix="/api/v1/invitations", tags=["invitations"])


# --- Schemas ---

class InvitationCreate(BaseModel):
    org_id: uuid.UUID
    email: EmailStr
    role: OrgRole


class InvitationResponse(BaseModel):
    id: uuid.UUID
    org_id: uuid.UUID
    invited_email: str
    role: OrgRole
    status: str
    expires_at: datetime
    created_at: datetime


class MessageResponse(BaseModel):
    message: str


# --- Helpers ---

def _get_invitation_or_404(session: Session, inv_id: uuid.UUID) -> OrgInvitation:
    inv = session.get(OrgInvitation, inv_id)
    if not inv:
        raise HTTPException(status_code=404, detail="Invitation not found")
    return inv


# --- Endpoints ---

@router.post("/", response_model=InvitationResponse, status_code=201)
def create_invitation(
    body: InvitationCreate,
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user),
):
    # Only owner or admin of the org can invite
    membership = org_service.get_membership(
        session, org_id=body.org_id, user_id=current_user.id
    )
    if not membership or membership.role not in (OrgRole.owner, OrgRole.admin):
        raise HTTPException(status_code=403, detail="Insufficient permissions")

    org = session.get_one = session.get(
        __import__("app.models.org", fromlist=["Organization"]).Organization,
        body.org_id,
    )
    if not org:
        raise HTTPException(status_code=404, detail="Organization not found")

    inv = invitation_service.create_invitation(
        session,
        org_id=body.org_id,
        invited_email=body.email,
        role=body.role,
        invited_by=current_user.id,
    )

    email_service.send(
        to=body.email,
        subject=f"You've been invited to join {org.name}",
        template="invite",
        context={
            "org_name": org.name,
            "invited_by_name": current_user.full_name,
            "role": body.role.value,
            "invitations_url": f"{settings.FRONTEND_URL}/invitations",
        },
    )

    return inv


@router.get("/", response_model=list[InvitationResponse])
def list_invitations(
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user),
):
    return invitation_service.list_pending_for_email(session, current_user.email)


@router.post("/{inv_id}/accept", response_model=MessageResponse)
def accept_invitation(
    inv_id: uuid.UUID,
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user),
):
    inv = _get_invitation_or_404(session, inv_id)
    success = invitation_service.accept_invitation(
        session, invitation=inv, user=current_user
    )
    if not success:
        raise HTTPException(status_code=403, detail="This invitation is not for you")
    return {"message": "Invitation accepted"}


@router.post("/{inv_id}/decline", response_model=MessageResponse)
def decline_invitation(
    inv_id: uuid.UUID,
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user),
):
    inv = _get_invitation_or_404(session, inv_id)
    success = invitation_service.decline_invitation(
        session, invitation=inv, user=current_user
    )
    if not success:
        raise HTTPException(status_code=403, detail="This invitation is not for you")
    return {"message": "Invitation declined"}
```

- [ ] **Step 3: Fix the org import in `invitations.py` — replace the clunky import**

The `create_invitation` endpoint above has an ugly inline import. Replace the org lookup block with a clean import at the top of the file. Edit the file: add this import near the top with the other model imports:

```python
from app.models.org import Organization, OrgRole
```

And replace the session.get block:
```python
    org = session.get(Organization, body.org_id)
    if not org:
        raise HTTPException(status_code=404, detail="Organization not found")
```

The full `create_invitation` function after fix:

```python
@router.post("/", response_model=InvitationResponse, status_code=201)
def create_invitation(
    body: InvitationCreate,
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user),
):
    membership = org_service.get_membership(
        session, org_id=body.org_id, user_id=current_user.id
    )
    if not membership or membership.role not in (OrgRole.owner, OrgRole.admin):
        raise HTTPException(status_code=403, detail="Insufficient permissions")

    org = session.get(Organization, body.org_id)
    if not org:
        raise HTTPException(status_code=404, detail="Organization not found")

    inv = invitation_service.create_invitation(
        session,
        org_id=body.org_id,
        invited_email=body.email,
        role=body.role,
        invited_by=current_user.id,
    )

    email_service.send(
        to=body.email,
        subject=f"You've been invited to join {org.name}",
        template="invite",
        context={
            "org_name": org.name,
            "invited_by_name": current_user.full_name,
            "role": body.role.value,
            "invitations_url": f"{settings.FRONTEND_URL}/invitations",
        },
    )

    return inv
```

Write `backend/app/api/v1/invitations.py` from scratch with the correct clean version:

```python
import uuid
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, EmailStr
from sqlmodel import Session

from app.api.deps import get_current_user
from app.core.config import settings
from app.core.db import get_session
from app.models.invitation import OrgInvitation
from app.models.org import Organization, OrgRole
from app.models.user import User
from app.services.email import email_service
from app.services.invitations import invitation_service
from app.services.orgs import org_service

router = APIRouter(prefix="/api/v1/invitations", tags=["invitations"])


class InvitationCreate(BaseModel):
    org_id: uuid.UUID
    email: EmailStr
    role: OrgRole


class InvitationResponse(BaseModel):
    id: uuid.UUID
    org_id: uuid.UUID
    invited_email: str
    role: OrgRole
    status: str
    expires_at: datetime
    created_at: datetime


class MessageResponse(BaseModel):
    message: str


def _get_invitation_or_404(session: Session, inv_id: uuid.UUID) -> OrgInvitation:
    inv = session.get(OrgInvitation, inv_id)
    if not inv:
        raise HTTPException(status_code=404, detail="Invitation not found")
    return inv


@router.post("/", response_model=InvitationResponse, status_code=201)
def create_invitation(
    body: InvitationCreate,
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user),
):
    membership = org_service.get_membership(
        session, org_id=body.org_id, user_id=current_user.id
    )
    if not membership or membership.role not in (OrgRole.owner, OrgRole.admin):
        raise HTTPException(status_code=403, detail="Insufficient permissions")

    org = session.get(Organization, body.org_id)
    if not org:
        raise HTTPException(status_code=404, detail="Organization not found")

    inv = invitation_service.create_invitation(
        session,
        org_id=body.org_id,
        invited_email=body.email,
        role=body.role,
        invited_by=current_user.id,
    )

    email_service.send(
        to=body.email,
        subject=f"You've been invited to join {org.name}",
        template="invite",
        context={
            "org_name": org.name,
            "invited_by_name": current_user.full_name,
            "role": body.role.value,
            "invitations_url": f"{settings.FRONTEND_URL}/invitations",
        },
    )

    return inv


@router.get("/", response_model=list[InvitationResponse])
def list_invitations(
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user),
):
    return invitation_service.list_pending_for_email(session, current_user.email)


@router.post("/{inv_id}/accept", response_model=MessageResponse)
def accept_invitation(
    inv_id: uuid.UUID,
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user),
):
    inv = _get_invitation_or_404(session, inv_id)
    success = invitation_service.accept_invitation(
        session, invitation=inv, user=current_user
    )
    if not success:
        raise HTTPException(status_code=403, detail="This invitation is not for you")
    return {"message": "Invitation accepted"}


@router.post("/{inv_id}/decline", response_model=MessageResponse)
def decline_invitation(
    inv_id: uuid.UUID,
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user),
):
    inv = _get_invitation_or_404(session, inv_id)
    success = invitation_service.decline_invitation(
        session, invitation=inv, user=current_user
    )
    if not success:
        raise HTTPException(status_code=403, detail="This invitation is not for you")
    return {"message": "Invitation declined"}
```

- [ ] **Step 4: Update `backend/app/main.py` — include invitations router**

Add import and include:

```python
from app.api.v1 import auth, health, invitations, orgs
```

Add after orgs router inclusion:
```python
app.include_router(invitations.router)
```

Full router section:
```python
app.include_router(health.router, tags=["health"])
app.include_router(auth.router)
app.include_router(orgs.router)
app.include_router(invitations.router)
```

- [ ] **Step 5: Verify app starts**

```bash
cd backend && python -c "from app.main import app; print('OK')"
```

Expected: `OK`

- [ ] **Step 6: Commit**

```bash
git add backend/app/api/v1/invitations.py backend/app/main.py backend/app/emails/templates/invite.html
git commit -m "feat: add invitations API endpoints and invite email template"
```

---

## Task 4: Invitation HTTP Tests + Factory + Seed Update

**Files:**
- Create: `backend/tests/test_invitations.py`
- Modify: `backend/tests/factories.py`
- Modify: `backend/seed.py`

- [ ] **Step 1: Update `backend/tests/factories.py` — add InvitationFactory**

Append to the existing file:

```python
from datetime import datetime, timedelta

from app.models.invitation import InvitationStatus, OrgInvitation


class InvitationFactory(factory.Factory):
    class Meta:
        model = OrgInvitation

    id = factory.LazyFunction(uuid.uuid4)
    org_id = factory.LazyFunction(uuid.uuid4)
    invited_email = factory.Sequence(lambda n: f"invite{n}@example.com")
    role = OrgRole.member
    invited_by = factory.LazyFunction(uuid.uuid4)
    status = InvitationStatus.pending
    expires_at = factory.LazyFunction(lambda: datetime.utcnow() + timedelta(days=7))
    created_at = factory.LazyFunction(datetime.utcnow)
```

- [ ] **Step 2: Create `backend/tests/test_invitations.py`**

```python
import uuid

import pytest
from fastapi.testclient import TestClient

from app.core.security import create_access_token
from app.models.invitation import InvitationStatus, OrgInvitation
from app.models.org import OrgMembership, OrgRole, Organization
from app.models.user import User
from app.services.auth import auth_service
from app.services.invitations import invitation_service
from app.services.orgs import org_service


def auth_header(user_id: uuid.UUID) -> dict:
    token = create_access_token(subject=str(user_id))
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture
def alice(session):
    return auth_service.create_user(
        session, email="alice@example.com", password="pass", full_name="Alice"
    )


@pytest.fixture
def bob(session):
    return auth_service.create_user(
        session, email="bob@example.com", password="pass", full_name="Bob"
    )


@pytest.fixture
def org(session, alice):
    return org_service.create_org(
        session, name="Acme", slug="acme", created_by=alice.id
    )


# --- Create invitation ---

def test_create_invitation_as_owner(client: TestClient, alice, org):
    resp = client.post(
        "/api/v1/invitations/",
        json={
            "org_id": str(org.id),
            "email": "newbie@example.com",
            "role": "member",
        },
        headers=auth_header(alice.id),
    )
    assert resp.status_code == 201
    data = resp.json()
    assert data["invited_email"] == "newbie@example.com"
    assert data["status"] == "pending"


def test_create_invitation_as_non_member_returns_403(client: TestClient, bob, org):
    resp = client.post(
        "/api/v1/invitations/",
        json={
            "org_id": str(org.id),
            "email": "newbie@example.com",
            "role": "member",
        },
        headers=auth_header(bob.id),
    )
    assert resp.status_code == 403


def test_create_invitation_as_plain_member_returns_403(client: TestClient, bob, org, session):
    org_service.add_member(session, org_id=org.id, user_id=bob.id, role=OrgRole.member)
    resp = client.post(
        "/api/v1/invitations/",
        json={
            "org_id": str(org.id),
            "email": "newbie@example.com",
            "role": "member",
        },
        headers=auth_header(bob.id),
    )
    assert resp.status_code == 403


# --- List invitations ---

def test_list_invitations_returns_pending_for_current_user(
    client: TestClient, alice, bob, org, session
):
    invitation_service.create_invitation(
        session,
        org_id=org.id,
        invited_email=bob.email,
        role=OrgRole.member,
        invited_by=alice.id,
    )
    resp = client.get("/api/v1/invitations/", headers=auth_header(bob.id))
    assert resp.status_code == 200
    data = resp.json()
    assert len(data) == 1
    assert data[0]["invited_email"] == bob.email


def test_list_invitations_empty_for_no_pending(client: TestClient, alice):
    resp = client.get("/api/v1/invitations/", headers=auth_header(alice.id))
    assert resp.status_code == 200
    assert resp.json() == []


# --- Accept ---

def test_accept_invitation(client: TestClient, alice, bob, org, session):
    inv = invitation_service.create_invitation(
        session,
        org_id=org.id,
        invited_email=bob.email,
        role=OrgRole.member,
        invited_by=alice.id,
    )
    resp = client.post(
        f"/api/v1/invitations/{inv.id}/accept",
        headers=auth_header(bob.id),
    )
    assert resp.status_code == 200
    assert resp.json()["message"] == "Invitation accepted"
    # Bob is now a member
    membership = org_service.get_membership(session, org_id=org.id, user_id=bob.id)
    assert membership is not None


def test_accept_invitation_wrong_user_returns_403(
    client: TestClient, alice, bob, org, session
):
    carol = auth_service.create_user(
        session, email="carol@example.com", password="pass", full_name="Carol"
    )
    inv = invitation_service.create_invitation(
        session,
        org_id=org.id,
        invited_email="carol@example.com",
        role=OrgRole.member,
        invited_by=alice.id,
    )
    resp = client.post(
        f"/api/v1/invitations/{inv.id}/accept",
        headers=auth_header(bob.id),
    )
    assert resp.status_code == 403


# --- Decline ---

def test_decline_invitation(client: TestClient, alice, bob, org, session):
    inv = invitation_service.create_invitation(
        session,
        org_id=org.id,
        invited_email=bob.email,
        role=OrgRole.member,
        invited_by=alice.id,
    )
    resp = client.post(
        f"/api/v1/invitations/{inv.id}/decline",
        headers=auth_header(bob.id),
    )
    assert resp.status_code == 200
    assert resp.json()["message"] == "Invitation declined"
    session.refresh(inv)
    assert inv.status == InvitationStatus.declined


def test_accept_nonexistent_returns_404(client: TestClient, alice):
    resp = client.post(
        f"/api/v1/invitations/{uuid.uuid4()}/accept",
        headers=auth_header(alice.id),
    )
    assert resp.status_code == 404
```

- [ ] **Step 3: Run invitation tests**

```bash
cd backend && pytest tests/test_invitations.py -v
```

Expected: 10 tests, all passing.

- [ ] **Step 4: Run full test suite**

```bash
cd backend && pytest tests/ -v
```

Expected: All tests passing.

- [ ] **Step 5: Update `backend/seed.py` — add pending invitation**

Find the org creation block and append invitation seeding after it:

```python
        # Create pending invitation for demonstration
        from app.models.invitation import OrgInvitation, InvitationStatus
        from sqlmodel import select as sa_select

        existing_invite = session.exec(
            sa_select(OrgInvitation).where(
                OrgInvitation.invited_email == "invited@example.com"
            )
        ).first()

        if not existing_invite and not existing_org:
            invitation_service.create_invitation(
                session,
                org_id=org.id,
                invited_email="invited@example.com",
                role=OrgRole.member,
                invited_by=admin.id,
            )
            print("Created pending invitation for: invited@example.com")
```

Also add the import at the top of seed.py:

```python
from app.services.invitations import invitation_service
```

- [ ] **Step 6: Commit**

```bash
git add backend/tests/factories.py backend/tests/test_invitations.py backend/seed.py
git commit -m "feat: add invitation tests, update factories and seed with pending invitation"
```

---

## Task 5: Frontend — Invitation Service + Queries

**Files:**
- Create: `frontend/src/services/invitations.ts`
- Create: `frontend/src/queries/invitations.ts`

- [ ] **Step 1: Create `frontend/src/services/invitations.ts`**

```typescript
import api from "./api";

export interface InvitationData {
  id: string;
  org_id: string;
  invited_email: string;
  role: "owner" | "admin" | "member";
  status: "pending" | "accepted" | "declined";
  expires_at: string;
  created_at: string;
}

export const invitationsService = {
  list: () =>
    api.get<InvitationData[]>("/v1/invitations/").then((r) => r.data),

  create: (data: { org_id: string; email: string; role: string }) =>
    api.post<InvitationData>("/v1/invitations/", data).then((r) => r.data),

  accept: (invId: string) =>
    api
      .post<{ message: string }>(`/v1/invitations/${invId}/accept`)
      .then((r) => r.data),

  decline: (invId: string) =>
    api
      .post<{ message: string }>(`/v1/invitations/${invId}/decline`)
      .then((r) => r.data),
};
```

- [ ] **Step 2: Create `frontend/src/queries/invitations.ts`**

```typescript
"use client";

import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { toast } from "sonner";

import { QUERY_KEYS } from "@/constants/queryKeys";
import { invitationsService } from "@/services/invitations";

export function useInvitations() {
  return useQuery({
    queryKey: QUERY_KEYS.invitations.list,
    queryFn: invitationsService.list,
  });
}

export function useAcceptInvitation() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (invId: string) => invitationsService.accept(invId),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: QUERY_KEYS.invitations.list });
      queryClient.invalidateQueries({ queryKey: QUERY_KEYS.orgs.list });
      toast.success("Invitation accepted! You are now a member.");
    },
    onError: () => {
      toast.error("Failed to accept invitation");
    },
  });
}

export function useDeclineInvitation() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (invId: string) => invitationsService.decline(invId),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: QUERY_KEYS.invitations.list });
      toast.success("Invitation declined");
    },
    onError: () => {
      toast.error("Failed to decline invitation");
    },
  });
}

export function useCreateInvitation() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (data: { org_id: string; email: string; role: string }) =>
      invitationsService.create(data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: QUERY_KEYS.invitations.list });
      toast.success("Invitation sent");
    },
    onError: () => {
      toast.error("Failed to send invitation");
    },
  });
}
```

- [ ] **Step 3: Commit**

```bash
git add frontend/src/services/invitations.ts frontend/src/queries/invitations.ts
git commit -m "feat: add invitations service and TanStack Query hooks"
```

---

## Task 6: Frontend — InvitationCard + Invitations Page

**Files:**
- Create: `frontend/src/components/shared/InvitationCard.tsx`
- Create: `frontend/src/app/invitations/page.tsx`

- [ ] **Step 1: Create `frontend/src/components/shared/InvitationCard.tsx`**

```tsx
"use client";

import { Button } from "@/components/ui/button";
import { Card, CardContent, CardFooter } from "@/components/ui/card";
import { ROLE_LABELS } from "@/constants/roles";
import { useAcceptInvitation, useDeclineInvitation } from "@/queries/invitations";
import type { InvitationData } from "@/services/invitations";

interface InvitationCardProps {
  invitation: InvitationData;
}

export function InvitationCard({ invitation }: InvitationCardProps) {
  const { mutate: accept, isPending: isAccepting } = useAcceptInvitation();
  const { mutate: decline, isPending: isDeclining } = useDeclineInvitation();

  const isPending = isAccepting || isDeclining;

  return (
    <Card>
      <CardContent className="pt-4">
        <p className="font-medium">Organization invitation</p>
        <p className="text-sm text-muted-foreground mt-1">
          You have been invited as a{" "}
          <span className="font-medium">{ROLE_LABELS[invitation.role]}</span>.
        </p>
        <p className="text-xs text-muted-foreground mt-1">
          Expires {new Date(invitation.expires_at).toLocaleDateString()}
        </p>
      </CardContent>
      <CardFooter className="flex gap-2">
        <Button
          size="sm"
          disabled={isPending}
          onClick={() => accept(invitation.id)}
        >
          {isAccepting ? "Accepting…" : "Accept"}
        </Button>
        <Button
          size="sm"
          variant="outline"
          disabled={isPending}
          onClick={() => decline(invitation.id)}
        >
          {isDeclining ? "Declining…" : "Decline"}
        </Button>
      </CardFooter>
    </Card>
  );
}
```

- [ ] **Step 2: Create `frontend/src/app/invitations/page.tsx`**

```tsx
"use client";

import { InvitationCard } from "@/components/shared/InvitationCard";
import { useInvitations } from "@/queries/invitations";

export default function InvitationsPage() {
  const { data: invitations, isLoading } = useInvitations();

  return (
    <div className="mx-auto max-w-2xl p-8">
      <h1 className="mb-6 text-2xl font-bold">Pending Invitations</h1>

      {isLoading && <p className="text-muted-foreground">Loading…</p>}

      {!isLoading && (!invitations || invitations.length === 0) && (
        <p className="text-muted-foreground">No pending invitations.</p>
      )}

      <div className="space-y-4">
        {invitations?.map((inv) => (
          <InvitationCard key={inv.id} invitation={inv} />
        ))}
      </div>
    </div>
  );
}
```

- [ ] **Step 3: Commit**

```bash
git add frontend/src/components/shared/InvitationCard.tsx frontend/src/app/invitations/
git commit -m "feat: add InvitationCard component and invitations page"
```

---

## Self-Review Checklist

**Spec coverage:**
- [x] `POST /api/v1/invitations/` — create invite (owner/admin only)
- [x] `GET /api/v1/invitations/` — pending invitations for current user (matched by email)
- [x] `POST /api/v1/invitations/{id}/accept` — accept; 403 if email mismatch
- [x] `POST /api/v1/invitations/{id}/decline` — decline; same email guard
- [x] OrgInvitation model: id, org_id, invited_email, role, invited_by, status, expires_at, created_at
- [x] InvitationStatus enum: pending, accepted, declined
- [x] Invite email with link to `/invitations` (no token in URL)
- [x] TTL: 7 days
- [x] Seed: 1 pending invitation (invited@example.com)
- [x] Frontend: invitations service (list, create, accept, decline)
- [x] Frontend: TanStack Query hooks (useInvitations, useAcceptInvitation, useDeclineInvitation, useCreateInvitation)
- [x] Frontend: InvitationCard component (accept/decline buttons, role label, expiry)
- [x] Frontend: /invitations page showing all pending cards
- [x] Invitation flow: middleware redirects unauthenticated users to /auth/login?redirect=/invitations (already handled by existing middleware from Plan 2)
